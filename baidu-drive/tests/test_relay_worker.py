from __future__ import annotations

import copy
import datetime as dt
import sys
from pathlib import Path
import unittest

TASK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_DIR))

import relay_state  # noqa: E402
import relay_worker  # noqa: E402

UTC = dt.timezone.utc
TEST_MD5 = "0123456789abcdef0123456789abcdef"


class FakeRepo:
    def __init__(self, record):
        self.record = copy.deepcopy(record)
        self.messages = []

    def read_record(self, task_id, file_id):
        if self.record["task_id"] != task_id or self.record["file_id"] != file_id:
            return None, None
        return copy.deepcopy(self.record), "sha"

    def mutate_record(self, task_id, file_id, mutator, message):
        current, _ = self.read_record(task_id, file_id)
        if current is None:
            raise RuntimeError("missing")
        self.record = mutator(current)
        self.messages.append(message)
        return copy.deepcopy(self.record)


def make_record(now, size=100):
    record = relay_state.new_record(
        "task-1",
        {
            "file_id": "file-1",
            "batch_id": "batch-1",
            "logical_path": "/file.bin",
            "parent_path": "/",
            "name": "file.bin",
            "size": size,
            "md5": "",
            "baidu_staging_path": "/BaiduDriveMover/task/batch/file-1",
            "drive_parent_id": "drive-root",
        },
        now,
    )
    return relay_state.claim(record, "lease-1", now)


