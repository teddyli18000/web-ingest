from __future__ import annotations

import csv
import io
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VOLUME_RE = re.compile(r"^\s*([\d,.]+)\s*([KMB]?)\s*\+?\s*$", re.I)


def load_config(root: Path) -> dict[str, Any]:
    data = json.loads((root / "config.json").read_text(encoding="utf-8"))
    geos = data.get("geos")
    if not isinstance(geos, list) or not geos:
        raise ValueError("config.geos must be a non-empty list")
    seen: set[str] = set()
    for geo in geos:
        code = str(geo.get("code", "")).upper()
        if not re.fullmatch(r"[A-Z]{2}", code):
            raise ValueError(f"invalid geo code: {code!r}")
        if code in seen:
            raise ValueError(f"duplicate geo code: {code}")
        seen.add(code)
        geo["code"] = code
    return data


def parse_volume(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = VOLUME_RE.fullmatch(text.replace(" ", ""))
    if not match:
        return None
    number = float(match.group(1).replace(",", ""))
    factor = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[match.group(2).upper()]
    return int(number * factor)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].split(":")[-1]


def child_text(element: ET.Element, name: str) -> str | None:
    for child in element:
        if local_name(child.tag) == name:
            text = " ".join((child.text or "").split())
            return text or None
    return None


def nested_text(element: ET.Element, name: str) -> str | None:
    for child in element.iter():
        if local_name(child.tag) == name:
            text = " ".join((child.text or "").split())
            return text or None
    return None


def parse_rss(xml_text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    items: list[dict[str, Any]] = []
    for item in root.iter():
        if local_name(item.tag) != "item":
            continue
        query = child_text(item, "title")
        if not query:
            continue
        volume_label = nested_text(item, "approx_traffic")
        pub_date = child_text(item, "pubDate")
        news: list[dict[str, str]] = []
        for node in item.iter():
            if local_name(node.tag) != "news_item":
                continue
            title = nested_text(node, "news_item_title")
            url = nested_text(node, "news_item_url")
            source = nested_text(node, "news_item_source")
            record = {k: v for k, v in {"title": title, "url": url, "source": source}.items() if v}
            if record and record not in news:
                news.append(record)
        items.append(
            {
                "rank": len(items) + 1,
                "query": query,
                "search_volume": parse_volume(volume_label),
                "search_volume_label": volume_label,
                "published_at": pub_date,
                "news": news,
            }
        )
    if not items:
        raise ValueError("Google Trends RSS contained no trend items")
    return items


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def parse_historical_csv(text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("historical CSV has no header")
    rows: list[dict[str, Any]] = []
    for raw in reader:
        row = {normalize_header(str(k)): (v or "").strip() for k, v in raw.items() if k is not None}
        query = row.get("trends") or row.get("trend") or row.get("query") or ""
        if not query:
            continue
        volume_label = row.get("search_volume") or row.get("approx_traffic") or ""
        breakdown = row.get("trend_breakdown") or ""
        related = [piece.strip() for piece in breakdown.split(",") if piece.strip()]
        record: dict[str, Any] = {
            "rank": len(rows) + 1,
            "query": query,
            "search_volume": parse_volume(volume_label),
            "search_volume_label": volume_label or None,
            "started_raw": row.get("started") or None,
            "ended_raw": row.get("ended") or None,
            "trend_breakdown": related,
            "explore_url": row.get("explore_link") or row.get("explore_url") or None,
        }
        rows.append(record)
    if not rows:
        raise ValueError("historical CSV contained no usable trend rows")
    return rows


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    geo = snapshot.get("geo")
    items = snapshot.get("items")
    if not isinstance(geo, str) or not re.fullmatch(r"[A-Z]{2}", geo):
        raise ValueError(f"invalid geo: {geo!r}")
    if not isinstance(items, list) or not items:
        raise ValueError(f"snapshot {geo} has no items")
    for expected, item in enumerate(items, start=1):
        if item.get("rank") != expected:
            raise ValueError(f"snapshot {geo} has non-contiguous ranks")
        if not isinstance(item.get("query"), str) or not item["query"].strip():
            raise ValueError(f"snapshot {geo} has empty query")


def validate_day(day: dict[str, Any]) -> None:
    if day.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    date = day.get("date")
    if not isinstance(date, str) or not DATE_RE.fullmatch(date):
        raise ValueError(f"invalid date: {date!r}")
    snapshots = day.get("snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        raise ValueError(f"{date}: no snapshots")
    seen: set[str] = set()
    for snapshot in snapshots:
        validate_snapshot(snapshot)
        geo = snapshot["geo"]
        if geo in seen:
            raise ValueError(f"{date}: duplicate geo {geo}")
        seen.add(geo)


def day_path(root: Path, date: str) -> Path:
    return root / "data" / date[:4] / date[5:7] / date[8:10] / "trending.json"


def read_day(path: Path) -> dict[str, Any]:
    day = json.loads(path.read_text(encoding="utf-8"))
    validate_day(day)
    return day


def write_day(root: Path, day: dict[str, Any]) -> Path:
    validate_day(day)
    path = day_path(root, day["date"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(day, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def merge_day(existing: dict[str, Any] | None, incoming: dict[str, Any], *, prefer_existing: bool = True) -> dict[str, Any]:
    if existing is None:
        validate_day(incoming)
        return incoming
    if existing.get("date") != incoming.get("date"):
        raise ValueError("cannot merge different dates")
    by_geo = {snapshot["geo"]: snapshot for snapshot in existing["snapshots"]}
    for snapshot in incoming["snapshots"]:
        if snapshot["geo"] not in by_geo or not prefer_existing:
            by_geo[snapshot["geo"]] = snapshot
    merged = dict(existing)
    merged["snapshots"] = sorted(by_geo.values(), key=lambda item: item["geo"])
    validate_day(merged)
    return merged
