from __future__ import annotations

import sys
from pathlib import Path
import unittest

TASK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_DIR))

import relay_coordinator  # noqa: E402
import relay_state  # noqa: E402


class RelayCoordinatorTests(unittest.TestCase):
    def base_task(self):
        return {
            "id": "bd-20261027T120000Z-abcdef",
            "status": "RUNNING",
            "files_total": 0,
            "files_done": 0,
            "bytes_total": 0,
            "bytes_done": 0,
        }

    def test_prepare_projection_keeps_full_manifest_totals(self):
        task = relay_coordinator.apply_prepare_projection(
            self.base_task(),
            {
                "mover_task_id": "mover-task",
                "drive_root_id": "root-id",
                "progress": {
                    "files_total": 20,
                    "bytes_total": 1000,
                    "files_done": 4,
                    "bytes_done": 100,
                },
            },
        )
        self.assertEqual(task["mover_task_id"], "mover-task")
        self.assertEqual(task["files_total"], 20)
        self.assertEqual(task["bytes_total"], 1000)
        self.assertEqual(
            task["drive_folder_url"],
            "https://drive.google.com/drive/folders/root-id",
        )

    def test_relay_projection_uses_byte_offsets_not_only_completed_files(self):
        task = self.base_task()
        task["files_total"] = 2
        task["bytes_total"] = 300
        records = [
            {
                "status": relay_state.ACTIVE,
                "size": 100,
                "confirmed_offset": 40,
            },
            {
                "status": relay_state.VERIFIED,
                "size": 200,
                "confirmed_offset": 200,
            },
        ]
        task = relay_coordinator.project_relay_progress(task, records)
        self.assertEqual(task["files_done"], 1)
        self.assertEqual(task["bytes_done"], 240)
        self.assertEqual(task["relay_active_workers"], 1)
        self.assertEqual(task["files_total"], 2)
        self.assertEqual(task["bytes_total"], 300)


if __name__ == "__main__":
    unittest.main()
