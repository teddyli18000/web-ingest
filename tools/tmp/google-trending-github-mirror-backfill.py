#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, time as clock_time, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = ROOT / "google-trending"
sys.path.insert(0, str(TASK_ROOT))

from archive_lib import REGIONS, archive_path, canonical_item, merge_region, read_json

SOURCE_REPO = "fdciabdul/Google-Trends-Keywords-Scraper"
SOURCE_URL = f"https://github.com/{SOURCE_REPO}"
SOURCE_NOTICE = "All Rights Reserved"
START = date(2024, 11, 28)
END = date(2026, 8, 31)
REQUIRED_GAP_START = date(2026, 1, 4)
REQUIRED_GAP_END = END
MANIFEST = TASK_ROOT / "mirror-manifest.json"
REPORT = ROOT / "tools" / "reports" / "google-trending-mirror-backfill-2026-09-01.md"
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
API = "https://api.github.com"
TARGET_UTC = clock_time(4, 30)  # ~12:30 Asia/Singapore
USER_AGENT = "web-ingest-google-trending-backfill/1"


def request_json(url: str, *, accept: str = "application/vnd.github+json", attempts: int = 4):
    headers = {
        "Accept": accept,
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code in (403, 429, 500, 502, 503, 504) and attempt < attempts:
                retry_after = exc.headers.get("Retry-After")
                delay = int(retry_after) if retry_after and retry_after.isdigit() else attempt * 2
                time.sleep(delay)
                continue
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API {exc.code} for {url}: {body[:300]}") from exc
        except (TimeoutError, urllib.error.URLError) as exc:
            if attempt < attempts:
                time.sleep(attempt * 2)
                continue
            raise RuntimeError(f"request failed for {url}: {exc}") from exc
    raise RuntimeError(f"request failed for {url}")


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_commit_time(item: dict) -> datetime:
    value = item["commit"]["committer"]["date"]
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def choose_commit(day: date) -> dict | None:
    target = datetime.combine(day, TARGET_UTC, timezone.utc)
    windows = [
        (target - timedelta(hours=2), target + timedelta(hours=2)),
        (datetime.combine(day, clock_time.min, timezone.utc), datetime.combine(day + timedelta(days=1), clock_time.min, timezone.utc)),
    ]
    for since, until in windows:
        query = urllib.parse.urlencode({
            "since": iso_z(since),
            "until": iso_z(until),
            "per_page": 100,
        })
        items = request_json(f"{API}/repos/{SOURCE_REPO}/commits?{query}")
        if isinstance(items, list) and items:
            return min(items, key=lambda item: abs((parse_commit_time(item) - target).total_seconds()))

    q = urllib.parse.quote(f'repo:{SOURCE_REPO} "Update Data {day.isoformat()}"')
    result = request_json(
        f"{API}/search/commits?q={q}&per_page=100",
        accept="application/vnd.github.text-match+json",
    )
    items = result.get("items", []) if isinstance(result, dict) else []
    if items:
        return min(items, key=lambda item: abs((parse_commit_time(item) - target).total_seconds()))
    return None


def fetch_region_payload(sha: str, geo: str) -> dict | None:
    path = urllib.parse.quote(f"data/{geo}.json", safe="/")
    url = f"{API}/repos/{SOURCE_REPO}/contents/{path}?ref={urllib.parse.quote(sha)}"
    result = request_json(url)
    if not isinstance(result, dict):
        return None
    encoded = result.get("content")
    if not isinstance(encoded, str):
        return None
    raw = base64.b64decode(encoded.replace("\n", ""))
    payload = json.loads(raw.decode("utf-8"))
    return payload if isinstance(payload, dict) else None


def region_items(payload: dict) -> list[dict]:
    rows = payload.get("data")
    if not isinstance(rows, list):
        return []
    items: list[dict] = []
    seen: set[str] = set()
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        query = str(raw.get("title") or "").strip()
        if not query:
            continue
        key = query.casefold()
        if key in seen:
            continue
        seen.add(key)
        item = canonical_item(
            {
                "query": query,
                "search_volume_label": raw.get("trafficCount"),
            },
            len(items) + 1,
        )
        if raw.get("pubDate"):
            item["source_pub_date"] = raw["pubDate"]
        items.append(item)
    return items


def existing_regions(day: date) -> set[str]:
    path = archive_path(day.isoformat())
    if not path.exists():
        return set()
    payload = read_json(path)
    regions = payload.get("regions", {})
    return {geo for geo in REGIONS if isinstance(regions, dict) and geo in regions}


def missing_by_region(start: date, end: date) -> Counter:
    counter: Counter = Counter()
    day = start
    while day <= end:
        present = existing_regions(day)
        for geo in REGIONS:
            if geo not in present:
                counter[geo] += 1
        day += timedelta(days=1)
    return counter


def main() -> int:
    if not TOKEN:
        raise SystemExit("GITHUB_TOKEN is required for the historical mirror backfill")

    before_missing = missing_by_region(START, END)
    writes: Counter = Counter()
    failures: list[str] = []
    days_needing_fill = 0
    commit_days_used = 0

    day = START
    while day <= END:
        missing = [geo for geo in REGIONS if geo not in existing_regions(day)]
        if not missing:
            day += timedelta(days=1)
            continue

        days_needing_fill += 1
        commit = choose_commit(day)
        if not commit:
            failures.append(f"{day}: no source commit found")
            day += timedelta(days=1)
            continue

        sha = str(commit.get("sha") or "")
        if not sha:
            failures.append(f"{day}: source commit had no SHA")
            day += timedelta(days=1)
            continue
        commit_days_used += 1

        for geo in missing:
            try:
                payload = fetch_region_payload(sha, geo)
                items = region_items(payload or {})
                if not payload or not items:
                    failures.append(f"{day} {geo}: source file missing or empty at {sha[:12]}")
                    continue
                region = {
                    "source": "github_rss_mirror",
                    "fetch_status": "historical_mirror",
                    "source_url": SOURCE_URL,
                    "source_commit": sha,
                    "source_file": f"data/{geo}.json",
                    "source_endpoint": f"https://trends.google.com/trending/rss?geo={geo}&hours=48",
                    "upstream_notice": SOURCE_NOTICE,
                    "captured_at": payload.get("lastUpdate"),
                    "window_hours": 48,
                    "sort": "source_json_order",
                    "items": items,
                }
                _, wrote = merge_region(day.isoformat(), geo, region)
                writes[geo] += int(wrote)
            except Exception as exc:
                failures.append(f"{day} {geo}: {exc}")

        day += timedelta(days=1)

    after_missing = missing_by_region(START, END)
    required_after = missing_by_region(REQUIRED_GAP_START, REQUIRED_GAP_END)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    manifest = {
        "schema_version": 1,
        "source": SOURCE_REPO,
        "source_url": SOURCE_URL,
        "upstream_notice": SOURCE_NOTICE,
        "source_endpoint": "https://trends.google.com/trending/rss?geo={GEO}&hours=48",
        "selection_policy": "for each archive date with a missing canonical region, use the source commit closest to 04:30 UTC (12:30 Asia/Singapore); fall back to the UTC day and then commit search",
        "range": {"start": START.isoformat(), "end": END.isoformat()},
        "required_gap": {"start": REQUIRED_GAP_START.isoformat(), "end": REQUIRED_GAP_END.isoformat()},
        "days_needing_fill": days_needing_fill,
        "source_commit_days_used": commit_days_used,
        "missing_before_by_region": dict(before_missing),
        "writes_by_region": dict(writes),
        "missing_after_by_region": dict(after_missing),
        "required_gap_missing_after_by_region": dict(required_after),
        "failure_count": len(failures),
        "failure_examples": failures[:30],
        "updated_at": now,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report_lines = [
        "# Google Trending GitHub mirror backfill",
        "",
        f"Generated: `{now}`",
        "",
        f"- Source: `{SOURCE_REPO}`",
        f"- Source notice recorded by upstream: **{SOURCE_NOTICE}**",
        f"- Requested archive range: **{START} through {END}**",
        f"- Required 2026 gap: **{REQUIRED_GAP_START} through {REQUIRED_GAP_END}**",
        f"- Archive days that needed at least one region: **{days_needing_fill}**",
        f"- Source commit-days used: **{commit_days_used}**",
        "",
        "## Region coverage",
        "",
        "| Region | Missing before | Mirrored writes | Missing after |",
        "| --- | ---: | ---: | ---: |",
    ]
    for geo in REGIONS:
        report_lines.append(f"| {geo} | {before_missing[geo]} | {writes[geo]} | {after_missing[geo]} |")
    report_lines.extend([
        "",
        "## Selection and provenance",
        "",
        "For each date that lacked one or more canonical regions, the importer chose the upstream commit closest to **04:30 UTC / 12:30 Asia/Singapore**, then copied only the missing region JSON in source order. Existing `googletrendarchive` and direct `google_trending_now` snapshots were never overwritten.",
        "",
        "Each mirrored region stores the upstream repository, exact commit SHA, source file, original 48-hour Google Trending RSS endpoint, and the upstream rights notice.",
        "",
        f"Failures recorded: **{len(failures)}**.",
    ])
    if failures:
        report_lines.extend(["", "### Failure examples", ""])
        report_lines.extend(f"- `{line}`" for line in failures[:20])
    REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    required_total = sum(required_after.values())
    print(json.dumps({
        "days_needing_fill": days_needing_fill,
        "source_commit_days_used": commit_days_used,
        "writes_by_region": dict(writes),
        "missing_after_by_region": dict(after_missing),
        "required_gap_missing_after": required_total,
        "failures": len(failures),
    }, indent=2))

    if required_total:
        raise SystemExit(f"required 2026 gap still has {required_total} missing region snapshots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
