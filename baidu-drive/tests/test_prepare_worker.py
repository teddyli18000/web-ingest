from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
import unittest
from unittest import mock

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

    def test_auth_updated_can_reenter_a_login_blocked_task(self):
        task_id = "bd-20261106T160000Z-abcd"
        task = {"id": task_id, "status": "NEEDS_LOGIN"}
        gh = mock.Mock()
        gh.read_json.return_value = ({"active_task": task_id}, None)
        gh.mock = None
        with mock.patch.object(prepare_worker.controller, "load_task", return_value=task), \
             mock.patch.object(prepare_worker, "prepare_ready", return_value=False), \
             mock.patch.object(prepare_worker.legacy_worker, "update_public_state") as update:
            result = prepare_worker.run_prepare_worker(gh, mock.Mock(), task_id, "auth-updated")
            self.assertEqual(result, 0)
            self.assertEqual(update.call_args.kwargs["status"], "NEEDS_LOGIN")

    def test_login_blocked_task_does_not_restart_without_new_authorization(self):
        task_id = "bd-20261106T160000Z-abcd"
        task = {"id": task_id, "status": "NEEDS_LOGIN"}
        gh = mock.Mock()
        gh.read_json.return_value = ({"active_task": task_id}, None)
        with mock.patch.object(prepare_worker.controller, "load_task", return_value=task), \
             mock.patch.object(prepare_worker, "prepare_ready") as ready:
            result = prepare_worker.run_prepare_worker(gh, mock.Mock(), task_id, "file-worker-completed")
            self.assertEqual(result, 0)
            ready.assert_not_called()

    def test_apply_prepare_result_keeps_manifest_totals_and_drive_root(self):
        task = {"id": "task-1", "files_total": 0, "bytes_total": 0, "files_done": 9, "bytes_done": 900}
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
        self.assertEqual(value["files_done"], 9)
        self.assertEqual(value["bytes_done"], 900)
        self.assertEqual(value["drive_folder_id"], "drive-root")

    def test_relay_projection_follows_current_remote_truth_even_backward(self):
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
        self.assertEqual(value["files_done"], 1)
        self.assertEqual(value["bytes_done"], 250)
        self.assertEqual(value["files_total"], 10)
        self.assertEqual(value["bytes_total"], 1000)

    def test_schedule_projection_blocks_only_when_no_safe_work_remains(self):
        blocked = relay_state.new_record("task-1", source("a", 100), self.now())
        blocked = relay_state.claim(blocked, "lease-a", self.now())
        blocked = relay_state.block_reconcile(blocked, "lease-a", self.now(), "expired")
        status, message = prepare_worker.schedule_projection(
            {"id": "task-1"}, [blocked], [], self.now()
        )
        self.assertEqual(status, "BLOCKED")
        self.assertIn("reconciliation", message.lower())
        self.assertIn("no unsafe replay", message.lower())

    def test_schedule_projection_can_continue_other_independent_files(self):
        blocked = relay_state.new_record("task-1", source("a", 100), self.now())
        blocked = relay_state.claim(blocked, "lease-a", self.now())
        blocked = relay_state.block_reconcile(blocked, "lease-a", self.now(), "expired")
        active = relay_state.new_record("task-1", source("b", 100), self.now())
        active = relay_state.claim(active, "lease-b", self.now())
        status, message = prepare_worker.schedule_projection(
            {"id": "task-1"}, [blocked, active], [], self.now()
        )
        self.assertEqual(status, "RUNNING")
        self.assertIn("awaiting reconciliation", message.lower())


if __name__ == "__main__":
    unittest.main()
