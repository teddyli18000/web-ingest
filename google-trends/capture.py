#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import json
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from archive_lib import day_path, load_config, parse_rss, read_day, validate_day, write_day

ROOT = Path(__file__).resolve().parent
TZ = ZoneInfo("Asia/Singapore")
RSS_TEMPLATE = "https://trends.google.com/trending/rss?geo={geo}"
USER_AGENT = "web-ingest-google-trends/1.0 (+https://github.com/teddyli18000/web-ingest)"


def fetch_geo(geo: dict, attempts: int = 3, timeout: int = 20) -> dict:
    code = geo["code"]
    url = RSS_TEMPLATE.format(geo=code)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml,text/xml,*/*"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
            return {
                "geo": code,
                "geo_name": geo["name"],
                "source": url,
                "source_kind": "google_rss",
                "items": parse_rss(body),
            }
        except (OSError, urllib.error.URLError, ValueError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(2 ** (attempt - 1))
    raise RuntimeError(f"{code}: RSS fetch failed after {attempts} attempts: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    config = load_config(ROOT)
    now = datetime.now(TZ)
    date = now.date().isoformat()
    path = day_path(ROOT, date)
    expected = {geo["code"] for geo in config["geos"]}

    if path.exists() and not args.force:
        existing = read_day(path)
        have = {snapshot["geo"] for snapshot in existing["snapshots"]}
        if expected.issubset(have):
            print(f"{date}: complete snapshot already exists; no-op")
            return 0

    snapshots: list[dict] = []
    errors: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch_geo, geo): geo["code"] for geo in config["geos"]}
        for future in concurrent.futures.as_completed(futures):
            code = futures[future]
            try:
                snapshot = future.result()
                snapshots.append(snapshot)
                print(f"{code}: {len(snapshot['items'])} trends")
            except Exception as exc:  # keep every failure visible before aborting
                errors.append(str(exc))

    if errors:
        raise RuntimeError("incomplete Google Trends capture:\n- " + "\n- ".join(sorted(errors)))

    day = {
        "schema_version": 1,
        "date": date,
        "captured_at": now.isoformat(timespec="seconds"),
        "period_hours": int(config.get("period_hours", 24)),
        "coverage": "core-geos",
        "snapshots": sorted(snapshots, key=lambda item: item["geo"]),
    }
    validate_day(day)
    write_day(ROOT, day)
    print(json.dumps({"date": date, "geos": len(snapshots), "path": path.as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
