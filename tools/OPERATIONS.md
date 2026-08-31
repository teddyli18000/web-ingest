# web-ingest Operations Notes

This file is a compact manager-facing working record for repository-wide decisions that are useful to future Agents. It is not a changelog and should stay short.

## Current operating model

- `web-ingest` only collects and stores public Internet snapshots.
- Each persistent collector owns one root task directory and one thin workflow entry point when automation is needed.
- `tools/` is the repository manager workspace for schedule guards, audits, maintenance helpers, and durable operational notes.
- Scheduled ingestion jobs are staggered using declared `timeout-minutes` plus a 15-minute planning buffer.
- One-shot historical backfills/repairs are temporary operations; their workflows are removed after validation.

## Current recurring load plan

| Task | Asia/Singapore schedule | Declared timeout |
| --- | --- | ---: |
| `ai-daily` | 08:05 | 65 min |
| `github-trending` | 09:27 / 10:27 / 11:27 | 15 min |
| `google-trending` | 12:17 / 13:17 | 15 min |

`github-trending` intentionally has three retry opportunities. `google-trending` has two; same-day source-quality/idempotency rules make later runs cheap once a full capture succeeds.

## GitHub Trending historical state

- Earliest recovered date: **2014-08-09**.
- Historical recovery through 2026-08-31: **4,345 dates**.
- Historical All-Languages coverage: **2,498 dates**, beginning 2018-07-01.
- Direct daily collection continues after the historical boundary.
- Public historical sources are retained as provenance in each snapshot rather than erased during normalization.
- Canonical scope repair is complete and its cumulative statistics are preserved in the task manifest.

## Google Trending rollout

- Long-term scope is fixed to **SG + US**.
- Live source is Google Trends Trending Now through pinned `google-trends-now@1.1.1`; RSS is a clearly marked limited fallback only.
- Historical source is `aurman/GoogleTrendArchive` (CC-BY-4.0, DOI `10.57967/hf/7531`). Only SG/US 1-day CSV material is imported; the upstream large ZIP is never committed.
- Source priority is `google_trending_now` > `googletrendarchive` > `rss_limited`, so reruns may upgrade but not downgrade a date/region.
- Initial historical recovery is performed on `agent/google-trending` by a temporary non-scheduled workflow and committed by year. Remove that workflow after validation before merging the feature branch.

## Maintenance principle

Prefer a small tool that makes a rule executable over a paragraph that relies on future Agents remembering it. Prefer documentation when a decision cannot or should not be enforced mechanically.
