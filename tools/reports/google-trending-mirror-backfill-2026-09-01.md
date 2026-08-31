# Google Trending GitHub mirror backfill

Generated: `2026-08-31T21:10:35+00:00`

- Source: `fdciabdul/Google-Trends-Keywords-Scraper`
- Source notice recorded by upstream: **All Rights Reserved**
- Requested archive range: **2024-11-28 through 2026-08-31**
- Required 2026 gap: **2026-01-04 through 2026-08-31**
- Archive days that needed at least one region: **282**
- Source commit-days used: **280**

## Region coverage

| Region | Missing before | Mirrored writes | Missing after |
| --- | ---: | ---: | ---: |
| SG | 274 | 272 | 2 |
| US | 271 | 269 | 2 |
| GB | 274 | 272 | 2 |
| HK | 270 | 268 | 2 |

## Selection and provenance

For each date that lacked one or more canonical regions, the importer chose the upstream commit closest to **04:30 UTC / 12:30 Asia/Singapore**, then copied only the missing region JSON in source order. Existing `googletrendarchive` and direct `google_trending_now` snapshots were never overwritten.

Each mirrored region stores the upstream repository, exact commit SHA, source file, original 48-hour Google Trending RSS endpoint, and the upstream rights notice.

Failures recorded: **5**.

### Failure examples

- `2025-02-05 SG: source file missing or empty at 4ff513d09419`
- `2025-02-05 US: source file missing or empty at 4ff513d09419`
- `2025-02-05 GB: source file missing or empty at 4ff513d09419`
- `2025-03-24: no source commit found`
- `2025-03-27: no source commit found`
