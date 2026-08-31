#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from archive_lib import REGIONS, TASK_ROOT, canonical_item, merge_region

DATASET_URL = "https://huggingface.co/datasets/aurman/GoogleTrendArchive"
DATASET_DOI = "10.57967/hf/7531"
MANIFEST = TASK_ROOT / "backfill-manifest.json"
DATE_RE = re.compile(r"(?<!\d)(20\d{6})(?!\d)")
GEO_RE = re.compile(r"(?:^|[/_.-])(SG|US)(?:$|[/_.-])", re.IGNORECASE)


def normalized_key(value: str) -> str:
    return " ".join(value.replace("_", " ").replace("-", " ").strip().lower().split())


def value_for(row: dict[str, str], *aliases: str) -> str | None:
    normalized = {normalized_key(key): value for key, value in row.items() if key is not None}
    for alias in aliases:
        value = normalized.get(normalized_key(alias))
        if value not in (None, ""):
            return value
    return None


def member_date(name: str) -> str | None:
    match = DATE_RE.search(PurePosixPath(name).name)
    if not match:
        return None
    raw = match.group(1)
    return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"


def member_geo(name: str) -> str | None:
    match = GEO_RE.search(name.replace("\\", "/"))
    return match.group(1).upper() if match else None


def is_daily_member(name: str) -> bool:
    lowered = name.lower().replace("\\", "/")
    basename = PurePosixPath(lowered).name
    return (
        "_1d_" in basename
        or "-1d-" in basename
        or basename.endswith("_1d.csv")
        or "/1d/" in lowered
    )


def select_members(zf: zipfile.ZipFile, year: int | None = None) -> dict[tuple[str, str], str]:
    candidates: dict[tuple[str, str], list[tuple[int, str]]] = defaultdict(list)
    for info in zf.infolist():
        if info.is_dir() or not info.filename.lower().endswith(".csv"):
            continue
        if not is_daily_member(info.filename):
            continue
        geo = member_geo(info.filename)
        day = member_date(info.filename)
        if geo not in REGIONS or day is None:
            continue
        if year is not None and not day.startswith(f"{year:04d}-"):
            continue
        candidates[(geo, day)].append((info.file_size, info.filename))

    # Some archives contain repeated snapshots for one region/day. The largest daily CSV is the
    # least-truncated candidate; tie-breaking by name keeps selection deterministic.
    return {
        key: max(entries, key=lambda item: (item[0], item[1]))[1]
        for key, entries in candidates.items()
    }


def parse_csv(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    items: list[dict] = []
    seen: set[str] = set()
    for row in reader:
        query = value_for(row, "Trends", "Trend", "query", "Search term")
        if not query or not query.strip():
            continue
        key = query.strip().casefold()
        if key in seen:
            continue
        seen.add(key)
        item = {
            "query": query.strip(),
            "Search volume": value_for(row, "Search volume", "search_volume", "Volume"),
            "Started": value_for(row, "Started", "started_at", "Start"),
            "Ended": value_for(row, "Ended", "ended_at", "End"),
            "Trend breakdown": value_for(row, "Trend breakdown", "trend_breakdown", "Breakdown"),
            "Explore link": value_for(row, "Explore link", "Explore URL", "explore_url"),
        }
        items.append(canonical_item(item, len(items) + 1))
    return items


def update_manifest(year: int | None, selected: dict[tuple[str, str], str], writes: int) -> None:
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    else:
        manifest = {
            "source": DATASET_URL,
            "dataset_doi": DATASET_DOI,
            "license": "CC-BY-4.0",
            "policy": "SG/US only; 1-day Trending Now CSVs; lower-quality sources never overwrite live captures",
            "years": {},
        }

    days = sorted({day for _, day in selected})
    geos = Counter(geo for geo, _ in selected)
    key = str(year) if year is not None else "all"
    manifest["years"][key] = {
        "selected_region_days": len(selected),
        "writes_or_upgrades": writes,
        "first_day": days[0] if days else None,
        "last_day": days[-1] if days else None,
        "selected_by_region": dict(sorted(geos.items())),
    }
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import SG/US GoogleTrendArchive daily Trending Now CSVs")
    parser.add_argument("--zip", required=True, help="path to upstream daily_compressed.zip")
    parser.add_argument("--year", type=int, help="only import one calendar year")
    args = parser.parse_args()

    writes = 0
    with zipfile.ZipFile(args.zip) as zf:
        selected = select_members(zf, args.year)
        if not selected:
            raise SystemExit("No matching SG/US 1-day CSV members found")

        for (geo, day), member in sorted(selected.items(), key=lambda pair: (pair[0][1], pair[0][0])):
            items = parse_csv(zf.read(member))
            if not items:
                print(f"WARN {geo} {day}: empty parsed CSV {member}", file=sys.stderr)
                continue
            region = {
                "source": "googletrendarchive",
                "fetch_status": "historical_import",
                "source_url": DATASET_URL,
                "source_member": member,
                "dataset_doi": DATASET_DOI,
                "license": "CC-BY-4.0",
                "captured_at": None,
                "window_hours": 24,
                "sort": "source_csv_order",
                "items": items,
            }
            _, wrote = merge_region(day, geo, region)
            writes += int(wrote)

    update_manifest(args.year, selected, writes)
    print(json.dumps({
        "year": args.year,
        "selected_region_days": len(selected),
        "writes_or_upgrades": writes,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
