from __future__ import annotations

import importlib.util
import io
import json
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "trigger_github_test_archive.py"
SPEC = importlib.util.spec_from_file_location("trigger_github_test_archive", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handoff)


class FakeResponse:
    def __init__(self, status: int, body: bytes = b"") -> None:
        self.status = status
        self.body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            return self.body
        return self.body[:size]


class FixedCapabilityTests(unittest.TestCase):
    def test_dispatch_target_is_fixed(self) -> None:
        self.assertEqual(
            handoff.DISPATCH_URL,
            "https://api.github.com/repos/teddyli18000/Github_test/"
            "actions/workflows/ai-daily-archive.yml/dispatches",
        )
        self.assertEqual(handoff.DISPATCH_REF, "master")
        self.assertEqual(handoff.TOKEN_ENV, "AI_DAILY_DISPATCH_TOKEN")

    def test_raw_urls_are_fixed_to_web_ingest_main(self) -> None:
        html_url, json_url = handoff.raw_urls("2026-09-03")
        self.assertEqual(
            html_url,
            "https://raw.githubusercontent.com/teddyli18000/web-ingest/main/"
            "ai-daily/data/2026/09/03/aihot-daily.html",
        )
        self.assertEqual(
            json_url,
            "https://raw.githubusercontent.com/teddyli18000/web-ingest/main/"
            "ai-daily/data/2026/09/03/aihot-daily.json",
        )

    def test_invalid_date_is_rejected(self) -> None:
        for value in ("2026-9-03", "2026-02-30", "../../main", "2026-09-03;echo x"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                handoff.validate_report_date(value)


class RawVisibilityTests(unittest.TestCase):
    def test_both_raw_files_must_be_readable(self) -> None:
        with (
            mock.patch.object(
                handoff,
                "raw_is_readable",
                side_effect=[False, False, True, True],
            ) as readable,
            mock.patch.object(handoff.time, "sleep") as sleep,
            mock.patch.object(handoff.time, "monotonic", return_value=0.0),
        ):
            handoff.wait_for_raw_mirror("2026-09-03")

        self.assertEqual(readable.call_count, 4)
        sleep.assert_called_once_with(5)

    def test_visibility_failure_stops_without_dispatch(self) -> None:
        with (
            mock.patch.object(handoff, "raw_is_readable", return_value=False),
            mock.patch.object(handoff.time, "sleep"),
            mock.patch.object(
                handoff.time,
                "monotonic",
                side_effect=[0.0] + [61.0] * handoff.RAW_ATTEMPTS,
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "did not become readable"):
                handoff.wait_for_raw_mirror("2026-09-03")


class DispatchTests(unittest.TestCase):
    def test_http_204_is_the_only_success(self) -> None:
        with mock.patch.object(
            handoff.urllib.request,
            "urlopen",
            return_value=FakeResponse(204),
        ) as urlopen:
            handoff.dispatch_archive("2026-09-03", "test-token")

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, handoff.DISPATCH_URL)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(
            json.loads(request.data.decode("utf-8")),
            {"ref": "master", "inputs": {"date": "2026-09-03"}},
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")

    def test_one_short_retry_is_allowed_for_503(self) -> None:
        error = urllib.error.HTTPError(
            handoff.DISPATCH_URL,
            503,
            "Service Unavailable",
            {},
            io.BytesIO(b'{"message":"temporary"}'),
        )
        with (
            mock.patch.object(
                handoff.urllib.request,
                "urlopen",
                side_effect=[error, FakeResponse(204)],
            ) as urlopen,
            mock.patch.object(handoff.time, "sleep") as sleep,
        ):
            handoff.dispatch_archive("2026-09-03", "test-token")

        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(handoff.DISPATCH_RETRY_SECONDS)

    def test_403_fails_without_retry(self) -> None:
        error = urllib.error.HTTPError(
            handoff.DISPATCH_URL,
            403,
            "Forbidden",
            {},
            io.BytesIO(b'{"message":"forbidden"}'),
        )
        with mock.patch.object(
            handoff.urllib.request,
            "urlopen",
            side_effect=error,
        ) as urlopen:
            with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
                handoff.dispatch_archive("2026-09-03", "test-token")

        self.assertEqual(urlopen.call_count, 1)


class WorkflowOrderingTests(unittest.TestCase):
    def test_handoff_is_after_successful_push_and_uses_only_actions_secret(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        warm = (repo_root / ".github/workflows/ai-daily-warm.yml").read_text()
        recovery = (repo_root / ".github/workflows/ai-daily.yml").read_text()

        for workflow in (warm, recovery):
            self.assertIn("id: commit", workflow)
            self.assertIn('echo "pushed=true" >> "$GITHUB_OUTPUT"', workflow)
            self.assertIn("git push origin HEAD:main", workflow)
            self.assertLess(
                workflow.index("git push origin HEAD:main"),
                workflow.index('echo "pushed=true" >> "$GITHUB_OUTPUT"'),
            )
            self.assertIn("steps.commit.outputs.pushed == 'true'", workflow)
            self.assertIn("github.run_attempt > 1", workflow)
            self.assertIn(
                "REPORT_DATE: ${{ steps.fetch.outputs.report_date || steps.snapshot.outputs.date }}",
                workflow,
            )
            self.assertIn(
                "AI_DAILY_DISPATCH_TOKEN: ${{ secrets.AI_DAILY_DISPATCH_TOKEN }}",
                workflow,
            )
            self.assertNotIn("vars.AI_DAILY_DISPATCH_TOKEN", workflow)
            self.assertIn(
                'python3 ai-daily/trigger_github_test_archive.py --date "$REPORT_DATE"',
                workflow,
            )

        self.assertIn(
            "if: github.event_name == 'schedule' && (steps.commit.outputs.pushed == 'true' || "
            "(github.run_attempt > 1 && steps.snapshot.outputs.present == 'true'))",
            recovery,
        )


if __name__ == "__main__":
    unittest.main()
