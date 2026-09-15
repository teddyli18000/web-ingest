# Google Trending Now Archive

A daily archive of Google Trends **Trending Now** for **Singapore (SG)**, the **United States (US)**, the **United Kingdom (GB)**, and **Hong Kong (HK)**.

The task preserves changing data useful later: **source order, query, search-volume signal, timing/breakdown/categories when the source actually provides them, source provenance, and Explore links when available**. It does not mirror pages, images, screenshots, or whole upstream repositories.

<!-- archive-dashboard:start -->

### Archive at a glance

| First day | Latest day | Days archived | SG days | US days | GB days | HK days |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **2024-11-28** | **2026-09-15** | **651** | **651** | **651** | **651** | **650** |

### Source mix

| Source | Region snapshots |
| --- | ---: |
| `googletrendarchive` | 1,479 |
| `github_rss_mirror` | 1,081 |
| `google_trending_now` | 40 |
| `github_hottrends_mirror` | 3 |

### Latest SG snapshot — 2026-09-15

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | margaret chung | 5000+ |
| 2 | psd reviewing civil servant housing data | 10000+ |
| 3 | singapore sms blaster phishing sentencing | 10000+ |
| 4 | private investigator | 1000+ |
| 5 | rts bukit chagar station | 1000+ |
| 6 | china | 1000+ |
| 7 | singapore | 2000+ |
| 8 | haze malaysia | 500+ |
| 9 | news | 1000+ |
| 10 | australia vs zimbabwe | 1000+ |

### Latest US snapshot — 2026-09-15

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | widows bay | 500000+ |
| 2 | broncos | 500000+ |
| 3 | bob mackie | 100000+ |
| 4 | macklemore | 100000+ |
| 5 | social security cola 2027 forecast | 50000+ |
| 6 | mitch mcconnell | 100000+ |
| 7 | travis kelce | 200000+ |
| 8 | tom pelphrey | 100000+ |
| 9 | yankees vs twins | 50000+ |
| 10 | braves vs cubs | 50000+ |

### Latest GB snapshot — 2026-09-15

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | leeds vs newcastle | 200000+ |
| 2 | traffic | 50000+ |
| 3 | matthew rhys | 50000+ |
| 4 | knebworth | 200000+ |
| 5 | ed sheeran | 50000+ |
| 6 | british royal family | 20000+ |
| 7 | next april pension rise forecast | 5000+ |
| 8 | gov.uk state pension forecast research | 20000+ |
| 9 | john torode | 2000+ |
| 10 | australia vs zimbabwe | 5000+ |

### Latest HK snapshot — 2026-09-15

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | 醫療券 | 5000+ |
| 2 | 百 佳 超市 | 500+ |
| 3 | 愛 回 家 之 三代 同 糖 | 1000+ |
| 4 | 消费券 | 500+ |
| 5 | china | 500+ |
| 6 | 超級 市場 | 1000+ |
| 7 | 香港施政報告 | 5000+ |
| 8 | ios 27 | 2000+ |
| 9 | 長者 生活 津貼 | 2000+ |
| 10 | 校長 | 1000+ |

[Open full snapshot →](data/2026/09/15/trending.json)

### Browse by year

[`2026`](data/2026/) · 253 days · [`2025`](data/2025/) · 364 days · [`2024`](data/2024/) · 34 days

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
