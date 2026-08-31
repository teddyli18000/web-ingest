# AGENTS.md — Google Trending

This directory owns the SG + US Google Trends **Trending Now** archive.

Read `README.md` before changing collection or historical behavior.

## Stable scope

- Long-term regions are exactly **SG** and **US** unless the repository owner explicitly changes that decision.
- Live primary source is the full Trending Now data path through the pinned `google-trends-now` collector.
- Google Trends RSS is fallback-only and must remain visibly marked `rss_limited`.
- Historical source is `aurman/GoogleTrendArchive`; only exact SG/US directory data from its public daily archive is retained.
- Source priority is `google_trending_now` > `googletrendarchive` > `rss_limited`; never downgrade a stored region snapshot.

## Data rules

- Canonical output: `data/YYYY/MM/DD/trending.json`.
- Preserve source provenance and historical source-member names.
- Missing upstream fields stay missing; do not infer counts, categories, timestamps, or rankings.
- Do not commit the upstream ZIP, images, screenshots, HTML pages, cookies, credentials, or signed URLs.
- A live run fetches both SG and US successfully before writing a new day.
- Same-day reruns must be safe and predictable.

## Validation and maintenance

- Task collection/conversion logic stays here, not in `tools/`.
- Parser/schema changes require deterministic tests under `tests/`.
- Before schedule changes run `python tools/check-repository-integrity.py --show`.
- After data/schema changes run `python google-trending/validate_archive.py` and refresh the README dashboard.
- Historical backfills/repairs are one-shot operations; temporary workflows must be removed after validation.
- Historical gaps are allowed when the source has no valid SG/US snapshot; never synthesize continuity.
