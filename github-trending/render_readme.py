#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from archive_lib import read_day

START = "<!-- archive-dashboard:start -->"
END = "<!-- archive-dashboard:end -->"


def collect(root: Path):
    files = sorted((root / "data").glob("*/*/*/trending.json")) if (root / "data").exists() else []
    rows = []
    years = Counter()
    for path in files:
        try:
            day = read_day(path)
        except Exception:
            continue
        rows.append((path, day))
        years[day["date"][:4]] += 1
    return rows, years


def dashboard(root: Path) -> str:
    rows, years = collect(root)
    if not rows:
        return f"{START}\n> Archive initialized. Historical backfill has not been committed yet.\n{END}"

    first = rows[0][1]["date"]
    latest_path, latest = rows[-1]
    latest_date = latest["date"]
    all_days = sum(any(s["scope"] == "all" for s in day["snapshots"]) for _, day in rows)
    latest_all = next((s for s in latest["snapshots"] if s["scope"] == "all"), None)

    lines = [START, "", "### Archive at a glance", "",
             "| First recovered day | Latest day | Days archived | All-Languages days |",
             "| --- | --- | ---: | ---: |",
             f"| **{first}** | **{latest_date}** | **{len(rows):,}** | **{all_days:,}** |", ""]

    if latest_all:
        lines += [f"### Latest All-Languages snapshot — {latest_date}", "",
                  "| # | Repository | Language | Stars today |",
                  "| ---: | --- | --- | ---: |"]
        for entry in latest_all["items"][:10]:
            repo = entry["repo"]
            language = entry.get("language", "—")
            stars = f"{entry['stars_today']:,}" if entry.get("stars_today") is not None else "—"
            lines.append(f"| {entry['rank']} | [{repo}](https://github.com/{repo}) | {language} | {stars} |")
        rel = latest_path.relative_to(root).as_posix()
        lines += ["", f"[Open full snapshot →]({rel})", ""]

    lines += ["### Browse by year", ""]
    lines.append("  \n".join(f"[`{year}`](data/{year}/) · {years[year]} days" for year in sorted(years, reverse=True)))
    lines += ["", END]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent))
    args = parser.parse_args()
    root = Path(args.root)
    path = root / "README.md"
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("README dashboard markers missing")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    path.write_text(before.rstrip() + "\n\n" + dashboard(root) + "\n\n" + after.lstrip(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
