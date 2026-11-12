# Google Trending Now Archive

A daily archive of Google Trends **Trending Now** for **Singapore (SG)**, the **United States (US)**, the **United Kingdom (GB)**, and **Hong Kong (HK)**.

The task preserves changing data useful later: **source order, query, search-volume signal, timing/breakdown/categories when the source actually provides them, source provenance, and Explore links when available**. It does not mirror pages, images, screenshots, or whole upstream repositories.

<!-- archive-dashboard:start -->

### Archive at a glance

| First day | Latest day | Days archived | SG days | US days | GB days | HK days |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **2024-11-28** | **2026-11-12** | **692** | **692** | **692** | **692** | **691** |

### Source mix

| Source | Region snapshots |
| --- | ---: |
| `googletrendarchive` | 1,479 |
| `github_rss_mirror` | 1,081 |
| `google_trending_now` | 204 |
| `github_hottrends_mirror` | 3 |

### Latest SG snapshot — 2026-11-12

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | kimberly powell | 20000+ |
| 2 | nvidia singapore sales reporting change | 5000+ |
| 3 | tony leung ka-fai | 2000+ |
| 4 | wok hey staff customer confrontation | 2000+ |
| 5 | prabowo subianto | 1000+ |
| 6 | alice huang singapore entry ban | 200+ |
| 7 | amd stock | 1000+ |
| 8 | 黄仁勋 | 200+ |
| 9 | singapore airlines fy2027 interim dividend | 500+ |
| 10 | dbs paylah china qr expansion | 2000+ |

### Latest US snapshot — 2026-11-12

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | kimberly powell | 500000+ |
| 2 | building collapse nyc | 500000+ |
| 3 | anthony clark | 200000+ |
| 4 | snow | 200000+ |
| 5 | dc shooting | 100000+ |
| 6 | disco singer rochelle fleming passes | 100000+ |
| 7 | warriors vs rockets | 200000+ |
| 8 | usman nurmagomedov | 200000+ |
| 9 | mark mcguinn | 50000+ |
| 10 | rex ryan | 100000+ |

### Latest GB snapshot — 2026-11-12

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | colette kress | 50000+ |
| 2 | usman nurmagomedov | 20000+ |
| 3 | polar vortex el niño winter weather | 10000+ |
| 4 | new york | 20000+ |
| 5 | body mass index misclassification uk | 10000+ |
| 6 | edinburgh bypass | 10000+ |
| 7 | winter storm | 10000+ |
| 8 | metro bank | 5000+ |
| 9 | washington dc | 5000+ |
| 10 | maldives | 10000+ |

### Latest HK snapshot — 2026-11-12

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | kimberly powell | 10000+ |
| 2 | 吳嘉儀 | 2000+ |
| 3 | 黃仁勳辭職 | 2000+ |
| 4 | 收入 中 位 數 | 1000+ |
| 5 | 明天的天氣 | 10000+ |
| 6 | bigbang | 2000+ |
| 7 | 英伟达 | 500+ |
| 8 | 肥媽 | 2000+ |
| 9 | cuaca besok | 1000+ |
| 10 | 鍾麗淇 | 200+ |

[Open full snapshot →](data/2026/11/12/trending.json)

### Browse by year

[`2026`](data/2026/) · 294 days · [`2025`](data/2025/) · 364 days · [`2024`](data/2024/) · 34 days

<!-- archive-dashboard:end -->

## Sources and priority

1. `google_trending_now` — direct live capture from the server-rendered Google Trending Now page (`ds:0`); highest quality.
2. `googletrendarchive` — CC-BY-4.0 historical daily recovery.
3. `github_rss_mirror` — historical Google Trending RSS snapshots mirrored from `fdciabdul/Google-Trends-Keywords-Scraper` only where a canonical region/date is missing. Exact commit/file provenance and the upstream **All Rights Reserved** notice are stored in every mirrored region.
4. `github_hottrends_mirror` — legacy Google Hot Trends Atom snapshots recovered from exact Git commits when the modern mirror has a hole; provenance includes the historical `pn` endpoint, commit and file path.
5. `rss_limited` — live fallback only.

The three historical sources have equal merge quality: they fill holes but never replace one another. Direct live data can upgrade any historical source.

### Historical recovery

The licensed `aurman/GoogleTrendArchive` daily ZIP covers recoverable configured-region snapshots from **2024-11-28 through 2026-01-03** with gaps recorded in `backfill-manifest.json`.

The GitHub RSS mirror is used to fill missing region snapshots without cloning the upstream repository. A one-shot manager tool selects the upstream commit closest to **12:30 Asia/Singapore** for each missing archive date, copies source JSON order, preserves the exact commit/file/RSS endpoint, and records results in `mirror-manifest.json`. For the isolated **2025-02-05** SG/US/GB hole, a second Git-history source preserved Google's predecessor Hot Trends Atom feed; those snapshots are kept separately as `github_hottrends_mirror` rather than being relabeled as modern RSS. Mirror imports never invent fields absent from their source.

## Schedule

Workflow: `.github/workflows/google-trending.yml`

Daily opportunities: **12:37 and 13:49 Asia/Singapore**. The first successful full capture normally makes the second attempt a no-op. The repository manager guard checks these slots against every other recurring workflow's timeout plus the 15-minute planning buffer.

Collection runs only from scheduled/manual workflow execution. Code changes are validated by repository-integrity CI instead of triggering collection.

## Output

Canonical daily file:

```text
google-trending/data/YYYY/MM/DD/trending.json
```

Each file contains one date and valid snapshots for the canonical regions. Missing upstream fields remain `null` or empty.

## Recovery and validation

- `capture.py` fetches the server-rendered `/trending` page for all four regions and reads its inline `ds:0` dataset before writing a newly-created live day. RSS is used only when the full page dataset is unavailable.
- Same-day reruns are idempotent by source quality.
- `backfill.py` converts the licensed GoogleTrendArchive ZIP.
- `mirror-manifest.json` records the GitHub mirror selection/import result after the one-shot backfill.
- `validate_archive.py` checks date/path consistency, supported regions/sources, contiguous ranks, non-empty queries, and duplicate queries.
- `render_readme.py` rebuilds this dashboard from committed data.
- Temporary research/backfill mechanisms live under `tools/` and self-remove after successful validation; durable reports/manifests remain.

## Files

- `AGENTS.md` — task boundaries and durable rules.
- `archive_lib.py` — schema, canonical regions, validation, source priority, merge behavior, and paths.
- `capture.py` — live four-region collector using Google’s server-rendered Trending Now dataset with RSS fallback.
- `backfill.py` / `backfill-manifest.json` — licensed historical recovery.
- `mirror-manifest.json` — GitHub RSS mirror provenance/coverage after the one-shot import.
- `validate_archive.py` — full archive validation.
- `render_readme.py` — README dashboard renderer.
- `tests/` — deterministic tests.
