# Google Trending Now Archive

A daily archive of Google Trends **Trending Now** for **Singapore (SG)**, the **United States (US)**, the **United Kingdom (GB)**, and **Hong Kong (HK)**.

The task preserves the changing data that is useful later: **trend order, query, search-volume signal, timing fields, breakdown, categories when available, source provenance, and Google Explore links**. It does not mirror Google pages, images, screenshots, or large upstream archives.

<!-- archive-dashboard:start -->

### Archive at a glance

| First day | Latest day | Days archived | SG days | US days | GB days | HK days |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **2024-11-28** | **2026-09-01** | **376** | **369** | **372** | **369** | **373** |

### Source mix

| Source | Region snapshots |
| --- | ---: |
| `googletrendarchive` | 1,479 |
| `google_trending_now` | 4 |

### Latest SG snapshot — 2026-09-01

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | taekwondo | 10000+ |
| 2 | aston villa vs arsenal | 2000+ |
| 3 | barcelona vs rayo vallecano | 500+ |
| 4 | alex yam | 5000+ |
| 5 | lee yong joo princess hours | 2000+ |
| 6 | non profit hospital | 5000+ |
| 7 | cooling center | 5000+ |
| 8 | collecting discarded cans for refunds | 2000+ |
| 9 | singapore hawker centre cleaning schedule | 5000+ |
| 10 | jack neo ah boys to firefighters | 500+ |

### Latest US snapshot — 2026-09-01

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | barcelona vs rayo vallecano | 200000+ |
| 2 | israel travel restrictions state department | 200000+ |
| 3 | aston villa vs arsenal | 100000+ |
| 4 | novak djokovic | 200000+ |
| 5 | outlook outage | 50000+ |
| 6 | khan | 50000+ |
| 7 | heavy mixed triplets california birth | 50000+ |
| 8 | messi | 50000+ |
| 9 | pro wrestler paul leduc passes | 20000+ |
| 10 | daniel richman fbi leak probe | 20000+ |

### Latest GB snapshot — 2026-09-01

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | aston villa vs arsenal | 100000+ |
| 2 | barcelona vs rayo vallecano | 10000+ |
| 3 | catherine, princess of wales | 20000+ |
| 4 | grand canyon flash floods | 10000+ |
| 5 | emmerdale emmerdale | 20000+ |
| 6 | revolut user account fraud jersey | 5000+ |
| 7 | atorvastatin | 10000+ |
| 8 | lindsay clancy | 20000+ |
| 9 | novak djokovic | 20000+ |
| 10 | james bond | 10000+ |

### Latest HK snapshot — 2026-09-01

| # | Trend | Search volume |
| ---: | --- | ---: |
| 1 | 夜生活 | 2000+ |
| 2 | 謝振軒 | 5000+ |
| 3 | 阿斯頓維拉對兵工廠 | 1000+ |
| 4 | aston villa vs arsenal | 500+ |
| 5 | 何超瓊 | 200+ |
| 6 | 謝淑怡 | 2000+ |
| 7 | 沙德爾 | 2000+ |
| 8 | 黎彼得 | 2000+ |
| 9 | low-pressure area | 2000+ |
| 10 | windy | 2000+ |

[Open full snapshot →](data/2026/09/01/trending.json)

### Browse by year

[`2026`](data/2026/) · 4 days · [`2025`](data/2025/) · 338 days · [`2024`](data/2024/) · 34 days

<!-- archive-dashboard:end -->

## Sources

### Live collection

Primary collector: pinned `google-trends-now@1.1.1`, which reads Google's current Trending Now web-data path. The task requests **SG + US + GB + HK**, past **24 hours**, all categories/statuses, Google's relevance order, and all available rows.

If the primary path fails, Google Trends RSS may be used as a bounded fallback. RSS output is stored explicitly as `rss_limited`; it is not treated as the full Trending Now pool and may later be upgraded by a complete same-day capture.

Source priority is:

1. `google_trending_now` — direct live capture;
2. `googletrendarchive` — licensed historical recovery;
3. `rss_limited` — fallback only.

Lower-priority data never overwrites a higher-priority region snapshot.

### Historical recovery

Canonical historical source: [`aurman/GoogleTrendArchive`](https://huggingface.co/datasets/aurman/GoogleTrendArchive), DOI `10.57967/hf/7531`, CC-BY-4.0.

The wider dataset reports observations beyond the raw daily archive's end date, but this repository only imports data that still preserves an actual daily Trending Now ordering. The canonical `daily_compressed.zip` provides exact configured-region daily CSV snapshots from **2024-11-28 through 2026-01-03**. The large ZIP itself is never committed; its SHA-256 and per-region coverage are recorded in `backfill-manifest.json`.

GitHub research has identified additional repositories whose Git history demonstrates that Google RSS snapshots exist during later 2026 dates. Those archives are useful as cross-validation evidence, but they are **not automatically importable**: bulk historical copying requires clear redistribution terms. A missing date therefore remains missing unless a suitably licensed source preserving the original ordering is found.

## Schedule

Workflow: `.github/workflows/google-trending.yml`

Daily opportunities: **12:17 and 13:17 Asia/Singapore**. The first successful full capture normally makes the second attempt a no-op. The repository manager guard checks these slots against every other recurring workflow's timeout plus the 15-minute planning buffer.

Collection runs only from the scheduled/manual workflow. Code changes are validated by repository-integrity CI instead of implicitly triggering an ingestion run.

## Output

Canonical daily file:

```text
google-trending/data/YYYY/MM/DD/trending.json
```

Each file contains one date and whatever valid snapshots exist for the four canonical regions. Historical source gaps are allowed; a new live day is written only after all configured regions are fetched successfully. Missing upstream fields remain `null` or empty; the archive does not infer exact counts, categories, timestamps, or rankings the source did not preserve.

## Recovery and validation

- `capture.py` fetches all four regions before writing a newly-created live day, preventing a hard failure from creating a partial new date.
- Same-day reruns are idempotent by source quality.
- RSS may upgrade to full live data; historical data may upgrade to direct live data; neither can downgrade a better source.
- `backfill.py` converts the licensed external daily ZIP and can batch by year.
- `validate_archive.py` checks date/path consistency, regions/sources, contiguous ranks, non-empty queries, and duplicate queries.
- `render_readme.py` rebuilds the dashboard from committed archive files and derives region columns from the canonical region set.
- Parser/schema changes are covered by `tests/` and governed by `AGENTS.md`.
- Gap research belongs in temporary repository-management tools; durable conclusions are recorded under `tools/` and temporary code/workflows are removed after use.

## Files

- `AGENTS.md` — task boundaries and durable rules.
- `archive_lib.py` — schema, canonical region set, validation, source priority, merge behavior, and paths.
- `capture.py` — live four-region collector.
- `backfill.py` — GoogleTrendArchive historical converter.
- `backfill-manifest.json` — licensed historical provenance and coverage.
- `validate_archive.py` — full archive validation.
- `render_readme.py` — README dashboard renderer.
- `tests/` — deterministic tests.
