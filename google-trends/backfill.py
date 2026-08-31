#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from archive_lib import day_path, load_config, merge_day, parse_historical_csv, read_day, write_day

ROOT = Path(__file__).resolve().parent
DATE8_RE = re.compile(r"(?<!\d)(20\d{6})(?!\d)")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def member_geo(name: str, selected: set[str]) -> str | None:
    for part in PurePosixPath(name).parts[:-1]:
        upper = part.upper()
        if upper in selected:
            return upper
    return None


def member_date(name: str) -> str | None:
    match = DATE8_RE.search(PurePosixPath(name).name)
    if not match:
        return None
    raw = match.group(1)
    return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Import selected geos from GoogleTrendArchive daily_compressed.zip")
    parser.add_argument("--zip", required=True, dest="zip_path")
    parser.add_argument("--source-url", default="https://huggingface.co/datasets/aurman/GoogleTrendArchive")
    parser.add_argument("--zip-sha256")
    args = parser.parse_args()

    zip_path = Path(args.zip_path).resolve()
    config = load_config(ROOT)
    geo_meta = {geo["code"]: geo for geo in config["geos"]}
    selected = set(geo_meta)

    candidates: dict[tuple[str, str], list[tuple[str, list[dict[str, Any]]]]] = defaultdict(list)
    scanned = 0
    parse_errors: list[str] = []

    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".csv"):
                continue
            geo = member_geo(info.filename, selected)
            date = member_date(info.filename)
            if not geo or not date:
                continue
            scanned += 1
            try:
                text = archive.read(info).decode("utf-8-sig", errors="replace")
                items = parse_historical_csv(text)
            except Exception as exc:
                parse_errors.append(f"{info.filename}: {exc}")
                continue
            candidates[(date, geo)].append((info.filename, items))

    if not candidates:
        raise RuntimeError("no selected-geo historical CSV snapshots found in archive")

    per_geo_days: Counter[str] = Counter()
    days: dict[str, list[dict[str, Any]]] = defaultdict(list)
    duplicate_candidates = 0
    for (date, geo), options in sorted(candidates.items()):
        duplicate_candidates += max(0, len(options) - 1)
        # Deterministic best candidate: preserve the fullest observed daily list;
        # tie-break by member path so reruns are stable.
        member, items = max(options, key=lambda pair: (len(pair[1]), pair[0]))
        per_geo_days[geo] += 1
        days[date].append(
            {
                "geo": geo,
                "geo_name": geo_meta[geo]["name"],
                "source": "aurman/GoogleTrendArchive",
                "source_kind": "historical_csv",
                "source_member": member,
                "items": items,
            }
        )

    changed = 0
    for date, snapshots in sorted(days.items()):
        incoming = {
            "schema_version": 1,
            "date": date,
            "captured_at": None,
            "period_hours": 24,
            "coverage": "core-geos",
            "snapshots": sorted(snapshots, key=lambda item: item["geo"]),
        }
        path = day_path(ROOT, date)
        existing = read_day(path) if path.exists() else None
        merged = merge_day(existing, incoming, prefer_existing=True)
        if existing != merged:
            write_day(ROOT, merged)
            changed += 1

    dates = sorted(days)
    manifest = {
        "schema_version": 1,
        "source": "aurman/GoogleTrendArchive",
        "source_url": args.source_url,
        "source_license": "CC-BY-4.0",
        "source_archive": zip_path.name,
        "source_archive_sha256": args.zip_sha256 or sha256_file(zip_path),
        "imported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "selected_geos": sorted(selected),
        "earliest_date": dates[0],
        "latest_date": dates[-1],
        "dates_with_selected_geo_data": len(dates),
        "per_geo_days": dict(sorted(per_geo_days.items())),
        "matching_csv_members_scanned": scanned,
        "duplicate_date_geo_candidates": duplicate_candidates,
        "parse_error_count": len(parse_errors),
        "parse_error_examples": parse_errors[:20],
        "files_changed": changed,
        "selection_policy": "for duplicate date+geo raw CSVs, choose most valid rows; tie-break by member path; existing direct snapshots win on overlap",
    }
    (ROOT / "backfill-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
