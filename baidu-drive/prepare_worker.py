#!/usr/bin/env python3
"""Serialized master scheduler for the direct Baidu -> Drive relay data plane.

This is the only global scheduling brain below the Release control plane. It
owns the shared SQLite checkpoint, safe staging/cleanup, and file-worker slot
assignment. File workers never choose their own work.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
from typing import Any

import controller
import relay_control
import relay_state
import scheduler
import worker as legacy_worker

RUNNABLE_TASK_STATES = {
    "BLOCKED_AUTH_SETUP",
    "BLOCKED",
    "PAUSED",
    "FAILED_RETRYABLE",
    "RUNNING",
}


class PrepareWorkerError(RuntimeError):
    pass


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def prepare_binary() -> Path | None:
    raw = os.environ.get("BAIDU_DRIVE_PREPARE_BIN", "").strip()
    return Path(raw) if raw else None


def prepare_ready() -> bool:
    binary = prepare_binary()
    return legacy_worker.auth_ready() and binary is not None and binary.is_file()


def parse_json_file(path: Path, default: Any) -> Any:
    if not path.is_file():
        return copy.deepcopy(default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PrepareWorkerError(f"invalid runner-local result file: {path.name}") from exc


def write_verified_results(repo: relay_control.GitHubRepo, task_id: str, path: Path) -> None:
    values = relay_control.verified_results(repo.list_records(task_id))
    path.write_text(json.dumps(values, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def prepare_command(
    task: dict[str, Any],
    binary: Path,
    work: Path,
    checkpoint: Path,
    result_path: Path,
    manifest_path: Path,
    verified_path: Path,
) -> list[str]:
    baidu_auth, rclone_config, rclone_bin = legacy_worker.auth_inputs()
    assert baidu_auth is not None and rclone_config is not None and rclone_bin is not None
    command = [
        str(binary),
        "--runtime-base", str(work / "runtime"),
        "--state-db", str(checkpoint),
        "--baidu-cookie-file", str(baidu_auth),
        "--rclone-config-file", str(rclone_config),
        "--rclone-bin", str(rclone_bin),
        "--result-json", str(result_path),
        "--relay-manifest-json", str(manifest_path),
        "--relay-results-json", str(verified_path),
        "--stage-window-bytes", os.environ.get("BAIDU_DRIVE_STAGE_WINDOW_BYTES", str(8 << 30)),
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


def apply_prepare_result(task: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(task)
    mover_task = str(result.get("mover_task_id") or "").strip()
    if mover_task:
        value["mover_task_id"] = mover_task
    progress = result.get("progress") or {}
    if isinstance(progress, dict):
        for key in ("files_total", "bytes_total"):
            if key in progress:
                value[key] = max(0, int(progress.get(key) or 0))
    drive_id = str(result.get("drive_root_id") or "").strip()
    if drive_id:
        value["drive_folder_id"] = drive_id
        value["drive_folder_url"] = f"https://drive.google.com/drive/folders/{drive_id}"
    return value


def merge_relay_progress(task: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Project current remote-confirmed relay truth, even when it moves backward."""
    value = copy.deepcopy(task)
    aggregate = relay_state.aggregate(records)
    value["files_done"] = aggregate["files_verified"]
    value["bytes_done"] = aggregate["bytes_confirmed"]
    value["relay_active_workers"] = aggregate["active_workers"]
    return value


