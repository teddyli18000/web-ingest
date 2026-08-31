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

## Google Trends operating decision

- Product archived: **Google Trends → Trending Now**, not generic Explore/interest-over-time data.
- Recurring source: Google's public Trending Now RSS export; no browser, cookie, API key, or GCP identity is required.
- Long-term core regions: `SG`, `US`, `GB`, `IN`, `JP`, `KR`, `HK`, `TW`.
- One day is committed only when all configured core regions succeed.
- Historical recovery source: `aurman/GoogleTrendArchive` raw daily CSV archive (CC-BY-4.0), filtered to the core-region set instead of copying the multi-gigabyte upstream dataset.
- Missing historical days remain missing; do not synthesize Trending Now rankings from BigQuery or keyword interest time series.

## Maintenance principle

Prefer a small tool that makes a rule executable over a paragraph that relies on future Agents remembering it. Prefer documentation when a decision cannot or should not be enforced mechanically.
