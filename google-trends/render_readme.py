#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path

from archive_lib import load_config, read_day

ROOT = Path(__file__).resolve().parent
START = "<!-- archive-dashboard:start -->"
END = "<!-- archive-dashboard:end -->"


def all_days() -> list[tuple[str, Path]]:
    out = []
    for path in ROOT.glob("data/*/*/*/trending.json"):
        try:
            day = read_day(path)
        except Exception:
            continue
        out.append((day["date"], path))
    return sorted(out)


def esc(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def dashboard() -> str:
    config = load_config(ROOT)
    days = all_days()
    if not days:
        return f"{START}\n\n_No archived snapshots yet._\n\n{END}"

    earliest = days[0][0]
    latest_date, latest_path = days[-1]
    latest = read_day(latest_path)
    years = Counter(date[:4] for date, _ in days)
    snapshots = {snap["geo"]: snap for snap in latest["snapshots"]}
    flags = {geo["code"]: geo.get("flag", "") for geo in config["geos"]}
    names = {geo["code"]: geo["name"] for geo in config["geos"]}

    lines = [
        START,
        "",
        "### Archive at a glance",
        "",
        "| First archived day | Latest day | Days with data | Core regions |",
        "| --- | --- | ---: | ---: |",
        f"| **{earliest}** | **{latest_date}** | **{len(days):,}** | **{len(config['geos'])}** |",
        "",
        f"### Latest regional pulse — {latest_date}",
        "",
        "| Region | #1 trend | Volume | Top 3 |",
        "| --- | --- | ---: | --- |",
    ]
    for geo in config["geos"]:
        code = geo["code"]
        snapshot = snapshots.get(code)
        if not snapshot:
            lines.append(f"| {flags.get(code,'')} {names[code]} | — | — | — |")
            continue
        items = snapshot["items"]
        first = items[0]
        volume = first.get("search_volume_label") or "—"
        top3 = " · ".join(esc(item["query"]) for item in items[:3])
        lines.append(f"| {flags.get(code,'')} {names[code]} | **{esc(first['query'])}** | {esc(volume)} | {top3} |")

    relative = latest_path.relative_to(ROOT).as_posix()
    lines += [
        "",
        f"[Open full {latest_date} snapshot →]({relative})",
        "",
        "### Browse by year",
        "",
        "  ".join(f"[`{year}`](data/{year}/) · {count} days" for year, count in sorted(years.items(), reverse=True)),
        "",
        END,
    ]
    return "\n".join(lines)


def main() -> int:
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise ValueError("README dashboard markers missing")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    readme.write_text(before.rstrip() + "\n\n" + dashboard() + "\n" + after.lstrip(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
