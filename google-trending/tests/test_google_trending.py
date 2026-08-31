from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archive_lib import canonical_item, new_document, validate_document
from backfill import member_date, member_geo, parse_csv


class GoogleTrendingTests(unittest.TestCase):
    def test_live_item_is_normalized(self):
        item = canonical_item({
            "query": "Example",
            "search_volume": 50000,
            "search_volume_label": "50K+",
            "trend_breakdown": ["example", "example news"],
        }, 1)
        self.assertEqual(item["rank"], 1)
        self.assertEqual(item["query"], "Example")
        self.assertEqual(item["search_volume"], 50000)
        self.assertEqual(item["trend_breakdown"], ["example", "example news"])

    def test_document_validation_requires_contiguous_unique_queries(self):
        payload = new_document("2026-09-01")
        payload["regions"]["SG"] = {
            "source": "google_trending_now",
            "items": [canonical_item({"query": "A"}, 1), canonical_item({"query": "B"}, 2)],
        }
        self.assertEqual(validate_document(payload, "2026-09-01"), [])
        payload["regions"]["SG"]["items"][1]["query"] = "A"
        self.assertTrue(any("duplicate query" in error for error in validate_document(payload, "2026-09-01")))

    def test_historical_csv_aliases(self):
        raw = (
            "Trends,Search volume,Started,Ended,Trend breakdown,Explore link\n"
            'hello world,20K+,2 hours ago,,"hello, world",https://example.test\n'
        ).encode()
        rows = parse_csv(raw)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["query"], "hello world")
        self.assertEqual(rows[0]["search_volume"], 20000)
        self.assertEqual(rows[0]["trend_breakdown"], ["hello", "world"])

    def test_member_detection(self):
        name = "archive/SG/google_trends_1d_20250102.csv"
        self.assertEqual(member_geo(name), "SG")
        self.assertEqual(member_date(name), "2025-01-02")


if __name__ == "__main__":
    unittest.main()
