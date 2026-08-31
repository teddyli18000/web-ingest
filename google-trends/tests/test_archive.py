import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archive_lib import day_path, merge_day, parse_historical_csv, parse_rss, parse_volume, validate_day
from backfill import member_date, member_geo


class GoogleTrendsArchiveTests(unittest.TestCase):
    def test_parse_volume(self):
        self.assertEqual(parse_volume("10K+"), 10000)
        self.assertEqual(parse_volume("2.5M+"), 2500000)
        self.assertEqual(parse_volume("500+"), 500)
        self.assertIsNone(parse_volume(""))

    def test_parse_rss(self):
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <rss xmlns:ht="https://trends.google.com/trending/rss"><channel>
          <item>
            <title>spurs vs newcastle</title>
            <ht:approx_traffic>5K+</ht:approx_traffic>
            <pubDate>Mon, 31 Aug 2026 23:00:00 -0700</pubDate>
            <ht:news_item><ht:news_item_title>Match report</ht:news_item_title><ht:news_item_url>https://example.com/a</ht:news_item_url><ht:news_item_source>Example</ht:news_item_source></ht:news_item>
          </item>
          <item><title>cyclist</title><ht:approx_traffic>10K+</ht:approx_traffic></item>
        </channel></rss>'''
        items = parse_rss(xml)
        self.assertEqual(items[0]["rank"], 1)
        self.assertEqual(items[0]["query"], "spurs vs newcastle")
        self.assertEqual(items[0]["search_volume"], 5000)
        self.assertEqual(items[0]["news"][0]["source"], "Example")
        self.assertEqual(items[1]["rank"], 2)

    def test_parse_historical_csv(self):
        text = 'Trends,Search volume,Started,Ended,Trend breakdown,Explore link\n"foo bar",50K+,"Aug 1, 2025","Aug 2, 2025","foo, bar",https://trends.google.com/x\n'
        items = parse_historical_csv(text)
        self.assertEqual(items[0]["query"], "foo bar")
        self.assertEqual(items[0]["search_volume"], 50000)
        self.assertEqual(items[0]["trend_breakdown"], ["foo", "bar"])

    def test_member_detection(self):
        selected = {"US", "SG"}
        name = "data/SG/trending_searches_1d_20250102.csv"
        self.assertEqual(member_geo(name, selected), "SG")
        self.assertEqual(member_date(name), "2025-01-02")

    def test_merge_preserves_direct_existing(self):
        existing = {"schema_version": 1, "date": "2026-01-01", "snapshots": [{"geo": "SG", "source": "google", "items": [{"rank": 1, "query": "live"}]}]}
        incoming = {"schema_version": 1, "date": "2026-01-01", "snapshots": [
            {"geo": "SG", "source": "archive", "items": [{"rank": 1, "query": "old"}]},
            {"geo": "US", "source": "archive", "items": [{"rank": 1, "query": "us"}]},
        ]}
        merged = merge_day(existing, incoming)
        by_geo = {x["geo"]: x for x in merged["snapshots"]}
        self.assertEqual(by_geo["SG"]["items"][0]["query"], "live")
        self.assertEqual(by_geo["US"]["items"][0]["query"], "us")

    def test_path_and_validation(self):
        path = day_path(Path("google-trends"), "2026-09-01")
        self.assertEqual(path.as_posix(), "google-trends/data/2026/09/01/trending.json")
        validate_day({"schema_version": 1, "date": "2026-09-01", "snapshots": [{"geo": "SG", "items": [{"rank": 1, "query": "x"}]}]})


if __name__ == "__main__":
    unittest.main()
