"""One master, one shared pool of three independent transfer workers."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

MAX_WORKERS = 3
TRANSIENT = {"READY", "PAUSED", "FAILED_RETRYABLE"}
RUNNING_TASKS = {"RUNNING", "PAUSED", "BLOCKED", "FAILED_RETRYABLE", "BLOCKED_AUTH_SETUP"}


@dataclass
class Provider:
    name: str
    task_id: str
    task_status: str
    records: list[dict]
    files_total: int = 0
    bytes_done: int = 0


def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def live(record: dict, now: dt.datetime) -> bool:
    if record.get("status") != "ACTIVE":
        return False
    timestamp = parse_time(record.get("heartbeat_at"))
    if timestamp is None:
        return False
    max_age = dt.timedelta(minutes=45 if int(record.get("lease_heartbeat_protocol") or 0) >= 2 else 360)
    return now - timestamp < max_age


def ready(record: dict, now: dt.datetime) -> bool:
    status = record.get("status")
    if status == "ACTIVE":
        return not live(record, now)
    if status not in TRANSIENT:
        return False
    retry = parse_time(record.get("next_retry_at"))
    return retry is None or retry <= now


def pending_count(provider: Provider, now: dt.datetime) -> int:
    if provider.task_status not in RUNNING_TASKS:
        return 0
    if not provider.records:
        return max(1, provider.files_total)
    ready_files = sum(ready(r, now) for r in provider.records)
    unstaged = max(0, provider.files_total - len(provider.records))
    if ready_files or unstaged:
        return ready_files + unstaged
    # Final verified files still require a master cleanup and task completion.
    if provider.task_status == "RUNNING" and all(r.get("status") == "VERIFIED" for r in provider.records):
        return 1
    return 0


def demand(provider: Provider, now: dt.datetime) -> bool:
    return pending_count(provider, now) > 0


def active_count(provider: Provider, now: dt.datetime) -> int:
    return sum(live(record, now) for record in provider.records)


def allocate(providers: list[Provider], now: dt.datetime, *, pool_size: int = MAX_WORKERS) -> dict[str, int]:
    """Assign new slots with one-per-provider fairness before longest-remaining."""
    result = {p.name: 0 for p in providers}
    free = max(0, pool_size - sum(active_count(p, now) for p in providers))
    if free == 0:
        return result
    eligible = [p for p in providers if demand(p, now)]
    pending = {p.name: pending_count(p, now) for p in eligible}
    eligible.sort(key=lambda p: p.name)
    for p in eligible:
        if free == 0:
            break
        result[p.name] += 1
        free -= 1
    while free and eligible:
        candidates = [p for p in eligible if result[p.name] < pending[p.name]]
        if not candidates:
            break
        p = max(candidates, key=lambda q: (sum(max(0, int(r.get("size") or 0) - int(r.get("confirmed_offset") or 0))
                                            for r in q.records if ready(r, now)) / (active_count(q, now) + result[q.name]),
                                          -len(q.name)))
        result[p.name] += 1
        free -= 1
    return result
