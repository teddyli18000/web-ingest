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


def demand(provider: Provider, now: dt.datetime) -> bool:
    if provider.task_status not in RUNNING_TASKS:
        return False
    if not provider.records:
        return True
    return any(ready(r, now) for r in provider.records)


def active_count(provider: Provider, now: dt.datetime) -> int:
    return sum(live(record, now) for record in provider.records)


def allocate(providers: list[Provider], now: dt.datetime, *, pool_size: int = MAX_WORKERS) -> dict[str, int]:
    """Assign new slots with one-per-provider fairness before longest-remaining."""
    result = {p.name: 0 for p in providers}
    free = max(0, pool_size - sum(active_count(p, now) for p in providers))
    if free == 0:
        return result
    eligible = [p for p in providers if demand(p, now)]
    eligible.sort(key=lambda p: p.name)
    for p in eligible:
        if free == 0:
            break
        result[p.name] += 1
        free -= 1
    while free and eligible:
        p = max(eligible, key=lambda q: (sum(max(0, int(r.get("size") or 0) - int(r.get("confirmed_offset") or 0))
                                            for r in q.records if ready(r, now)) / (active_count(q, now) + result[q.name]),
                                          -len(q.name)))
        result[p.name] += 1
        free -= 1
    return result
