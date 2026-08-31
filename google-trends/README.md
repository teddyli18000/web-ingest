# Google Trends — Trending Now Archive

A compact historical archive of **Google Trends → Trending Now** for Singapore and the United States.

Trending Now is intentionally ephemeral: Google exposes short rolling windows and refreshes them frequently. A daily snapshot preserves what was suddenly capturing attention at that moment instead of trying to reconstruct a vanished ranking later.

This task stores text/metadata only. It does **not** mirror images, screenshots, article bodies, or Google pages.

<!-- archive-dashboard:start -->

### Archive at a glance

| First archived day | Latest day | Days with data | Core regions |
| --- | --- | ---: | ---: |
| **2024-11-28** | **2026-09-01** | **374** | **2** |

### Latest regional pulse — 2026-09-01

| Region | #1 trend | Volume | Top 3 |
| --- | --- | ---: | --- |
| 🇸🇬 Singapore | **barcelona vs rayo vallecano** | 200+ | barcelona vs rayo vallecano · aston villa vs arsenal · lecce vs roma |
| 🇺🇸 United States | **crime** | 500+ | crime · barca · barcelona schedule |

[Open full 2026-09-01 snapshot →](data/2026/09/01/trending.json)

### Browse by year

[`2026`](data/2026/) · 4 days  [`2025`](data/2025/) · 336 days  [`2024`](data/2024/) · 34 days

<!-- archive-dashboard:end -->
## Core regions

The long-term contract is intentionally small and stable:

| Code | Region | Role |
| --- | --- | --- |
| SG | Singapore | local daily context |
| US | United States | broad English-language / global technology and news reference |

The canonical set lives in `config.json`. Do not silently expand it. If the scope ever changes, historical files and documentation must be migrated deliberately rather than leaving mixed-region output behind.

## Live source

Daily collection uses Google's public Trending Now RSS export:

```text
https://trends.google.com/trending/rss?geo=<CC>
```

RSS is preferred over browser automation because it is public, keyless, compact, and less brittle. It preserves ranking/order, trend title, approximate search-volume bucket, feed timestamp, and related news metadata when Google includes them. Fields unavailable in RSS stay absent rather than being guessed.

## Schedule

Workflow: `.github/workflows/google-trends.yml`

The collector gets three daily opportunities at **12:07, 13:07, and 14:07 Asia/Singapore**. It runs after the AI Daily and GitHub Trending morning windows. Repository-wide schedule validation reserves each workflow's declared timeout plus a 15-minute buffer, so recurring jobs do not pile up on one runner window.

A date is written only when **both SG and US** are fetched successfully. Once a complete valid file exists, later same-day retry slots exit without rewriting it.

The workflow can also be run manually.

## Output

```text
google-trends/data/YYYY/MM/DD/trending.json
```

Schema v1 keeps one daily file with one snapshot per available configured region:

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

`backfill.py` converts the public **GoogleTrendArchive** raw daily export into the same schema, but only for the configured SG/US scope.

The source archive was collected from Google's Trending Now UI by Aleksandra Urman, Anikó Hannák, and Joachim Baumann and is published as `aurman/GoogleTrendArchive` under **CC-BY-4.0**. Its collection begins on **2024-11-28**. The upstream archive is large, so this repository retains only normalized SG/US daily snapshots, not the original bulk ZIP.

The initial recovery was performed on 2026-09-01. `backfill-manifest.json` records the exact source archive SHA-256, SG/US historical coverage, source gaps, and import provenance after scope normalization.

There is a known exact-ranking gap from **2026-01-04 through 2026-08-31**. A source search found no reliable public archive preserving those missing daily Trending Now rankings, so direct collection resumes with 2026-09-01 rather than synthesizing the gap from a different Google Trends product.

Historical rows can be richer than RSS. When the source preserved them, records may also include `started_raw`, `ended_raw`, `trend_breakdown`, and `explore_url`. Raw timestamp strings are preserved rather than reinterpreted with guessed timezone semantics.

If multiple upstream CSVs exist for the same `date + geo`, the importer selects the candidate with the most usable rows, with a deterministic path tie-break. Existing direct Google snapshots always win on overlap. A missing historical date remains missing; rankings are never manufactured from keyword-interest time series or unrelated Google Trends products.

## Validation and maintenance

- Re-running a complete live date is a no-op.
- Historical files are not silently overwritten by later third-party backfills.
- Trend ranks must be contiguous and queries non-empty.
- A partial live day is not committed: SG and US must both succeed.
- `validate_archive.py` checks every stored file against the configured region set and path/date schema.
- `prune_to_config.py` is the task-local repair tool for deliberately shrinking the configured region set without mutating surviving source rows.
- Images and page screenshots are deliberately excluded.
- Task code uses Python's standard library only.
- Repository-wide scheduling and CI policy live under `tools/` and `.github/workflows/`.

## Files

- `config.json` — canonical SG/US region set and collection window.
- `archive_lib.py` — schema, RSS/CSV parsing, validation, merge helpers.
- `capture.py` — daily RSS collector.
- `backfill.py` — GoogleTrendArchive raw ZIP importer.
- `prune_to_config.py` — config-driven historical scope repair.
- `validate_archive.py` — full archive validator.
- `render_readme.py` — rebuilds the dashboard from stored files.
- `tests/` — deterministic parser/schema/backfill tests.
