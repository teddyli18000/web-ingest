from __future__ import annotations

import argparse
import importlib.util
import json
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "fetch_aihot_daily.py"
SPEC = importlib.util.spec_from_file_location("fetch_aihot_daily", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
aihot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(aihot)


def args(
    *,
    allow_not_ready: bool,
    attempts: int = 1,
    retry_seconds: int = 0,
    request_timeout: float = 5,
    date: str | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        date=date,
        attempts=attempts,
        retry_seconds=retry_seconds,
        request_timeout=request_timeout,
        allow_not_ready=allow_not_ready,
    )


def report(report_date: str) -> bytes:
    return json.dumps(
        {
            "schemaVersion": 1,
            "report": {
                "date": report_date,
                "sections": [],
                "links": {"aihot": f"https://aihot.virxact.com/daily/{report_date}"},
            },
        }
    ).encode()


def page(report_date: str) -> bytes:
    return f"<!doctype html><html><body>{report_date}</body></html>".encode()


def http_error(url: str, status: int, headers: dict[str, str] | None = None) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url, status, "test error", headers or {}, None)


class EarlyProbeTests(unittest.TestCase):
    def test_expected_not_ready_can_exit_successfully(self) -> None:
        with (
            mock.patch.object(aihot, "parse_args", return_value=args(allow_not_ready=True)),
            mock.patch.object(aihot, "today_beijing", return_value="2026-09-02"),
            mock.patch.object(aihot, "fetch_raw", return_value=report("2026-09-01")),
        ):
            self.assertEqual(aihot.main(), 0)

    def test_not_ready_remains_failure_without_soft_probe_mode(self) -> None:
        with (
            mock.patch.object(aihot, "parse_args", return_value=args(allow_not_ready=False)),
            mock.patch.object(aihot, "today_beijing", return_value="2026-09-02"),
            mock.patch.object(aihot, "fetch_raw", return_value=report("2026-09-01")),
        ):
            self.assertEqual(aihot.main(), 1)

    def test_hard_fetch_error_is_not_hidden_by_soft_probe_mode(self) -> None:
        with (
            mock.patch.object(aihot, "parse_args", return_value=args(allow_not_ready=True)),
            mock.patch.object(aihot, "today_beijing", return_value="2026-09-02"),
            mock.patch.object(aihot, "fetch_raw", side_effect=RuntimeError("boom")),
        ):
            self.assertEqual(aihot.main(), 1)


class PublicationBoundaryTests(unittest.TestCase):
    def run_successfully_with_fetches(
        self,
        fetches: list[bytes | BaseException],
        *,
        parsed_args: argparse.Namespace,
        today: str = "2026-09-03",
    ) -> mock.Mock:
        with (
            mock.patch.object(aihot, "parse_args", return_value=parsed_args),
            mock.patch.object(aihot, "today_beijing", return_value=today),
            mock.patch.object(aihot, "fetch_raw", side_effect=fetches) as fetch_raw,
            mock.patch.object(aihot, "write_snapshot"),
            mock.patch.object(aihot, "set_github_outputs"),
            mock.patch.object(aihot.time, "sleep"),
        ):
            self.assertEqual(aihot.main(), 0)
            return fetch_raw

    def test_live_watch_uses_date_specific_endpoint_and_short_timeout(self) -> None:
        fetch_raw = self.run_successfully_with_fetches(
            [report("2026-09-03"), page("2026-09-03")],
            parsed_args=args(allow_not_ready=True, request_timeout=5),
        )

        self.assertEqual(
            fetch_raw.call_args_list[0],
            mock.call(
                "https://aihot.virxact.com/api/v1/dailies/2026-09-03",
                "application/json",
                5,
            ),
        )
        self.assertEqual(
            fetch_raw.call_args_list[1],
            mock.call(
                "https://aihot.virxact.com/daily/2026-09-03",
                "text/html,application/xhtml+xml",
                5,
            ),
        )

    def test_live_404_before_publication_retries_then_succeeds(self) -> None:
        api_url = "https://aihot.virxact.com/api/v1/dailies/2026-09-03"
        fetch_raw = self.run_successfully_with_fetches(
            [
                http_error(api_url, 404),
                report("2026-09-03"),
                page("2026-09-03"),
            ],
            parsed_args=args(allow_not_ready=True, attempts=2),
        )
        self.assertEqual(fetch_raw.call_count, 3)

    def test_page_can_lag_api_without_losing_the_publication(self) -> None:
        page_url = "https://aihot.virxact.com/daily/2026-09-03"
        fetch_raw = self.run_successfully_with_fetches(
            [
                report("2026-09-03"),
                http_error(page_url, 404),
                report("2026-09-03"),
                page("2026-09-03"),
            ],
            parsed_args=args(allow_not_ready=True, attempts=2),
        )
        self.assertEqual(fetch_raw.call_count, 4)

    def test_retry_after_is_obeyed_for_rate_limit(self) -> None:
        api_url = "https://aihot.virxact.com/api/v1/dailies/2026-09-03"
        with (
            mock.patch.object(
                aihot,
                "parse_args",
                return_value=args(
                    allow_not_ready=True,
                    attempts=2,
                    retry_seconds=1,
                ),
            ),
            mock.patch.object(aihot, "today_beijing", return_value="2026-09-03"),
            mock.patch.object(
                aihot,
                "fetch_raw",
                side_effect=[
                    http_error(api_url, 429, {"Retry-After": "7"}),
                    report("2026-09-03"),
                    page("2026-09-03"),
                ],
            ),
            mock.patch.object(aihot, "write_snapshot"),
            mock.patch.object(aihot, "set_github_outputs"),
            mock.patch.object(aihot.time, "sleep") as sleep,
        ):
            self.assertEqual(aihot.main(), 0)
            sleep.assert_called_once_with(7.0)

    def test_historical_404_is_a_hard_failure(self) -> None:
        api_url = "https://aihot.virxact.com/api/v1/dailies/2026-01-01"
        with (
            mock.patch.object(
                aihot,
                "parse_args",
                return_value=args(
                    allow_not_ready=True,
                    date="2026-01-01",
                ),
            ),
            mock.patch.object(
                aihot,
                "fetch_raw",
                side_effect=http_error(api_url, 404),
            ),
        ):
            self.assertEqual(aihot.main(), 1)


if __name__ == "__main__":
    unittest.main()
