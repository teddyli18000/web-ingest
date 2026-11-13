# Google Trending Now Archive

A daily archive of Google Trends **Trending Now** for **Singapore (SG)**, the **United States (US)**, the **United Kingdom (GB)**, and **Hong Kong (HK)**.

The task preserves changing data useful later: **source order, query, search-volume signal, timing/breakdown/categories when the source actually provides them, source provenance, and Explore links when available**. It does not mirror pages, images, screenshots, or whole upstream repositories.

<!-- archive-dashboard:start -->

### Archive at a glance

| First day | Latest day | Days archived | SG days | US days | GB days | HK days |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **2024-11-28** | **2026-11-13** | **693** | **693** | **693** | **693** | **692** |

### Source mix

| Source | Region snapshots |
| --- | ---: |
| `googletrendarchive` | 1,479 |
| `github_rss_mirror` | 1,081 |
| `google_trending_now` | 208 |
| `github_hottrends_mirror` | 3 |

### Latest SG snapshot — 2026-11-13

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | microsoft outage | 200000+ |
| 2 | jensen huang third affair | 20000+ |
| 3 | singapore vs paraguay | 2000+ |
| 4 | spencer huang | 2000+ |
| 5 | reverse vending machine | 2000+ |
| 6 | treasury bill | 2000+ |
| 7 | microsoft share price | 2000+ |
| 8 | hougang prank | 1000+ |
| 9 | 刘欢 | 500+ |
| 10 | arrest | 2000+ |

### Latest US snapshot — 2026-11-13

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | microsoft outage | 10000000+ |
| 2 | mark mcguinn | 200000+ |
| 3 | dan hicks | 500000+ |
| 4 | social security cuts | 200000+ |
| 5 | giants | 500000+ |
| 6 | dc shooting | 500000+ |
| 7 | jensen huang third affair | 200000+ |
| 8 | italy vs france | 200000+ |
| 9 | mavericks vs timberwolves | 100000+ |
| 10 | raptors vs 76ers | 100000+ |

### Latest GB snapshot — 2026-11-13

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | microsoft outage | 1000000+ |
| 2 | lisa maxwell daughter beau | 100000+ |
| 3 | friday uk weather snowfall list | 50000+ |
| 4 | england national football team vs croatia national football team standings | 200000+ |
| 5 | polar vortex el niño winter weather | 50000+ |
| 6 | england vs australia | 50000+ |
| 7 | download 2027 | 50000+ |
| 8 | dpd warehouse immigration enforcement | 10000+ |
| 9 | italy vs france | 50000+ |
| 10 | microsoft share price | 10000+ |

### Latest HK snapshot — 2026-11-13

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | outlook | 100000+ |
| 2 | outlook 死機 | 20000+ |
| 3 | 新世界 | 2000+ |
| 4 | 王書麒 | 1000+ |
| 5 | 無敵小柑 | 1000+ |
| 6 | 郭羨妮 | 500+ |
| 7 | black friday | 1000+ |
| 8 | 死亡 | 500+ |
| 9 | jensen huang third affair | 5000+ |
| 10 | 王忠林 | 500+ |

[Open full snapshot →](data/2026/11/13/trending.json)

### Browse by year

[`2026`](data/2026/) · 295 days · [`2025`](data/2025/) · 364 days · [`2024`](data/2024/) · 34 days

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
