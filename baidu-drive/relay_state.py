#!/usr/bin/env python3
"""Pure per-file state transitions for parallel Baidu -> Drive relay workers."""
from __future__ import annotations

import copy
import datetime as dt
import re
from typing import Any, Iterable

ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")

READY = "READY"
ACTIVE = "ACTIVE"
PAUSED = "PAUSED"
FAILED_RETRYABLE = "FAILED_RETRYABLE"
FAILED_PERMANENT = "FAILED_PERMANENT"
VERIFIED = "VERIFIED"

RUNNABLE = {READY, PAUSED, FAILED_RETRYABLE}
TERMINAL = {VERIFIED, FAILED_PERMANENT}
DEFAULT_STALE_SECONDS = 60 * 60


class RelayStateError(RuntimeError):
    pass


def now_iso(now: dt.datetime | None = None) -> str:
    value = now or dt.datetime.now(dt.timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds")


def _parse_time(value: Any) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _safe_id(value: Any, label: str) -> str:
    value = str(value or "").strip()
    if not value or not ID_PATTERN.fullmatch(value):
        raise RelayStateError(f"unsafe {label}")
    return value


def state_path(task_id: str, file_id: str) -> str:
    task = _safe_id(task_id, "task id")
    file = _safe_id(file_id, "file id")
    return f"baidu-drive/state/files/{task}/{file}.json"


def new_record(task_id: str, source: dict[str, Any], now: dt.datetime | None = None) -> dict[str, Any]:
    task = _safe_id(task_id, "task id")
    file_id = _safe_id(source.get("file_id"), "file id")
    batch_id = _safe_id(source.get("batch_id"), "batch id")
    size = int(source.get("size") or 0)
    if size < 0:
        raise RelayStateError("file size cannot be negative")
    name = str(source.get("name") or "")
    logical_path = str(source.get("logical_path") or "")
    parent_path = str(source.get("parent_path") or "")
    staging = str(source.get("baidu_staging_path") or "")
    parent_id = str(source.get("drive_parent_id") or "").strip()
    if not name or not logical_path or not parent_path or not staging or not parent_id:
        raise RelayStateError("relay manifest entry is incomplete")
    stamp = now_iso(now)
    return {
        "schema": 1,
        "task_id": task,
        "file_id": file_id,
        "batch_id": batch_id,
        "logical_path": logical_path,
        "parent_path": parent_path,
        "name": name,
        "size": size,
        "md5": str(source.get("md5") or ""),
        "baidu_staging_path": staging,
        "drive_parent_id": parent_id,
        "status": READY,
        "confirmed_offset": 0,
        "drive_file_id": None,
        "drive_md5": None,
        "session_sealed": None,
        "lease_id": None,
        "lease_started_at": None,
        "heartbeat_at": None,
        "attempts": 0,
        "last_error": "",
        "created_at": stamp,
        "updated_at": stamp,
    }


def heartbeat_stale(record: dict[str, Any], now: dt.datetime, stale_seconds: int = DEFAULT_STALE_SECONDS) -> bool:
    heartbeat = _parse_time(record.get("heartbeat_at"))
    if heartbeat is None:
        return True
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    return (now.astimezone(dt.timezone.utc) - heartbeat).total_seconds() >= stale_seconds


def runnable(record: dict[str, Any], now: dt.datetime, stale_seconds: int = DEFAULT_STALE_SECONDS) -> bool:
    status = str(record.get("status") or "")
    if status in RUNNABLE:
        return int(record.get("confirmed_offset") or 0) < int(record.get("size") or 0) or int(record.get("size") or 0) == 0
    return status == ACTIVE and heartbeat_stale(record, now, stale_seconds)


def claim(record: dict[str, Any], lease_id: str, now: dt.datetime, stale_seconds: int = DEFAULT_STALE_SECONDS) -> dict[str, Any]:
    lease_id = _safe_id(lease_id, "lease id")
    value = copy.deepcopy(record)
    if not runnable(value, now, stale_seconds):
        raise RelayStateError(f"file is not runnable from {value.get('status')}")
    stamp = now_iso(now)
    value["status"] = ACTIVE
    value["lease_id"] = lease_id
    value["lease_started_at"] = stamp
    value["heartbeat_at"] = stamp
    value["attempts"] = int(value.get("attempts") or 0) + 1
    value["last_error"] = ""
    value["updated_at"] = stamp
    return value


def require_lease(record: dict[str, Any], lease_id: str) -> None:
    if str(record.get("status") or "") != ACTIVE or str(record.get("lease_id") or "") != lease_id:
        raise RelayStateError("worker no longer owns this file lease")


def attach_session(record: dict[str, Any], lease_id: str, sealed: str, now: dt.datetime) -> dict[str, Any]:
    value = copy.deepcopy(record)
    require_lease(value, lease_id)
    sealed = str(sealed or "").strip()
    if not sealed.startswith("v1."):
        raise RelayStateError("invalid sealed session")
    existing = str(value.get("session_sealed") or "")
    if existing and existing != sealed:
        raise RelayStateError("refusing to replace a live resumable session implicitly")
    value["session_sealed"] = sealed
    value["heartbeat_at"] = now_iso(now)
    value["updated_at"] = value["heartbeat_at"]
    return value


def replace_expired_session(record: dict[str, Any], lease_id: str, sealed: str, now: dt.datetime) -> dict[str, Any]:
    value = copy.deepcopy(record)
    require_lease(value, lease_id)
    sealed = str(sealed or "").strip()
    if not sealed.startswith("v1."):
        raise RelayStateError("invalid sealed session")
    # A new Drive resumable session has no bytes from the expired session.
    # Reset the checkpoint rather than pretending the new remote owns them.
    value["session_sealed"] = sealed
    value["confirmed_offset"] = 0
    value["heartbeat_at"] = now_iso(now)
    value["updated_at"] = value["heartbeat_at"]
    return value


def apply_remote_progress(record: dict[str, Any], lease_id: str, remote_offset: int, now: dt.datetime) -> dict[str, Any]:
    value = copy.deepcopy(record)
    require_lease(value, lease_id)
    size = int(value.get("size") or 0)
    offset = int(remote_offset)
    if offset < 0 or offset > size:
        raise RelayStateError("remote offset is outside file size")
    # Deliberately allow the value to move backwards: Drive is authority and a
    # stale repository hint must never force the remote state forward.
    value["confirmed_offset"] = offset
    value["heartbeat_at"] = now_iso(now)
    value["updated_at"] = value["heartbeat_at"]
    return value


def pause(record: dict[str, Any], lease_id: str, now: dt.datetime, message: str = "") -> dict[str, Any]:
    value = copy.deepcopy(record)
    require_lease(value, lease_id)
    value["status"] = PAUSED
    value["lease_id"] = None
    value["lease_started_at"] = None
    value["heartbeat_at"] = None
    value["last_error"] = str(message or "")[:300]
    value["updated_at"] = now_iso(now)
    return value


def fail(record: dict[str, Any], lease_id: str, now: dt.datetime, message: str, permanent: bool = False) -> dict[str, Any]:
    value = copy.deepcopy(record)
    require_lease(value, lease_id)
    value["status"] = FAILED_PERMANENT if permanent else FAILED_RETRYABLE
    value["lease_id"] = None
    value["lease_started_at"] = None
    value["heartbeat_at"] = None
    value["last_error"] = str(message or "")[:300]
    value["updated_at"] = now_iso(now)
    return value


def complete(
    record: dict[str, Any],
    lease_id: str,
    drive_file_id: str,
    drive_md5: str,
    now: dt.datetime,
) -> dict[str, Any]:
    value = copy.deepcopy(record)
    require_lease(value, lease_id)
    drive_file_id = str(drive_file_id or "").strip()
    if not drive_file_id:
        raise RelayStateError("verified Drive file ID is required")
    size = int(value.get("size") or 0)
    value["confirmed_offset"] = size
    value["drive_file_id"] = drive_file_id
    value["drive_md5"] = str(drive_md5 or "").strip() or None
    value["session_sealed"] = None
    value["status"] = VERIFIED
    value["lease_id"] = None
    value["lease_started_at"] = None
    value["heartbeat_at"] = None
    value["last_error"] = ""
    value["updated_at"] = now_iso(now)
    return value


def aggregate(records: Iterable[dict[str, Any]]) -> dict[str, int]:
    files_total = 0
    files_verified = 0
    bytes_total = 0
    bytes_confirmed = 0
    active = 0
    for record in records:
        files_total += 1
        size = max(0, int(record.get("size") or 0))
        offset = max(0, min(size, int(record.get("confirmed_offset") or 0)))
        bytes_total += size
        bytes_confirmed += offset
        if record.get("status") == VERIFIED:
            files_verified += 1
            bytes_confirmed -= offset
            bytes_confirmed += size
        if record.get("status") == ACTIVE:
            active += 1
    return {
        "files_total": files_total,
        "files_verified": files_verified,
        "bytes_total": bytes_total,
        "bytes_confirmed": bytes_confirmed,
        "active_workers": active,
    }
