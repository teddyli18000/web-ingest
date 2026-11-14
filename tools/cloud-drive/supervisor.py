#!/usr/bin/env python3
"""GitHub-only reconciler for Baidu/Quark's shared 1+3 worker pool."""
from __future__ import annotations

import base64
import datetime as dt
import json
import os
import uuid
import urllib.error
import urllib.parse
import urllib.request

from pool import Provider, active_count, allocate, ready, live, demand, parse_time

STATE = "tools/cloud-drive/state/supervisor.json"
WORKFLOWS = {"baidu": "baidu-drive-worker.yml", "quark": "quark-drive-worker.yml"}


class GitHub:
    def __init__(self):
        self.base = "https://api.github.com/repos/" + os.environ["GITHUB_REPOSITORY"]
        self.headers = {
            "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "web-ingest-cloud-drive-supervisor",
        }

    def request(self, method: str, path: str, payload: dict | None = None):
        headers = dict(self.headers)
        data = None
        if payload is not None:
            data = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=45) as res:
                raw = res.read()
        except urllib.error.HTTPError as e:
            if e.code == 404 and method == "GET":
                return None
            raise RuntimeError(f"GitHub supervisor API HTTP {e.code}") from None
        return json.loads(raw) if raw else None

    def read(self, path: str) -> tuple[dict | None, str | None]:
        url = "/contents/" + urllib.parse.quote(path, safe="/") + "?ref=main"
        item = self.request("GET", url)
        if item is None:
            return None, None
        return json.loads(base64.b64decode(item["content"])), item["sha"]

    def directory(self, path: str) -> list[str]:
        value = self.request("GET", "/contents/" + urllib.parse.quote(path, safe="/") + "?ref=main")
        if value is None:
            return []
        return [x["path"] for x in value if x["type"] == "file" and x["name"].endswith(".json")]

    def write(self, path: str, obj: dict, sha: str | None):
        data = base64.b64encode((json.dumps(obj, indent=2, sort_keys=True) + "\n").encode()).decode()
        params = {"message": "cloud-drive: checkpoint shared supervisor dispatch",
                  "branch": "main", "content": data}
        if sha:
            params["sha"] = sha
        self.request("PUT", "/contents/" + urllib.parse.quote(path, safe="/"), params)

    def dispatch(self, provider: str, task_id: str, capacity: int, reason: str, reservation_id: str):
        self.request("POST", "/actions/workflows/" + WORKFLOWS[provider] + "/dispatches", {
            "ref": "main",
            "inputs": {
                "task_id": task_id,
                "reason": reason,
                "max_workers": str(capacity),
                "reservation_id": reservation_id,
            },
        })

    def workflow_status(self, provider: str, reservation_id: str) -> str | None:
        """Find the uniquely named preparation run for a persisted reservation."""
        path = "/actions/workflows/" + WORKFLOWS[provider] + "/runs?event=workflow_dispatch&per_page=100"
        response = self.request("GET", path)
        for run in response.get("workflow_runs", []):
            if run.get("display_title") == "Cloud prepare " + reservation_id:
                return str(run.get("status"))
        return None


def load_provider(gh: GitHub, name: str) -> Provider | None:
    runtime, _ = gh.read(f"{name}-drive/state/runtime.json")
    task_id = str((runtime or {}).get("active_task") or "")
    if not task_id:
        return None
    task, _ = gh.read(f"{name}-drive/state/tasks/{task_id}.json")
    if not task:
        return None
    root = f"{name}-drive/state/files/{task_id}"
    records = [gh.read(p)[0] for p in gh.directory(root)]
    return Provider(name=name, task_id=task_id, task_status=str(task.get("status") or ""),
                    records=[r for r in records if r], files_total=int(task.get("files_total") or 0),
                    bytes_done=int(task.get("bytes_done") or 0))


def run(gh: GitHub, now: dt.datetime, reason: str = "shared-supervisor") -> dict[str, int]:
    providers = [p for name in WORKFLOWS if (p := load_provider(gh, name)) is not None]
    if reason == "auth-updated":
        for p in providers:
            if p.task_status == "NEEDS_LOGIN":
                p.task_status = "BLOCKED_AUTH_SETUP"
    state, sha = gh.read(STATE)
    state = state or {"schema": 1, "dispatched": {}}
    dispatch_state = state["dispatched"]
    # The next master inherits in-flight reservations from the last master.
    # GitHub can keep a workflow queued longer than a timer threshold, so check
    # real workflow state before releasing a pending reservation.
    reserved = 0
    eligible = []
    for p in providers:
        last = dispatch_state.get(p.name, {})
        then = parse_time(last.get("at")) if last.get("task_id") == p.task_id else None
        if then is not None:
            seen = max(0, active_count(p, now) - int(last.get("active_before") or 0))
            held = max(0, int(last.get("slots") or 0) - seen)
            if held:
                age = now - then
                pending = age < dt.timedelta(minutes=12)
                if not pending:
                    run_status = gh.workflow_status(p.name, str(last.get("reservation_id") or ""))
                    pending = run_status in {"queued", "in_progress", "waiting", "pending", "requested"}
                if pending:
                    reserved += held
                    continue
        eligible.append(p)
    # Ineligible providers still consume their real ACTIVE slots, and all
    # queued-but-not-yet-ACTIVE reservations reduce global free capacity.
    shadow = [
        Provider(q.name, q.task_id, "IDLE", q.records)
        for q in providers if q not in eligible
    ]
    allocations = allocate(eligible + shadow, now, pool_size=max(0, 3 - reserved))
    plans = []
    for p in providers:
        cap = allocations[p.name]
        if cap == 0:
            continue
        reservation_id = uuid.uuid4().hex
        dispatch_state[p.name] = {
            "task_id": p.task_id,
            "at": now.isoformat(timespec="seconds"),
            "active_before": active_count(p, now),
            "slots": cap,
            "reservation_id": reservation_id,
        }
        plans.append((p, cap, reservation_id))

    # Durable intent is written *before* any external dispatch. If a master
    # dies here, a successor can re-read and safely retry after checking runs.
    if plans:
        gh.write(STATE, state, sha)
        for p, cap, reservation_id in plans:
            gh.dispatch(p.name, p.task_id, active_count(p, now) + cap, reason, reservation_id)
    return allocations


def main() -> None:
    result = run(GitHub(), dt.datetime.now(dt.timezone.utc), os.environ.get("CLOUD_DRIVE_REASON", "shared-supervisor"))
    print("Shared supervisor dispatch:", {k: v for k, v in result.items() if v})


if __name__ == "__main__":
    main()
