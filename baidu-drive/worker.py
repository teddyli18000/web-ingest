#!/usr/bin/env python3
"""Actions worker/state adapter for the Release-controlled Baidu Drive task.

The worker owns only non-secret durable state. Authentication files are supplied
by the workflow in the ephemeral runner filesystem. Until that provisioning is
configured, the worker exits successfully in BLOCKED_AUTH_SETUP.
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import zlib
from typing import Any

import controller

CHECKPOINT_DIR = "baidu-drive/state/checkpoints"
RUNNABLE_STATES = {"BLOCKED_AUTH_SETUP", "BLOCKED", "PAUSED", "FAILED_RETRYABLE"}


def checkpoint_path(task_id: str) -> str:
    controller.task_path(task_id)  # validates the opaque task id
    return f"{CHECKPOINT_DIR}/{task_id}.sqlite.zlib.b64"


def read_text(gh: controller.GitHub, path: str) -> tuple[str | None, str | None]:
    url = f"{gh.api}/contents/{urllib.parse.quote(path, safe='/')}?ref=main"
    req = urllib.request.Request(url, headers=gh.headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            item = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, None
        raise controller.ProtocolError(f"GitHub contents read failed for {path}: HTTP {exc.code}") from None
    raw = base64.b64decode(item["content"])
    return raw.decode("utf-8"), item.get("sha")


def write_text(gh: controller.GitHub, path: str, text: str, message: str) -> None:
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    for attempt in range(3):
        _, sha = read_text(gh, path)
        body: dict[str, Any] = {"message": message, "content": encoded, "branch": "main"}
        if sha:
            body["sha"] = sha
        try:
            gh.request("PUT", f"{gh.api}/contents/{urllib.parse.quote(path, safe='/')}", obj=body)
            return
        except controller.ProtocolError as exc:
            if attempt == 2 or not any(code in str(exc) for code in ("HTTP 409", "HTTP 422")):
                raise
    raise controller.ProtocolError(f"failed to write {path}")


def restore_checkpoint(gh: controller.GitHub, task_id: str, out: Path) -> bool:
    text, _ = read_text(gh, checkpoint_path(task_id))
    if text is None:
        return False
    try:
        packed = base64.b64decode(text.strip(), validate=True)
        raw = zlib.decompress(packed)
    except (ValueError, zlib.error) as exc:
        raise controller.ProtocolError("stored mover checkpoint is invalid") from exc
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    os.chmod(out, 0o600)
    return True


def persist_checkpoint(gh: controller.GitHub, task_id: str, source: Path) -> None:
    if not source.is_file():
        return
    packed = zlib.compress(source.read_bytes(), level=9)
    text = base64.b64encode(packed).decode("ascii") + "\n"
    write_text(gh, checkpoint_path(task_id), text, f"baidu-drive: checkpoint {task_id}")


def auth_inputs() -> tuple[Path | None, Path | None, Path | None]:
    def path(name: str) -> Path | None:
        value = os.environ.get(name, "").strip()
        return Path(value) if value else None

    return path("BAIDU_DRIVE_BAIDU_AUTH_FILE"), path("BAIDU_DRIVE_RCLONE_CONFIG_FILE"), path("BAIDU_DRIVE_RCLONE_BIN")


def auth_ready() -> bool:
    return all(item is not None and item.is_file() for item in auth_inputs())


def update_public_state(
    gh: controller.GitHub,
    runtime: dict[str, Any],
    task: dict[str, Any],
    *,
    reason: str,
    status: str | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    value = copy.deepcopy(task)
    if status is not None:
        value["status"] = status
    if message is not None:
        value["message"] = message[:300]
    value = controller.save_task(gh, value, reason)
    release = gh.ensure_release()
    gh.patch_release(
        release,
        controller.render_release(
            controller.default_control(), runtime, value,
            str(value.get("status") or "UNKNOWN"), str(value.get("message") or "-"),
        ),
    )
    return value


def bridge_command(task: dict[str, Any], bridge: Path, work: Path, checkpoint: Path, result: Path) -> list[str]:
    baidu_auth, rclone_config, rclone_bin = auth_inputs()
    assert baidu_auth is not None and rclone_config is not None and rclone_bin is not None
    command = [
        str(bridge),
        "--runtime-base", str(work / "runtime"),
        "--state-db", str(checkpoint),
        "--baidu-cookie-file", str(baidu_auth),
        "--rclone-config-file", str(rclone_config),
        "--rclone-bin", str(rclone_bin),
        "--result-json", str(result),
        "--max-cache-bytes", os.environ.get("BAIDU_DRIVE_MAX_CACHE_BYTES", str(6 << 30)),
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


def map_result(task: dict[str, Any], result: dict[str, Any], returncode: int) -> tuple[dict[str, Any], str]:
    value = copy.deepcopy(task)
    mover_task = str(result.get("mover_task_id") or "").strip()
    if mover_task:
        value["mover_task_id"] = mover_task
    progress = result.get("progress") or {}
    for key in ("files_total", "files_done", "bytes_total", "bytes_done"):
        value[key] = int(progress.get(key) or 0)
    drive_id = str(result.get("drive_root_id") or "").strip()
    if drive_id:
        value["drive_folder_id"] = drive_id
        value["drive_folder_url"] = f"https://drive.google.com/drive/folders/{drive_id}"

    mover_status = str(result.get("status") or "").upper()
    paused = bool(result.get("pipeline_paused"))
    if mover_status == "COMPLETED":
        value["status"] = "COMPLETED"
        message = "Transfer completed, independently verified on Drive, and tool-owned staging cleanup finished."
    elif paused or mover_status == "PAUSED":
        value["status"] = "PAUSED"
        message = "Transfer paused at a durable checkpoint and can be retried safely."
    elif mover_status in {"BLOCKED", "AUTH_REQUIRED"}:
        value["status"] = "BLOCKED"
        message = "Transfer is blocked at a durable checkpoint; retry after the reported operational issue is resolved."
    elif returncode != 0:
        value["status"] = "BLOCKED"
        message = "Transfer worker stopped safely. The durable checkpoint was preserved; inspect the Action run before retrying."
    else:
        value["status"] = "PAUSED"
        message = "Transfer pass ended without completion; the durable checkpoint was preserved."
    value["message"] = message
    return value, message


def run_worker(gh: controller.GitHub, requested_task: str | None) -> int:
    runtime, _ = gh.read_json(controller.RUNTIME_PATH, default=controller.DEFAULT_RUNTIME)
    task_id = (requested_task or "").strip() or str(runtime.get("active_task") or "").strip()
    if not task_id:
        return 0
    task = controller.load_task(gh, task_id)
    if not task:
        return 0
    if runtime.get("active_task") != task_id:
        return 0
    if str(task.get("status")) not in RUNNABLE_STATES:
        return 0

    if not auth_ready():
        update_public_state(
            gh, runtime, task,
            reason="auth-setup-block",
            status="BLOCKED_AUTH_SETUP",
            message="Transfer worker is ready, but ephemeral authentication inputs are not configured yet.",
        )
        return 0

    bridge_value = os.environ.get("BAIDU_DRIVE_BRIDGE_BIN", "").strip()
    bridge = Path(bridge_value) if bridge_value else None
    if bridge is None or not bridge.is_file():
        update_public_state(
            gh, runtime, task,
            reason="bridge-block",
            status="BLOCKED",
            message="Transfer bridge is not available in this worker run.",
        )
        return 0

    work = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / f"baidu-drive-{task_id}"
    work.mkdir(parents=True, exist_ok=True)
    checkpoint = work / "state.db"
    result_path = work / "result.json"
    restore_checkpoint(gh, task_id, checkpoint)
    task = update_public_state(
        gh, runtime, task,
        reason="worker-start",
        status="RUNNING",
        message="Transfer worker started; progress will be committed at the next durable checkpoint.",
    )

    proc = subprocess.run(bridge_command(task, bridge, work, checkpoint, result_path), check=False)
    persist_checkpoint(gh, task_id, checkpoint)
    try:
        result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else {}
    except (OSError, ValueError):
        result = {}
    task, message = map_result(task, result if isinstance(result, dict) else {}, proc.returncode)
    task = controller.save_task(gh, task, "worker-result")

    new_runtime = copy.deepcopy(runtime)
    if task["status"] == "COMPLETED":
        new_runtime["active_task"] = None
        new_runtime["last_task"] = task_id
    new_runtime = controller.save_runtime_if_changed(gh, runtime, new_runtime, "worker-result")
    release = gh.ensure_release()
    gh.patch_release(
        release,
        controller.render_release(controller.default_control(), new_runtime, task, task["status"], message),
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", default="")
    args = parser.parse_args(argv)
    gh = controller.GitHub(os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", ""))
    return run_worker(gh, args.task_id)


if __name__ == "__main__":
    raise SystemExit(main())
