#!/usr/bin/env python3
"""Mirror one AIHOT daily report and its webpage byte-for-byte."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

API_BASE = "https://aihot.virxact.com/api/v1/dailies"
TIMEZONE = ZoneInfo("Asia/Shanghai")
USER_AGENT = "web-ingest/1.0 (+https://github.com/teddyli18000/web-ingest)"


class ReportNotReady(RuntimeError):
    """The endpoint is healthy, but today's report has not been published yet."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mirror an AIHOT daily report")
    parser.add_argument(
        "--date",
        help="Beijing calendar date (YYYY-MM-DD). Omit to wait for today's report.",
    )
    parser.add_argument("--attempts", type=int, default=1, help="Maximum fetch attempts")
    parser.add_argument(
        "--retry-seconds", type=int, default=300, help="Seconds between attempts"
    )
    parser.add_argument(
        "--request-timeout",
        type=float,
        default=15,
        help="Per-request timeout in seconds",
    )
    parser.add_argument(
        "--allow-not-ready",
        action="store_true",
        help="Exit successfully when every attempt only shows that today's report is not published yet",
    )
    return parser.parse_args()


def today_beijing() -> str:
    return datetime.now(TIMEZONE).date().isoformat()


def fetch_raw(url: str, accept: str, timeout_seconds: float) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": USER_AGENT,
            # The live collector cares about publication freshness. The date-specific
            # URL already avoids cross-day /latest caching; these headers additionally
            # ask intermediaries to revalidate rather than serve a stale response.
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        if response.status != 200:
            raise RuntimeError(f"unexpected HTTP status {response.status} for {url}")
        return response.read()


def retry_after_seconds(error: urllib.error.HTTPError) -> float | None:
    value = error.headers.get("Retry-After") if error.headers is not None else None
    if not value:
        return None

    try:
        return max(0.0, float(value))
    except ValueError:
        pass

    try:
        retry_at = parsedate_to_datetime(value)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return None


def transient_retry_seconds(base_seconds: int, attempt: int) -> float:
    if base_seconds <= 0:
        return 0.0
    return float(min(base_seconds * (2 ** max(0, attempt - 1)), 60))


def parse_and_validate_api(raw_body: bytes, expected_date: str) -> dict:
    payload = json.loads(raw_body)
    if not isinstance(payload, dict):
        raise RuntimeError("AIHOT response root is not a JSON object")
    if payload.get("schemaVersion") != 1:
        raise RuntimeError("unexpected AIHOT schemaVersion")

    report = payload.get("report")
    if not isinstance(report, dict):
        raise RuntimeError("AIHOT response does not contain report")

    report_date = report.get("date")
    if report_date != expected_date:
        raise ReportNotReady(
            f"report is {report_date!r}, waiting for {expected_date!r}"
        )
    if not isinstance(report.get("sections"), list):
        raise RuntimeError("AIHOT report.sections is missing or invalid")

    links = report.get("links")
    if not isinstance(links, dict):
        raise RuntimeError("AIHOT report.links is missing or invalid")
    page_url = links.get("aihot")
    expected_page_url = f"https://aihot.virxact.com/daily/{expected_date}"
    if page_url != expected_page_url:
        raise RuntimeError(
            f"unexpected AIHOT daily page URL: {page_url!r}; expected {expected_page_url!r}"
        )

    return report


def validate_page(raw_html: bytes, report_date: str) -> None:
    prefix = raw_html[:4096].lower()
    if b"<!doctype html" not in prefix and b"<html" not in prefix:
        raise RuntimeError("AIHOT daily page response is not HTML")

    try:
        text = raw_html.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("AIHOT daily page is not valid UTF-8 HTML") from exc

    if report_date not in text:
        raise RuntimeError(f"AIHOT daily page does not contain report date {report_date}")


def output_dir(report_date: str) -> Path:
    year, month, day = report_date.split("-")
    return Path(__file__).resolve().parent / "data" / year / month / day


