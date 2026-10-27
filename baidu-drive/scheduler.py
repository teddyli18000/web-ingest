#!/usr/bin/env python3
"""Deterministic scheduling policy for the Baidu -> Drive transfer task.

This module is intentionally pure: it does not call GitHub, Baidu, or Google.
The control plane may persist its decisions, but remote truth always wins when
an executor reconciles a file.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Iterable

KIB = 1 << 10
MIB = 1 << 20
GIB = 1 << 30

DRIVE_CHUNK_QUANTUM = 256 * KIB
DEFAULT_MAX_WORKERS = 3
DEFAULT_CHUNK_BYTES = 512 * MIB
DEFAULT_SOFT_RUNTIME_SECONDS = 5 * 60 * 60
DEFAULT_HARD_RUNTIME_SECONDS = 330 * 60
DEFAULT_STALE_HEARTBEAT_SECONDS = 60 * 60

RUNNABLE_FILE_STATES = {"READY", "PAUSED", "FAILED_RETRYABLE"}


@dataclass(frozen=True)
class Policy:
    max_workers: int = DEFAULT_MAX_WORKERS
    chunk_bytes: int = DEFAULT_CHUNK_BYTES
    soft_runtime_seconds: int = DEFAULT_SOFT_RUNTIME_SECONDS
    hard_runtime_seconds: int = DEFAULT_HARD_RUNTIME_SECONDS
    stale_heartbeat_seconds: int = DEFAULT_STALE_HEARTBEAT_SECONDS

    def validate(self) -> "Policy":
        if self.max_workers <= 0:
            raise ValueError("max_workers must be positive")
        if self.chunk_bytes <= 0 or self.chunk_bytes % DRIVE_CHUNK_QUANTUM != 0:
            raise ValueError("chunk_bytes must be a positive multiple of 256 KiB")
        if self.soft_runtime_seconds <= 0:
            raise ValueError("soft_runtime_seconds must be positive")
        if self.hard_runtime_seconds <= self.soft_runtime_seconds:
            raise ValueError("hard runtime must exceed soft runtime")
        if self.stale_heartbeat_seconds <= 0:
            raise ValueError("stale heartbeat window must be positive")
        return self


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


def remaining_bytes(file_state: dict[str, Any]) -> int:
    size = max(0, int(file_state.get("size") or 0))
    confirmed = max(0, int(file_state.get("confirmed_offset") or 0))
    return max(0, size - min(size, confirmed))


def heartbeat_is_stale(
    file_state: dict[str, Any],
    now: dt.datetime,
    policy: Policy = Policy(),
) -> bool:
    policy.validate()
    heartbeat = _parse_time(file_state.get("heartbeat_at"))
    if heartbeat is None:
        return True
    age = (now.astimezone(dt.timezone.utc) - heartbeat).total_seconds()
    return age >= policy.stale_heartbeat_seconds


def is_active(file_state: dict[str, Any], now: dt.datetime, policy: Policy = Policy()) -> bool:
    return str(file_state.get("status") or "").upper() == "ACTIVE" and not heartbeat_is_stale(
        file_state, now, policy
    )


def is_runnable(file_state: dict[str, Any], now: dt.datetime, policy: Policy = Policy()) -> bool:
    status = str(file_state.get("status") or "").upper()
    if remaining_bytes(file_state) == 0:
        return False
    if status in RUNNABLE_FILE_STATES:
        return True
    return status == "ACTIVE" and heartbeat_is_stale(file_state, now, policy)


def choose_files(
    files: Iterable[dict[str, Any]],
    now: dt.datetime,
    policy: Policy = Policy(),
) -> list[str]:
    """Choose independent files for currently free worker slots.

    Existing live workers consume capacity. Remaining files use longest-
    remaining-first ordering to reduce the final long tail without splitting a
    single Drive upload across concurrent VMs.
    """
    policy.validate()
    values = list(files)
    active = sum(1 for item in values if is_active(item, now, policy))
    slots = max(0, policy.max_workers - active)
    if slots == 0:
        return []

    candidates = [item for item in values if is_runnable(item, now, policy)]
    candidates.sort(
        key=lambda item: (
            -remaining_bytes(item),
            str(item.get("logical_path") or ""),
            str(item.get("id") or ""),
        )
    )
    return [str(item["id"]) for item in candidates[:slots] if item.get("id")]


def chunk_window(
    confirmed_offset: int,
    total_size: int,
    policy: Policy = Policy(),
) -> tuple[int, int] | None:
    """Return inclusive [start, end] for the next Drive-compatible relay chunk.

    The relay streams the Baidu response directly into Drive; it does not
    materialize a chunk on runner disk. Every non-final chunk therefore keeps
    the configured fixed Drive-compatible size.
    """
    policy.validate()
    total = max(0, int(total_size))
    start = max(0, int(confirmed_offset))
    if start >= total:
        return None
    chunk = min(policy.chunk_bytes, total - start)
    return start, start + chunk - 1


def should_soft_stop(
    started_at: dt.datetime,
    now: dt.datetime,
    policy: Policy = Policy(),
) -> bool:
    policy.validate()
    elapsed = (
        now.astimezone(dt.timezone.utc) - started_at.astimezone(dt.timezone.utc)
    ).total_seconds()
    return elapsed >= policy.soft_runtime_seconds


def reconcile_confirmed_offset(
    persisted_offset: int,
    remote_offset: int,
    total_size: int,
) -> int:
    """Return the offset proven by the current Drive remote state.

    A repo checkpoint is a recovery hint, not authority. The caller must only
    pass a remote offset proven by the active resumable session or by final
    destination verification.
    """
    total = max(0, int(total_size))
    remote = max(0, min(total, int(remote_offset)))
    return remote
