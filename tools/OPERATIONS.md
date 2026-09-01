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
| `ai-daily` | 08:07 / 08:19 / 08:31 / 08:43 / 08:55 / 09:09 | 6 min |
| `github-trending` | 09:31 / 10:43 / 11:55 | 15 min |
| `google-trending` | 12:37 / 13:49 | 15 min |

The minute values are deliberately varied rather than copied between bots. AI Daily uses six short idempotent opportunities because GitHub scheduled events are best-effort and can be delayed or dropped; the first complete snapshot wins and later slots no-op against the latest `main`. Its final slot reserves through 09:30, immediately before GitHub Trending at 09:31. `github-trending` has three retry opportunities; `google-trending` has two. Collection workflows run only on schedule or manual dispatch; repository-integrity owns code/workflow validation.

### AI Daily scheduler incident — 2026-09-01

- AIHOT's archived API response says the 2026-09-01 report was generated at **00:01:42Z / 08:01:42 UTC+8**.
- The original single 08:07 scheduled GitHub Actions run was not created until **04:57:49Z / 12:57:49 UTC+8**.
- That run fetched successfully on its first request and committed at about 12:58, proving the delay was in GitHub's scheduled trigger path rather than the AIHOT collector or publication time.
- Durable response: do not rely on one long sleeping cron for AI Daily. Use multiple short schedule events, latest-main checkout, complete-snapshot early exit, and rebase-before-push.

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
- Repository-owner direction permits using `fdciabdul/Google-Trends-Keywords-Scraper` as a historical mirror to fill otherwise missing region snapshots. Store modern-feed snapshots as `github_rss_mirror`, preserve exact commit/file provenance and the upstream **All Rights Reserved** notice, and never use the mirror to overwrite an existing `googletrendarchive` or direct snapshot.
- The required **2026-01-04 through 2026-08-31** SG/US/GB/HK mirror gap is complete. Mirror selection targets the source commit closest to **12:30 Asia/Singapore** for each missing archive date, with deterministic fallbacks recorded in `google-trending/mirror-manifest.json`.
- The isolated **2025-02-05** SG/US/GB hole was recovered from an exact historical commit in `connorodea/Google-Trends-Keywords-Scraper`. That commit used Google's predecessor Hot Trends Atom feed, so those snapshots are stored separately as `github_hottrends_mirror` with the historical `pn` endpoint rather than being relabeled as modern RSS.
- Remaining source-side gaps are **2025-03-24 (SG/US/GB/HK)** and **2025-03-27 (HK)**. The primary mirror plus 12 long-lived forks were checked and had no commits on those UTC dates; do not synthesize or backdate later snapshots to fill them.
- Source quality order is `google_trending_now` > (`googletrendarchive` = `github_rss_mirror` = `github_hottrends_mirror`) > `rss_limited`. Equal-quality historical sources do not overwrite one another.
- Durable reports: `tools/reports/google-trending-gap-audit-2026-09-01.md` and `tools/reports/google-trending-residual-recovery-2026-09-01.md`.

## Maintenance principle

Prefer a small executable guard/tool over relying on future Agents to remember a rule. Keep durable provenance and decisions; remove temporary mechanisms after they finish.
