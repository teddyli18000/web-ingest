# web-ingest Operations Notes

This file is a compact manager-facing working record for repository-wide decisions that are useful to future Agents. It is not a changelog and should stay short.

## Current operating model

- `web-ingest` only collects and stores public Internet snapshots.
- Each persistent collector owns one root task directory and one thin workflow entry point when automation is needed.
- `tools/` is the repository manager workspace for schedule guards, audits, maintenance helpers, and durable operational notes.
- Scheduled ingestion jobs are staggered using declared `timeout-minutes` plus a 15-minute planning buffer.
- One-shot historical backfills/repairs/research probes are temporary operations; their scripts/workflows are removed after results are validated and durable conclusions are recorded.

## Current recurring load plan

| Task | Asia/Singapore schedule | Declared timeout |
| --- | --- | ---: |
| `ai-daily` | 08:05 | 65 min |
| `github-trending` | 09:27 / 10:27 / 11:27 | 15 min |
| `google-trending` | 12:17 / 13:17 | 15 min |

`github-trending` intentionally has three retry opportunities. `google-trending` has two; same-day source-quality/idempotency rules make later runs cheap once a full capture succeeds.

Collection workflows are not generic code-validation hooks. Repository-integrity CI validates code/workflow changes; recurring collectors run on their planned schedule or explicit manual dispatch.

## GitHub Trending historical state

- Earliest recovered date: **2014-08-09**.
- Historical recovery through 2026-08-31: **4,345 dates**.
- Historical All-Languages coverage: **2,498 dates**, beginning 2018-07-01.
- Direct daily collection continues after the historical boundary.
- Public historical sources are retained as provenance in each snapshot rather than erased during normalization.
- Canonical scope repair is complete and its cumulative statistics are preserved in the task manifest.

## Google Trending operating state

- Long-term regions are exactly **SG + US + GB + HK**.
- Live source is Google Trends Trending Now through pinned `google-trends-now@1.1.1`; RSS is a clearly marked limited fallback only.
- Canonical licensed historical source is `aurman/GoogleTrendArchive` (CC-BY-4.0, DOI `10.57967/hf/7531`). Its raw `daily_compressed.zip` preserves recoverable daily ordering from **2024-11-28 through 2026-01-03**.
- Licensed historical region coverage is: **SG 368 days, US 371, GB 368, HK 372**. The source has one known empty GB CSV on 2025-10-01; that file is recorded as a parse error rather than fabricated.
- 2026-09-01 was captured directly for all four regions after the scope migration. Direct captures outrank historical/fallback data.
- The wider Hugging Face dataset reports later 2026 observations, but its post-Jan material is processed/episode-oriented and does not expose an original daily rank field. Do not manufacture rankings from it.
- GitHub gap cross-check verified complete **SG/US/GB/HK** snapshots at six tested anchors spanning **2026-01-04, 2026-02-15, 2026-04-15, 2026-06-16, 2026-07-01, and 2026-08-31**. The evidence comes from `fdciabdul/Google-Trends-Keywords-Scraper` and a large fork/mirror in the same scraper lineage, so it demonstrates that snapshots existed on those dates but is **not independent provenance or proof of every intervening day**.
- The tested GitHub archive lineage has no declared SPDX license and advertises **All Rights Reserved**; it remains research evidence only and is not approved for bulk historical import. Separate open-source collectors independently confirm use of Google's Trending RSS endpoint, but they do not supply a suitably licensed gap-wide historical archive.
- Durable audit report: `tools/reports/google-trending-gap-audit-2026-09-01.md`.
- Source priority remains `google_trending_now` > `googletrendarchive` > `rss_limited`; research-only sources do not enter this priority chain.
- Missing dates remain missing until a source both preserves the relevant historical state and has suitable redistribution terms.

## Maintenance principle

Prefer a small tool that makes a rule executable over a paragraph that relies on future Agents remembering it. Use temporary tools for one-off audits/recovery work, keep the resulting evidence/report when useful, and remove the temporary mechanism afterwards.
