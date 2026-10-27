#!/usr/bin/env python3
"""Release-backed control plane for the web-ingest Baidu -> Google Drive task.

The fixed GitHub Release is the human control surface. Durable machine state is
stored under baidu-drive/state/. Credentials never belong in either place.
"""
from __future__ import annotations

import argparse
import base64
import copy
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

RELEASE_TAG = "baidu-drive-live"
RELEASE_NAME = "Baidu -> Google Drive"
RUNTIME_PATH = "baidu-drive/state/runtime.json"
TASK_DIR = "baidu-drive/state/tasks"
VALID_COMMANDS = {"none", "start", "retry", "cancel"}
TERMINAL_STATES = {"COMPLETED", "CANCELED", "FAILED_PERMANENT"}
RETRYABLE_STATES = {"BLOCKED_AUTH_SETUP", "BLOCKED", "PAUSED", "FAILED_RETRYABLE"}
BAIDU_HOSTS = {"pan.baidu.com", "yun.baidu.com"}

DEFAULT_RUNTIME: dict[str, Any] = {
    "schema": 1,
    "active_task": None,
    "last_task": None,
    "updated_at": None,
}


class ProtocolError(RuntimeError):
    pass


class GitHub:
    def __init__(self, repo: str, token: str):
        if not repo or not token:
            raise ProtocolError("GITHUB_REPOSITORY/GITHUB_TOKEN is missing")
        self.repo = repo
        self.token = token
        self.api = f"https://api.github.com/repos/{repo}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "web-ingest-baidu-drive",
        }

    def request(
        self,
        method: str,
        url: str,
        *,
        obj: Any = None,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        request_headers = dict(self.headers)
        if headers:
            request_headers.update(headers)
        if obj is not None:
            data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, method=method, data=data, headers=request_headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                payload = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read(4096).decode("utf-8", errors="replace")
            raise ProtocolError(f"GitHub API {method} failed: HTTP {exc.code}: {detail[:300]}") from None
        return json.loads(payload.decode("utf-8")) if payload else None

    def release(self) -> dict[str, Any] | None:
        url = f"{self.api}/releases/tags/{urllib.parse.quote(RELEASE_TAG)}"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise ProtocolError(f"GitHub release lookup failed: HTTP {exc.code}") from None

    def ensure_release(self) -> dict[str, Any]:
        release = self.release()
        if release is not None:
            return release
        return self.request(
            "POST",
            f"{self.api}/releases",
            obj={
                "tag_name": RELEASE_TAG,
                "target_commitish": "main",
                "name": RELEASE_NAME,
                "body": render_release(default_control(), DEFAULT_RUNTIME, None, "IDLE", "Ready. Configure authentication before starting a transfer."),
                "draft": False,
                "prerelease": False,
            },
        )

    def patch_release(self, release: dict[str, Any], body: str) -> None:
        if body != (release.get("body") or ""):
            self.request("PATCH", release["url"], obj={"body": body})

    def read_json(self, path: str, default: dict[str, Any] | None = None) -> tuple[dict[str, Any], str | None]:
        url = f"{self.api}/contents/{urllib.parse.quote(path, safe='/')}?ref=main"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                item = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and default is not None:
                return copy.deepcopy(default), None
            raise ProtocolError(f"GitHub contents read failed for {path}: HTTP {exc.code}") from None
        raw = base64.b64decode(item["content"])
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ProtocolError(f"invalid JSON in {path}: {exc}") from None
        if not isinstance(value, dict):
            raise ProtocolError(f"expected JSON object in {path}")
        return value, item.get("sha")

    def write_json(self, path: str, value: dict[str, Any], message: str) -> None:
        encoded = base64.b64encode((json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")).decode("ascii")
        for attempt in range(3):
            _, sha = self.read_json(path, default={})
            body: dict[str, Any] = {
                "message": message,
                "content": encoded,
                "branch": "main",
            }
            if sha:
                body["sha"] = sha
            try:
                self.request("PUT", f"{self.api}/contents/{urllib.parse.quote(path, safe='/')}", obj=body)
                return
            except ProtocolError as exc:
                if attempt == 2 or not any(code in str(exc) for code in ("HTTP 409", "HTTP 422")):
                    raise
        raise ProtocolError(f"failed to write {path}")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def default_control() -> dict[str, str]:
    return {"command": "none", "share_url": "-", "extraction_code": "-"}


def line_value(body: str, key: str) -> str | None:
    match = re.search(rf"(?im)^\s*{re.escape(key)}\s*[:=]\s*(.*?)\s*$", body or "")
    return match.group(1).strip() if match else None


def parse_control(body: str) -> dict[str, str]:
    command = (line_value(body, "command") or "").strip().lower()
    share_url = (line_value(body, "share_url") or "-").strip()
    extraction_code = (line_value(body, "extraction_code") or "-").strip()
    return {"command": command, "share_url": share_url, "extraction_code": extraction_code}


def validate_share_url(raw: str) -> str:
    try:
        parsed = urllib.parse.urlparse(raw)
    except ValueError:
        raise ProtocolError("share_url is not a valid URL") from None
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in BAIDU_HOSTS:
        raise ProtocolError("share_url must be an HTTPS Baidu Netdisk share URL")
    if not parsed.path or parsed.path == "/":
        raise ProtocolError("share_url has no share path")
    return raw


def task_id(source_url: str, when: dt.datetime | None = None) -> str:
    when = when or dt.datetime.now(dt.timezone.utc)
    suffix = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:6]
    return f"bd-{when:%Y%m%dT%H%M%SZ}-{suffix}"


def task_path(task: str) -> str:
    if not re.fullmatch(r"bd-[A-Za-z0-9-]+", task):
        raise ProtocolError("unsafe task id")
    return f"{TASK_DIR}/{task}.json"


def status_projection(task: dict[str, Any] | None) -> tuple[str, str]:
    if not task:
        return "IDLE", "Ready. Configure authentication before starting a transfer."
    state = str(task.get("status") or "UNKNOWN")
    message = str(task.get("message") or "-")
    return state, message


def render_release(
    control: dict[str, str],
    runtime: dict[str, Any],
    task: dict[str, Any] | None,
    public_state: str,
    message: str,
) -> str:
    task_id_value = task.get("id") if task else "-"
    source = task.get("source_url") if task else "-"
    files_done = int(task.get("files_done") or 0) if task else 0
    files_total = int(task.get("files_total") or 0) if task else 0
    bytes_done = int(task.get("bytes_done") or 0) if task else 0
    bytes_total = int(task.get("bytes_total") or 0) if task else 0
    drive_url = task.get("drive_folder_url") if task else None
    updated = task.get("updated_at") if task else runtime.get("updated_at")
    return "\n".join([
        "# Baidu -> Google Drive",
        "",
        "> [!NOTE]",
        "> This Release is the public control/status surface. Use it only for public Baidu shares. Never paste account credentials, cookies, OAuth tokens, signed URLs, or private data here.",
        "",
        "## Request",
        "",
        "Edit only these values, then save the Release. Accepted commands are consumed back to `none`.",
        "",
        f"command: {control.get('command', 'none')}",
        f"share_url: {control.get('share_url', '-')}",
        f"extraction_code: {control.get('extraction_code', '-')}",
        "",
        "## Status (managed by Action)",
        "",
        f"State: {public_state}",
        f"Task: {task_id_value or '-'}",
        f"Source: {source or '-'}",
        f"Files: {files_done}/{files_total if files_total else '-'}",
        f"Bytes: {bytes_done}/{bytes_total if bytes_total else '-'}",
        f"Drive folder: {drive_url or '-'}",
        f"Updated: {updated or '-'}",
        f"Message: {message[:300] if message else '-'}",
        "",
        "## Commands",
        "",
        "- `start`: accept a new public Baidu share as the active task.",
        "- `retry`: requeue the active retryable task after an operational block is resolved.",
        "- `cancel`: mark the active non-terminal task canceled.",
        "- `none`: no request.",
        "",
        "Authentication is intentionally not stored in this Release or repository. Until the OAuth/secret setup is wired, accepted start/retry requests stop safely in `BLOCKED_AUTH_SETUP`.",
        "",
    ])


def load_task(gh: GitHub, task_id_value: Any) -> dict[str, Any] | None:
    if not task_id_value:
        return None
    task, _ = gh.read_json(task_path(str(task_id_value)), default={})
    return task or None


def load_active_task(gh: GitHub, runtime: dict[str, Any]) -> dict[str, Any] | None:
    return load_task(gh, runtime.get("active_task"))


def load_display_task(gh: GitHub, runtime: dict[str, Any]) -> dict[str, Any] | None:
    return load_task(gh, runtime.get("active_task")) or load_task(gh, runtime.get("last_task"))


def save_runtime_if_changed(gh: GitHub, old: dict[str, Any], new: dict[str, Any], reason: str) -> dict[str, Any]:
    old_cmp = copy.deepcopy(old)
    new_cmp = copy.deepcopy(new)
    old_cmp.pop("updated_at", None)
    new_cmp.pop("updated_at", None)
    if old_cmp == new_cmp:
        new["updated_at"] = old.get("updated_at")
        return new
    new["updated_at"] = now_iso()
    gh.write_json(RUNTIME_PATH, new, f"baidu-drive: {reason} runtime state")
    return new


def save_task(gh: GitHub, task: dict[str, Any], reason: str) -> dict[str, Any]:
    task = copy.deepcopy(task)
    task["updated_at"] = now_iso()
    gh.write_json(task_path(str(task["id"])), task, f"baidu-drive: {reason} {task['id']}")
    return task


def new_task(control: dict[str, str]) -> dict[str, Any]:
    source = validate_share_url(control["share_url"])
    code = control.get("extraction_code", "-")
    if code == "-":
        code = ""
    created = now_iso()
    return {
        "schema": 1,
        "id": task_id(source),
        "status": "BLOCKED_AUTH_SETUP",
        "source_url": source,
        "extraction_code": code,
        "created_at": created,
        "updated_at": created,
        "files_total": 0,
        "files_done": 0,
        "bytes_total": 0,
        "bytes_done": 0,
        "drive_folder_url": None,
        "attempt": 0,
        "message": "Task accepted. OAuth/secret-backed transfer worker is not configured yet.",
    }


def apply_command(
    command: str,
    control: dict[str, str],
    runtime: dict[str, Any],
    active: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any] | None, str]:
    runtime = copy.deepcopy(runtime)
    if command not in VALID_COMMANDS:
        raise ProtocolError("command must be one of: none, start, retry, cancel")
    if command == "none":
        return runtime, active, "State reconciled."

    if command == "start":
        if active and str(active.get("status")) not in TERMINAL_STATES:
            raise ProtocolError(f"active task {active.get('id')} is still {active.get('status')}; cancel or complete it first")
        task = new_task(control)
        runtime["active_task"] = task["id"]
        runtime["last_task"] = task["id"]
        return runtime, task, task["message"]

    if not active:
        raise ProtocolError(f"cannot {command}: there is no active task")

    if command == "cancel":
        if str(active.get("status")) in TERMINAL_STATES:
            raise ProtocolError(f"cannot cancel terminal task {active.get('id')}")
        task = copy.deepcopy(active)
        task["status"] = "CANCELED"
        task["message"] = "Canceled from the Release control surface."
        runtime["active_task"] = None
        runtime["last_task"] = task["id"]
        return runtime, task, task["message"]

    if str(active.get("status")) not in RETRYABLE_STATES:
        raise ProtocolError(f"task {active.get('id')} is not retryable from {active.get('status')}")
    task = copy.deepcopy(active)
    task["attempt"] = int(task.get("attempt") or 0) + 1
    task["status"] = "BLOCKED_AUTH_SETUP"
    task["message"] = "Retry accepted. OAuth/secret-backed transfer worker is still not configured."
    return runtime, task, task["message"]


def reconcile(gh: GitHub) -> int:
    release = gh.ensure_release()
    control = parse_control(release.get("body") or "")
    runtime, _ = gh.read_json(RUNTIME_PATH, default=DEFAULT_RUNTIME)
    active = load_active_task(gh, runtime)
    display = load_display_task(gh, runtime)

    original_runtime = copy.deepcopy(runtime)
    public_state, message = status_projection(display)
    consumed = default_control()

    try:
        runtime, changed_task, message = apply_command(control["command"], control, runtime, active)
        if changed_task is not None and (active is None or changed_task != active):
            changed_task = save_task(gh, changed_task, control["command"])
            if changed_task["status"] == "CANCELED":
                active = changed_task
            else:
                active = changed_task
        runtime = save_runtime_if_changed(gh, original_runtime, runtime, control["command"])
        display = active or load_display_task(gh, runtime)
        public_state, _ = status_projection(display)
    except ProtocolError as exc:
        public_state = "CONTROL_ERROR"
        message = str(exc)
        # Consume malformed/failed commands too; otherwise the same edit would
        # be replayed by every later reconcile event.
        runtime = save_runtime_if_changed(gh, original_runtime, runtime, "control-error")

    display = active or load_display_task(gh, runtime)
    gh.patch_release(release, render_release(consumed, runtime, display, public_state, message))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("reconcile",))
    args = parser.parse_args(argv)
    gh = GitHub(os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", ""))
    if args.command == "reconcile":
        return reconcile(gh)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
