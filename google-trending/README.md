# Google Trending Now Archive

A daily archive of Google Trends **Trending Now** for **Singapore (SG)**, the **United States (US)**, the **United Kingdom (GB)**, and **Hong Kong (HK)**.

The task preserves changing data useful later: **source order, query, search-volume signal, timing/breakdown/categories when the source actually provides them, source provenance, and Explore links when available**. It does not mirror pages, images, screenshots, or whole upstream repositories.

<!-- archive-dashboard:start -->

### Archive at a glance

| First day | Latest day | Days archived | SG days | US days | GB days | HK days |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **2024-11-28** | **2026-09-14** | **650** | **650** | **650** | **650** | **649** |

### Source mix

| Source | Region snapshots |
| --- | ---: |
| `googletrendarchive` | 1,479 |
| `github_rss_mirror` | 1,081 |
| `google_trending_now` | 36 |
| `github_hottrends_mirror` | 3 |

### Latest SG snapshot — 2026-09-14

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | psi singapore now | 50000+ |
| 2 | bangladesh | 2000+ |
| 3 | hyrox | 2000+ |
| 4 | foresque residences balcony concrete lawsuit | 1000+ |
| 5 | taiwan | 1000+ |
| 6 | jamil khir baharom | 500+ |
| 7 | suahasil nazara | 1000+ |
| 8 | singapore telecommunications limited | 500+ |
| 9 | hawker centre | 200+ |
| 10 | man utd vs man city | 20000+ |

### Latest US snapshot — 2026-09-14

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | cowboys | 2000000+ |
| 2 | commanders vs eagles | 1000000+ |
| 3 | packers vs vikings | 1000000+ |
| 4 | bloodhound q50 | 500000+ |
| 5 | nfl scores | 1000000+ |
| 6 | bears vs panthers | 1000000+ |
| 7 | saints vs lions | 1000000+ |
| 8 | dolphins vs raiders | 500000+ |
| 9 | kyler murray | 200000+ |
| 10 | falcons vs steelers | 500000+ |

### Latest GB snapshot — 2026-09-14

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | sydney sweeney ad | 20000+ |
| 2 | prince george eton college boarding | 20000+ |
| 3 | manchester united f.c. vs man city standings | 200000+ |
| 4 | boris johnson | 20000+ |
| 5 | martin brundle | 10000+ |
| 6 | sweden elections | 10000+ |
| 7 | brest vs psg | 20000+ |
| 8 | ludek miklosko | 5000+ |
| 9 | diogo jota | 10000+ |
| 10 | what did meghan share in her video of the family's uk return | 20000+ |

### Latest HK snapshot — 2026-09-14

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | 任正非 | 5000+ |
| 2 | 李嘉诚 | 2000+ |
| 3 | 香港人 | 1000+ |
| 4 | 林 行止 | 2000+ |
| 5 | tides | 500+ |
| 6 | 超級 市場 | 2000+ |
| 7 | 預測 | 2000+ |
| 8 | 氣象廳 | 500+ |
| 9 | 曼聯對曼城 | 10000+ |
| 10 | 吳兆麟 | 5000+ |

[Open full snapshot →](data/2026/09/14/trending.json)

### Browse by year

[`2026`](data/2026/) · 252 days · [`2025`](data/2025/) · 364 days · [`2024`](data/2024/) · 34 days

<!-- archive-dashboard:end -->

## Sources and priority

1. `google_trending_now` — direct live Trending Now capture; highest quality.
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

- `capture.py` fetches all four regions before writing a newly-created live day.
- Same-day reruns are idempotent by source quality.
- `backfill.py` converts the licensed GoogleTrendArchive ZIP.
- `mirror-manifest.json` records the GitHub mirror selection/import result after the one-shot backfill.
- `validate_archive.py` checks date/path consistency, supported regions/sources, contiguous ranks, non-empty queries, and duplicate queries.
- `render_readme.py` rebuilds this dashboard from committed data.
- Temporary research/backfill mechanisms live under `tools/` and self-remove after successful validation; durable reports/manifests remain.

## Files

- `AGENTS.md` — task boundaries and durable rules.
- `archive_lib.py` — schema, canonical regions, validation, source priority, merge behavior, and paths.
- `capture.py` — live four-region collector.
- `backfill.py` / `backfill-manifest.json` — licensed historical recovery.
- `mirror-manifest.json` — GitHub RSS mirror provenance/coverage after the one-shot import.
- `validate_archive.py` — full archive validation.
- `render_readme.py` — README dashboard renderer.
- `tests/` — deterministic tests.
