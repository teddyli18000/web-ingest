from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
import unittest

TASK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_DIR))

import prepare_worker  # noqa: E402
import relay_state  # noqa: E402

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


class PrepareWorkerTests(unittest.TestCase):
    def now(self):
        return dt.datetime(2026, 10, 27, 16, 0, tzinfo=UTC)

    def test_apply_prepare_result_keeps_public_total_and_drive_root(self):
        task = {"id": "task-1", "files_total": 0, "bytes_total": 0}
        value = prepare_worker.apply_prepare_result(
            task,
            {
                "mover_task_id": "mover-1",
                "drive_root_id": "drive-root",
                "progress": {
                    "files_total": 10,
                    "files_done": 4,
                    "bytes_total": 1000,
                    "bytes_done": 400,
                },
            },
        )
        self.assertEqual(value["mover_task_id"], "mover-1")
        self.assertEqual(value["files_total"], 10)
        self.assertEqual(value["bytes_total"], 1000)
        self.assertEqual(value["drive_folder_id"], "drive-root")
        self.assertIn("drive-root", value["drive_folder_url"])

    def test_relay_progress_never_moves_public_progress_backwards(self):
        task = {
            "id": "task-1",
            "files_done": 5,
            "bytes_done": 500,
            "files_total": 10,
            "bytes_total": 1000,
        }
        first = relay_state.new_record("task-1", source("a", 200), self.now())
        first = relay_state.claim(first, "lease-a", self.now())
        first = relay_state.apply_relay_checkpoint(
            first, "lease-a", 150, 150, "opaque", None, self.now()
        )
        second = relay_state.new_record("task-1", source("b", 100), self.now())
        second = relay_state.claim(second, "lease-b", self.now())
        second = relay_state.apply_relay_checkpoint(
            second, "lease-b", 100, 100, "opaque-final", TEST_MD5, self.now()
        )
        second = relay_state.complete(
            second, "lease-b", "drive-b", TEST_MD5, TEST_MD5, self.now()
        )
        value = prepare_worker.merge_relay_progress(task, [first, second])
        self.assertEqual(value["files_done"], 5)
        self.assertEqual(value["bytes_done"], 500)
        self.assertEqual(value["files_total"], 10)
        self.assertEqual(value["bytes_total"], 1000)

    def test_relay_progress_can_advance_beyond_last_cleanup_checkpoint(self):
        task = {
            "id": "task-1",
            "files_done": 0,
            "bytes_done": 0,
            "files_total": 2,
            "bytes_total": 300,
        }
        record = relay_state.new_record("task-1", source("a", 200), self.now())
        record = relay_state.claim(record, "lease-a", self.now())
        record = relay_state.apply_relay_checkpoint(
            record, "lease-a", 150, 150, "opaque", None, self.now()
        )
        value = prepare_worker.merge_relay_progress(task, [record])
        self.assertEqual(value["bytes_done"], 150)
        self.assertEqual(value["files_done"], 0)


if __name__ == "__main__":
    unittest.main()
