#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

from archive_lib import day_path, parse_trending_html, read_day, validate_day, write_day

TZ = ZoneInfo("Asia/Singapore")
TRENDING_URL = "https://github.com/trending?since=daily"
USER_AGENT = "web-ingest/github-trending (+https://github.com/teddyli18000/web-ingest)"


def fetch_text(url: str, attempts: int = 4, accept: str = "text/html") -> str:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(3 * (2 ** attempt))
    raise RuntimeError(f"failed to fetch {url}: {last}")


def fallback_anton(date: str) -> list[dict] | None:
    url = (
        "https://raw.githubusercontent.com/antonkomarev/github-trending-archive/"
        f"master/archive/repository/{date[:4]}/{date}/(null).json"
    )
    try:
        obj = json.loads(fetch_text(url, attempts=2, accept="application/json"))
    except Exception:
        return None
    repos = obj.get("list") if isinstance(obj, dict) else None
    if not isinstance(repos, list) or not repos:
        return None
    return [{"rank": rank, "repo": repo} for rank, repo in enumerate(repos, start=1)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent))
    parser.add_argument("--date", help="Asia/Singapore date, YYYY-MM-DD")
    parser.add_argument("--html-file", help="test fixture instead of network")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    now = dt.datetime.now(TZ)
    date = args.date or now.date().isoformat()
    target = day_path(root, date)
    if target.exists() and not args.force:
        read_day(target)
        print(f"already archived: {target}")
        return 0

    source = "https://github.com/trending?since=daily"
    try:
        html = Path(args.html_file).read_text(encoding="utf-8") if args.html_file else fetch_text(TRENDING_URL)
        items = parse_trending_html(html)
    except Exception as direct_error:
        if args.html_file:
            raise
        items = fallback_anton(date)
        if not items:
            print(f"direct capture failed and fallback unavailable: {direct_error}", file=sys.stderr)
            return 2
        source = "https://github.com/antonkomarev/github-trending-archive (same-day fallback)"

    day = {
        "schema_version": 1,
        "date": date,
        "captured_at": now.isoformat(timespec="seconds"),
        "snapshots": [{"scope": "all", "source": source, "items": items}],
    }
    validate_day(day)
    path = write_day(root, day)
    print(f"wrote {path} ({len(items)} repositories)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
