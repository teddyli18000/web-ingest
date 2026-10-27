from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
import unittest

TASK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_DIR))

import relay_state  # noqa: E402

UTC = dt.timezone.utc


class RelayStateTests(unittest.TestCase):
    def now(self):
        return dt.datetime(2026, 10, 27, 13, 0, tzinfo=UTC)

    def source(self, size=1024):
        return {
            "file_id": "file-1",
            "batch_id": "batch-1",
            "logical_path": "/alpha/file.bin",
            "parent_path": "/alpha",
            "name": "file.bin",
            "size": size,
            "md5": "0123456789abcdef0123456789abcdef",
            "baidu_staging_path": "/BaiduDriveMover/task/batch/file-1",
            "drive_parent_id": "drive-parent",
        }

    def record(self, size=1024):
        return relay_state.new_record("task-1", self.source(size), self.now())

    def test_new_record_is_ready_and_path_scoped(self):
        record = self.record()
        self.assertEqual(record["status"], relay_state.READY)
        self.assertEqual(record["confirmed_offset"], 0)
        self.assertEqual(
            relay_state.state_path("task-1", "file-1"),
            "baidu-drive/state/files/task-1/file-1.json",
        )

    def test_claim_creates_single_lease(self):
        record = relay_state.claim(self.record(), "lease-1", self.now())
        self.assertEqual(record["status"], relay_state.ACTIVE)
        self.assertEqual(record["lease_id"], "lease-1")
        self.assertEqual(record["attempts"], 1)
        with self.assertRaises(relay_state.RelayStateError):
            relay_state.claim(record, "lease-2", self.now() + dt.timedelta(minutes=1))

    def test_stale_active_lease_can_be_reclaimed(self):
        record = relay_state.claim(self.record(), "lease-old", self.now())
        reclaimed = relay_state.claim(
            record,
            "lease-new",
            self.now() + dt.timedelta(hours=2),
        )
        self.assertEqual(reclaimed["lease_id"], "lease-new")
        self.assertEqual(reclaimed["attempts"], 2)

    def test_stale_worker_cannot_write_after_reclaim(self):
        record = relay_state.claim(self.record(), "lease-old", self.now())
        record = relay_state.claim(
            record,
            "lease-new",
            self.now() + dt.timedelta(hours=2),
        )
        with self.assertRaises(relay_state.RelayStateError):
            relay_state.apply_remote_progress(
                record,
                "lease-old",
                512,
                self.now() + dt.timedelta(hours=2, minutes=1),
            )

    def test_drive_remote_truth_may_move_checkpoint_backwards(self):
        record = relay_state.claim(self.record(4096), "lease-1", self.now())
        record = relay_state.apply_remote_progress(record, "lease-1", 2048, self.now())
        record = relay_state.apply_remote_progress(
            record,
            "lease-1",
            1024,
            self.now() + dt.timedelta(minutes=1),
        )
        self.assertEqual(record["confirmed_offset"], 1024)

    def test_attach_session_refuses_implicit_replacement(self):
        record = relay_state.claim(self.record(), "lease-1", self.now())
        record = relay_state.attach_session(record, "lease-1", "v1.a.b", self.now())
        with self.assertRaises(relay_state.RelayStateError):
            relay_state.attach_session(record, "lease-1", "v1.c.d", self.now())

    def test_expired_session_reset_rewinds_remote_offset(self):
        record = relay_state.claim(self.record(4096), "lease-1", self.now())
        record = relay_state.attach_session(record, "lease-1", "v1.a.b", self.now())
        record = relay_state.apply_remote_progress(record, "lease-1", 3072, self.now())
        record = relay_state.replace_expired_session(
            record,
            "lease-1",
            "v1.c.d",
            self.now() + dt.timedelta(minutes=1),
        )
        self.assertEqual(record["confirmed_offset"], 0)
        self.assertEqual(record["session_sealed"], "v1.c.d")

    def test_pause_releases_lease_but_keeps_session_and_progress(self):
        record = relay_state.claim(self.record(4096), "lease-1", self.now())
        record = relay_state.attach_session(record, "lease-1", "v1.a.b", self.now())
        record = relay_state.apply_remote_progress(record, "lease-1", 2048, self.now())
        record = relay_state.pause(record, "lease-1", self.now(), "soft stop")
        self.assertEqual(record["status"], relay_state.PAUSED)
        self.assertIsNone(record["lease_id"])
        self.assertEqual(record["confirmed_offset"], 2048)
        self.assertEqual(record["session_sealed"], "v1.a.b")

    def test_complete_clears_capability_and_lease(self):
        record = relay_state.claim(self.record(4096), "lease-1", self.now())
        record = relay_state.attach_session(record, "lease-1", "v1.a.b", self.now())
        record = relay_state.complete(
            record,
            "lease-1",
            "drive-file",
            "abcdef",
            self.now(),
        )
        self.assertEqual(record["status"], relay_state.VERIFIED)
        self.assertEqual(record["confirmed_offset"], 4096)
        self.assertIsNone(record["session_sealed"])
        self.assertIsNone(record["lease_id"])

    def test_zero_byte_file_is_runnable(self):
        record = self.record(0)
        self.assertTrue(relay_state.runnable(record, self.now()))

    def test_aggregate_counts_remote_progress(self):
        a = self.record(100)
        b = relay_state.new_record("task-1", {**self.source(200), "file_id": "file-2"}, self.now())
        b = relay_state.claim(b, "lease-2", self.now())
        b = relay_state.apply_remote_progress(b, "lease-2", 50, self.now())
        self.assertEqual(
            relay_state.aggregate([a, b]),
            {
                "files_total": 2,
                "files_verified": 0,
                "bytes_total": 300,
                "bytes_confirmed": 50,
                "active_workers": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
