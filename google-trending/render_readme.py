#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path

from archive_lib import REGIONS, iter_archive_files, read_json

README = Path(__file__).resolve().parent / "README.md"
START = "<!-- archive-dashboard:start -->"
END = "<!-- archive-dashboard:end -->"


def render_dashboard() -> str:
    files = iter_archive_files()
    if not files:
        return "> Archive initialized; historical backfill and the first live capture are pending."

    rows = [(path.parent.name, read_json(path), path) for path in files]
    first_day = rows[0][0]
    last_day = rows[-1][0]
    coverage = Counter()
    sources = Counter()
    years = Counter()

    for day, payload, _ in rows:
        years[day[:4]] += 1
        for geo, region in payload.get("regions", {}).items():
            coverage[geo] += 1
            sources[str(region.get("source", "unknown"))] += 1

    lines = [
        "### Archive at a glance",
        "",
        "| First day | Latest day | Days archived | SG days | US days |",
        "| --- | --- | ---: | ---: | ---: |",
        f"| **{first_day}** | **{last_day}** | **{len(rows):,}** | **{coverage['SG']:,}** | **{coverage['US']:,}** |",
        "",
        "### Source mix",
        "",
        "| Source | Region snapshots |",
        "| --- | ---: |",
    ]
    for source, count in sources.most_common():
        lines.append(f"| `{source}` | {count:,} |")

    latest_day, latest, latest_path = rows[-1]
    for geo in REGIONS:
        region = latest.get("regions", {}).get(geo)
        if not region:
            continue
        lines.extend([
            "",
            f"### Latest {geo} snapshot — {latest_day}",
            "",
            "| # | Trend | Search volume |",
            "| ---: | --- | ---: |",
        ])
        for item in region.get("items", [])[:10]:
            query = str(item.get("query", "")).replace("|", "\\|")
            volume = item.get("search_volume_label") or item.get("search_volume") or "—"
            lines.append(f"| {item.get('rank')} | {query} | {volume} |")

    relative = latest_path.relative_to(README.parent).as_posix()
    lines.extend(["", f"[Open full snapshot →]({relative})", "", "### Browse by year", ""])
    lines.append(" · ".join(f"[`{year}`](data/{year}/) · {count} days" for year, count in sorted(years.items(), reverse=True)))
    return "\n".join(lines)


def main() -> int:
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("README dashboard markers missing")
    before, remainder = text.split(START, 1)
    _, after = remainder.split(END, 1)
    README.write_text(before + START + "\n\n" + render_dashboard() + "\n\n" + END + after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
