#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from archive_lib import load_config, read_day

ROOT = Path(__file__).resolve().parent


def main() -> int:
    config = load_config(ROOT)
    allowed = {geo["code"] for geo in config["geos"]}
    files = sorted(ROOT.glob("data/*/*/*/trending.json"))
    if not files:
        raise RuntimeError("Google Trends archive has no daily files")

    counts = {geo: 0 for geo in sorted(allowed)}
    seen_dates: set[str] = set()
    for path in files:
        day = read_day(path)
        date = day["date"]
        if date in seen_dates:
            raise RuntimeError(f"duplicate archive date: {date}")
        seen_dates.add(date)
        expected_path = ROOT / "data" / date[:4] / date[5:7] / date[8:10] / "trending.json"
        if path != expected_path:
            raise RuntimeError(f"path/date mismatch: {path.relative_to(ROOT)} != {expected_path.relative_to(ROOT)}")

        geos = {snapshot["geo"] for snapshot in day["snapshots"]}
        unexpected = geos - allowed
        if unexpected:
            raise RuntimeError(f"{date}: unexpected geos: {sorted(unexpected)}")
        for geo in geos:
            counts[geo] += 1

    if not all(counts.values()):
        raise RuntimeError(f"configured geo has zero archive coverage: {counts}")

    print(
        json.dumps(
            {
                "days": len(files),
                "first": min(seen_dates),
                "latest": max(seen_dates),
                "configured_geos": sorted(allowed),
                "per_geo_days": counts,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
