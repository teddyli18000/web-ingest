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

`github-trending` intentionally has three retry opportunities. Same-day idempotency makes later runs cheap once the first capture succeeds.

## GitHub Trending historical state

- Earliest recovered date: **2014-08-09**.
- Historical recovery through 2026-08-31: **4,345 dates**.
- Historical All-Languages coverage: **2,498 dates**, beginning 2018-07-01.
- Direct daily collection continues after the historical boundary.
- Public historical sources are retained as provenance in each snapshot rather than erased during normalization.

A one-time normalization repair is being used to collapse unambiguous source-specific scope aliases such as `cpp` → `c++` and percent-encoded `c%23` → `c#`. The repair must not invent ranks, repositories, stars, or other source data.

## Next collection candidate

Google Trends / Trending Now is the next candidate to investigate. Before implementation, decide what historical window is actually recoverable and what minimal fields are worth preserving; avoid blindly mirroring a high-frequency firehose.

## Maintenance principle

Prefer a small tool that makes a rule executable over a paragraph that relies on future Agents remembering it. Prefer documentation when a decision cannot or should not be enforced mechanically.
