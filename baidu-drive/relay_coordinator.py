#!/usr/bin/env python3
"""Serialized master scheduler for the Release-controlled Baidu -> Drive task."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
from typing import Any

import controller
import relay_control
import relay_state
import worker as checkpoint_worker


def _env_path(name: str) -> Path | None:
    value = os.environ.get(name, "").strip()
    return Path(value) if value else None


def prepare_inputs() -> tuple[Path | None, Path | None, Path | None, Path | None]:
    return (
        _env_path("BAIDU_DRIVE_BAIDU_AUTH_FILE"),
        _env_path("BAIDU_DRIVE_RCLONE_CONFIG_FILE"),
        _env_path("BAIDU_DRIVE_RCLONE_BIN"),
        _env_path("BAIDU_DRIVE_PREPARE_BIN"),
    )


def prepare_ready() -> bool:
    return all(path is not None and path.is_file() for path in prepare_inputs())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def prepare_command(
    task: dict[str, Any],
    work: Path,
    checkpoint: Path,
    result: Path,
    manifest: Path,
    verified: Path,
) -> list[str]:
    baidu_auth, rclone_config, rclone_bin, prepare_bin = prepare_inputs()
    assert baidu_auth is not None and rclone_config is not None and rclone_bin is not None and prepare_bin is not None
    command = [
        str(prepare_bin),
        "--runtime-base", str(work / "runtime"),
        "--state-db", str(checkpoint),
        "--baidu-cookie-file", str(baidu_auth),
        "--rclone-config-file", str(rclone_config),
        "--rclone-bin", str(rclone_bin),
        "--result-json", str(result),
        "--relay-manifest-json", str(manifest),
        "--relay-results-json", str(verified),
    ]
    mover_task = str(task.get("mover_task_id") or "").strip()
    if mover_task:
        command += ["--resume", mover_task]
    else:
        command += ["--share-url", str(task.get("source_url") or "")]
        code = str(task.get("extraction_code") or "")
        if code:
            command += ["--extraction-code", code]
    return command


def apply_prepare_projection(task: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(task)
    mover_task = str(result.get("mover_task_id") or "").strip()
    if mover_task:
        value["mover_task_id"] = mover_task
    drive_id = str(result.get("drive_root_id") or "").strip()
    if drive_id:
        value["drive_folder_id"] = drive_id
        value["drive_folder_url"] = f"https://drive.google.com/drive/folders/{drive_id}"
    progress = result.get("progress") or {}
    if isinstance(progress, dict):
        value["files_total"] = int(progress.get("files_total") or 0)
        value["bytes_total"] = int(progress.get("bytes_total") or 0)
    return value


def project_relay_progress(task: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    value = copy.deepcopy(task)
    aggregate = relay_state.aggregate(records)
    value["files_done"] = aggregate["files_verified"]
    value["bytes_done"] = aggregate["bytes_confirmed"]
    value["relay_active_workers"] = aggregate["active_workers"]
    return value


def complete_task(
    gh: controller.GitHub,
    runtime: dict[str, Any],
    task: dict[str, Any],
) -> None:
    task = copy.deepcopy(task)
    task["status"] = "COMPLETED"
    task["files_done"] = int(task.get("files_total") or 0)
    task["bytes_done"] = int(task.get("bytes_total") or 0)
    task["message"] = "Transfer completed, Drive verification passed, and tool-owned Baidu staging cleanup finished."
    task = controller.save_task(gh, task, "relay-complete")
    new_runtime = copy.deepcopy(runtime)
    new_runtime["active_task"] = None
    new_runtime["last_task"] = task["id"]
    new_runtime = controller.save_runtime_if_changed(gh, runtime, new_runtime, "relay-complete")
    release = gh.ensure_release()
    gh.patch_release(
        release,
        controller.render_release(controller.default_control(), new_runtime, task, "COMPLETED", task["message"]),
    )


def run_coordinator(gh: controller.GitHub, requested_task: str | None) -> int:
    runtime, _ = gh.read_json(controller.RUNTIME_PATH, default=controller.DEFAULT_RUNTIME)
    task_id = (requested_task or "").strip() or str(runtime.get("active_task") or "").strip()
    if not task_id or runtime.get("active_task") != task_id:
        return 0
    task = controller.load_task(gh, task_id)
    if not task or str(task.get("status") or "") in controller.TERMINAL_STATES:
        return 0

    if not prepare_ready():
        checkpoint_worker.update_public_state(
            gh,
            runtime,
            task,
            reason="relay-auth-setup-block",
            status="BLOCKED_AUTH_SETUP",
            message="Relay scheduler is ready, but ephemeral authentication provisioning is not configured yet.",
        )
        return 0

    repo = relay_control.GitHubRepo(os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", ""))
    work = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / f"baidu-drive-scheduler-{task_id}"
    work.mkdir(parents=True, exist_ok=True)
    checkpoint = work / "state.db"
    result_path = work / "prepare-result.json"
    manifest_path = work / "relay-manifest.json"
    verified_path = work / "verified-results.json"
    checkpoint_worker.restore_checkpoint(gh, task_id, checkpoint)

    existing_records = repo.list_records(task_id)
    write_json(verified_path, relay_control.verified_results(existing_records))
    task = checkpoint_worker.update_public_state(
        gh,
        runtime,
        task,
        reason="relay-scheduler-start",
        status="RUNNING",
        message="Scheduler is reconciling remote state and assigning independent file workers.",
    )

    completed = subprocess.run(
        prepare_command(task, work, checkpoint, result_path, manifest_path, verified_path),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    checkpoint_worker.persist_checkpoint(gh, task_id, checkpoint)

    try:
        result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else {}
    except (OSError, ValueError):
        result = {}
    if not isinstance(result, dict):
        result = {}
    task = apply_prepare_projection(task, result)

    if completed.returncode != 0:
        task["status"] = "BLOCKED"
        task["message"] = "Scheduler preparation stopped safely; the durable checkpoint was preserved."
        task = controller.save_task(gh, task, "relay-prepare-block")
        release = gh.ensure_release()
        gh.patch_release(
            release,
            controller.render_release(controller.default_control(), runtime, task, task["status"], task["message"]),
        )
        return 0

    if str(result.get("status") or "").upper() == "COMPLETED":
        complete_task(gh, runtime, task)
        return 0

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else []
    except (OSError, ValueError) as exc:
        raise controller.ProtocolError(f"relay preparation returned an invalid manifest: {exc}") from None
    if not isinstance(manifest, list):
        raise controller.ProtocolError("relay preparation manifest is not a list")
    if not manifest:
        task["status"] = "BLOCKED"
        task["message"] = "Scheduler found no runnable relay batch after preparation."
        task = controller.save_task(gh, task, "relay-empty-block")
        release = gh.ensure_release()
        gh.patch_release(
            release,
            controller.render_release(controller.default_control(), runtime, task, task["status"], task["message"]),
        )
        return 0

    relay_control.sync_manifest(repo, task_id, manifest, relay_control.utc_now())
    dispatched = relay_control.schedule_once(
        repo,
        task_id,
        relay_control.utc_now(),
        os.environ.get("GITHUB_RUN_ID", "local"),
    )
    records = repo.list_records(task_id)
    task = project_relay_progress(task, records)
    permanent = sum(1 for record in records if record.get("status") == relay_state.FAILED_PERMANENT)
    if permanent:
        task["status"] = "BLOCKED"
        task["message"] = f"Scheduler is blocked by {permanent} permanently failed relay file(s); no unsafe replay was attempted."
    else:
        task["status"] = "RUNNING"
        task["message"] = (
            f"Scheduler active: {len(dispatched)} new worker(s) dispatched; "
            f"{task.get('relay_active_workers', 0)} file worker(s) active."
        )
    task = controller.save_task(gh, task, "relay-schedule")
    release = gh.ensure_release()
    gh.patch_release(
        release,
        controller.render_release(controller.default_control(), runtime, task, task["status"], task["message"]),
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", default="")
    args = parser.parse_args(argv)
    gh = controller.GitHub(os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", ""))
    return run_coordinator(gh, args.task_id)


if __name__ == "__main__":
    raise SystemExit(main())
