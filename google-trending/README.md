# Google Trending Now Archive

A daily archive of Google Trends **Trending Now** for **Singapore (SG)** and the **United States (US)**.

The goal is not to mirror Google pages or media. The task preserves the historically useful changing data: **trend order, query, search-volume signal, timing fields, breakdown, categories when available, source provenance, and Google Explore links**.

- **SG** is the local signal.
- **US** is a larger English-language / global-Internet reference signal.
- Images, screenshots, HTML pages, and the upstream 500MB+ historical ZIP are not committed.

<!-- archive-dashboard:start -->

### Archive at a glance

| First day | Latest day | Days archived | SG days | US days |
| --- | --- | ---: | ---: | ---: |
| **2024-11-28** | **2026-01-03** | **373** | **368** | **371** |

### Source mix

| Source | Region snapshots |
| --- | ---: |
| `googletrendarchive` | 739 |

### Latest SG snapshot — 2026-01-03

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | venezuela | 2K+ |
| 2 | venezuela news | 1K+ |
| 3 | cdc vouchers singapore | 500+ |
| 4 | fan bingbing | 200+ |
| 5 | melbourne city fc vs sydney fc | 100+ |
| 6 | lakers vs grizzlies | 1K+ |
| 7 | bbc | 100+ |
| 8 | warriors vs thunder | 500+ |
| 9 | al-ahli saudi vs al-nassr | 2K+ |
| 10 | toto singapore | 2K+ |

### Latest US snapshot — 2026-01-03

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | venezuela | 500K+ |
| 2 | grizzlies vs lakers | 100K+ |
| 3 | thunder vs warriors | 100K+ |
| 4 | celina powell | 20K+ |
| 5 | akay diamonds | 20K+ |
| 6 | wake forest vs ms state | 100K+ |
| 7 | hawks vs knicks | 50K+ |
| 8 | nuggets vs cavaliers | 50K+ |
| 9 | navy vs cincinnati | 200K+ |
| 10 | spurs vs pacers | 50K+ |

[Open full snapshot →](data/2026/01/03/trending.json)

### Browse by year

[`2026`](data/2026/) · 3 days · [`2025`](data/2025/) · 336 days · [`2024`](data/2024/) · 34 days

<!-- archive-dashboard:end -->

## Sources

### Live collection

Primary collector: `google-trends-now@1.1.1`, an unofficial client for Google's current Trending Now web-data path.

The task requests:

- region: `SG` and `US`;
- window: past **24 hours**;
- category: all;
- trend status: all;
- order: Google's Trending Now relevance order;
- limit: all available rows.

If the primary Trending Now request fails, the collector may use Google Trends RSS as a bounded fallback. RSS output is explicitly stored as `rss_limited`; it never masquerades as the full Trending Now pool and can later be upgraded by a full same-day capture.

### Historical recovery

Historical source: [`aurman/GoogleTrendArchive`](https://huggingface.co/datasets/aurman/GoogleTrendArchive), DOI `10.57967/hf/7531`, CC-BY-4.0.

The dataset preserves Google Trending Now observations beginning **2024-11-28** and currently extends through **2026-05-17**. The backfill imports only SG / US **1-day** CSV material and converts it into this task's schema. The large upstream archive remains external.

Historical source data and current live captures are not treated as identical-quality observations. Source priority is:

1. `google_trending_now` — direct live capture;
2. `googletrendarchive` — historical recovery;
3. `rss_limited` — fallback only.

A lower-priority source never overwrites a higher-priority region snapshot.

## Schedule

Workflow: `.github/workflows/google-trending.yml`

The workflow gets two daily opportunities at **12:17 and 13:17 Singapore/Beijing time**. The first successful full capture normally makes the second run a no-op. Multiple slots protect against transient Google/network failure without crowding the existing morning collectors.

The repository-wide schedule guard (`python tools/check-repository-integrity.py --show`) validates this timing against every other recurring workflow's declared timeout plus the repository's 15-minute planning buffer.

The workflow can also be run manually.

## Output

Canonical daily file:

```text
google-trending/data/YYYY/MM/DD/trending.json
```

Schema v1 shape:

```json
{
  "schema_version": 1,
  "date": "2026-09-01",
  "kind": "google-trends-trending-now-daily",
  "regions": {
    "SG": {
      "source": "google_trending_now",
      "fetch_status": "success",
      "source_url": "https://trends.google.com/trending?...",
      "captured_at": "2026-09-01T04:17:00.000Z",
      "window_hours": 24,
      "items": [
        {
          "rank": 1,
          "query": "example",
          "search_volume": 50000,
          "search_volume_label": "50K+",
          "increase_percentage": 200,
          "started_at": "...",
          "ended_at": null,
          "active": true,
          "trend_breakdown": [],
          "categories": [],
          "explore_url": "..."
        }
      ]
    },
    "US": { "...": "..." }
  }
}
```

Missing upstream fields remain `null` or empty. The archive does not infer categories, timestamps, volumes, or rankings that the source did not preserve.

## Historical backfill and recovery

`backfill.py` converts the external GoogleTrendArchive ZIP and supports `--year` so large imports can be committed by natural year boundaries. It is safe to rerun: existing equal/higher-quality region snapshots remain unchanged.

The initial backfill is executed by a temporary, non-scheduled workflow on the implementation branch. After the recovered output is validated and merged, that temporary workflow is removed. Reusable historical conversion logic stays here for future repair.

## Validation and reruns

- `capture.py` fetches **both regions before writing either**, so a hard failure cannot leave a new half-captured day.
- A same-day valid direct capture is append-only by default; later scheduled attempts exit without rewriting it.
- RSS can be upgraded to a full live capture automatically.
- Historical data can be upgraded by a direct capture for the same date, but cannot downgrade live data.
- `--force` exists only for explicit same-day repair and should not be used casually.
- `validate_archive.py` checks date/path consistency, supported regions/sources, contiguous ranks, non-empty queries, and duplicate queries.
- `render_readme.py` rebuilds the dashboard from committed archive files.

## Files

- `archive_lib.py` — schema, validation, source priority, merge behavior, and paths.
- `capture.py` — live SG + US collector.
- `backfill.py` — GoogleTrendArchive historical converter.
- `validate_archive.py` — full archive validation.
- `render_readme.py` — README dashboard renderer.
- `tests/` — deterministic schema and historical-parser tests.
