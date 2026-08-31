# web-ingest Operations Notes

This file is a compact manager-facing record for repository-wide decisions. It is not a changelog.

## Current operating model

- `web-ingest` only collects and stores public Internet snapshots.
- Each persistent collector owns one root task directory and one thin workflow entry point.
- `tools/` is the repository manager workspace for schedule guards, audits, temporary migrations/backfills, and durable operational notes.
- Scheduled ingestion jobs are staggered using declared `timeout-minutes` plus a 15-minute planning buffer.
- One-shot backfills/repairs/probes are temporary; their scripts/workflows are removed after validation while reports/manifests remain.

## Current recurring load plan

| Task | Asia/Singapore schedule | Declared timeout |
| --- | --- | ---: |
| `ai-daily` | 08:07 | 65 min |
| `github-trending` | 09:31 / 10:43 / 11:55 | 15 min |
| `google-trending` | 12:37 / 13:49 | 15 min |

The minute values are deliberately different rather than copied between bots. `github-trending` has three retry opportunities; `google-trending` has two. Collection workflows run only on schedule or manual dispatch; repository-integrity owns code/workflow validation.

## GitHub Trending historical state

- Earliest recovered date: **2014-08-09**.
- Historical recovery through 2026-08-31: **4,345 dates**.
- Historical All-Languages coverage: **2,498 dates**, beginning 2018-07-01.
- Direct daily collection continues after the historical boundary.
- Public historical sources remain visible as provenance.

## Google Trending operating state

- Long-term regions are exactly **SG + US + GB + HK**.
- Live source is Google Trends Trending Now through pinned `google-trends-now@1.1.1`; RSS is a marked fallback.
- `aurman/GoogleTrendArchive` remains the CC-BY-4.0 historical source where available.
- Repository-owner direction permits using `fdciabdul/Google-Trends-Keywords-Scraper` as a historical mirror to fill otherwise missing region snapshots. Store it as `github_rss_mirror`, preserve exact commit/file provenance and the upstream **All Rights Reserved** notice, and never use it to overwrite an existing `googletrendarchive` or direct snapshot.
- Mirror selection targets the source commit closest to **12:30 Asia/Singapore** for each missing archive date, with deterministic fallbacks recorded in `google-trending/mirror-manifest.json`.
- Source quality order is `google_trending_now` > (`googletrendarchive` = `github_rss_mirror`) > `rss_limited`. Equal-quality historical sources do not overwrite one another.
- Durable audit/background report: `tools/reports/google-trending-gap-audit-2026-09-01.md`; the one-shot mirror backfill writes a separate completion report.

## Maintenance principle

Prefer a small executable guard/tool over relying on future Agents to remember a rule. Keep durable provenance and decisions; remove temporary mechanisms after they finish.
