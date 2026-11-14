#!/usr/bin/env python3
"""One Quark provider-preparation pass under the global three-worker master."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
from pathlib import Path

import api
import auth_session
import controller
import drive
import relay_control
import relay_state
import scheduler

SOURCE_ROOT = "quark-drive/state/sources"
CLEANUP_ROOT = "quark-drive/state/cleanup"
STAGING_ROOT = "QuarkDriveMover"
BUFFER_BYTES = 100 << 20


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def source_id(file: api.ShareFile) -> str:
    text = f"{file.fid}\n{file.relative_path}\n{file.size}"
    return hashlib.sha256(text.encode()).hexdigest()[:20]


def snapshot(files: list[api.ShareFile]) -> list[dict]:
    return [{
        "file_id": source_id(file), "source_fid": file.fid,
        "name": file.name, "size": file.size,
        "relative_path": file.relative_path,
        "parent_path": file.relative_path.rpartition("/")[0],
    } for file in files]


def stage_one(client: api.Client, share_id: str, token: str,
              file: api.ShareFile, parent_fid: str) -> str:
    # Isolated per-file staging means retries cannot mix files from a user's drive.
    existing = [i for i in client.list_folder(parent_fid)
                if not i.get("dir") and i.get("file_name") == file.name and int(i.get("size") or 0) == file.size]
    if len(existing) > 1:
        raise api.QuarkProviderError("Ambiguous tool-owned staged file")
    if existing:
        return str(existing[0]["fid"])
    task_id = client.submit_save(share_id, token, file, parent_fid)
    return client.poll_save(task_id)


def clean_verified(client: api.Client, gh: controller.GitHub, task_id: str,
                   records: list[dict]) -> set[str]:
    path = f"{CLEANUP_ROOT}/{task_id}.json"
    state, _ = gh.read_json(path, default={"schema": 1, "files": []})
    done = set(state["files"])
    for record in records:
        if record.get("status") != relay_state.VERIFIED or record["file_id"] in done:
            continue
        # Only delete the fid recorded under this task's own staging folder,
        # and only after the worker independently verified Google Drive MD5.
        client.delete_staged([record["quark_fid"]])
        done.add(record["file_id"])
        gh.write_json(path, {"schema": 1, "files": sorted(done)},
                      f"quark-drive: confirm cleaned verified {record['file_id']}")
    return done


def run(gh: controller.GitHub, repo: relay_control.GitHubRepo,
        task_id: str, reason: str, client: api.Client, folders: drive.DriveFolders,
        cap: int) -> int:
    runtime, _ = gh.read_json(controller.RUNTIME_PATH, default=controller.DEFAULT_RUNTIME)
    if runtime.get("active_task") != task_id:
        return 0
    task = controller.load_task(gh, task_id)
    if not task or task.get("status") in {"CANCELED", "COMPLETED"}:
        return 0
    if task.get("status") == "NEEDS_LOGIN" and reason != "auth-updated":
        return 0
    if reason not in {"auth-updated", "retry"}:
        expired = any(
            record.get("status") == relay_state.FAILED_RETRYABLE
            and "authentication is unavailable or expired" in str(record.get("last_error") or "").lower()
            for record in repo.list_records(task_id)
        )
        if expired:
            task["status"] = "NEEDS_LOGIN"
            task["message"] = "Quark or Google authorization expired. Run local authorization helper."
            controller.save_task(gh, task, "expired-auth")
            return 0

    share_id, url_code = api.parse_share_url(task["source_url"])
    token = client.share_token(share_id, task.get("extraction_code") or url_code)
    scanned = client.scan(share_id, token)
    current_files = {source_id(file): file for file in scanned}
    path = f"{SOURCE_ROOT}/{task_id}.json"
    stored, _ = gh.read_json(path, default={})
    if not stored:
        files = snapshot(scanned)
        gh.write_json(path, {"schema":1,"files":files}, "quark-drive: snapshot public source file identities")
    else:
        files = stored["files"]
    task["files_total"] = len(files)
    task["bytes_total"] = sum(int(f["size"]) for f in files)

    root_id = folders.folder("root", f"{STAGING_ROOT}-{task_id}")
    task["drive_folder_id"] = root_id
    task["drive_folder_url"] = f"https://drive.google.com/drive/folders/{root_id}"
    quark_root = client.ensure_folder("0", STAGING_ROOT)
    quark_task = client.ensure_folder(quark_root, task_id)

    records = repo.list_records(task_id)
    cleaned = clean_verified(client, gh, task_id, records)
    existing = {r["file_id"] for r in records}
    pending = sum(r.get("status") != relay_state.VERIFIED for r in records)
    available = client.space_available() - BUFFER_BYTES
    for entry in files:
        if pending >= cap:
            break
        key = entry["file_id"]
        if key in existing:
            continue
        file = current_files.get(key)
        if file is None:
            raise api.QuarkTemporaryError("Source file became temporarily unavailable")
        if file.size > available:
            continue
        staging_folder = client.ensure_folder(quark_task, key)
        quark_fid = stage_one(client, share_id, token, file, staging_folder)
        drive_parent = folders.parent_path(root_id, entry["parent_path"])
        repo.ensure_record(task_id, {
            "file_id":key, "batch_id":key,
            "logical_path":"/"+entry["relative_path"],
            "parent_path":"/"+entry["parent_path"],
            "name":entry["name"], "size":entry["size"], "md5":"",
            "quark_fid":quark_fid, "drive_parent_id":drive_parent,
        },now())
        existing.add(key)
        available -= file.size
        pending += 1

    records = repo.list_records(task_id)
    progress = relay_state.aggregate(records)
    task["bytes_done"] = progress["bytes_confirmed"]
    task["files_done"] = progress["files_verified"]
    task["relay_active_workers"] = progress["active_workers"]
    if files and len(cleaned) == len(files) and all(r["status"] == relay_state.VERIFIED for r in records):
        task["status"] = "COMPLETED"
        task["message"] = "All Quark files verified on Drive; task-owned staging cleaned."
        previous_runtime = dict(runtime)
        runtime["active_task"] = None
        runtime["last_task"] = task_id
        controller.save_runtime_if_changed(gh, previous_runtime, runtime, "complete")
    else:
        task["status"] = "RUNNING"
        task["message"] = f"Shared supervisor: {progress['active_workers']} active file workers."
    if task["status"] == "RUNNING":
        dispatched = relay_control.schedule_once(repo, task_id, now(), os.environ.get("GITHUB_RUN_ID", "quark-prepare"),
                                                    policy=scheduler.Policy(max_workers=cap))
        task["message"] = f"Shared supervisor: {len(dispatched)} new, {task['relay_active_workers']} prior active."
        records = repo.list_records(task_id)
        progress = relay_state.aggregate(records)
        task["relay_active_workers"] = progress["active_workers"]
    task = controller.save_task(gh, task, "prepare")
    release = gh.ensure_release()
    gh.patch_release(release, controller.render_release(controller.default_control(), runtime, task, task["status"],task["message"]))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id",default="")
    parser.add_argument("--reason",default="shared-supervisor")
    args=parser.parse_args()
    gh=controller.GitHub(os.environ["GITHUB_REPOSITORY"],os.environ["GITHUB_TOKEN"])
    repo=relay_control.GitHubRepo(os.environ["GITHUB_REPOSITORY"],os.environ["GITHUB_TOKEN"])
    runtime,_=gh.read_json(controller.RUNTIME_PATH, default=controller.DEFAULT_RUNTIME)
    task_id=args.task_id or str(runtime.get("active_task") or "")
    if not task_id: return 0
    cookie_path = os.environ.get("QUARK_DRIVE_QUARK_AUTH_FILE")
    access_path = os.environ.get("QUARK_DRIVE_GOOGLE_ACCESS_TOKEN_FILE")
    if not cookie_path or not access_path:
        task = controller.load_task(gh, task_id)
        task["status"] = "NEEDS_LOGIN"
        task["message"] = "Quark or Google login required. Run the local authorization helper."
        controller.save_task(gh, task, "login-required")
        release = gh.ensure_release()
        gh.patch_release(release, controller.render_release(controller.default_control(), runtime, task, "NEEDS_LOGIN", task["message"]))
        return 0
    cookie = Path(cookie_path).read_text(encoding="utf-8")
    access = Path(access_path).read_text(encoding="utf-8").strip()
    client=api.Client(cookie)
    folders=drive.DriveFolders(access)
    try:
        return run(gh,repo,task_id,args.reason,client,folders,int(os.environ.get("CLOUD_DRIVE_MAX_WORKERS","3")))
    except api.QuarkAuthRequired:
        task=controller.load_task(gh,task_id)
        task["status"]="NEEDS_LOGIN"
        task["message"]="Quark browser login expired. Run the local authorization helper."
        controller.save_task(gh,task,"login-required")
        release=gh.ensure_release()
        gh.patch_release(release, controller.render_release(controller.default_control(),runtime,task,"NEEDS_LOGIN",task["message"]))
        return 0
    finally:
        auth_session.save_if_changed(gh,os.environ["QUARK_DRIVE_QUARK_SESSION"],os.environ["QUARK_DRIVE_STATE_KEY"],client.cookie)


if __name__=="__main__":
    raise SystemExit(main())
