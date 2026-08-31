#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import os
import re
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
from render_readme import main as render_readme

TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
API = "https://api.github.com"
TARGET_TIME = clock_time(4, 30)  # 12:30 Asia/Singapore
USER_AGENT = "web-ingest-google-trending-residual-recovery/1"
REPORT = ROOT / "tools" / "reports" / "google-trending-residual-recovery-2026-09-01.md"
MANIFEST = TASK_ROOT / "mirror-manifest.json"
TARGETS = {
    date(2025, 2, 5): ("SG", "US", "GB"),
    date(2025, 3, 24): ("SG", "US", "GB", "HK"),
    date(2025, 3, 27): ("HK",),
}
COUNTRY_NAMES = {
    "SG": ("SINGAPORE",),
    "US": ("UNITED STATES", "UNITED_STATES"),
    "GB": ("UNITED KINGDOM", "UNITED_KINGDOM"),
    "HK": ("HONG KONG", "HONG_KONG"),
}


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
                retry = exc.headers.get("Retry-After")
                time.sleep(int(retry) if retry and retry.isdigit() else attempt * 2)
                continue
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API {exc.code}: {body[:250]}") from exc
    raise RuntimeError(f"request failed: {url}")


def fetch_text(repo: str, path: str, sha: str) -> str | None:
    encoded_path = urllib.parse.quote(path, safe="/")
    result = request_json(f"{API}/repos/{repo}/contents/{encoded_path}?ref={urllib.parse.quote(sha)}")
    if not isinstance(result, dict) or not isinstance(result.get("content"), str):
        return None
    raw = base64.b64decode(result["content"].replace("\n", ""))
    return raw.decode("utf-8", errors="replace")


def parse_commit_time(item: dict) -> datetime:
    nested = item.get("commit", {})
    value = nested.get("committer", {}).get("date") or nested.get("author", {}).get("date")
    if not value:
        return datetime.max.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def candidate_repositories() -> list[str]:
    # Search the full public lineage by exact repository-name family.
    query = urllib.parse.quote("Google-Trends-Keywords-Scraper in:name")
    result = request_json(f"{API}/search/repositories?q={query}&per_page=100")
    repos: list[str] = []
    if isinstance(result, dict):
        for item in result.get("items", []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "")
            full = str(item.get("full_name") or "")
            if name == "Google-Trends-Keywords-Scraper" and full:
                repos.append(full)
    primary = "fdciabdul/Google-Trends-Keywords-Scraper"
    if primary in repos:
        repos.remove(primary)
    return [primary, *repos]


def commits_for_day(repo: str, day: date) -> list[dict]:
    since = datetime.combine(day, clock_time.min, timezone.utc)
    until = since + timedelta(days=1) - timedelta(seconds=1)
    query = urllib.parse.urlencode({
        "since": since.isoformat().replace("+00:00", "Z"),
        "until": until.isoformat().replace("+00:00", "Z"),
        "per_page": 100,
    })
    items = request_json(f"{API}/repos/{repo}/commits?{query}")
    if not isinstance(items, list):
        return []
    target = datetime.combine(day, TARGET_TIME, timezone.utc)
    return sorted(items, key=lambda item: abs((parse_commit_time(item) - target).total_seconds()))


def parse_json_region(text: str | None) -> tuple[list[dict], str | None]:
    if not text:
        return [], None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return [], None
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        return [], None
    items: list[dict] = []
    seen: set[str] = set()
    for raw in payload["data"]:
        if not isinstance(raw, dict):
            continue
        query = str(raw.get("title") or "").strip()
        if not query or query.casefold() in seen:
            continue
        seen.add(query.casefold())
        item = canonical_item({"query": query, "search_volume_label": raw.get("trafficCount")}, len(items) + 1)
        if raw.get("pubDate"):
            item["source_pub_date"] = raw["pubDate"]
        items.append(item)
    return items, str(payload.get("lastUpdate")) if payload.get("lastUpdate") else None


def split_markdown_row(line: str) -> list[str]:
    if not line.lstrip().startswith("|"):
        return []
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def readme_region(readme: str | None, geo: str) -> tuple[list[dict], str | None]:
    if not readme:
        return [], None
    aliases = set(COUNTRY_NAMES[geo])
    for line in readme.splitlines():
        cells = split_markdown_row(line)
        if len(cells) < 2 or cells[0].strip().upper() not in aliases:
            continue
        # Two known historical layouts:
        # | Country | Keyword | Last Update |
        # | Country | Flag | Trends | Last Update |
        if len(cells) >= 4 and "flag" not in cells[1].lower():
            trend_cell, stamp = cells[1], cells[-1]
        elif len(cells) >= 4:
            trend_cell, stamp = cells[2], cells[-1]
        else:
            trend_cell, stamp = cells[1], cells[-1]
        # Remove Markdown links while keeping link labels as query text.
        trend_cell = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", trend_cell)
        queries = [part.strip() for part in trend_cell.split(",") if part.strip()]
        items: list[dict] = []
        seen: set[str] = set()
        for query in queries:
            key = query.casefold()
            if key in seen:
                continue
            seen.add(key)
            items.append(canonical_item({"query": query}, len(items) + 1))
        return items, stamp or None
    return [], None


