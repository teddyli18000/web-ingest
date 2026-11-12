#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from archive_lib import REGIONS, canonical_item, merge_region

BASE_URL = "https://trends.google.com"
HOURS = 24
HL = "en-US"
LOCAL_TZ = ZoneInfo("Asia/Singapore")
HT = "{https://trends.google.com/trending/rss}"
CATEGORY_NAMES = {
    1: "Autos and Vehicles",
    2: "Beauty and Fashion",
    3: "Business and Finance",
    4: "Entertainment",
    5: "Food and Drink",
    6: "Games",
    7: "Health",
    8: "Hobbies and Leisure",
    9: "Jobs and Education",
    10: "Law and Government",
    11: "Other",
    13: "Pets and Animals",
    14: "Politics",
    15: "Science",
    16: "Shopping",
    17: "Sports",
    18: "Technology",
    19: "Travel and Transportation",
    20: "Climate",
}


def _iso_timestamp(value: object) -> str | None:
    if not isinstance(value, list) or not value:
        return None
    timestamp = value[0]
    if not isinstance(timestamp, (int, float)):
        return None
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z")


def _volume_label(value: object) -> str | None:
    if isinstance(value, (int, float)):
        return f"{int(value)}+"
    return None


def _explore_url(query: str, geo: str) -> str:
    return "https://trends.google.com/trends/explore?" + urlencode(
        {"date": "now 1-d", "geo": geo, "q": query}
    )


def parse_trending_html(html: str, geo: str) -> list[dict]:
    marker = "AF_initDataCallback({key: 'ds:0'"
    start = html.find(marker)
    if start < 0:
        raise RuntimeError(f"{geo}: Trending Now page has no ds:0 data block")

    data_start = html.find("data:", start)
    if data_start < 0:
        raise RuntimeError(f"{geo}: Trending Now ds:0 block has no data payload")

    payload, _ = json.JSONDecoder().raw_decode(html[data_start + len("data:"):].lstrip())
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        raise RuntimeError(f"{geo}: Trending Now ds:0 payload has no trend rows")

    items = []
    for row in payload[1]:
        if not isinstance(row, list) or len(row) < 13 or not isinstance(row[0], str):
            raise RuntimeError(f"{geo}: malformed Trending Now row")
        query = row[0]
        normalized_query = row[12] if isinstance(row[12], str) and row[12] else query
        category_ids = row[10] if isinstance(row[10], list) else []
        items.append(
            {
                "query": query,
                "normalized_query": normalized_query,
                "search_volume": row[6] if isinstance(row[6], (int, float)) else None,
                "search_volume_label": _volume_label(row[6]),
                "increase_percentage": row[8],
                "started_at": _iso_timestamp(row[3]),
                "ended_at": _iso_timestamp(row[4]),
                "active": row[4] is None,
                "trend_breakdown": row[9] if isinstance(row[9], list) else [],
                "categories": [
                    {"id": category_id, "name": CATEGORY_NAMES.get(category_id, str(category_id))}
                    for category_id in category_ids
                ],
                "explore_url": _explore_url(normalized_query, geo),
            }
        )

    if not items:
        raise RuntimeError(f"{geo}: Trending Now page returned no trend rows")
    return items


def parse_rss_xml(xml: bytes, geo: str) -> list[dict]:
    items = []
    for entry in ET.fromstring(xml).iter("item"):
        query = (entry.findtext("title") or "").strip()
        traffic = (entry.findtext(HT + "approx_traffic") or "").strip() or None
        pub_date = entry.findtext("pubDate")
        started_at = parsedate_to_datetime(pub_date).isoformat() if pub_date else None
        items.append(
            {
                "query": query,
                "normalized_query": query,
                "search_volume_label": traffic,
                "increase_percentage": None,
                "started_at": started_at,
                "ended_at": None,
                "active": None,
                "trend_breakdown": [
                    title
                    for node in entry.findall(HT + "news_item")
                    if (title := (node.findtext(HT + "news_item_title") or "").strip())
                ],
                "categories": [],
                "explore_url": _explore_url(query, geo),
            }
        )
    return items


def fetch_trending_page(geo: str) -> tuple[str, list[dict]]:
    source_url = BASE_URL + "/trending?" + urlencode({"geo": geo, "hl": HL, "hours": HOURS})
    request = urllib.request.Request(source_url, headers={"Accept": "text/html,*/*"})
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")
    return source_url, parse_trending_html(html, geo)


def fetch_rss(geo: str) -> tuple[str, list[dict]]:
    source_url = BASE_URL + "/trending/rss?" + urlencode({"geo": geo})
    request = urllib.request.Request(
        source_url,
        headers={"Accept": "application/rss+xml,text/xml,*/*"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        xml = response.read()
    items = parse_rss_xml(xml, geo)
    if not items:
        raise RuntimeError(f"{geo}: RSS fallback returned no trend rows")
    return source_url, items


def fetch_region(geo: str) -> dict:
    try:
        source_url, items = fetch_trending_page(geo)
        source = "google_trending_now"
        status = "success"
        collector = "google-trending-page-ds0"
    except (OSError, UnicodeError, ValueError, RuntimeError):
        source_url, items = fetch_rss(geo)
        source = "rss_limited"
        status = "rss_limited"
        collector = "google-trending-rss"

    return {
        "source": source,
        "fetch_status": status,
        "source_url": source_url,
        "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "window_hours": HOURS,
        "sort": "relevance",
        "collector": collector,
        "items": [canonical_item(item, rank) for rank, item in enumerate(items, start=1)],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=f"Capture Google Trends Trending Now for {', '.join(REGIONS)}")
    parser.add_argument("--force", action="store_true", help="explicitly replace an existing same-day region")
    args = parser.parse_args()

    day = datetime.now(LOCAL_TZ).date().isoformat()
    candidates = {geo: fetch_region(geo) for geo in REGIONS}

    changed = False
    for geo in REGIONS:
        path, wrote = merge_region(day, geo, candidates[geo], force=args.force)
        changed = changed or wrote
        print(f"{geo}: {'wrote' if wrote else 'kept'} {path}")
    if not changed:
        print("No snapshot changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
