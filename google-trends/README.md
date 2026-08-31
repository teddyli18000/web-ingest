# Google Trends — Trending Now Archive

A compact historical archive of **Google Trends → Trending Now** for a fixed set of regions.

Trending Now is intentionally ephemeral: Google lets you inspect trends that started in the past **4 hours, 24 hours, 48 hours, or 7 days**, and refreshes the view frequently. That makes a daily snapshot useful later: it preserves what was suddenly capturing attention at that moment instead of trying to reconstruct it from keyword searches after the fact.

This task stores text/metadata only. It does **not** mirror images, screenshots, article bodies, or Google pages.

<!-- archive-dashboard:start -->

_No archived snapshots yet._

<!-- archive-dashboard:end -->

## Core regions

The long-term archive intentionally uses a compact, stable set rather than crawling every available Google region:

| Code | Region | Why it is in the core set |
| --- | --- | --- |
| SG | Singapore | local context |
| US | United States | major global English/news/technology signal |
| GB | United Kingdom | English-language European signal |
| IN | India | large South Asian web/search market |
| JP | Japan | major East Asian search market |
| KR | South Korea | major East Asian search market |
| HK | Hong Kong | Chinese-language Google-heavy market |
| TW | Taiwan | Chinese-language Google-heavy market |

The canonical set lives in `config.json`. New regions can be added later without changing schema v1.

## Live source

Daily collection uses Google's official Trending Now RSS export:

```text
https://trends.google.com/trending/rss?geo=<CC>
```

Google documents RSS as an export option for Trending Now. The RSS path is deliberately preferred over browser automation because it is public, keyless, small, and much less brittle.

RSS preserves ranking/order, trend title, approximate search-volume bucket, feed timestamp, and related news metadata when Google includes it. Fields unavailable in RSS are left absent rather than guessed.

## Schedule

Workflow: `.github/workflows/google-trends.yml`

The collector gets three daily opportunities at **12:07, 13:07, and 14:07 Asia/Singapore**. It runs after the AI Daily and GitHub Trending morning windows, and the repository schedule guard verifies that recurring workflows do not overlap another workflow's reserved timeout window.

A date is written only when **all eight core regions** were fetched successfully. A later retry is a no-op once a complete valid file exists.

## Output

```text
google-trends/data/YYYY/MM/DD/trending.json
```

Schema v1 keeps one daily file with one snapshot per region:

```json
{
  "schema_version": 1,
  "date": "2026-09-01",
  "captured_at": "2026-09-01T12:07:12+08:00",
  "period_hours": 24,
  "coverage": "core-geos",
  "snapshots": [
    {
      "geo": "SG",
      "geo_name": "Singapore",
      "source": "https://trends.google.com/trending/rss?geo=SG",
      "source_kind": "google_rss",
      "items": [
        {
          "rank": 1,
          "query": "example trend",
          "search_volume": 10000,
          "search_volume_label": "10K+",
          "published_at": "...",
          "news": []
        }
      ]
    }
  ]
}
```

## Historical recovery

`backfill.py` converts the public **GoogleTrendArchive** raw daily export archive into the same schema for the eight core regions.

The source archive was collected from Google's Trending Now UI by Aleksandra Urman, Anikó Hannák, and Joachim Baumann and is published as `aurman/GoogleTrendArchive` under **CC-BY-4.0**. Its collection begins on **2024-11-28**. The upstream dataset is large, so this repository does not copy it wholesale: the one-time importer reads `daily_compressed.zip` directly and retains only the configured core-region daily CSVs.

Historical rows can be richer than RSS. When the source preserved them, records may also include `started_raw`, `ended_raw`, `trend_breakdown`, and `explore_url`. Raw timestamp strings are preserved rather than reinterpreted with guessed timezone semantics.

If multiple upstream CSVs exist for the same `date + geo`, the importer selects the candidate with the most usable rows, with a deterministic path tie-break. Existing direct Google snapshots always win on overlap. Exact source archive SHA-256, coverage, gaps, and importer statistics are recorded in `backfill-manifest.json`.

A missing historical date remains missing. We do not manufacture rankings from keyword-interest data, BigQuery time series, or unrelated Google Trends products.

## Validation and maintenance

- Re-running a complete live date is a no-op.
- Historical files are not silently overwritten by later third-party backfills.
- Trend ranks must be contiguous and queries non-empty.
- A partial live day is not committed: all configured core regions must succeed.
- Images and page screenshots are deliberately excluded.
- Task code uses Python's standard library only.
- Repository-wide scheduling and CI policy live under `tools/` and `.github/workflows/`.

## Files

- `config.json` — canonical regions and collection window.
- `archive_lib.py` — schema, RSS/CSV parsing, validation, merge helpers.
- `capture.py` — daily official-RSS collector.
- `backfill.py` — one-time GoogleTrendArchive raw ZIP importer.
- `render_readme.py` — rebuilds the dashboard from stored files.
- `tests/` — deterministic parser/schema/backfill tests.
