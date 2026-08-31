#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from archive_lib import make_item, merge_candidate, normalize_repo, parse_markdown_language_archive, to_int, validate_day, write_day
from scope_normalization import normalize_scope

SOURCES = {
    "larsbijl": ("https://github.com/larsbijl/trending_archive.git", 220, None),
    "hanishrao": ("https://github.com/hanishrao/trending-collection.git", 180, None),
    "ifyour": ("https://github.com/ifyour/github-trending-archive.git", 360, "data"),
    "leko": ("https://github.com/Leko/github-trending-archive.git", 420, "archive/raw"),
    "anton": ("https://github.com/antonkomarev/github-trending-archive.git", 380, "archive/repository"),
}
DATE_MD = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
DATE_JSON = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def clone_sources(base: Path, selected: set[str]) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    for key in sorted(selected):
        url, _, sparse = SOURCES[key]
        dest = base / key
        print(f"cloning {key}")
        if sparse:
            subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--no-checkout", url, str(dest)], check=True)
            subprocess.run(["git", "-C", str(dest), "sparse-checkout", "set", sparse], check=True)
            subprocess.run(["git", "-C", str(dest), "checkout"], check=True)
        else:
            subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", url, str(dest)], check=True)
        roots[key] = dest
    return roots


def snapshot(scope: str, source: str, path: Path, root: Path, items: list[dict]) -> dict:
    return {"scope": scope, "source": source,
            "source_path": path.relative_to(root).as_posix(), "items": items}


def merge(store, date: str, scope: str, score: int, candidate: dict) -> bool:
    """Merge one historical candidate using the canonical scope key."""
    canonical = normalize_scope(scope)
    if candidate.get("scope") != canonical:
        candidate = dict(candidate)
        candidate["scope"] = canonical
    return merge_candidate(store, date, canonical, score, candidate)


def import_markdown(store, root: Path, source: str, score: int) -> Counter:
    stats = Counter()
    for path in root.rglob("*.md"):
        match = DATE_MD.fullmatch(path.name)
        if not match or path.name.endswith("_short.md"):
            continue
        date = match.group(1)
        scopes = parse_markdown_language_archive(path.read_text(encoding="utf-8", errors="replace"))
        if scopes:
            stats["dates_seen"] += 1
        for scope, items in scopes.items():
            if merge(store, date, scope, score, snapshot(scope, source, path, root, items)):
                stats["selected_snapshots"] += 1
            else:
                stats["lower_priority_snapshots"] += 1
    return stats


def import_ifyour(store, root: Path, score: int) -> Counter:
    stats = Counter()
    for path in (root / "data").glob("*.json"):
        match = DATE_JSON.fullmatch(path.name)
        if not match:
            continue
        date = match.group(1)
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            stats["errors"] += 1
            continue
        items: list[dict] = []
        for row in rows if isinstance(rows, list) else []:
            repo = normalize_repo(str(row.get("title") or row.get("url") or ""))
            if not repo or any(x["repo"].casefold() == repo.casefold() for x in items):
                continue
            lang = row.get("lang") if isinstance(row.get("lang"), str) else None
            items.append(make_item(len(items) + 1, repo, language=lang))
        if items:
            if merge(store, date, "all", score,
                     snapshot("all", "ifyour/github-trending-archive", path, root, items)):
                stats["selected_snapshots"] += 1
            else:
                stats["lower_priority_snapshots"] += 1
            stats["dates_seen"] += 1
    return stats


def import_leko(store, root: Path, score: int) -> Counter:
    stats = Counter()
    base = root / "archive" / "raw"
    if not base.exists():
        return stats
    for day_dir in base.iterdir():
        if not day_dir.is_dir() or not DATE.fullmatch(day_dir.name):
            continue
        any_snapshot = False
        for path in day_dir.glob("*.csv"):
            if path.stat().st_size == 0:
                continue
            try:
                with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
                    rows = list(csv.DictReader(fh))
            except OSError:
                stats["errors"] += 1
                continue
            items: list[dict] = []
            scope = path.stem.casefold()
            for row in rows:
                repo = normalize_repo(f"{row.get('owner','')}/{row.get('name','')}") or normalize_repo(row.get("url", ""))
                if not repo or any(x["repo"].casefold() == repo.casefold() for x in items):
                    continue
                language = row.get("language") or None
                items.append(make_item(len(items) + 1, repo, language=language,
                                       stars_today=to_int(row.get("starsToday")),
                                       total_stars=to_int(row.get("stargazers"))))
            if items:
                if merge(store, day_dir.name, scope, score,
                         snapshot(scope, "Leko/github-trending-archive", path, root, items)):
                    stats["selected_snapshots"] += 1
                else:
                    stats["lower_priority_snapshots"] += 1
                any_snapshot = True
        if any_snapshot:
            stats["dates_seen"] += 1
    return stats


