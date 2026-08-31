# AGENTS.md — Google Trending

This directory owns the SG + US + GB + HK Google Trends **Trending Now** archive.

Read `README.md` before changing collection or historical behavior.

## Stable scope

- Long-term regions are exactly **SG**, **US**, **GB**, and **HK** unless the repository owner explicitly changes that decision.
- Live primary source is the full Trending Now data path through the pinned `google-trends-now` collector.
- Google Trends RSS is fallback-only and must remain visibly marked `rss_limited`.
- Canonical licensed historical source is `aurman/GoogleTrendArchive`; only exact configured-region directory data from its public daily archive is retained.
- Source priority is `google_trending_now` > `googletrendarchive` > `rss_limited`; never downgrade a stored region snapshot.
- A third-party archive may be used as research evidence without becoming an import source. Do not bulk-copy historical data whose redistribution rights are unclear.

## Data rules

- Canonical output: `data/YYYY/MM/DD/trending.json`.
- Preserve source provenance and historical source-member names.
- Missing upstream fields stay missing; do not infer counts, categories, timestamps, or rankings.
- Do not commit upstream ZIPs, images, screenshots, HTML pages, cookies, credentials, signed URLs, or temporary research downloads.
- A live run fetches every configured region successfully before writing a newly-created day.
- Same-day reruns must be safe and predictable.

## Validation and maintenance

- Task collection/conversion logic stays here, not in `tools/`.
- Repository-level research/audits, migration helpers, and other one-shot management work may use temporary scripts under `tools/`; remove temporary tools after their result is recorded.
- Parser/schema changes require deterministic tests under `tests/`.
- Before schedule changes run `python tools/check-repository-integrity.py --show`.
- After data/schema changes run `python google-trending/validate_archive.py` and refresh the README dashboard.
- Historical backfills/repairs are one-shot operations; temporary workflows must be removed after validation.
- Historical gaps are allowed when no suitably licensed source preserves the original state; never synthesize continuity from unrelated Google Trends products or rankless aggregates.