def source_region(repo: str, sha: str, geo: str) -> tuple[list[dict], str | None, str | None]:
    text = fetch_text(repo, f"data/{geo}.json", sha)
    items, stamp = parse_json_region(text)
    if items:
        return items, stamp, f"data/{geo}.json"
    readme = fetch_text(repo, "README.md", sha)
    items, stamp = readme_region(readme, geo)
    if items:
        return items, stamp, "README.md"
    return [], None, None


def source_commit_date_matches(day: date, stamp: str | None, commit: dict) -> bool:
    # Commit itself must be on the target UTC date. If source has a visible timestamp,
    # tolerate local formatting but reject an explicit different YYYY-MM-DD date.
    if parse_commit_time(commit).date() != day:
        return False
    if stamp:
        iso_match = re.search(r"(20\d{2})[-/](\d{2})[-/](\d{2})", stamp)
        if iso_match:
            observed = date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            if observed != day:
                return False
        dmy_match = re.search(r"\b(\d{2})-(\d{2})-(20\d{2})\b", stamp)
        if dmy_match:
            observed = date(int(dmy_match.group(3)), int(dmy_match.group(2)), int(dmy_match.group(1)))
            if observed != day:
                return False
    return True


def existing_missing(day: date) -> list[str]:
    path = archive_path(day.isoformat())
    if not path.exists():
        return list(REGIONS)
    payload = read_json(path)
    regions = payload.get("regions", {})
    return [geo for geo in REGIONS if not isinstance(regions, dict) or geo not in regions]


def main() -> int:
    if not TOKEN:
        raise SystemExit("GITHUB_TOKEN required")

    repos = candidate_repositories()
    recovered: list[dict] = []
    unresolved: dict[str, list[str]] = {}
    scanned: Counter = Counter()

    for day, expected in TARGETS.items():
        missing = [geo for geo in expected if geo in existing_missing(day)]
        if not missing:
            continue
        for repo in repos:
            if not missing:
                break
            try:
                commits = commits_for_day(repo, day)
            except Exception:
                continue
            if not commits:
                continue
            scanned[day.isoformat()] += 1
            for commit in commits:
                if not missing:
                    break
                sha = str(commit.get("sha") or "")
                if not sha:
                    continue
                for geo in tuple(missing):
                    try:
                        items, stamp, source_file = source_region(repo, sha, geo)
                    except Exception:
                        continue
                    if not items or not source_file or not source_commit_date_matches(day, stamp, commit):
                        continue
                    region = {
                        "source": "github_rss_mirror",
                        "fetch_status": "historical_residual_recovery",
                        "source_url": f"https://github.com/{repo}",
                        "source_commit": sha,
                        "source_file": source_file,
                        "source_endpoint": f"https://trends.google.com/trending/rss?geo={geo}&hours=48",
                        "upstream_notice": "mirror lineage; see source repository",
                        "captured_at": stamp,
                        "window_hours": 48,
                        "sort": "source_json_order" if source_file.startswith("data/") else "source_readme_order",
                        "items": items,
                    }
                    _, wrote = merge_region(day.isoformat(), geo, region)
                    if wrote:
                        recovered.append({
                            "date": day.isoformat(), "region": geo, "repository": repo,
                            "commit": sha, "source_file": source_file, "items": len(items),
                        })
                        missing.remove(geo)
        if missing:
            unresolved[day.isoformat()] = missing

    # Rebuild mirror manifest coverage after the residual pass.
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"schema_version": 1}
    range_start = date.fromisoformat(manifest.get("range", {}).get("start", "2024-11-28"))
    range_end = date.fromisoformat(manifest.get("range", {}).get("end", "2026-08-31"))
    missing_after = Counter()
    cursor = range_start
    while cursor <= range_end:
        for geo in existing_missing(cursor):
            missing_after[geo] += 1
        cursor += timedelta(days=1)
    manifest["missing_after_by_region"] = {geo: missing_after[geo] for geo in REGIONS if missing_after[geo]}
    manifest["residual_recovery"] = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repositories_considered": len(repos),
        "repositories_with_target_day_commits": dict(scanned),
        "recovered": recovered,
        "unresolved": unresolved,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    render_readme()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Google Trending residual historical recovery",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat(timespec='seconds')}`",
        "",
        f"Lineage repositories considered: **{len(repos)}**.",
        "",
        "## Recovered snapshots",
        "",
        "| Date | Region | Source repository | Commit | Format | Items |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for row in recovered:
        lines.append(f"| {row['date']} | {row['region']} | `{row['repository']}` | `{row['commit'][:12]}` | `{row['source_file']}` | {row['items']} |")
    if not recovered:
        lines.append("| — | — | — | — | — | 0 |")
    lines.extend(["", "## Unresolved", ""])
    if unresolved:
        for day, geos in unresolved.items():
            lines.append(f"- `{day}`: {', '.join(geos)}")
    else:
        lines.append("All known residual region/date gaps were recovered.")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"repos": len(repos), "recovered": recovered, "unresolved": unresolved}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
