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

PRIMARY_REPO = "fdciabdul/Google-Trends-Keywords-Scraper"
PRIMARY_SHA_2026_10_07 = "4ed36fbd20a1a953bb4deae50c54ca02bdc44b8a"
UPSTREAM_NOTICE = "All Rights Reserved"
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
API = "https://api.github.com"
TARGET_UTC = clock_time(4, 30)
USER_AGENT = "web-ingest-google-trending-gap-recovery/1"
MANIFEST = TASK_ROOT / "mirror-manifest.json"

# Previously checked mirrors plus additional GitHub mirrors found during the 2026-10-07 handoff audit.
MIRRORS = [
    PRIMARY_REPO,
    "connorodea/Google-Trends-Keywords-Scraper",
    "DutchErwin/Google-Trends-Keywords-Scraper",
    "mapledxf/Google-Trends-Keywords-Scraper",
    "253611069/Google-Trends-Keywords-Scraper",
    "langtuandroid/Google-Trends-Keywords-Scraper",
    "mupsje/Google-Trends-Keywords-Scraper",
    "dennyhaq/Google-Trends-Keywords-Scraper",
    "CattleZoe/Google-Trends-Keywords-Scraper",
    "VisionDirectingStudio/Google-Trends-Keywords-Scraper",
    "pixelapps-dev/Google-Trends-Keywords-Scraper",
    "danteGPT/Google-Trends-Keywords-Scraper",
    "e5dmnyKSA/Google-Trends-Keywords-Scraper",
    "evil1morty/Google-Trends-Keywords-Scraper",
    "ahrimango/Google-Trends-Keywords-Scraper",
    "cyberpay/Google-Trends-Keywords-Scraper",
    "albaspro/Google-Trends-Keywords-Scraper",
    "ibeae/Google-Trends-Keywords-Scraper",
    "suwen-min/Google-Trends-Keywords-Scraper",
    "baybae/Google-Trends-Keywords-Scraper",
    "daqab/Google-Trends-Keywords-Scraper",
    "imheyday/Google-Trends-Keywords-Scraper",
    "babybirdprd/Google-Trends-Keywords-Scraper",
    "magecommerce/Google-Trends-Keywords-Scraper",
    "arifarfx/Google-Trends-Keywords-Scraper",
    "perbinder/Google-Trends-Keywords-Scraper",
    "rendisadia/Google-Trends-Keywords-Scraper",
    "MaximOm/Google-Trends-Keywords-Scraper",
    "doim/Google-Trends-Keywords-Scraper",
    "classicvalues/Google-Trends-Keywords-Scraper",
    "zakirkun/Google-Trends-Keywords-Scraper",
    "mughu-id/Google-Trends-Keywords-Scraper",
    "lihuibng/Google-Trends-Keywords-Scraper",
    "sukakcoding/Google-Trends-Keywords-Scraper",
    "DineshAitha16/Google-Trends-Keywords-Scraper",
    "Zaperking/Google-Trends-Keywords-Scraper",
    "bbrooks870/Google-Trends-Keywords-Scraper",
    "wanghaisheng/Google-Trends-Keywords-Scraper",
    "ctrlCcode/Google-Trends-Keywords-Scraper",
    "Pro-click/Google-Trends-Keywords-Scraper",
    "Gudang-Source/Google-Trends-Keywords-Scraper",
]

HISTORICAL_TARGETS = {
    date(2025, 3, 24): set(REGIONS),
    date(2025, 3, 27): {"HK"},
}
CURRENT_TARGET = date(2026, 10, 7)
ARCHIVE_RANGE = (date(2024, 11, 28), date(2026, 8, 31))
REQUIRED_RANGE = (date(2026, 1, 4), date(2026, 8, 31))


