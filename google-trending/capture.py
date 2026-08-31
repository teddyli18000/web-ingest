#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from archive_lib import REGIONS, canonical_item, merge_region

PACKAGE = "google-trends-now@1.1.1"
LOCAL_TZ = ZoneInfo("Asia/Singapore")


def fetch_region(geo: str) -> dict:
    command = [
        "npx", "--yes", PACKAGE,
        "trending",
        "--geo", geo,
        "--hours", "24",
        "--sort", "relevance",
        "--limit", "all",
        "--format", "json",
        "--fallback", "rss",
        "--retries", "2",
        "--timeout-ms", "30000",
    ]
    process = subprocess.run(command, text=True, capture_output=True, check=False)
    if process.returncode != 0:
        raise RuntimeError(f"{geo}: collector failed: {process.stderr.strip()}")
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{geo}: collector returned invalid JSON") from exc

    source = payload.get("source")
    status = payload.get("fetch_status")
    items = payload.get("items")
    if source not in {"google_trending_now", "rss_limited"}:
        raise RuntimeError(f"{geo}: unexpected source {source!r}")
    if status not in {"success", "rss_limited"}:
        raise RuntimeError(f"{geo}: fetch status {status!r}: {payload.get('error')}")
    if not isinstance(items, list) or not items:
        raise RuntimeError(f"{geo}: empty trend list")

    return {
        "source": source,
        "fetch_status": status,
        "source_url": payload.get("source_url"),
        "captured_at": payload.get("observed_at") or datetime.now(LOCAL_TZ).isoformat(),
        "window_hours": payload.get("hours", 24),
        "sort": payload.get("sort", "relevance"),
        "collector": PACKAGE,
        "items": [canonical_item(item, rank) for rank, item in enumerate(items, start=1)],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture SG and US Google Trends Trending Now")
    parser.add_argument("--force", action="store_true", help="explicitly replace an existing same-day region")
    args = parser.parse_args()

    day = datetime.now(LOCAL_TZ).date().isoformat()
    # Fetch both regions before writing either one, so a hard failure does not leave a half-captured day.
    candidates = {geo: fetch_region(geo) for geo in REGIONS}

    changed = False
    for geo in REGIONS:
        path, wrote = merge_region(day, geo, candidates[geo], force=args.force)
        changed = changed or wrote
        print(f"{geo}: {'wrote' if wrote else 'kept'} {path}")
    if not changed:
        print("No snapshot changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
