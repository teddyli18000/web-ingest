from __future__ import annotations

import copy
import datetime as dt
import sys
from pathlib import Path
import unittest

TASK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_DIR))

import relay_control  # noqa: E402
import relay_state  # noqa: E402
import scheduler  # noqa: E402

UTC = dt.timezone.utc


def source():
    return {
        "file_id": "file-1",
        "batch_id": "batch-1",
        "logical_path": "/file.bin",
        "parent_path": "/",
        "name": "file.bin",
        "size": 100,
        "md5": "",
        "baidu_staging_path": "/BaiduDriveMover/task/batch/file-1",
        "drive_parent_id": "drive-root",
    }


class MemoryRepo:
    def __init__(self, record):
        self.record = copy.deepcopy(record)

    def list_records(self, task_id):
        return [copy.deepcopy(self.record)] if self.record["task_id"] == task_id else []

    def mutate_record(self, task_id, file_id, mutator, message):
        self.record = mutator(copy.deepcopy(self.record))
        return copy.deepcopy(self.record)


class RetryPolicyTests(unittest.TestCase):
    def now(self):
        return dt.datetime(2026, 10, 27, 17, 0, tzinfo=UTC)

    def failed_record(self, failures):
        record = relay_state.new_record("task-1", source(), self.now())
        for i in range(failures):
            record = relay_state.claim(record, f"lease-{i}", self.now())
            record = relay_state.fail(record, f"lease-{i}", self.now(), "transport", permanent=False)
        return record

    def test_three_failed_workers_stop_automatic_rescheduling(self):
        record = self.failed_record(3)
        self.assertEqual(record["retryable_failures"], 3)
        self.assertFalse(scheduler.is_runnable(record, self.now()))
        self.assertFalse(relay_state.runnable(record, self.now()))

    def test_confirmed_forward_progress_resets_failure_counter(self):
        record = self.failed_record(2)
        record = relay_state.claim(record, "lease-progress", self.now())
        record = relay_state.apply_relay_checkpoint(
            record,
            "lease-progress",
            50,
            50,
            "opaque-md5-state",
            None,
            self.now(),
        )
        self.assertEqual(record["retryable_failures"], 0)

    def test_explicit_task_retry_rearms_retryable_file(self):
        repo = MemoryRepo(self.failed_record(3))
        reset = relay_control.reset_retryable_files(repo, "task-1", self.now())
        self.assertEqual(reset, 1)
        self.assertEqual(repo.record["status"], relay_state.PAUSED)
        self.assertEqual(repo.record["retryable_failures"], 0)
        self.assertTrue(scheduler.is_runnable(repo.record, self.now()))


if __name__ == "__main__":
    unittest.main()
