# Google Trending 2026 gap cross-check

Generated: `2026-08-31T20:44:34+00:00`

Purpose: cross-check whether public GitHub history preserves genuine Google Trending Now/RSS snapshots during the licensed archive gap `2026-01-04` through `2026-08-31`. This is evidence review, not an import authorization.

## Historical archive lineage

| Repository | Fork | Declared SPDX | All Rights Reserved | Jan 04 | Feb 15 | Apr 15 | Jun 16 | Jul 01 | Aug 31 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `fdciabdul/Google-Trends-Keywords-Scraper` | no | none | yes | error | error | 10/10/10/10 | 10/10/10/10 | 10/10/10/10 | 10/10/10/10 |
| `253611069/Google-Trends-Keywords-Scraper` | yes | none | yes | 10/10/10/10 | 10/10/10/10 | 10/10/10/10 | 10/10/10/10 | — | — |
| `DutchErwin/Google-Trends-Keywords-Scraper` | yes | none | yes | — | — | — | — | — | — |
| `imheyday/Google-Trends-Keywords-Scraper` | yes | none | yes | — | — | — | — | — | — |
| `connorodea/Google-Trends-Keywords-Scraper` | yes | none | yes | — | — | — | — | — | — |

Cell values are `SG/US/GB/HK` item counts from the first matching commit on that UTC date. A dash means no `data/SG.json` commit was found for that anchor date; it does **not** prove the repository had no data at nearby times.

## Independent collector cross-check

| Repository | Google Trending RSS endpoint visible in indexed code |
| --- | --- |
| `RuochenLyu/google-trends-now` | no/unknown |
| `aymenhmaidiwastaken/daily-country-search-trends` | yes |
| `flack0x/trendspyg` | yes |

## Evidence by anchor

- `2026-01-04`: `253611069/Google-Trends-Keywords-Scraper`
- `2026-02-15`: `253611069/Google-Trends-Keywords-Scraper`
- `2026-04-15`: `fdciabdul/Google-Trends-Keywords-Scraper`, `253611069/Google-Trends-Keywords-Scraper`
- `2026-06-16`: `fdciabdul/Google-Trends-Keywords-Scraper`, `253611069/Google-Trends-Keywords-Scraper`
- `2026-07-01`: `fdciabdul/Google-Trends-Keywords-Scraper`
- `2026-08-31`: `fdciabdul/Google-Trends-Keywords-Scraper`

## Decision

- The CC-BY-4.0 `aurman/GoogleTrendArchive` daily ZIP remains the only approved bulk historical import source currently recorded by `web-ingest`; its exact daily ordering ends on `2026-01-03`.
- GitHub history cross-checks verify complete four-region snapshots on selected later dates from `2026-01-04` through `2026-08-31` among the tested anchors.
- These GitHub repositories are the same scraper lineage or mirrors/forks, so they are **supporting evidence, not independent provenance**.
- No tested repository provides a clearly licensed, gap-wide archive that is safe to bulk redistribute into `web-ingest`. Missing days therefore stay missing.
- The previous report wording `throughout the gap` was too strong and is superseded by this report.

Temporary audit code/workflow should be removed after this report is committed.
