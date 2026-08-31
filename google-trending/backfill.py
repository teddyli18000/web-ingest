#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    for part in PurePosixPath(name.replace("\\", "/")).parts[:-1]:
        upper = part.upper()
        if upper in REGIONS:
            return upper
    return None


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


def select_members(zf: zipfile.ZipFile, year: int | None = None) -> tuple[dict[tuple[str, str], tuple[str, list[dict]]], list[str], int]:
    candidates: dict[tuple[str, str], list[tuple[str, list[dict]]]] = defaultdict(list)
    parse_errors: list[str] = []
    scanned = 0
    for info in zf.infolist():
        if info.is_dir() or not info.filename.lower().endswith(".csv"):
            continue
        geo = member_geo(info.filename)
        day = member_date(info.filename)
        if geo not in REGIONS or day is None:
            continue
        if year is not None and not day.startswith(f"{year:04d}-"):
            continue
        scanned += 1
        try:
            items = parse_csv(zf.read(info))
        except Exception as exc:
            parse_errors.append(f"{info.filename}: {exc}")
            continue
        if not items:
            parse_errors.append(f"{info.filename}: historical CSV contained no usable trend rows")
            continue
        candidates[(geo, day)].append((info.filename, items))

    selected = {
        key: max(options, key=lambda pair: (len(pair[1]), pair[0]))
        for key, options in candidates.items()
    }
    return selected, parse_errors, scanned


def update_manifest(year: int | None, selected: dict[tuple[str, str], tuple[str, list[dict]]], writes: int, parse_errors: list[str], scanned: int, zip_sha256: str) -> None:
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    else:
        manifest = {
            "schema_version": 1,
            "source": "aurman/GoogleTrendArchive",
            "source_url": DATASET_URL,
            "dataset_doi": DATASET_DOI,
            "license": "CC-BY-4.0",
            "policy": "SG/US only; daily_compressed.zip CSVs; lower-quality sources never overwrite live captures",
            "years": {},
        }

    days = sorted({day for _, day in selected})
    geos = Counter(geo for geo, _ in selected)
    key = str(year) if year is not None else "all"
    manifest["source_archive"] = "daily_compressed.zip"
    manifest["source_archive_sha256"] = zip_sha256
    manifest["years"][key] = {
        "selected_region_days": len(selected),
        "writes_or_upgrades": writes,
        "first_day": days[0] if days else None,
        "last_day": days[-1] if days else None,
        "selected_by_region": dict(sorted(geos.items())),
        "matching_csv_members_scanned": scanned,
        "duplicate_or_extra_candidates": max(0, scanned - len(selected) - len(parse_errors)),
        "parse_error_count": len(parse_errors),
        "parse_error_examples": parse_errors[:10],
    }
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import SG/US GoogleTrendArchive daily Trending Now CSVs")
    parser.add_argument("--zip", required=True, help="path to upstream daily_compressed.zip")
    parser.add_argument("--zip-sha256", help="known SHA-256 for the upstream ZIP")
    parser.add_argument("--year", type=int, help="only import one calendar year")
    args = parser.parse_args()

    zip_path = Path(args.zip).resolve()
    zip_sha256 = args.zip_sha256 or sha256_file(zip_path)
    writes = 0
    with zipfile.ZipFile(zip_path) as zf:
        selected, parse_errors, scanned = select_members(zf, args.year)
        if not selected:
            raise SystemExit("No matching SG/US daily CSV members found")
        for (geo, day), (member, items) in sorted(selected.items(), key=lambda pair: (pair[0][1], pair[0][0])):
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

    update_manifest(args.year, selected, writes, parse_errors, scanned, zip_sha256)
    print(json.dumps({"year": args.year, "selected_region_days": len(selected), "writes_or_upgrades": writes, "matching_csv_members_scanned": scanned, "parse_errors": len(parse_errors)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
