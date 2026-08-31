#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from archive_lib import read_day, validate_day, write_day
from scope_normalization import choose_snapshot, normalize_scope


def canonicalize_day(day: dict[str, Any]) -> tuple[dict[str, Any], int, int]:
    """Normalize scopes and resolve alias collisions without touching item data."""
    selected: dict[str, dict[str, Any]] = {}
    renamed = 0
    collisions = 0

    for original in day["snapshots"]:
        canonical = normalize_scope(original["scope"])
        candidate = dict(original)
        candidate["scope"] = canonical
        if canonical != original["scope"]:
            renamed += 1

        current = selected.get(canonical)
        if current is None:
            selected[canonical] = candidate
            continue

        collisions += 1
        selected[canonical] = choose_snapshot(current, candidate)

    snapshots = [selected[key] for key in sorted(selected, key=lambda value: (value != "all", value))]
    repaired = dict(day)
    repaired["snapshots"] = snapshots
    validate_day(repaired)
    return repaired, renamed, collisions


def historical_paths(root: Path, through: str) -> list[Path]:
    paths: list[Path] = []
    for path in (root / "data").glob("*/*/*/trending.json"):
        date = path.parent.name
        month = path.parent.parent.name
        year = path.parent.parent.parent.name
        full_date = f"{year}-{month}-{date}"
        if full_date <= through:
            paths.append(path)
    return sorted(paths)


def normalization_summary(manifest: dict[str, Any], renamed: int,
                          collisions: int, changed_files: int) -> dict[str, Any]:
    """Return cumulative repair statistics so a no-op rerun cannot erase history."""
    previous = manifest.get("scope_normalization")
    previous = previous if isinstance(previous, dict) else {}

    def previous_int(key: str) -> int:
        value = previous.get(key, 0)
        return value if isinstance(value, int) and value >= 0 else 0

    return {
        "aliases": {"cpp": "c++", "c%23": "c#"},
        "collision_resolution": "same deterministic historical source priority used by backfill; ties keep the existing snapshot",
        "renamed_snapshots_seen": previous_int("renamed_snapshots_seen") + renamed,
        "alias_collisions_resolved": previous_int("alias_collisions_resolved") + collisions,
        "files_changed": previous_int("files_changed") + changed_files,
    }


def refresh_manifest(root: Path, manifest: dict[str, Any], through: str,
                     renamed: int, collisions: int, changed_files: int) -> dict[str, Any]:
    years: Counter[str] = Counter()
    scopes: Counter[str] = Counter()
    sources: Counter[str] = Counter()
    dates: list[str] = []
    all_dates: list[str] = []

    for path in historical_paths(root, through):
        day = read_day(path)
        date = day["date"]
        dates.append(date)
        years[date[:4]] += 1
        has_all = False
        for snapshot in day["snapshots"]:
            scope = snapshot["scope"]
            if normalize_scope(scope) != scope:
                raise ValueError(f"non-canonical scope remains in {path}: {scope}")
            scopes[scope] += 1
            sources[str(snapshot.get("source", "unknown"))] += 1
            has_all = has_all or scope == "all"
        if has_all:
            all_dates.append(date)

    updated = dict(manifest)
    updated.update({
        "earliest_date": dates[0] if dates else None,
        "latest_date": dates[-1] if dates else None,
        "dates": len(dates),
        "all_scope_dates": len(all_dates),
        "earliest_all_scope_date": all_dates[0] if all_dates else None,
        "latest_all_scope_date": all_dates[-1] if all_dates else None,
        "year_counts": dict(sorted(years.items())),
        "source_counts": dict(sorted(sources.items())),
        "scope_counts": dict(sorted(scopes.items())),
        "merge_policy": "one canonical snapshot per date+scope; deterministic source priority; no synthesized cross-language ranking",
        "scope_normalization": normalization_summary(manifest, renamed, collisions, changed_files),
    })
    return updated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent))
    parser.add_argument("--through", help="last historical date to mutate; defaults to manifest.latest_date")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest_path = root / "backfill-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    through = args.through or manifest["latest_date"]

    changed_files = 0
    renamed = 0
    collisions = 0
    for path in historical_paths(root, through):
        day = read_day(path)
        repaired, day_renamed, day_collisions = canonicalize_day(day)
        renamed += day_renamed
        collisions += day_collisions
        if repaired != day:
            write_day(root, repaired)
            changed_files += 1

    updated_manifest = refresh_manifest(root, manifest, through, renamed, collisions, changed_files)
    manifest_path.write_text(json.dumps(updated_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "through": through,
        "files_changed_this_run": changed_files,
        "renamed_snapshots_this_run": renamed,
        "alias_collisions_resolved_this_run": collisions,
        "cumulative_scope_normalization": updated_manifest["scope_normalization"],
        "dates": updated_manifest["dates"],
        "scopes": len(updated_manifest["scope_counts"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
