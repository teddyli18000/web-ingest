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
| `google-trends` | 12:07 / 13:07 / 14:07 | 20 min |

Retry-slot collectors are same-day idempotent. Once a valid daily snapshot exists, later opportunities should exit without rewriting it.

## GitHub Trending historical state

- Earliest recovered date: **2014-08-09**.
- Historical recovery through 2026-08-31: **4,345 dates**.
- Historical All-Languages coverage: **2,498 dates**, beginning 2018-07-01.
- Direct daily collection continues after the historical boundary.
- Public historical sources are retained as provenance in each snapshot rather than erased during normalization.
- Canonical historical scopes collapse unambiguous source aliases such as `cpp` → `c++` and `c%23` → `c#`; the migration counters are preserved across no-op reruns.

## Google Trends historical state

- Product archived: **Google Trends → Trending Now**, not generic Explore/interest-over-time data.
- Long-term region contract: **SG + US only**.
- Recurring source: Google's public Trending Now RSS export; no browser, cookie, API key, or GCP identity is required.
- One live day is committed only when both SG and US succeed.
- Historical source: `aurman/GoogleTrendArchive` raw daily CSV archive (CC-BY-4.0), normalized into the task schema instead of copying the bulk upstream archive.
- SG/US historical recovery covers **373 dates** from **2024-11-28 through 2026-01-03**; SG is present on 368 days and US on 371 days.
- The direct 2026-09-01 capture brings the current archive to **374 stored dates** total after pruning non-core regions.
- Known exact-ranking gap: **2026-01-04 through 2026-08-31**. Do not substitute BigQuery or keyword-interest time series for this gap.
- The original 8-region import was deliberately pruned to SG/US; `backfill-manifest.json` preserves the original import statistics and records the scope-repair provenance.
- Temporary backfill/repair workflows must be removed once validation succeeds.

## Maintenance principle

Prefer a small tool that makes a rule executable over a paragraph that relies on future Agents remembering it. Prefer documentation when a decision cannot or should not be enforced mechanically.
