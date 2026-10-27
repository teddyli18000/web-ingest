#!/usr/bin/env python3
"""Serialized global scheduler runner for Baidu -> Drive relay workers."""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import os
from typing import Any

import controller
import relay_control
import relay_state
import scheduler

PREPARE_WORKFLOW = "baidu-drive-worker.yml"


class SchedulerRunnerError(RuntimeError):
    pass


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def dispatch_prepare(repo: relay_control.GitHubRepo, task_id: str, reason: str) -> None:
    repo._request(
        "POST",
        f"{repo.api}/actions/workflows/{PREPARE_WORKFLOW}/dispatches",
        {
            "ref": "main",
            "inputs": {
                "task_id": task_id,
                "reason": reason,
            },
        },
    )


def update_release_projection(
    gh: controller.GitHub,
    runtime: dict[str, Any],
    task: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    aggregate = relay_state.aggregate(records)
    value = copy.deepcopy(task)
    value["files_done"] = max(int(value.get("files_done") or 0), aggregate["files_verified"])
    value["bytes_done"] = max(int(value.get("bytes_done") or 0), aggregate["bytes_confirmed"])
    active = aggregate["active_workers"]
    if value.get("status") not in {"BLOCKED", "BLOCKED_AUTH_SETUP", "FAILED", "COMPLETED", "CANCELLED"}:
        value["status"] = "RUNNING"
    value["message"] = (
        f"Relay active: {active} worker(s); "
        f"verified {aggregate['files_verified']}/{aggregate['files_total']} registered file(s)."
    )
    value = controller.save_task(gh, value, "relay-scheduler-projection")
    release = gh.ensure_release()
    gh.patch_release(
        release,
        controller.render_release(
            controller.default_control(),
            runtime,
            value,
            str(value.get("status") or "RUNNING"),
            str(value.get("message") or "-"),
        ),
    )
    return value


def run_scheduler(
    gh: controller.GitHub,
    repo: relay_control.GitHubRepo,
    task_id: str,
    *,
    now: dt.datetime | None = None,
    run_id: str = "scheduler",
    policy: scheduler.Policy = scheduler.Policy(),
) -> str:
    now = now or utc_now()
    runtime, _ = gh.read_json(controller.RUNTIME_PATH, default=controller.DEFAULT_RUNTIME)
    active_task = str(runtime.get("active_task") or "").strip()
    if not task_id or active_task != task_id:
        return "inactive"
    task = controller.load_task(gh, task_id)
    if not task or str(task.get("status") or "") in {"COMPLETED", "CANCELLED"}:
        return "terminal"

    records = repo.list_records(task_id)
    update_release_projection(gh, runtime, task, records)
    dispatched = relay_control.schedule_once(repo, task_id, now, run_id, policy=policy)
    if dispatched:
        return "files_dispatched"

    records = repo.list_records(task_id)
    if any(scheduler.is_active(record, now, policy) for record in records):
        return "workers_active"
    if any(scheduler.is_runnable(record, now, policy) for record in records):
        # This should normally mean another serialized scheduler run claimed it
        # between reads. Do not invent a second decision path.
        return "runnable_pending"

    failed = [record for record in records if record.get("status") == relay_state.FAILED_PERMANENT]
    if failed:
        task = controller.load_task(gh, task_id) or task
        task["status"] = "BLOCKED"
        task["message"] = f"{len(failed)} relay file(s) require intervention before the task can continue."
        task = controller.save_task(gh, task, "relay-permanent-failure")
        release = gh.ensure_release()
        gh.patch_release(
            release,
            controller.render_release(
                controller.default_control(), runtime, task, task["status"], task["message"]
            ),
        )
        return "blocked"

    # No active/runnable files means the current staged batch is drained (or no
    # file records exist yet). The serialized preparation worker imports all
    # verified results, cleans the old staging batch, and decides whether to
    # stage another batch or finish the task.
    dispatch_prepare(repo, task_id, "relay-drained")
    return "prepare_dispatched"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    args = parser.parse_args(argv)
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    gh = controller.GitHub(repository, token)
    repo = relay_control.GitHubRepo(repository, token)
    try:
        outcome = run_scheduler(
            gh,
            repo,
            args.task_id,
            run_id=os.environ.get("GITHUB_RUN_ID", "scheduler"),
        )
    except (SchedulerRunnerError, controller.ProtocolError, relay_control.ControlError, relay_state.RelayStateError) as exc:
        print(f"relay scheduler stopped safely: {str(exc)[:300]}")
        return 1
    print(f"relay scheduler outcome: {outcome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