def write_snapshot(path: Path, raw_body: bytes, label: str) -> None:
    if path.exists():
        existing = path.read_bytes()
        if existing == raw_body:
            print(f"{label} already exists and is byte-identical: {path}")
            return
        raise RuntimeError(
            f"{label} already exists with different bytes: {path}; "
            "refusing to silently rewrite history"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw_body)
    print(f"Saved byte-for-byte {label}: {path}")


def set_github_outputs(
    report_date: str,
    api_path: Path,
    page_path: Path,
    api_raw: bytes,
    page_raw: bytes,
) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")
    if not output_file:
        return
    with open(output_file, "a", encoding="utf-8") as handle:
        handle.write(f"report_date={report_date}\n")
        handle.write(f"api_path={api_path.as_posix()}\n")
        handle.write(f"page_path={page_path.as_posix()}\n")
        handle.write(f"api_sha256={hashlib.sha256(api_raw).hexdigest()}\n")
        handle.write(f"page_sha256={hashlib.sha256(page_raw).hexdigest()}\n")


def main() -> int:
    args = parse_args()
    if args.attempts < 1:
        raise SystemExit("--attempts must be at least 1")
    if args.retry_seconds < 0:
        raise SystemExit("--retry-seconds cannot be negative")
    if args.request_timeout <= 0:
        raise SystemExit("--request-timeout must be positive")

    live_mode = args.date is None
    expected_date = args.date or today_beijing()
    # Use the date-specific endpoint even for today's live watch. Unlike /latest,
    # this URL cannot still represent yesterday when today's report is being published.
    api_url = f"{API_BASE}/{expected_date}"

    last_error: Exception | None = None
    saw_hard_error = False
    for attempt in range(1, args.attempts + 1):
        retry_delay = float(args.retry_seconds)
        try:
            api_raw = fetch_raw(api_url, "application/json", args.request_timeout)
            report = parse_and_validate_api(api_raw, expected_date)
            page_url = report["links"]["aihot"]
            page_raw = fetch_raw(
                page_url,
                "text/html,application/xhtml+xml",
                args.request_timeout,
            )
            validate_page(page_raw, report["date"])

            day_dir = output_dir(report["date"])
            api_path = day_dir / "aihot-daily.json"
            page_path = day_dir / "aihot-daily.html"
            write_snapshot(api_path, api_raw, "AIHOT v1 API response")
            write_snapshot(page_path, page_raw, "AIHOT daily webpage response")
            set_github_outputs(
                report["date"], api_path, page_path, api_raw, page_raw
            )
            return 0
        except ReportNotReady as exc:
            last_error = exc
            print(f"Attempt {attempt}/{args.attempts} not ready: {exc}", file=sys.stderr)
        except urllib.error.HTTPError as exc:
            if live_mode and exc.code == 404:
                last_error = ReportNotReady(
                    f"AIHOT report or page for {expected_date} is not published yet"
                )
                print(
                    f"Attempt {attempt}/{args.attempts} not ready: {last_error}",
                    file=sys.stderr,
                )
            else:
                saw_hard_error = True
                last_error = exc
                if exc.code == 429:
                    retry_after = retry_after_seconds(exc)
                    if retry_after is not None:
                        retry_delay = retry_after
                elif 500 <= exc.code < 600:
                    retry_delay = transient_retry_seconds(args.retry_seconds, attempt)
                print(f"Attempt {attempt}/{args.attempts} failed: {exc}", file=sys.stderr)
        except (
            urllib.error.URLError,
            TimeoutError,
            RuntimeError,
            json.JSONDecodeError,
        ) as exc:
            saw_hard_error = True
            last_error = exc
            retry_delay = transient_retry_seconds(args.retry_seconds, attempt)
            print(f"Attempt {attempt}/{args.attempts} failed: {exc}", file=sys.stderr)

        if attempt < args.attempts:
            time.sleep(retry_delay)

    if (
        args.allow_not_ready
        and not saw_hard_error
        and isinstance(last_error, ReportNotReady)
    ):
        print(
            f"AIHOT report for {expected_date} is not published yet; "
            "scheduled publication watch exits successfully."
        )
        return 0

    print(f"Collection failed: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