class RelayWorkerTests(unittest.TestCase):
    def now(self):
        return dt.datetime(2026, 10, 27, 15, 0, tzinfo=UTC)

    def test_worker_checkpoints_each_window_then_verifies(self):
        repo = FakeRepo(make_record(self.now(), 100))
        outputs = iter([
            (0, {
                "session_sealed": "v1.a.b",
                "confirmed_offset": 50,
                "hash_offset": 50,
                "md5_state": "opaque-half",
                "complete": False,
            }),
            (0, {
                "session_sealed": "v1.a.b",
                "confirmed_offset": 100,
                "hash_offset": 100,
                "md5_state": "opaque-final",
                "computed_md5": TEST_MD5,
                "complete": True,
                "drive_file_id": "drive-file",
                "drive_md5": TEST_MD5,
            }),
        ])
        status = relay_worker.run_worker_loop(
            repo,
            "task-1",
            "file-1",
            "lease-1",
            lambda record: next(outputs),
            now_fn=self.now,
            monotonic_fn=lambda: 0.0,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(status, relay_state.VERIFIED)
        self.assertEqual(repo.record["status"], relay_state.VERIFIED)
        self.assertEqual(repo.record["confirmed_offset"], 100)
        self.assertEqual(repo.record["computed_md5"], TEST_MD5)
        self.assertIsNone(repo.record["session_sealed"])
        self.assertEqual(len(repo.messages), 2)

    def test_retryable_error_keeps_reconciled_checkpoint_before_retry(self):
        repo = FakeRepo(make_record(self.now(), 100))
        calls = 0
        sleeps = []

        def step(record):
            nonlocal calls
            calls += 1
            if calls == 1:
                return 1, {
                    "session_sealed": "v1.a.b",
                    "confirmed_offset": 25,
                    "hash_offset": 25,
                    "md5_state": "opaque-quarter",
                    "error_kind": "retryable",
                }
            return 0, {
                "session_sealed": "v1.a.b",
                "confirmed_offset": 100,
                "hash_offset": 100,
                "md5_state": "opaque-final",
                "computed_md5": TEST_MD5,
                "complete": True,
                "drive_file_id": "drive-file",
                "drive_md5": TEST_MD5,
            }

        status = relay_worker.run_worker_loop(
            repo,
            "task-1",
            "file-1",
            "lease-1",
            step,
            now_fn=self.now,
            monotonic_fn=lambda: 0.0,
            sleep_fn=sleeps.append,
        )
        self.assertEqual(status, relay_state.VERIFIED)
        self.assertEqual(sleeps, [])
        self.assertEqual(calls, 2)
        self.assertEqual(repo.record["confirmed_offset"], 100)

    def test_bounded_retry_failure_releases_lease(self):
        repo = FakeRepo(make_record(self.now(), 100))
        sleeps = []

        def step(record):
            return 1, {
                "session_sealed": "v1.a.b",
                "confirmed_offset": int(record.get("confirmed_offset") or 0),
                "hash_offset": int(record.get("hash_offset") or 0),
                "md5_state": record.get("md5_state"),
                "error_kind": "retryable",
            }

        status = relay_worker.run_worker_loop(
            repo,
            "task-1",
            "file-1",
            "lease-1",
            step,
            now_fn=self.now,
            monotonic_fn=lambda: 0.0,
            sleep_fn=sleeps.append,
            retry_limit=3,
        )
        self.assertEqual(status, relay_state.FAILED_RETRYABLE)
        self.assertEqual(sleeps, [1.0, 2.0])
        self.assertEqual(repo.record["status"], relay_state.FAILED_RETRYABLE)
        self.assertIsNone(repo.record["lease_id"])
        self.assertEqual(repo.record["last_error"], relay_worker.public_error("retryable"))

    def test_soft_stop_pauses_before_starting_new_window(self):
        repo = FakeRepo(make_record(self.now(), 100))
        monotonic = iter([0.0, 18_000.0])
        called = False

        def step(record):
            nonlocal called
            called = True
            return 0, {}

        status = relay_worker.run_worker_loop(
            repo,
            "task-1",
            "file-1",
            "lease-1",
            step,
            now_fn=self.now,
            monotonic_fn=lambda: next(monotonic),
            sleep_fn=lambda _: None,
            soft_runtime_seconds=18_000,
        )
        self.assertEqual(status, relay_state.PAUSED)
        self.assertFalse(called)
        self.assertEqual(repo.record["status"], relay_state.PAUSED)
        self.assertIsNone(repo.record["lease_id"])

    def test_expired_session_restarts_from_zero_then_finishes(self):
        repo = FakeRepo(make_record(self.now(), 100))
        calls = 0

        def step(record):
            nonlocal calls
            calls += 1
            if calls == 1:
                return 0, {
                    "session_sealed": "v1.old.session",
                    "confirmed_offset": 50,
                    "hash_offset": 50,
                    "md5_state": "opaque-half",
                }
            if calls == 2:
                return 1, {
                    "session_sealed": "v1.old.session",
                    "error_kind": "session_expired",
                }
            self.assertFalse(record.get("session_sealed"))
            self.assertEqual(record.get("confirmed_offset"), 0)
            self.assertEqual(record.get("hash_offset"), 0)
            return 0, {
                "session_sealed": "v1.new.session",
                "confirmed_offset": 100,
                "hash_offset": 100,
                "md5_state": "opaque-final",
                "computed_md5": TEST_MD5,
                "complete": True,
                "drive_file_id": "drive-file",
                "drive_md5": TEST_MD5,
            }

        status = relay_worker.run_worker_loop(
            repo,
            "task-1",
            "file-1",
            "lease-1",
            step,
            now_fn=self.now,
            monotonic_fn=lambda: 0.0,
            sleep_fn=lambda _: None,
        )
        self.assertEqual(status, relay_state.VERIFIED)
        self.assertEqual(calls, 3)
        self.assertEqual(repo.record["confirmed_offset"], 100)

    def test_repeated_expiry_becomes_retryable_not_permanent(self):
        repo = FakeRepo(make_record(self.now(), 100))
        status = relay_worker.run_worker_loop(
            repo,
            "task-1",
            "file-1",
            "lease-1",
            lambda record: (1, {
                "session_sealed": str(record.get("session_sealed") or "v1.a.b"),
                "error_kind": "session_expired",
            }),
            now_fn=self.now,
            monotonic_fn=lambda: 0.0,
            sleep_fn=lambda _: None,
            session_restart_limit=1,
        )
        self.assertEqual(status, relay_state.FAILED_RETRYABLE)
        self.assertEqual(repo.record["status"], relay_state.FAILED_RETRYABLE)

    def test_step_cannot_swap_session_capability(self):
        record = make_record(self.now(), 100)
        record = relay_state.attach_session(record, "lease-1", "v1.old.session", self.now())
        with self.assertRaises(relay_worker.WorkerError):
            relay_worker.apply_step_output(
                record,
                "lease-1",
                {
                    "session_sealed": "v1.new.session",
                    "confirmed_offset": 0,
                    "hash_offset": 0,
                },
                self.now(),
            )

    def test_step_cannot_rewind_confirmed_offset(self):
        record = make_record(self.now(), 100)
        record = relay_state.attach_session(record, "lease-1", "v1.a.b", self.now())
        record = relay_state.apply_relay_checkpoint(
            record, "lease-1", 50, 50, "opaque-half", None, self.now()
        )
        with self.assertRaises(relay_worker.WorkerError):
            relay_worker.apply_step_output(
                record,
                "lease-1",
                {
                    "session_sealed": "v1.a.b",
                    "confirmed_offset": 25,
                    "hash_offset": 25,
                    "md5_state": "opaque-quarter",
                },
                self.now(),
            )


if __name__ == "__main__":
    unittest.main()
