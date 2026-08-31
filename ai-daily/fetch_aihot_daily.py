#!/usr/bin/env python3
"""Mirror one AIHOT daily report into this repository."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

API_BASE = "https://aihot.virxact.com/api/v1/dailies"
TIMEZONE = ZoneInfo("Asia/Shanghai")
USER_AGENT = "web-ingest/1.0 (+https://github.com/teddyli18000/web-ingest)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mirror an AIHOT daily report")
    parser.add_argument(
        "--date",
        help="Beijing calendar date (YYYY-MM-DD). Omit to wait for today's latest report.",
    )
    parser.add_argument("--attempts", type=int, default=1, help="Maximum fetch attempts")
    parser.add_argument(
        "--retry-seconds", type=int, default=300, help="Seconds between attempts"
    )
    return parser.parse_args()


def today_beijing() -> str:
    return datetime.now(TIMEZONE).date().isoformat()


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"unexpected HTTP status: {response.status}")
        return json.load(response)


def validate(payload: dict, expected_date: str) -> dict:
    if payload.get("schemaVersion") != 1:
        raise RuntimeError("unexpected AIHOT schemaVersion")

    report = payload.get("report")
    if not isinstance(report, dict):
        raise RuntimeError("AIHOT response does not contain report")

    report_date = report.get("date")
    if report_date != expected_date:
        raise RuntimeError(
            f"latest report is {report_date!r}, waiting for {expected_date!r}"
        )

    if not isinstance(report.get("sections"), list):
        raise RuntimeError("AIHOT report.sections is missing or invalid")

    return report


def output_path(report_date: str) -> Path:
    year, month, day = report_date.split("-")
    return (
        Path(__file__).resolve().parent
        / "data"
        / year
        / month
        / day
        / "aihot-daily.json"
    )


def write_snapshot(payload: dict, report_date: str) -> Path:
    path = output_path(report_date)
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            print(f"Snapshot already exists and is unchanged: {path}")
            return path
        raise RuntimeError(
            f"snapshot already exists with different content: {path}; "
            "refusing to silently rewrite history"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Saved AIHOT daily {report_date}: {path}")
    return path


def set_github_outputs(report_date: str, path: Path) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")
    if not output_file:
        return
    with open(output_file, "a", encoding="utf-8") as handle:
        handle.write(f"report_date={report_date}\n")
        handle.write(f"output_path={path.as_posix()}\n")


def main() -> int:
    args = parse_args()
    if args.attempts < 1:
        raise SystemExit("--attempts must be at least 1")
    if args.retry_seconds < 0:
        raise SystemExit("--retry-seconds cannot be negative")

    expected_date = args.date or today_beijing()
    url = f"{API_BASE}/{expected_date}" if args.date else f"{API_BASE}/latest"

    last_error: Exception | None = None
    for attempt in range(1, args.attempts + 1):
        try:
            payload = fetch_json(url)
            report = validate(payload, expected_date)
            path = write_snapshot(payload, report["date"])
            set_github_outputs(report["date"], path)
            return 0
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, json.JSONDecodeError) as exc:
            last_error = exc
            print(f"Attempt {attempt}/{args.attempts} failed: {exc}", file=sys.stderr)
            if attempt < args.attempts:
                time.sleep(args.retry_seconds)

    print(f"Collection failed: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
