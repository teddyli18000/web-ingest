from __future__ import annotations

import argparse
import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "fetch_aihot_daily.py"
SPEC = importlib.util.spec_from_file_location("fetch_aihot_daily", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
aihot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(aihot)


def args(*, allow_not_ready: bool) -> argparse.Namespace:
    return argparse.Namespace(
        date=None,
        attempts=1,
        retry_seconds=0,
        allow_not_ready=allow_not_ready,
    )


def previous_report() -> bytes:
    return json.dumps(
        {
            "schemaVersion": 1,
            "report": {
                "date": "2026-09-01",
                "sections": [],
                "links": {"aihot": "https://aihot.virxact.com/daily/2026-09-01"},
            },
        }
    ).encode()


class EarlyProbeTests(unittest.TestCase):
    def test_expected_not_ready_can_exit_successfully(self) -> None:
        with (
            mock.patch.object(aihot, "parse_args", return_value=args(allow_not_ready=True)),
            mock.patch.object(aihot, "today_beijing", return_value="2026-09-02"),
            mock.patch.object(aihot, "fetch_raw", return_value=previous_report()),
        ):
            self.assertEqual(aihot.main(), 0)

    def test_not_ready_remains_failure_without_soft_probe_mode(self) -> None:
        with (
            mock.patch.object(aihot, "parse_args", return_value=args(allow_not_ready=False)),
            mock.patch.object(aihot, "today_beijing", return_value="2026-09-02"),
            mock.patch.object(aihot, "fetch_raw", return_value=previous_report()),
        ):
            self.assertEqual(aihot.main(), 1)

    def test_hard_fetch_error_is_not_hidden_by_soft_probe_mode(self) -> None:
        with (
            mock.patch.object(aihot, "parse_args", return_value=args(allow_not_ready=True)),
            mock.patch.object(aihot, "today_beijing", return_value="2026-09-02"),
            mock.patch.object(aihot, "fetch_raw", side_effect=RuntimeError("boom")),
        ):
            self.assertEqual(aihot.main(), 1)


if __name__ == "__main__":
    unittest.main()
