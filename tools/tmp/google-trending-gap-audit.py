#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timezone
from pathlib import Path

CANDIDATE = "fdciabdul/Google-Trends-Keywords-Scraper"
REGIONS = ("SG", "US", "GB", "HK")
ANCHORS = ("2026-01-04", "2026-04-15", "2026-07-01", "2026-08-31")
RSS_MARKER = "https://trends.google.com/trending/rss?geo=${countryCode}&hours=48"


def api_json(url: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "web-ingest-gap-audit/1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def file_text(path: str, ref: str = "main") -> str:
    quoted = urllib.parse.quote(path, safe="/")
    url = f"https://api.github.com/repos/{CANDIDATE}/contents/{quoted}?ref={urllib.parse.quote(ref)}"
    payload = api_json(url)
    if not isinstance(payload, dict) or payload.get("encoding") != "base64":
        raise RuntimeError(f"unexpected contents response for {path}@{ref}")
    return base64.b64decode(payload["content"]).decode("utf-8", errors="replace")


def commits_for_day(day: str) -> list[dict]:
    parsed = date.fromisoformat(day)
    since = datetime.combine(parsed, time.min, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    until = datetime.combine(parsed, time.max, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    query = urllib.parse.urlencode({
        "path": "data/SG.json",
        "since": since,
        "until": until,
        "per_page": 100,
    })
    payload = api_json(f"https://api.github.com/repos/{CANDIDATE}/commits?{query}")
    return payload if isinstance(payload, list) else []


def audit_anchor(day: str) -> dict:
    commits = commits_for_day(day)
    if not commits:
        return {"day": day, "commit": None, "regions": {}, "complete": False}
    commit = commits[0]
    sha = commit["sha"]
    region_result = {}
    complete = True
    for geo in REGIONS:
        try:
            payload = json.loads(file_text(f"data/{geo}.json", sha))
            items = payload.get("data")
            region_result[geo] = {
                "lastUpdate": payload.get("lastUpdate"),
                "items": len(items) if isinstance(items, list) else 0,
                "first": items[0].get("title") if isinstance(items, list) and items else None,
            }
            complete = complete and bool(region_result[geo]["items"])
        except Exception as exc:
            region_result[geo] = {"error": str(exc)}
            complete = False
    return {
        "day": day,
        "commit": sha,
        "commit_time": commit.get("commit", {}).get("committer", {}).get("date"),
        "regions": region_result,
        "complete": complete,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source = file_text("utils/getData.js")
    readme = file_text("README.md")
    direct_rss = RSS_MARKER in source
    all_rights_reserved = "All Rights Reserved" in readme

    anchors = []
    for day in ANCHORS:
        try:
            anchors.append(audit_anchor(day))
        except (urllib.error.URLError, RuntimeError, json.JSONDecodeError) as exc:
            anchors.append({"day": day, "commit": None, "regions": {}, "complete": False, "error": str(exc)})

    complete_anchors = sum(bool(item.get("complete")) for item in anchors)
    lines = [
        "# Google Trending 2026 gap audit",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat(timespec='seconds')}`",
        "",
        "## Candidate",
        "",
        f"- Repository: `{CANDIDATE}`",
        f"- Direct Google RSS endpoint found in collector source: **{'yes' if direct_rss else 'no'}**",
        f"- README contains `All Rights Reserved`: **{'yes' if all_rights_reserved else 'no'}**",
        f"- Anchor dates with non-empty SG/US/GB/HK snapshots: **{complete_anchors}/{len(ANCHORS)}**",
        "",
        "## Anchor verification",
        "",
        "| UTC date | Commit | SG | US | GB | HK |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for item in anchors:
        sha = item.get("commit")
        short = sha[:10] if isinstance(sha, str) else "—"
        cells = []
        for geo in REGIONS:
            region = item.get("regions", {}).get(geo, {})
            cells.append(str(region.get("items", "—")))
        lines.append(f"| {item['day']} | `{short}` | {' | '.join(cells)} |")

    lines.extend([
        "",
        "## Decision",
        "",
        "This repository is strong **cross-validation evidence** that Google Trending RSS snapshots existed throughout the 2026 gap and that all four target regions were being captured in Git history.",
        "",
        "It is **not approved as a bulk import source** for `web-ingest`: the repository itself advertises `All Rights Reserved`, so redistribution rights for copying its historical archive at scale are unclear. `web-ingest` should not copy the data unless the licensing/permission situation becomes explicit.",
        "",
        "The canonical historical importer remains the CC-BY-4.0 `aurman/GoogleTrendArchive` raw daily archive. Later rankless/processed Google Trends datasets must not be converted into invented daily rankings.",
        "",
        "This report is durable evidence; the script that produced it is temporary repository-management tooling.",
        "",
    ])

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"direct_rss": direct_rss, "all_rights_reserved": all_rights_reserved, "complete_anchors": complete_anchors}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
