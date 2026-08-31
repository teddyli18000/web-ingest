#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from archive_lib import load_config, read_day, write_day

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "backfill-manifest.json"


def archive_files() -> list[Path]:
    return sorted(ROOT.glob("data/*/*/*/trending.json"))


def prune_day(day: dict[str, Any], selected: set[str]) -> tuple[dict[str, Any] | None, set[str]]:
    before = {snapshot["geo"] for snapshot in day["snapshots"]}
    kept = [snapshot for snapshot in day["snapshots"] if snapshot["geo"] in selected]
    removed = before - {snapshot["geo"] for snapshot in kept}
    if not kept:
        return None, removed
    updated = dict(day)
    updated["coverage"] = "core-geos"
    updated["snapshots"] = sorted(kept, key=lambda snapshot: snapshot["geo"])
    return updated, removed


def remove_empty_parents(path: Path) -> None:
    parent = path.parent
    data_root = ROOT / "data"
    while parent != data_root and parent.is_dir():
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def historical_stats() -> tuple[list[str], Counter[str]]:
    dates: list[str] = []
    per_geo: Counter[str] = Counter()
    for path in archive_files():
        day = read_day(path)
        historical = [snapshot for snapshot in day["snapshots"] if snapshot.get("source_kind") == "historical_csv"]
        if not historical:
            continue
        dates.append(day["date"])
        per_geo.update(snapshot["geo"] for snapshot in historical)
    return sorted(set(dates)), per_geo


def rewrite_manifest(selected: set[str], repair_stats: dict[str, Any]) -> bool:
    if not MANIFEST_PATH.exists():
        return False
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    original = dict(manifest)

    if "original_import_stats" not in manifest:
        manifest["original_import_stats"] = {
            "selected_geos": manifest.get("selected_geos"),
            "dates_with_selected_geo_data": manifest.get("dates_with_selected_geo_data"),
            "per_geo_days": manifest.get("per_geo_days"),
            "matching_csv_members_scanned": manifest.get("matching_csv_members_scanned"),
            "duplicate_date_geo_candidates": manifest.get("duplicate_date_geo_candidates"),
            "parse_error_count": manifest.get("parse_error_count"),
            "parse_error_examples": manifest.get("parse_error_examples"),
            "files_changed": manifest.get("files_changed"),
        }

    for key in (
        "matching_csv_members_scanned",
        "duplicate_date_geo_candidates",
        "parse_error_count",
        "parse_error_examples",
        "files_changed",
    ):
        manifest.pop(key, None)

    dates, per_geo = historical_stats()
    manifest["selected_geos"] = sorted(selected)
    manifest["earliest_date"] = dates[0] if dates else None
    manifest["latest_date"] = dates[-1] if dates else None
    manifest["dates_with_selected_geo_data"] = len(dates)
    manifest["per_geo_days"] = {geo: per_geo.get(geo, 0) for geo in sorted(selected)}

    if repair_stats["rewritten_files"] or repair_stats["deleted_files"] or "core_geo_repair" not in manifest:
        previous = manifest.get("core_geo_repair")
        if previous and not repair_stats["rewritten_files"] and not repair_stats["deleted_files"]:
            repair = previous
        else:
            repair = {
                "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "selected_geos": sorted(selected),
                "removed_geos": sorted(repair_stats["removed_geos"]),
                "rewritten_files": repair_stats["rewritten_files"],
                "deleted_files": repair_stats["deleted_files"],
                "policy": "keep only geos currently declared in config.json; preserve surviving source rows unchanged",
            }
        manifest["core_geo_repair"] = repair

    if manifest == original:
        return False
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def main() -> int:
    config = load_config(ROOT)
    selected = {geo["code"] for geo in config["geos"]}
    if not selected:
        raise RuntimeError("config selected no geos")

    rewritten = 0
    deleted = 0
    removed_geos: set[str] = set()

    for path in archive_files():
        day = read_day(path)
        updated, removed = prune_day(day, selected)
        removed_geos.update(removed)
        if updated is None:
            path.unlink()
            remove_empty_parents(path)
            deleted += 1
            continue
        if updated != day:
            write_day(ROOT, updated)
            rewritten += 1

    stats = {
        "selected_geos": sorted(selected),
        "removed_geos": removed_geos,
        "rewritten_files": rewritten,
        "deleted_files": deleted,
    }
    manifest_changed = rewrite_manifest(selected, stats)
    print(
        json.dumps(
            {
                **{key: (sorted(value) if isinstance(value, set) else value) for key, value in stats.items()},
                "manifest_changed": manifest_changed,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
