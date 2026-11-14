#!/usr/bin/env python3
"""Renew a leased file's heartbeat independently from long-lived HTTP uploads."""
from __future__ import annotations

import argparse
import datetime as dt
import os
import time

import relay_control
import relay_state

INTERVAL_SECONDS = 5 * 60


def renew_once(repo: relay_control.GitHubRepo, task_id: str, file_id: str, lease_id: str) -> bool:
    record, _ = repo.read_record(task_id, file_id)
    if record is None or record.get("status") != relay_state.ACTIVE or record.get("lease_id") != lease_id:
        return False
    repo.mutate_record(
        task_id, file_id,
        lambda current: relay_state.renew_lease(current, lease_id, dt.datetime.now(dt.timezone.utc)),
        f"baidu-drive: renew lease for {file_id}",
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--file-id", required=True)
    parser.add_argument("--lease-id", required=True)
    args = parser.parse_args()
    repo = relay_control.GitHubRepo(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    while True:
        try:
            if not renew_once(repo, args.task_id, args.file_id, args.lease_id):
                return 0
        except relay_state.RelayStateError:
            return 0
        except relay_control.ControlError:
            print("GitHub lease renewal temporarily unavailable.")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
