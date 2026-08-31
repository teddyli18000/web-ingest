# Google Trends task rules

Read `README.md` and `config.json` before changing this task.

## Stable contract

- This task archives Google **Trending Now**, not arbitrary keyword interest-over-time queries.
- Daily canonical output is `data/YYYY/MM/DD/trending.json` using schema v1.
- The configured core geo set is deliberate. Do not silently expand it to every supported region.
- Prefer Google's official RSS export for recurring collection. Do not replace it with Selenium/Playwright unless RSS becomes unusable and the tradeoff is documented.
- Missing fields stay missing; never infer exact search counts or timestamps from volume buckets/labels.
- Do not download or commit images, screenshots, page HTML, article bodies, browser profiles, cookies, or session state.
- Existing direct Google snapshots beat third-party historical backfills on date/geo overlap.

## Changes

- Parser/schema changes require deterministic tests.
- If `config.json` geos change, update `README.md` and verify Action load with `python tools/check-repository-integrity.py --show`.
- Historical import is deliberate maintenance, not a recurring scheduled job. Temporary backfill workflows must remove themselves after success.
- Normal daily data commits should only touch `google-trends/data/**` and the dashboard block in `google-trends/README.md`.
