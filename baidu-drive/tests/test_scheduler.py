from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
import unittest

TASK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_DIR))

import scheduler  # noqa: E402


UTC = dt.timezone.utc


class SchedulerTests(unittest.TestCase):
    def now(self):
        return dt.datetime(2026, 10, 27, 12, 0, tzinfo=UTC)

    def file(self, file_id, size, offset=0, status="READY", heartbeat=None, path=None):
        return {
            "id": file_id,
            "logical_path": path or f"/{file_id}.bin",
            "size": size,
            "confirmed_offset": offset,
            "status": status,
            "heartbeat_at": heartbeat,
        }

    def test_small_file_is_one_relay_chunk(self):
        policy = scheduler.Policy(chunk_bytes=512 * scheduler.MIB)
        window = scheduler.chunk_window(0, 100 * scheduler.MIB, policy)
        self.assertEqual(window, (0, 100 * scheduler.MIB - 1))

    def test_large_file_uses_fixed_drive_compatible_chunk(self):
        window = scheduler.chunk_window(
            2 * scheduler.GIB,
            20 * scheduler.GIB,
        )
        self.assertEqual(
            window,
            (2 * scheduler.GIB, 2 * scheduler.GIB + 512 * scheduler.MIB - 1),
        )

    def test_final_chunk_may_be_smaller(self):
        start = 2 * scheduler.GIB
        total = start + 7 * scheduler.MIB + 13
        self.assertEqual(
            scheduler.chunk_window(start, total),
            (start, total - 1),
        )

    def test_chunk_size_must_be_drive_aligned(self):
        with self.assertRaises(ValueError):
            scheduler.Policy(chunk_bytes=512 * scheduler.MIB + 1).validate()

    def test_remote_confirmed_offset_wins(self):
        self.assertEqual(
            scheduler.reconcile_confirmed_offset(
                4 * scheduler.GIB,
                5 * scheduler.GIB,
                20 * scheduler.GIB,
            ),
            5 * scheduler.GIB,
        )

    def test_remote_offset_can_prove_less_than_stale_repo_hint(self):
        self.assertEqual(
            scheduler.reconcile_confirmed_offset(
                5 * scheduler.GIB,
                4 * scheduler.GIB,
                20 * scheduler.GIB,
            ),
            4 * scheduler.GIB,
        )

    def test_scheduler_prefers_independent_longest_remaining_files(self):
        files = [
            self.file("a", 1 * scheduler.GIB),
            self.file("b", 9 * scheduler.GIB),
            self.file("c", 5 * scheduler.GIB),
            self.file("d", 2 * scheduler.GIB),
        ]
        self.assertEqual(
            scheduler.choose_files(files, self.now()),
            ["b", "c", "d"],
        )

    def test_live_worker_consumes_capacity(self):
        heartbeat = (self.now() - dt.timedelta(minutes=1)).isoformat()
        files = [
            self.file("active", 20 * scheduler.GIB, status="ACTIVE", heartbeat=heartbeat),
            self.file("b", 9 * scheduler.GIB),
            self.file("c", 5 * scheduler.GIB),
            self.file("d", 2 * scheduler.GIB),
        ]
        self.assertEqual(scheduler.choose_files(files, self.now()), ["b", "c"])

    def test_stale_worker_is_reclaimable(self):
        heartbeat = (self.now() - dt.timedelta(hours=2)).isoformat()
        files = [
            self.file("stale", 20 * scheduler.GIB, status="ACTIVE", heartbeat=heartbeat),
            self.file("b", 9 * scheduler.GIB),
            self.file("c", 5 * scheduler.GIB),
        ]
        self.assertEqual(
            scheduler.choose_files(files, self.now()),
            ["stale", "b", "c"],
        )

    def test_same_file_is_never_split_across_multiple_assignments(self):
        files = [self.file("only", 100 * scheduler.GIB)]
        self.assertEqual(scheduler.choose_files(files, self.now()), ["only"])

    def test_soft_stop_leaves_hard_timeout_margin(self):
        policy = scheduler.Policy()
        started = self.now()
        self.assertFalse(
            scheduler.should_soft_stop(
                started,
                started + dt.timedelta(hours=4, minutes=59),
                policy,
            )
        )
        self.assertTrue(
            scheduler.should_soft_stop(
                started,
                started + dt.timedelta(hours=5),
                policy,
            )
        )
        self.assertGreater(policy.hard_runtime_seconds, policy.soft_runtime_seconds)


if __name__ == "__main__":
    unittest.main()
