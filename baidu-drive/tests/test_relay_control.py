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

UTC = dt.timezone.utc
TEST_MD5 = "0123456789abcdef0123456789abcdef"


class FakeRepo:
    def __init__(self):
        self.records = {}
        self.dispatched = []
        self.fail_dispatch_for = set()

    def ensure_record(self, task_id, source, now):
        candidate = relay_state.new_record(task_id, source, now)
        key = (task_id, candidate["file_id"])
        if key in self.records:
            relay_control.assert_same_source(self.records[key], candidate)
            return copy.deepcopy(self.records[key])
        self.records[key] = candidate
        return copy.deepcopy(candidate)

    def list_records(self, task_id):
        return [copy.deepcopy(v) for (task, _), v in sorted(self.records.items()) if task == task_id]

    def mutate_record(self, task_id, file_id, mutator, message):
        key = (task_id, file_id)
        if key not in self.records:
            raise relay_control.ControlError("missing")
        updated = mutator(copy.deepcopy(self.records[key]))
        self.records[key] = updated
        return copy.deepcopy(updated)

    def dispatch_file_worker(self, task_id, file_id, lease_id, workflow):
        if file_id in self.fail_dispatch_for:
            raise relay_control.ControlError("dispatch failed")
        self.dispatched.append((task_id, file_id, lease_id, workflow))


class RelayControlTests(unittest.TestCase):
    def now(self):
        return dt.datetime(2026, 10, 27, 14, 0, tzinfo=UTC)

    def source(self, file_id="file-1", size=100, path=None):
        name = f"{file_id}.bin"
        return {
            "file_id": file_id,
            "batch_id": "batch-1",
            "logical_path": path or f"/{name}",
            "parent_path": "/",
            "name": name,
            "size": size,
            "md5": "",
            "baidu_staging_path": f"/BaiduDriveMover/task/batch/{file_id}",
            "drive_parent_id": "drive-root",
        }

    def test_sync_manifest_is_idempotent(self):
        repo = FakeRepo()
        manifest = [self.source()]
        relay_control.sync_manifest(repo, "task-1", manifest, self.now())
        relay_control.sync_manifest(repo, "task-1", manifest, self.now())
        self.assertEqual(len(repo.records), 1)

    def test_sync_manifest_rejects_changed_source_identity(self):
        repo = FakeRepo()
        relay_control.sync_manifest(repo, "task-1", [self.source()], self.now())
        with self.assertRaises(relay_control.ControlError):
            relay_control.sync_manifest(
                repo,
                "task-1",
                [self.source(path="/changed.bin")],
                self.now(),
            )

    def test_schedule_dispatches_three_longest_independent_files(self):
        repo = FakeRepo()
        manifest = [
            self.source("a", 1),
            self.source("b", 9),
            self.source("c", 5),
            self.source("d", 2),
        ]
        relay_control.sync_manifest(repo, "task-1", manifest, self.now())
        dispatched = relay_control.schedule_once(repo, "task-1", self.now(), "123")
        self.assertEqual([item[0] for item in dispatched], ["b", "c", "d"])
        self.assertEqual(len(repo.dispatched), 3)
        for file_id, lease_id in dispatched:
            record = repo.records[("task-1", file_id)]
            self.assertEqual(record["status"], relay_state.ACTIVE)
            self.assertEqual(record["lease_id"], lease_id)

    def test_live_workers_reduce_available_slots(self):
        repo = FakeRepo()
        manifest = [self.source("a", 20), self.source("b", 9), self.source("c", 5), self.source("d", 2)]
        relay_control.sync_manifest(repo, "task-1", manifest, self.now())
        repo.records[("task-1", "a")] = relay_state.claim(
            repo.records[("task-1", "a")], "lease-existing", self.now()
        )
        dispatched = relay_control.schedule_once(repo, "task-1", self.now(), "123")
        self.assertEqual([item[0] for item in dispatched], ["b", "c"])

    def test_dispatch_failure_releases_claim(self):
        repo = FakeRepo()
        relay_control.sync_manifest(repo, "task-1", [self.source("a", 9)], self.now())
        repo.fail_dispatch_for.add("a")
        with self.assertRaises(relay_control.ControlError):
            relay_control.schedule_once(repo, "task-1", self.now(), "123")
        record = repo.records[("task-1", "a")]
        self.assertEqual(record["status"], relay_state.PAUSED)
        self.assertIsNone(record["lease_id"])

    def test_zero_byte_file_gets_worker(self):
        repo = FakeRepo()
        relay_control.sync_manifest(repo, "task-1", [self.source("empty", 0)], self.now())
        dispatched = relay_control.schedule_once(repo, "task-1", self.now(), "123")
        self.assertEqual([item[0] for item in dispatched], ["empty"])

    def test_verified_results_are_sorted_and_minimal(self):
        repo = FakeRepo()
        relay_control.sync_manifest(repo, "task-1", [self.source("b"), self.source("a")], self.now())
        for file_id in ("a", "b"):
            record = relay_state.claim(repo.records[("task-1", file_id)], f"lease-{file_id}", self.now())
            repo.records[("task-1", file_id)] = relay_state.complete(
                record,
                f"lease-{file_id}",
                f"drive-{file_id}",
                TEST_MD5,
                TEST_MD5,
                self.now(),
            )
        self.assertEqual(
            relay_control.verified_results(repo.list_records("task-1")),
            [
                {"file_id": "a", "drive_id": "drive-a"},
                {"file_id": "b", "drive_id": "drive-b"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
