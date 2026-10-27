from __future__ import annotations

import copy
import datetime as dt
import sys
from pathlib import Path
import unittest
from unittest import mock

TASK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_DIR))

import relay_state  # noqa: E402
import scheduler_runner  # noqa: E402

UTC = dt.timezone.utc
TEST_MD5 = "0123456789abcdef0123456789abcdef"


def source(file_id, size):
    return {
        "file_id": file_id,
        "batch_id": "batch-1",
        "logical_path": f"/{file_id}.bin",
        "parent_path": "/",
        "name": f"{file_id}.bin",
        "size": size,
        "md5": "",
        "baidu_staging_path": f"/BaiduDriveMover/mover/batch-1/{file_id}",
        "drive_parent_id": "drive-root",
    }


class FakeGH:
    def __init__(self):
        self.runtime = {"active_task": "task-1", "last_task": None}

    def read_json(self, path, default=None):
        return copy.deepcopy(self.runtime), "sha"


class FakeRepo:
    def __init__(self, records):
        self.records = {record["file_id"]: copy.deepcopy(record) for record in records}
        self.file_dispatches = []
        self.prepare_dispatches = []

    def list_records(self, task_id):
        return [copy.deepcopy(self.records[key]) for key in sorted(self.records)]

    def mutate_record(self, task_id, file_id, mutator, message):
        self.records[file_id] = mutator(copy.deepcopy(self.records[file_id]))
        return copy.deepcopy(self.records[file_id])

    def dispatch_file_worker(self, task_id, file_id, lease_id, workflow):
        self.file_dispatches.append((task_id, file_id, lease_id, workflow))

    def _request(self, method, url, obj=None):
        self.prepare_dispatches.append((method, url, copy.deepcopy(obj)))
        return None


class SchedulerRunnerTests(unittest.TestCase):
    def now(self):
        return dt.datetime(2026, 10, 27, 17, 0, tzinfo=UTC)

    def record(self, file_id, size):
        return relay_state.new_record("task-1", source(file_id, size), self.now())

    def test_scheduler_fills_three_independent_slots(self):
        repo = FakeRepo([
            self.record("a", 1),
            self.record("b", 9),
            self.record("c", 5),
            self.record("d", 2),
        ])
        with mock.patch.object(scheduler_runner.controller, "load_task", return_value={"id": "task-1", "status": "RUNNING"}), \
             mock.patch.object(scheduler_runner, "update_release_projection", return_value={}):
            outcome = scheduler_runner.run_scheduler(
                FakeGH(), repo, "task-1", now=self.now(), run_id="77"
            )
        self.assertEqual(outcome, "files_dispatched")
        self.assertEqual([item[1] for item in repo.file_dispatches], ["b", "c", "d"])
        self.assertEqual(len(repo.prepare_dispatches), 0)

    def test_all_verified_dispatches_prepare_instead_of_another_file_worker(self):
        records = []
        for file_id in ("a", "b"):
            record = self.record(file_id, 100)
            record = relay_state.claim(record, f"lease-{file_id}", self.now())
            record = relay_state.apply_relay_checkpoint(
                record, f"lease-{file_id}", 100, 100, "opaque", TEST_MD5, self.now()
            )
            record = relay_state.complete(
                record,
                f"lease-{file_id}",
                f"drive-{file_id}",
                TEST_MD5,
                TEST_MD5,
                self.now(),
            )
            records.append(record)
        repo = FakeRepo(records)
        with mock.patch.object(scheduler_runner.controller, "load_task", return_value={"id": "task-1", "status": "RUNNING"}), \
             mock.patch.object(scheduler_runner, "update_release_projection", return_value={}):
            outcome = scheduler_runner.run_scheduler(
                FakeGH(), repo, "task-1", now=self.now(), run_id="77"
            )
        self.assertEqual(outcome, "prepare_dispatched")
        self.assertEqual(repo.file_dispatches, [])
        self.assertEqual(len(repo.prepare_dispatches), 1)
        self.assertIn("baidu-drive-worker.yml", repo.prepare_dispatches[0][1])

    def test_active_worker_prevents_prepare_dispatch(self):
        record = self.record("a", 100)
        record = relay_state.claim(record, "lease-a", self.now())
        repo = FakeRepo([record])
        with mock.patch.object(scheduler_runner.controller, "load_task", return_value={"id": "task-1", "status": "RUNNING"}), \
             mock.patch.object(scheduler_runner, "update_release_projection", return_value={}):
            outcome = scheduler_runner.run_scheduler(
                FakeGH(), repo, "task-1", now=self.now(), run_id="77"
            )
        self.assertEqual(outcome, "workers_active")
        self.assertEqual(repo.prepare_dispatches, [])


if __name__ == "__main__":
    unittest.main()
