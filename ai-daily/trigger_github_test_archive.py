#!/usr/bin/env python3
"""Hand off one committed AI Daily snapshot to the fixed Github_test archive workflow."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date

RAW_BASE = "https://raw.githubusercontent.com/teddyli18000/web-ingest/main/ai-daily/data"
DISPATCH_URL = (
    "https://api.github.com/repos/teddyli18000/Github_test/"
    "actions/workflows/ai-daily-archive.yml/dispatches"
)
DISPATCH_REF = "master"
TOKEN_ENV = "AI_DAILY_DISPATCH_TOKEN"
RAW_ATTEMPTS = 12
RAW_RETRY_SECONDS = 5
RAW_REQUEST_TIMEOUT = 5
RAW_VISIBILITY_DEADLINE_SECONDS = 60
DISPATCH_ATTEMPTS = 2
DISPATCH_RETRY_SECONDS = 2
DISPATCH_REQUEST_TIMEOUT = 15
USER_AGENT = "web-ingest/ai-daily-handoff"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trigger the fixed Github_test AI Daily archive workflow"
    )
    parser.add_argument("--date", required=True, help="Committed AI Daily date (YYYY-MM-DD)")
    return parser.parse_args()


def validate_report_date(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"invalid report date: {value!r}")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid report date: {value!r}") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"invalid report date: {value!r}")
    return value


def raw_urls(report_date: str) -> tuple[str, str]:
    year, month, day = report_date.split("-")
    base = f"{RAW_BASE}/{year}/{month}/{day}"
    return f"{base}/aihot-daily.html", f"{base}/aihot-daily.json"


def raw_is_readable(url: str) -> bool:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=RAW_REQUEST_TIMEOUT) as response:
            if response.status != 200:
                return False
            response.read(1)
            return True
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return False


def wait_for_raw_mirror(report_date: str) -> None:
    html_url, json_url = raw_urls(report_date)
    started = time.monotonic()

    for attempt in range(1, RAW_ATTEMPTS + 1):
        html_ready = raw_is_readable(html_url)
        json_ready = raw_is_readable(json_url)
        if html_ready and json_ready:
            print(f"Raw AI Daily mirror is readable for {report_date}.")
            return

        elapsed = time.monotonic() - started
        if attempt >= RAW_ATTEMPTS or elapsed >= RAW_VISIBILITY_DEADLINE_SECONDS:
            break

        remaining = RAW_VISIBILITY_DEADLINE_SECONDS - elapsed
        time.sleep(min(RAW_RETRY_SECONDS, max(0.0, remaining)))

    raise RuntimeError(
        f"AI Daily {report_date} was pushed but both raw mirror files did not become "
        "readable within the visibility window"
    )


def dispatch_archive(report_date: str, token: str) -> None:
    payload = json.dumps(
        {"ref": DISPATCH_REF, "inputs": {"date": report_date}},
        separators=(",", ":"),
    ).encode("utf-8")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }

    for attempt in range(1, DISPATCH_ATTEMPTS + 1):
        request = urllib.request.Request(
            DISPATCH_URL,
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request, timeout=DISPATCH_REQUEST_TIMEOUT
            ) as response:
                status = response.status
                body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            status = exc.code
            body = exc.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Github_test Bot 1 dispatch request failed: {exc}") from exc

        if status == 204:
            print(f"Github_test AI Daily Bot 1 dispatched for {report_date} (HTTP 204).")
            return

        if status in {500, 502, 503, 504} and attempt < DISPATCH_ATTEMPTS:
            print(
                f"Github_test Bot 1 dispatch returned HTTP {status}; retrying once.",
                file=sys.stderr,
            )
            time.sleep(DISPATCH_RETRY_SECONDS)
            continue

        detail = body.strip()
        if detail:
            raise RuntimeError(
                f"Github_test Bot 1 dispatch failed with HTTP {status}: {detail}"
            )
        raise RuntimeError(f"Github_test Bot 1 dispatch failed with HTTP {status}")

    raise RuntimeError("Github_test Bot 1 dispatch failed")


def main() -> int:
    args = parse_args()
    try:
        report_date = validate_report_date(args.date)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    token = os.environ.get(TOKEN_ENV)
    if not token:
        print(f"Required Actions secret environment {TOKEN_ENV} is not set.", file=sys.stderr)
        return 1

    try:
        wait_for_raw_mirror(report_date)
        dispatch_archive(report_date, token)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
