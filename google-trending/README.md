# Google Trending Now Archive

A daily archive of Google Trends **Trending Now** for **Singapore (SG)** and the **United States (US)**.

The task preserves the changing data that is useful later: **trend order, query, search-volume signal, timing fields, breakdown, categories when available, source provenance, and Google Explore links**. It does not mirror Google pages, images, screenshots, or the large upstream historical ZIP.

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

Primary collector: pinned `google-trends-now@1.1.1`, which reads Google's current Trending Now web-data path. The task requests **SG + US**, past **24 hours**, all categories/statuses, Google's relevance order, and all available rows.

If the primary path fails, Google Trends RSS may be used as a bounded fallback. RSS output is stored explicitly as `rss_limited`; it is not treated as the full Trending Now pool and may later be upgraded by a complete same-day capture.

Source priority is:

1. `google_trending_now` — direct live capture;
2. `googletrendarchive` — historical recovery;
3. `rss_limited` — fallback only.

Lower-priority data never overwrites a higher-priority region snapshot.

### Historical recovery

Historical source: [`aurman/GoogleTrendArchive`](https://huggingface.co/datasets/aurman/GoogleTrendArchive), DOI `10.57967/hf/7531`, CC-BY-4.0.

The wider dataset reports observations from 2024-11-28 through 2026-05-17. For this repository, the canonical backfill uses its public `daily_compressed.zip`; exact SG/US directory snapshots recover **2024-11-28 through 2026-01-03**. No valid SG/US daily snapshot is invented for the later gap.

Initial clean recovery: **373 dates / 739 region snapshots** — SG 368 days, US 371 days. The source ZIP SHA-256 is recorded in `backfill-manifest.json`. The 500MB+ ZIP itself is never committed.

## Schedule

Workflow: `.github/workflows/google-trending.yml`

Daily opportunities: **12:17 and 13:17 Asia/Singapore**. The first successful full capture normally makes the second attempt a no-op. The repository manager guard checks these slots against every other recurring workflow's timeout plus the 15-minute planning buffer.

The workflow also supports manual recovery through `workflow_dispatch`.

## Output

Canonical daily file:

```text
google-trending/data/YYYY/MM/DD/trending.json
```

Each file contains one date and whatever valid SG/US region snapshots exist for that date. Missing upstream fields remain `null` or empty; the archive does not infer exact counts, categories, timestamps, or ranks the source did not preserve.

## Recovery and validation

- `capture.py` fetches both SG and US before writing a new live day, preventing a new half-captured day after a hard failure.
- Same-day reruns are idempotent by source quality.
- RSS may upgrade to full live data; historical data may upgrade to direct live data; neither can downgrade a better source.
- `backfill.py` converts the external daily ZIP and can batch by year.
- The initial historical backfill completed successfully on a clean pre-data branch. Its temporary workflow is removed before merge; reusable conversion code remains.
- `validate_archive.py` checks date/path consistency, regions/sources, contiguous ranks, non-empty queries, and duplicate queries.
- `render_readme.py` rebuilds the dashboard from committed archive files.
- Parser/schema changes are covered by `tests/` and governed by `AGENTS.md`.

## Files

- `AGENTS.md` — task boundaries and durable rules.
- `archive_lib.py` — schema, validation, source priority, merge behavior, and paths.
- `capture.py` — live SG + US collector.
- `backfill.py` — GoogleTrendArchive historical converter.
- `backfill-manifest.json` — historical provenance and coverage.
- `validate_archive.py` — full archive validation.
- `render_readme.py` — README dashboard renderer.
- `tests/` — deterministic tests.
