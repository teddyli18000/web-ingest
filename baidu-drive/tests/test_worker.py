from __future__ import annotations

import sys
from pathlib import Path
import unittest

TASK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_DIR))

import worker  # noqa: E402


class WorkerTests(unittest.TestCase):
    def base_task(self):
        return {
            "id": "bd-20261027T120000Z-abcdef",
            "status": "RUNNING",
            "source_url": "https://pan.baidu.com/s/abc",
            "files_total": 0,
            "files_done": 0,
            "bytes_total": 0,
            "bytes_done": 0,
        }

    def test_checkpoint_path_is_task_scoped(self):
        self.assertEqual(
            worker.checkpoint_path("bd-20261027T120000Z-abcdef"),
            "baidu-drive/state/checkpoints/bd-20261027T120000Z-abcdef.sqlite.zlib.b64",
        )

    def test_completed_result_projects_drive_link_and_progress(self):
        result = {
            "mover_task_id": "task-upstream",
            "status": "COMPLETED",
            "drive_root_id": "drive-folder-id",
            "progress": {
                "files_total": 5,
                "files_done": 5,
                "bytes_total": 100,
                "bytes_done": 100,
            },
        }
        task, _ = worker.map_result(self.base_task(), result, 0)
        self.assertEqual(task["status"], "COMPLETED")
        self.assertEqual(task["mover_task_id"], "task-upstream")
        self.assertEqual(task["files_done"], 5)
        self.assertEqual(task["bytes_done"], 100)
        self.assertEqual(
            task["drive_folder_url"],
            "https://drive.google.com/drive/folders/drive-folder-id",
        )

    def test_paused_bridge_result_is_retryable(self):
        task, _ = worker.map_result(
            self.base_task(),
            {"status": "PAUSED", "pipeline_paused": True, "progress": {}},
            1,
        )
        self.assertEqual(task["status"], "PAUSED")

    def test_nonzero_unknown_result_fails_closed_to_blocked(self):
        task, message = worker.map_result(self.base_task(), {}, 1)
        self.assertEqual(task["status"], "BLOCKED")
        self.assertNotIn("token", message.lower())


if __name__ == "__main__":
    unittest.main()
