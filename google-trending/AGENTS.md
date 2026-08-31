# AGENTS.md — Google Trending

This directory owns the SG + US + GB + HK Google Trends **Trending Now** archive.

Read `README.md` before changing collection or historical behavior.

## Stable scope

- Long-term regions are exactly **SG**, **US**, **GB**, and **HK** unless the repository owner explicitly changes that decision.
- Live primary source is the full Trending Now data path through the pinned `google-trends-now` collector.
- Google Trends RSS live fallback is visibly marked `rss_limited`.
- `aurman/GoogleTrendArchive` is the licensed CC-BY-4.0 historical source where it preserves daily ordering.
- `fdciabdul/Google-Trends-Keywords-Scraper` may be mirrored as `github_rss_mirror` to fill otherwise missing historical region snapshots. Preserve exact source repository, commit SHA, file path, RSS endpoint, and upstream rights notice.
- Older Git-history recovery may use the predecessor Google Hot Trends Atom feed as `github_hottrends_mirror` only when the exact source commit and feed endpoint are verifiable. Never relabel those snapshots as modern Trending RSS.
- Source quality is `google_trending_now` > (`googletrendarchive` = `github_rss_mirror` = `github_hottrends_mirror`) > `rss_limited`. Equal-quality historical sources never overwrite one another.

## Data rules

- Canonical output: `data/YYYY/MM/DD/trending.json`.
- Preserve source order and provenance. Never invent ranking, counts, categories, timestamps, breakdowns, or Explore links absent from the source.
- Mirror imports fill missing regions only; they do not replace existing licensed/direct snapshots.
- Do not commit upstream repository clones, ZIPs, images, screenshots, HTML pages, cookies, credentials, signed URLs, or temporary research downloads.
- A live run fetches every configured region successfully before writing a newly-created day.
- Same-day reruns must be safe and predictable.

## Validation and maintenance

- Persistent task collection/schema logic stays here. One-shot repository-management importers/audits may live temporarily under `tools/`.
- Parser/schema changes require deterministic tests under `tests/`.
- Before schedule changes run `python tools/check-repository-integrity.py --show`.
- After data/schema changes run `python google-trending/validate_archive.py` and refresh the README dashboard.
- Historical backfills/repairs are one-shot operations; temporary scripts/workflows must be removed after validation, while manifests/reports remain.
