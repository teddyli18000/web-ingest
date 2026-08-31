#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

TASK_ROOT = Path(__file__).resolve().parent
DATA_ROOT = TASK_ROOT / "data"
REGIONS = ("SG", "US", "GB", "HK")
SCHEMA_VERSION = 1
SOURCE_QUALITY = {
    "rss_limited": 1,
    "googletrendarchive": 2,
    "google_trending_now": 3,
}


def archive_path(day: str) -> Path:
    parsed = date.fromisoformat(day)
    return DATA_ROOT / f"{parsed.year:04d}" / f"{parsed.month:02d}" / f"{parsed.day:02d}" / "trending.json"


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_volume_label(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip().upper().replace(",", "").replace("+", "")
    if not text:
        return None
    multiplier = 1
    if text.endswith("K"):
        multiplier, text = 1_000, text[:-1]
    elif text.endswith("M"):
        multiplier, text = 1_000_000, text[:-1]
    try:
        return int(float(text) * multiplier)
    except ValueError:
        return None


def normalize_breakdown(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def canonical_item(item: dict[str, Any], rank: int) -> dict[str, Any]:
    query = item.get("query") or item.get("Trends") or item.get("Trend") or ""
    label = item.get("search_volume_label")
    if label is None:
        raw_volume = item.get("Search volume")
        label = raw_volume if isinstance(raw_volume, str) else None

    numeric = item.get("search_volume")
    if not isinstance(numeric, (int, float)):
        numeric = item.get("search_volume_lower")
    if not isinstance(numeric, (int, float)):
        numeric = parse_volume_label(label)

    categories = item.get("categories")
    if not isinstance(categories, list):
        categories = []

    return {
        "rank": rank,
        "query": str(query).strip(),
        "normalized_query": item.get("normalized_query"),
        "search_volume": int(numeric) if isinstance(numeric, (int, float)) else None,
        "search_volume_label": str(label).strip() if label not in (None, "") else None,
        "increase_percentage": item.get("increase_percentage"),
        "started_at": item.get("started_at") or item.get("Started"),
        "ended_at": item.get("ended_at") or item.get("Ended"),
        "active": item.get("active"),
        "trend_breakdown": normalize_breakdown(item.get("trend_breakdown") or item.get("Trend breakdown")),
        "categories": categories,
        "explore_url": item.get("explore_url") or item.get("Explore link") or item.get("Explore URL"),
    }


def new_document(day: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "date": day,
        "kind": "google-trends-trending-now-daily",
        "regions": {},
    }


def validate_document(payload: dict[str, Any], expected_date: str | None = None) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    day = payload.get("date")
    try:
        parsed = date.fromisoformat(day) if isinstance(day, str) else None
    except ValueError:
        parsed = None
    if parsed is None:
        errors.append("date must be YYYY-MM-DD")
    elif expected_date and day != expected_date:
        errors.append(f"date mismatch: {day} != {expected_date}")

    regions = payload.get("regions")
    if not isinstance(regions, dict) or not regions:
        errors.append("regions must be a non-empty object")
        return errors

    for geo, region in regions.items():
        if geo not in REGIONS:
            errors.append(f"unsupported region: {geo}")
            continue
        if not isinstance(region, dict):
            errors.append(f"{geo}: region must be an object")
            continue
        source = region.get("source")
        if source not in SOURCE_QUALITY:
            errors.append(f"{geo}: unsupported source {source!r}")
        items = region.get("items")
        if not isinstance(items, list) or not items:
            errors.append(f"{geo}: items must be a non-empty list")
            continue

        seen: set[str] = set()
        for rank, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                errors.append(f"{geo}: item {rank} must be an object")
                continue
            if item.get("rank") != rank:
                errors.append(f"{geo}: rank {rank} stored as {item.get('rank')!r}")
            query = item.get("query")
            if not isinstance(query, str) or not query.strip():
                errors.append(f"{geo}: item {rank} has empty query")
                continue
            key = query.strip().casefold()
            if key in seen:
                errors.append(f"{geo}: duplicate query at rank {rank}: {query}")
            seen.add(key)
    return errors


def merge_region(day: str, geo: str, candidate: dict[str, Any], *, force: bool = False) -> tuple[Path, bool]:
    if geo not in REGIONS:
        raise ValueError(f"unsupported region: {geo}")
    path = archive_path(day)
    payload = read_json(path) if path.exists() else new_document(day)
    current = payload.setdefault("regions", {}).get(geo)

    if current and not force:
        old_quality = SOURCE_QUALITY.get(str(current.get("source")), 0)
        new_quality = SOURCE_QUALITY.get(str(candidate.get("source")), 0)
        if new_quality <= old_quality:
            return path, False

    payload["regions"][geo] = candidate
    errors = validate_document(payload, day)
    if errors:
        raise ValueError("; ".join(errors))
    write_json(path, payload)
    return path, True


def iter_archive_files() -> list[Path]:
    if not DATA_ROOT.exists():
        return []
    return sorted(DATA_ROOT.glob("[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]/trending.json"))
