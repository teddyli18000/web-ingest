#!/usr/bin/env python3
"""GitHub-only reconciler for Baidu/Quark's shared 1+3 worker pool."""
from __future__ import annotations

import base64
import datetime as dt
import json
import os
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

    def dispatch(self, provider: str, task_id: str, capacity: int):
        self.request("POST", "/actions/workflows/" + WORKFLOWS[provider] + "/dispatches", {
            "ref": "main",
            "inputs": {"task_id": task_id, "reason": "shared-supervisor", "max_workers": str(capacity)},
        })


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


def run(gh: GitHub, now: dt.datetime) -> dict[str, int]:
    providers = [p for name in WORKFLOWS if (p := load_provider(gh, name)) is not None]
    state, sha = gh.read(STATE)
    state = state or {"schema": 1, "dispatched": {}}
    dispatch_state = state["dispatched"]
    # A dispatch holds its assigned slots while its provider preparation job
    # is queued/starting. At least 12 minutes between attempts to that provider.
    eligible = []
    for p in providers:
        last = dispatch_state.get(p.name, {})
        if last.get("task_id") == p.task_id:
            then = parse_time(last.get("at"))
            if then and now - then < dt.timedelta(minutes=12):
                # A new confirmed active lease is a sufficient handoff receipt.
                previous_active = int(last.get("active_before") or 0)
                if active_count(p, now) <= previous_active:
                    continue
        eligible.append(p)
    # All providers, including ones with a pending prepare dispatch, consume
    # their currently confirmed active worker slots globally.
    allocations = allocate(providers, now)
    allowed = {p.name for p in eligible}
    for p in providers:
        if p.name not in allowed:
            allocations[p.name] = 0
    # Reallocate unused allocations only among eligible providers, preserving
    # live worker counts from ineligible providers.
    if len(eligible) < len(providers):
        extra = allocate([*eligible, *[
            Provider(name=q.name, task_id=q.task_id, task_status="IDLE",
                     records=q.records) for q in providers if q.name not in allowed]], now)
        allocations = {p.name: extra.get(p.name, 0) for p in providers}
    changes = False
    for p in providers:
        cap = allocations[p.name]
        if cap == 0:
            continue
        local_limit = active_count(p, now) + cap
        dispatch_state[p.name] = {
            "task_id": p.task_id,
            "at": now.isoformat(timespec="seconds"),
            "active_before": active_count(p, now),
        }
        # Reserve the chance before launching another workflow.
        changes = True
    if changes:
        gh.write(STATE, state, sha)
        for p in providers:
            if allocations[p.name]:
                gh.dispatch(p.name, p.task_id, active_count(p, now) + allocations[p.name])
    return allocations


def main() -> None:
    result = run(GitHub(), dt.datetime.now(dt.timezone.utc))
    print("Shared supervisor dispatch:", {k: v for k, v in result.items() if v})


if __name__ == "__main__":
    main()
