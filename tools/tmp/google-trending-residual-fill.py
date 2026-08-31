#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = ROOT / "google-trending"
sys.path.insert(0, str(TASK_ROOT))

from archive_lib import REGIONS, archive_path, canonical_item, merge_region, read_json, validate_document  # noqa: E402

DAY = "2025-02-05"
SOURCE_REPO = "connorodea/Google-Trends-Keywords-Scraper"
SOURCE_COMMIT = "ce3c2897587e504e2934535795498f93e805d342"
SOURCE_COMMIT_URL = f"https://github.com/{SOURCE_REPO}/commit/{SOURCE_COMMIT}"
TARGETS = {
    "SG": ("SINGAPORE.json", "p5"),
    "US": ("UNITED STATES.json", "p1"),
    "GB": ("UNITED KINGDOM.json", "p9"),
}
CHECKED_FORKS = [
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
]


def fetch_source(filename: str) -> dict:
    encoded = urllib.parse.quote(filename)
    url = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/data/{encoded}"
    request = urllib.request.Request(url, headers={"User-Agent": "web-ingest-residual-fill/1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def source_region(geo: str, filename: str, pn: str, payload: dict) -> dict:
    last_update = str(payload.get("lastUpdate") or "").strip()
    parsed = datetime.strptime(last_update, "%d-%m-%Y , %H:%M:%S")
    if parsed.date().isoformat() != DAY:
        raise ValueError(f"{geo}: source lastUpdate {last_update!r} is not {DAY}")

    rows = payload.get("data")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{geo}: source data is empty")

    items = []
    for rank, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or not str(row.get("title") or "").strip():
            raise ValueError(f"{geo}: invalid row {rank}")
        label = row.get("approxtraffic") or row.get("trafficCount")
        items.append(
            canonical_item(
                {
                    "query": row.get("title"),
                    "search_volume_label": label,
                    "started_at": row.get("pubdate") or row.get("pubDate"),
                    "explore_url": row.get("link"),
                },
                rank,
            )
        )

    return {
        "source": "github_hottrends_mirror",
        "fetch_status": "historical_mirror",
        "source_endpoint": f"https://trends.google.com/trends/hottrends/atom/feed?pn={pn}",
        "source_repo": SOURCE_REPO,
        "source_commit": SOURCE_COMMIT,
        "source_commit_url": SOURCE_COMMIT_URL,
        "source_path": f"data/{filename}",
        "source_last_update": last_update,
        "captured_at": None,
        "window_hours": None,
        "sort": "source_feed_order",
        "items": items,
    }


def missing_between(start: str, end: str) -> dict[str, int]:
    cursor = date.fromisoformat(start)
    finish = date.fromisoformat(end)
    counts = {geo: 0 for geo in REGIONS}
    while cursor <= finish:
        path = archive_path(cursor.isoformat())
        regions = read_json(path).get("regions", {}) if path.exists() else {}
        for geo in REGIONS:
            if geo not in regions:
                counts[geo] += 1
        cursor += timedelta(days=1)
    return {geo: count for geo, count in counts.items() if count}


def update_manifest(writes: dict[str, int]) -> None:
    path = TASK_ROOT / "mirror-manifest.json"
    manifest = read_json(path)
    for geo, count in writes.items():
        manifest.setdefault("writes_by_region", {})[geo] = int(manifest.get("writes_by_region", {}).get(geo, 0)) + count

    manifest["missing_after_by_region"] = missing_between(manifest["range"]["start"], manifest["range"]["end"])
    manifest["required_gap_missing_after_by_region"] = missing_between(
        manifest["required_gap"]["start"], manifest["required_gap"]["end"]
    )
    manifest["failure_count"] = 2
    manifest["failure_examples"] = [
        "2025-03-24: no source commit found in the primary mirror or 12 checked long-lived forks",
        "2025-03-27: no source commit found in the primary mirror or 12 checked long-lived forks; HK remains missing",
    ]
    manifest["residual_recovery"] = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fallback_source_repo": SOURCE_REPO,
        "fallback_source_commit": SOURCE_COMMIT,
        "fallback_source_kind": "google_hottrends_atom",
        "recovered": {DAY: sorted(writes)},
        "unresolved": {
            "2025-03-24": list(REGIONS),
            "2025-03-27": ["HK"],
        },
        "checked_forks": CHECKED_FORKS,
        "note": "The primary mirror repository was also checked. The listed forks had no commits on the unresolved UTC dates.",
    }
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_readme_source_notes() -> None:
    path = TASK_ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    old = """1. `google_trending_now` — direct live Trending Now capture; highest quality.\n2. `googletrendarchive` — CC-BY-4.0 historical daily recovery.\n3. `github_rss_mirror` — historical Google Trending RSS snapshots mirrored from `fdciabdul/Google-Trends-Keywords-Scraper` only where a canonical region/date is missing. Exact commit/file provenance and the upstream **All Rights Reserved** notice are stored in every mirrored region.\n4. `rss_limited` — live fallback only.\n\n`googletrendarchive` and `github_rss_mirror` have equal merge quality: neither replaces the other when a region already exists. Direct live data can upgrade either historical source.\n"""
    new = """1. `google_trending_now` — direct live Trending Now capture; highest quality.\n2. `googletrendarchive` — CC-BY-4.0 historical daily recovery.\n3. `github_rss_mirror` — historical Google Trending RSS snapshots mirrored from `fdciabdul/Google-Trends-Keywords-Scraper` only where a canonical region/date is missing. Exact commit/file provenance and the upstream **All Rights Reserved** notice are stored in every mirrored region.\n4. `github_hottrends_mirror` — legacy Google Hot Trends Atom snapshots recovered from exact Git commits when the modern mirror has a hole; provenance includes the historical `pn` endpoint, commit and file path.\n5. `rss_limited` — live fallback only.\n\nThe three historical sources have equal merge quality: they fill holes but never replace one another. Direct live data can upgrade any historical source.\n"""
    if old not in text:
        raise ValueError("README source-priority block changed unexpectedly")
    text = text.replace(old, new)

    old2 = """The GitHub RSS mirror is used to fill missing region snapshots without cloning the upstream repository. A one-shot manager tool selects the upstream commit closest to **12:30 Asia/Singapore** for each missing archive date, copies source JSON order, preserves the exact commit/file/RSS endpoint, and records results in `mirror-manifest.json`. It never invents breakdowns, categories, timestamps, or Explore URLs that the RSS mirror did not preserve.\n"""
    new2 = """The GitHub RSS mirror is used to fill missing region snapshots without cloning the upstream repository. A one-shot manager tool selects the upstream commit closest to **12:30 Asia/Singapore** for each missing archive date, copies source JSON order, preserves the exact commit/file/RSS endpoint, and records results in `mirror-manifest.json`. For the isolated **2025-02-05** SG/US/GB hole, a second Git-history source preserved Google's predecessor Hot Trends Atom feed; those snapshots are kept separately as `github_hottrends_mirror` rather than being relabeled as modern RSS. Mirror imports never invent fields absent from their source.\n"""
    if old2 not in text:
        raise ValueError("README historical-recovery block changed unexpectedly")
    path.write_text(text.replace(old2, new2), encoding="utf-8")


def write_report(writes: dict[str, int]) -> None:
    report_dir = ROOT / "tools" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "google-trending-residual-recovery-2026-09-01.md"
    recovered = ", ".join(sorted(writes)) or "none"
    fork_lines = "\n".join(f"- `{repo}`" for repo in CHECKED_FORKS)
    path.write_text(
        f"""# Google Trending residual recovery — 2026-09-01\n\n## Recovered\n\n- **2025-02-05:** recovered **{recovered}** from `{SOURCE_REPO}` commit `{SOURCE_COMMIT}`.\n- The source collector at that commit directly used Google's legacy Hot Trends Atom endpoint. Region IDs were SG=`p5`, US=`p1`, GB=`p9`.\n- Source feed order, item titles, published timestamps and Google links were preserved. Search-volume fields remain `null` where the old snapshot did not preserve them.\n- Existing HK data from `googletrendarchive` was not replaced.\n\n## Unresolved source-side gaps\n\n- **2025-03-24:** SG / US / GB / HK remain unavailable.\n- **2025-03-27:** HK remains unavailable.\n\nThe primary GitHub RSS mirror had no source commit for those UTC dates. The following long-lived forks were also checked and had no commit on the unresolved dates:\n\n{fork_lines}\n\nBecause these repositories share the same scraper lineage and all show the same date-level outage, no later 48-hour snapshot is backdated or synthesized as a missing daily snapshot.\n\n## 2026 required gap\n\nThe required **2026-01-04 through 2026-08-31** mirror range remains complete for SG / US / GB / HK.\n""",
        encoding="utf-8",
    )


def main() -> int:
    target = archive_path(DAY)
    before = read_json(target)
    expected_missing = {"SG", "US", "GB"}
    actual_missing = expected_missing - set(before.get("regions", {}))
    if actual_missing != expected_missing:
        raise SystemExit(f"unexpected pre-state for {DAY}: missing={sorted(actual_missing)}")

    writes: dict[str, int] = {}
    for geo, (filename, pn) in TARGETS.items():
        raw = fetch_source(filename)
        candidate = source_region(geo, filename, pn, raw)
        _, changed = merge_region(DAY, geo, candidate)
        if not changed:
            raise SystemExit(f"{geo}: expected missing region was not written")
        writes[geo] = 1

    errors = validate_document(read_json(target), DAY)
    if errors:
        raise SystemExit("; ".join(errors))

    update_manifest(writes)
    update_readme_source_notes()
    write_report(writes)
    print(json.dumps({"recovered": writes, "remaining": missing_between("2024-11-28", "2026-08-31")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