def import_anton(store, root: Path, score: int) -> Counter:
    stats = Counter()
    base = root / "archive" / "repository"
    seen_dates: set[str] = set()
    if not base.exists():
        return stats
    for path in base.glob("*/*/*.json"):
        date = path.parent.name
        if not DATE.fullmatch(date):
            continue
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            stats["errors"] += 1
            continue
        repos = obj.get("list") if isinstance(obj, dict) else None
        if not isinstance(repos, list) or not repos:
            continue
        raw_scope = obj.get("language")
        scope = "all" if raw_scope in (None, "", "null") or path.stem == "(null)" else str(raw_scope).casefold().replace(" ", "-")
        items: list[dict] = []
        for value in repos:
            repo = normalize_repo(str(value))
            if repo and not any(x["repo"].casefold() == repo.casefold() for x in items):
                items.append(make_item(len(items) + 1, repo))
        if items:
            if merge(store, date, scope, score,
                     snapshot(scope, "antonkomarev/github-trending-archive", path, root, items)):
                stats["selected_snapshots"] += 1
            else:
                stats["lower_priority_snapshots"] += 1
            seen_dates.add(date)
    stats["dates_seen"] = len(seen_dates)
    return stats


def build_output(store, output: Path, stats: dict[str, Counter]) -> dict:
    dates = sorted(store)
    years = Counter()
    source_counts = Counter()
    scope_counts = Counter()
    for date in dates:
        snapshots = [value[1] for scope, value in sorted(store[date].items(), key=lambda kv: (kv[0] != "all", kv[0]))]
        for snap in snapshots:
            source_counts[snap["source"]] += 1
            scope_counts[snap["scope"]] += 1
        day = {"schema_version": 1, "date": date, "captured_at": None, "snapshots": snapshots}
        validate_day(day)
        write_day(output, day)
        years[date[:4]] += 1

    all_dates = [date for date in dates if "all" in store[date]]
    manifest = {
        "schema_version": 1,
        "generated_from_public_archives": True,
        "earliest_date": dates[0] if dates else None,
        "latest_date": dates[-1] if dates else None,
        "dates": len(dates),
        "all_scope_dates": len(all_dates),
        "earliest_all_scope_date": all_dates[0] if all_dates else None,
        "latest_all_scope_date": all_dates[-1] if all_dates else None,
        "year_counts": dict(sorted(years.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "scope_counts": dict(sorted(scope_counts.items())),
        "source_scan_stats": {key: dict(value) for key, value in sorted(stats.items())},
        "merge_policy": "one canonical snapshot per date+scope; deterministic source priority; no synthesized cross-language ranking",
    }
    (output / "backfill-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--source", action="append", choices=sorted(SOURCES))
    parser.add_argument("--source-root", action="append", default=[], metavar="KEY=PATH")
    args = parser.parse_args()

    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    selected = set(args.source or SOURCES)
    explicit: dict[str, Path] = {}
    for spec in args.source_root:
        key, sep, value = spec.partition("=")
        if not sep or key not in SOURCES:
            parser.error(f"invalid --source-root {spec!r}")
        explicit[key] = Path(value).resolve()
        selected.add(key)

    with tempfile.TemporaryDirectory(prefix="github-trending-backfill-") as tmp:
        roots = dict(explicit)
        roots.update(clone_sources(Path(tmp), selected - roots.keys()))
        store: dict[str, dict[str, tuple[int, dict]]] = {}
        stats: dict[str, Counter] = defaultdict(Counter)
        if "larsbijl" in roots:
            stats["larsbijl"] = import_markdown(store, roots["larsbijl"], "larsbijl/trending_archive", SOURCES["larsbijl"][1])
        if "hanishrao" in roots:
            stats["hanishrao"] = import_markdown(store, roots["hanishrao"], "hanishrao/trending-collection", SOURCES["hanishrao"][1])
        if "ifyour" in roots:
            stats["ifyour"] = import_ifyour(store, roots["ifyour"], SOURCES["ifyour"][1])
        if "leko" in roots:
            stats["leko"] = import_leko(store, roots["leko"], SOURCES["leko"][1])
        if "anton" in roots:
            stats["anton"] = import_anton(store, roots["anton"], SOURCES["anton"][1])
        manifest = build_output(store, output, stats)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
