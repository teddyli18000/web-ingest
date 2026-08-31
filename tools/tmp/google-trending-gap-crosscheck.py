#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time as dt_time, timezone
from pathlib import Path

REGIONS = ("SG", "US", "GB", "HK")
ANCHORS = (
    "2026-01-04",
    "2026-02-15",
    "2026-04-15",
    "2026-06-16",
    "2026-07-01",
    "2026-08-31",
)
ARCHIVE_CANDIDATES = (
    "fdciabdul/Google-Trends-Keywords-Scraper",
    "253611069/Google-Trends-Keywords-Scraper",
    "DutchErwin/Google-Trends-Keywords-Scraper",
    "imheyday/Google-Trends-Keywords-Scraper",
    "connorodea/Google-Trends-Keywords-Scraper",
)
COLLECTOR_EVIDENCE = (
    "RuochenLyu/google-trends-now",
    "aymenhmaidiwastaken/daily-country-search-trends",
    "flack0x/trendspyg",
)


def api_json(url: str, retries: int = 4) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "web-ingest-gap-crosscheck/1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    last: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"GitHub API failed after {retries} attempts: {url}: {last}")


def repo_meta(repo: str) -> dict:
    payload = api_json(f"https://api.github.com/repos/{repo}")
    if not isinstance(payload, dict):
        return {}
    license_obj = payload.get("license")
    return {
        "fork": bool(payload.get("fork")),
        "parent": (payload.get("parent") or {}).get("full_name") if isinstance(payload.get("parent"), dict) else None,
        "size_kb": payload.get("size"),
        "updated_at": payload.get("updated_at"),
        "license": license_obj.get("spdx_id") if isinstance(license_obj, dict) else None,
    }


def file_text(repo: str, path: str, ref: str = "main") -> str:
    quoted = urllib.parse.quote(path, safe="/")
    url = f"https://api.github.com/repos/{repo}/contents/{quoted}?ref={urllib.parse.quote(ref, safe='')}"
    payload = api_json(url)
    if not isinstance(payload, dict) or payload.get("encoding") != "base64":
        raise RuntimeError(f"unexpected contents response for {repo}:{path}@{ref}")
    return base64.b64decode(payload["content"]).decode("utf-8", errors="replace")