def render_and_save(
    gh: controller.GitHub,
    runtime: dict[str, Any],
    task: dict[str, Any],
    *,
    reason: str,
    status: str,
    message: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    value = copy.deepcopy(task)
    value["status"] = status
    value["message"] = message[:300]
    value = controller.save_task(gh, value, reason)
    next_runtime = copy.deepcopy(runtime)
    if status == "COMPLETED":
        next_runtime["active_task"] = None
        next_runtime["last_task"] = value["id"]
    next_runtime = controller.save_runtime_if_changed(gh, runtime, next_runtime, reason)
    release = gh.ensure_release()
    gh.patch_release(
        release,
        controller.render_release(
            controller.default_control(),
            next_runtime,
            value,
            status,
            message,
        ),
    )
    return next_runtime, value


def schedule_projection(
    task: dict[str, Any],
    records: list[dict[str, Any]],
    dispatched: list[tuple[str, str]],
    now: dt.datetime,
) -> tuple[str, str]:
    active = sum(1 for record in records if scheduler.is_active(record, now))
    blocked_reconcile = sum(1 for record in records if record.get("status") == relay_state.BLOCKED_RECONCILE)
    permanent = sum(1 for record in records if record.get("status") == relay_state.FAILED_PERMANENT)
    runnable = sum(1 for record in records if scheduler.is_runnable(record, now))

    if not dispatched and active == 0 and runnable == 0 and (blocked_reconcile or permanent):
        parts = []
        if blocked_reconcile:
            parts.append(f"{blocked_reconcile} file(s) require Drive destination reconciliation")
        if permanent:
            parts.append(f"{permanent} file(s) failed permanently")
        return "BLOCKED", "; ".join(parts) + ". No unsafe replay was attempted."

    detail = f"{len(dispatched)} new worker(s) dispatched; {active} worker(s) active"
    if blocked_reconcile:
        detail += f"; {blocked_reconcile} file(s) awaiting reconciliation"
    if permanent:
        detail += f"; {permanent} permanent failure(s)"
    return "RUNNING", "Scheduler active: " + detail + "."


def run_prepare_worker(
    gh: controller.GitHub,
    relay_repo: relay_control.GitHubRepo,
    requested_task: str | None,
    reason: str,
) -> int:
    runtime, _ = gh.read_json(controller.RUNTIME_PATH, default=controller.DEFAULT_RUNTIME)
    task_id = (requested_task or "").strip() or str(runtime.get("active_task") or "").strip()
    if not task_id:
        return 0
    task = controller.load_task(gh, task_id)
    if not task or runtime.get("active_task") != task_id:
        return 0
    if str(task.get("status") or "") == "COMPLETED":
        return 0
    if str(task.get("status") or "") not in RUNNABLE_TASK_STATES:
        return 0

    if not prepare_ready():
        legacy_worker.update_public_state(
            gh,
            runtime,
            task,
            reason="relay-auth-setup-block",
            status="BLOCKED_AUTH_SETUP",
            message="Relay scheduler is ready, but ephemeral authentication inputs are not configured yet.",
        )
        return 0

    binary = prepare_binary()
    assert binary is not None
    work = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / f"baidu-drive-prepare-{task_id}"
    work.mkdir(parents=True, exist_ok=True)
    checkpoint = work / "state.db"
    result_path = work / "result.json"
    manifest_path = work / "relay-manifest.json"
    verified_path = work / "verified-results.json"
    legacy_worker.restore_checkpoint(gh, task_id, checkpoint)
    write_verified_results(relay_repo, task_id, verified_path)

    task = legacy_worker.update_public_state(
        gh,
        runtime,
        task,
        reason="relay-prepare-start",
        status="RUNNING",
        message="Scheduler is reconciling verified results and the next bounded staging batch.",
    )
    proc = subprocess.run(
        prepare_command(task, binary, work, checkpoint, result_path, manifest_path, verified_path),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    legacy_worker.persist_checkpoint(gh, task_id, checkpoint)
    result = parse_json_file(result_path, {})
    if not isinstance(result, dict):
        result = {}
    task = apply_prepare_result(task, result)

    if proc.returncode != 0:
        render_and_save(
            gh,
            runtime,
            task,
            reason="relay-prepare-blocked",
            status="BLOCKED",
            message="Scheduler preparation stopped safely at a durable checkpoint.",
        )
        return 0

    manifest = parse_json_file(manifest_path, [])
    if not isinstance(manifest, list):
        raise PrepareWorkerError("relay manifest is not a list")
    relay_control.sync_manifest(relay_repo, task_id, manifest, utc_now())
    records = relay_repo.list_records(task_id)
    task = merge_relay_progress(task, records)

    if str(result.get("status") or "").upper() == "COMPLETED":
        task["files_done"] = int(task.get("files_total") or task.get("files_done") or 0)
        task["bytes_done"] = int(task.get("bytes_total") or task.get("bytes_done") or 0)
        render_and_save(
            gh,
            runtime,
            task,
            reason="relay-complete",
            status="COMPLETED",
            message="Transfer completed, independently verified on Drive, and tool-owned Baidu staging was cleaned.",
        )
        return 0

    if not manifest:
        render_and_save(
            gh,
            runtime,
            task,
            reason="relay-empty-manifest-block",
            status="BLOCKED",
            message="Scheduler found no staged relay files before task completion.",
        )
        return 0

    now = utc_now()
    dispatched = relay_control.schedule_once(
        relay_repo,
        task_id,
        now,
        os.environ.get("GITHUB_RUN_ID", "prepare"),
    )
    records = relay_repo.list_records(task_id)
    task = merge_relay_progress(task, records)
    status, message = schedule_projection(task, records, dispatched, now)
    render_and_save(
        gh,
        runtime,
        task,
        reason="relay-schedule",
        status=status,
        message=message,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", default="")
    parser.add_argument("--reason", default="manual")
    args = parser.parse_args(argv)
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    gh = controller.GitHub(repository, token)
    relay_repo = relay_control.GitHubRepo(repository, token)
    try:
        return run_prepare_worker(gh, relay_repo, args.task_id, args.reason)
    except (PrepareWorkerError, controller.ProtocolError, relay_control.ControlError, relay_state.RelayStateError) as exc:
        print(f"relay scheduler stopped safely: {str(exc)[:300]}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