def request_json(url: str, *, attempts: int = 4):
    headers = {
        "Accept": "application/vnd.github+json",
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
            if exc.code in {403, 429, 500, 502, 503, 504} and attempt < attempts:
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


def commits_for_day(repo: str, day: date) -> list[dict]:
    start = datetime.combine(day, clock_time.min, timezone.utc)
    end = start + timedelta(days=1) - timedelta(seconds=1)
    query = urllib.parse.urlencode({"since": iso_z(start), "until": iso_z(end), "per_page": 100})
    result = request_json(f"{API}/repos/{repo}/commits?{query}")
    return result if isinstance(result, list) else []


def fetch_region_payload(repo: str, sha: str, geo: str) -> dict | None:
    path = urllib.parse.quote(f"data/{geo}.json", safe="/")
    result = request_json(f"{API}/repos/{repo}/contents/{path}?ref={urllib.parse.quote(sha)}")
    if not isinstance(result, dict) or not isinstance(result.get("content"), str):
        return None
    raw = base64.b64decode(result["content"].replace("\n", ""))
    payload = json.loads(raw.decode("utf-8"))
    return payload if isinstance(payload, dict) else None


def payload_matches_day(payload: dict, day: date) -> bool:
    value = payload.get("lastUpdate")
    return isinstance(value, str) and value.startswith(day.isoformat())


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
        item = canonical_item({"query": query, "search_volume_label": raw.get("trafficCount")}, len(items) + 1)
        if raw.get("pubDate"):
            item["source_pub_date"] = raw["pubDate"]
        items.append(item)
    return items


def build_region(repo: str, sha: str, geo: str, payload: dict) -> dict:
    return {
        "source": "github_rss_mirror",
        "fetch_status": "historical_mirror",
        "source_url": f"https://github.com/{repo}",
        "source_commit": sha,
        "source_file": f"data/{geo}.json",
        "source_endpoint": f"https://trends.google.com/trending/rss?geo={geo}&hours=48",
        "upstream_notice": UPSTREAM_NOTICE,
        "captured_at": payload.get("lastUpdate"),
        "window_hours": 48,
        "sort": "source_json_order",
        "items": region_items(payload),
    }


def existing_regions(day: date) -> set[str]:
    path = archive_path(day.isoformat())
    if not path.exists():
        return set()
    regions = read_json(path).get("regions", {})
    return {geo for geo in REGIONS if isinstance(regions, dict) and geo in regions}


def recover_exact(repo: str, sha: str, day: date, geos: set[str]) -> dict[str, str]:
    recovered: dict[str, str] = {}
    for geo in sorted(geos):
        payload = fetch_region_payload(repo, sha, geo)
        if not payload or not payload_matches_day(payload, day):
            continue
        region = build_region(repo, sha, geo, payload)
        if not region["items"]:
            continue
        _, wrote = merge_region(day.isoformat(), geo, region)
        if wrote:
            recovered[geo] = f"{repo}@{sha}"
    return recovered


def recover_historical(day: date, geos: set[str]) -> tuple[dict[str, str], list[str]]:
    missing = set(geos) - existing_regions(day)
    recovered: dict[str, str] = {}
    checked: list[str] = []
    target = datetime.combine(day, TARGET_UTC, timezone.utc)
    for repo in MIRRORS:
        if not missing:
            break
        commits = commits_for_day(repo, day)
        if not commits:
            checked.append(repo)
            continue
        commits.sort(key=lambda item: abs((parse_commit_time(item) - target).total_seconds()))
        checked.append(repo)
        for commit in commits:
            sha = str(commit.get("sha") or "")
            if not sha:
                continue
            for geo in list(sorted(missing)):
                payload = fetch_region_payload(repo, sha, geo)
                if not payload or not payload_matches_day(payload, day):
                    continue
                region = build_region(repo, sha, geo, payload)
                if not region["items"]:
                    continue
                _, wrote = merge_region(day.isoformat(), geo, region)
                if wrote:
                    recovered[geo] = f"{repo}@{sha}"
                    missing.remove(geo)
            if not missing:
                break
    return recovered, checked


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


def update_manifest(result: dict) -> None:
    payload = read_json(MANIFEST) if MANIFEST.exists() else {"schema_version": 1}
    payload["missing_after_by_region"] = dict(missing_by_region(*ARCHIVE_RANGE))
    payload["required_gap_missing_after_by_region"] = dict(missing_by_region(*REQUIRED_RANGE))
    payload["handoff_gap_recovery"] = result
    payload["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if not TOKEN:
        raise SystemExit("GITHUB_TOKEN is required")

    result: dict = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "policy": "exact-date GitHub mirror commits only; no adjacent-day synthesis",
        "current_recovery": {},
        "historical_recovery": {},
        "historical_checked_repositories": {},
        "unresolved": {},
    }

    current_missing = set(REGIONS) - existing_regions(CURRENT_TARGET)
    if current_missing:
        result["current_recovery"] = recover_exact(
            PRIMARY_REPO,
            PRIMARY_SHA_2026_10_07,
            CURRENT_TARGET,
            current_missing,
        )

    for day, geos in HISTORICAL_TARGETS.items():
        recovered, checked = recover_historical(day, geos)
        result["historical_recovery"][day.isoformat()] = recovered
        result["historical_checked_repositories"][day.isoformat()] = checked
        remaining = sorted(geos - existing_regions(day))
        if remaining:
            result["unresolved"][day.isoformat()] = remaining

    current_remaining = sorted(set(REGIONS) - existing_regions(CURRENT_TARGET))
    if current_remaining:
        result["unresolved"][CURRENT_TARGET.isoformat()] = current_remaining

    update_manifest(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if current_remaining:
        raise SystemExit(f"2026-10-07 still missing regions: {', '.join(current_remaining)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