def commits_for_day(repo: str, day: str) -> list[dict]:
    parsed = date.fromisoformat(day)
    since = datetime.combine(parsed, dt_time.min, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    until = datetime.combine(parsed, dt_time.max, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    query = urllib.parse.urlencode({
        "path": "data/SG.json",
        "since": since,
        "until": until,
        "per_page": 5,
    })
    payload = api_json(f"https://api.github.com/repos/{repo}/commits?{query}")
    return payload if isinstance(payload, list) else []


def verify_commit(repo: str, sha: str) -> dict:
    regions: dict[str, object] = {}
    complete = True
    for geo in REGIONS:
        try:
            payload = json.loads(file_text(repo, f"data/{geo}.json", sha))
            items = payload.get("data")
            count = len(items) if isinstance(items, list) else 0
            first = items[0].get("title") if count and isinstance(items[0], dict) else None
            regions[geo] = {"items": count, "first": first, "lastUpdate": payload.get("lastUpdate")}
            complete = complete and count > 0
        except Exception as exc:
            regions[geo] = {"error": str(exc)}
            complete = False
    return {"complete": complete, "regions": regions}


def audit_repo(repo: str) -> dict:
    result = {"repo": repo, "meta": {}, "rights": {}, "anchors": {}}
    try:
        result["meta"] = repo_meta(repo)
    except Exception as exc:
        result["meta_error"] = str(exc)
    try:
        readme = file_text(repo, "README.md")
        lower = readme.lower()
        result["rights"] = {
            "all_rights_reserved": "all rights reserved" in lower,
            "license_word": "license" in lower,
        }
    except Exception as exc:
        result["rights_error"] = str(exc)

    for day in ANCHORS:
        entry: dict[str, object] = {"commit": None, "complete": False, "regions": {}}
        try:
            commits = commits_for_day(repo, day)
            if commits:
                commit = commits[0]
                sha = str(commit.get("sha"))
                entry["commit"] = sha
                entry["commit_time"] = (commit.get("commit") or {}).get("committer", {}).get("date")
                entry.update(verify_commit(repo, sha))
        except Exception as exc:
            entry["error"] = str(exc)
        result["anchors"][day] = entry
    return result


def collector_check(repo: str) -> dict:
    result = {"repo": repo, "rss_endpoint_evidence": False}
    try:
        search = api_json(
            "https://api.github.com/search/code?" + urllib.parse.urlencode({
                "q": f'"trends.google.com/trending/rss" repo:{repo}',
                "per_page": 10,
            })
        )
        items = search.get("items", []) if isinstance(search, dict) else []
        result["rss_endpoint_evidence"] = bool(items)
        result["matches"] = [item.get("path") for item in items[:5] if isinstance(item, dict)]
    except Exception as exc:
        result["error"] = str(exc)
    return result


def render(audits: list[dict], collectors: list[dict]) -> str:
    verified_dates: dict[str, list[str]] = {day: [] for day in ANCHORS}
    for audit in audits:
        for day, entry in audit["anchors"].items():
            if entry.get("complete"):
                verified_dates[day].append(audit["repo"])

    lines = [
        "# Google Trending 2026 gap cross-check",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat(timespec='seconds')}`",
        "",
        "Purpose: cross-check whether public GitHub history preserves genuine Google Trending Now/RSS snapshots during the licensed archive gap `2026-01-04` through `2026-08-31`. This is evidence review, not an import authorization.",
        "",
        "## Historical archive lineage",
        "",
        "| Repository | Fork | Declared SPDX | All Rights Reserved | Jan 04 | Feb 15 | Apr 15 | Jun 16 | Jul 01 | Aug 31 |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for audit in audits:
        meta = audit.get("meta", {})
        rights = audit.get("rights", {})
        cells = []
        for day in ANCHORS:
            entry = audit["anchors"].get(day, {})
            if entry.get("complete"):
                counts = [str(entry.get("regions", {}).get(g, {}).get("items", 0)) for g in REGIONS]
                cells.append("/".join(counts))
            elif entry.get("commit"):
                cells.append("partial")
            elif entry.get("error"):
                cells.append("error")
            else:
                cells.append("—")
        lines.append(
            f"| `{audit['repo']}` | {'yes' if meta.get('fork') else 'no'} | {meta.get('license') or 'none'} | "
            f"{'yes' if rights.get('all_rights_reserved') else 'no/unknown'} | {' | '.join(cells)} |"
        )

    lines.extend([
        "",
        "Cell values are `SG/US/GB/HK` item counts from the first matching commit on that UTC date. A dash means no `data/SG.json` commit was found for that anchor date; it does **not** prove the repository had no data at nearby times.",
        "",
        "## Independent collector cross-check",
        "",
        "| Repository | Google Trending RSS endpoint visible in indexed code |",
        "| --- | --- |",
    ])
    for collector in collectors:
        lines.append(f"| `{collector['repo']}` | {'yes' if collector.get('rss_endpoint_evidence') else 'no/unknown'} |")

    lines.extend(["", "## Evidence by anchor", ""])
    for day in ANCHORS:
        repos = verified_dates[day]
        lines.append(f"- `{day}`: " + (", ".join(f"`{repo}`" for repo in repos) if repos else "no complete four-region GitHub snapshot verified by this audit"))

    earliest = next((day for day in ANCHORS if verified_dates[day]), None)
    latest = next((day for day in reversed(ANCHORS) if verified_dates[day]), None)
    lines.extend([
        "",
        "## Decision",
        "",
        "- The CC-BY-4.0 `aurman/GoogleTrendArchive` daily ZIP remains the only approved bulk historical import source currently recorded by `web-ingest`; its exact daily ordering ends on `2026-01-03`.",
        f"- GitHub history cross-checks verify complete four-region snapshots on selected later dates" + (f" from `{earliest}` through `{latest}` among the tested anchors." if earliest and latest else "."),
        "- These GitHub repositories are the same scraper lineage or mirrors/forks, so they are **supporting evidence, not independent provenance**.",
        "- No tested repository provides a clearly licensed, gap-wide archive that is safe to bulk redistribute into `web-ingest`. Missing days therefore stay missing.",
        "- The previous report wording `throughout the gap` was too strong and is superseded by this report.",
        "",
        "Temporary audit code/workflow should be removed after this report is committed.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    audits = [audit_repo(repo) for repo in ARCHIVE_CANDIDATES]
    collectors = [collector_check(repo) for repo in COLLECTOR_EVIDENCE]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(audits, collectors), encoding="utf-8")
    print(json.dumps({
        "archive_candidates": len(audits),
        "collector_checks": len(collectors),
        "complete_anchor_hits": sum(
            1 for audit in audits for entry in audit["anchors"].values() if entry.get("complete")
        ),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
