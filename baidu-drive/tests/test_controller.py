from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "controller.py"
spec = importlib.util.spec_from_file_location("baidu_drive_controller", MODULE_PATH)
controller = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(controller)


class ControlTests(unittest.TestCase):
    def test_parse_control(self):
        body = """command: start\nshare_url: https://pan.baidu.com/s/abc\nextraction_code: 1234\n"""
        self.assertEqual(
            controller.parse_control(body),
            {
                "command": "start",
                "share_url": "https://pan.baidu.com/s/abc",
                "extraction_code": "1234",
            },
        )

    def test_validate_share_url_rejects_non_baidu(self):
        with self.assertRaises(controller.ProtocolError):
            controller.validate_share_url("https://example.com/s/abc")

    def test_task_id_is_stable_for_timestamp(self):
        when = dt.datetime(2026, 10, 27, 12, 30, tzinfo=dt.timezone.utc)
        value = controller.task_id("https://pan.baidu.com/s/abc", when)
        self.assertRegex(value, r"^bd-20261027T123000Z-[0-9a-f]{6}$")

    def test_start_creates_auth_blocked_task(self):
        runtime = dict(controller.DEFAULT_RUNTIME)
        control = {
            "command": "start",
            "share_url": "https://pan.baidu.com/s/abc",
            "extraction_code": "1234",
        }
        new_runtime, task, message = controller.apply_command("start", control, runtime, None)
        self.assertEqual(task["status"], "BLOCKED_AUTH_SETUP")
        self.assertEqual(task["extraction_code"], "1234")
        self.assertEqual(new_runtime["active_task"], task["id"])
        self.assertIn("OAuth", message)

    def test_start_refuses_second_active_task(self):
        active = {"id": "bd-1", "status": "BLOCKED_AUTH_SETUP"}
        with self.assertRaises(controller.ProtocolError):
            controller.apply_command(
                "start",
                {"command": "start", "share_url": "https://pan.baidu.com/s/abc", "extraction_code": "-"},
                dict(controller.DEFAULT_RUNTIME),
                active,
            )

    def test_cancel_clears_active(self):
        runtime = dict(controller.DEFAULT_RUNTIME)
        runtime["active_task"] = "bd-1"
        active = {"id": "bd-1", "status": "BLOCKED_AUTH_SETUP", "message": "x"}
        new_runtime, task, _ = controller.apply_command("cancel", controller.default_control(), runtime, active)
        self.assertEqual(task["status"], "CANCELED")
        self.assertIsNone(new_runtime["active_task"])
        self.assertEqual(new_runtime["last_task"], "bd-1")

    def test_retry_only_from_retryable_state(self):
        runtime = dict(controller.DEFAULT_RUNTIME)
        active = {"id": "bd-1", "status": "COMPLETED", "attempt": 0}
        with self.assertRaises(controller.ProtocolError):
            controller.apply_command("retry", controller.default_control(), runtime, active)

    def test_render_release_never_echoes_extraction_code_into_status(self):
        task = {
            "id": "bd-1",
            "status": "BLOCKED_AUTH_SETUP",
            "source_url": "https://pan.baidu.com/s/abc",
            "files_done": 0,
            "files_total": 0,
            "bytes_done": 0,
            "bytes_total": 0,
            "extraction_code": "secret-ish-share-code",
        }
        body = controller.render_release(controller.default_control(), controller.DEFAULT_RUNTIME, task, task["status"], "blocked")
        self.assertNotIn("secret-ish-share-code", body)


if __name__ == "__main__":
    unittest.main()
