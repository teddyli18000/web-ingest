# Google Trends task rules

Read `README.md` and `config.json` before changing this task.

## Stable contract

- This task archives Google **Trending Now**, not arbitrary keyword interest-over-time queries.
- Long-term geographic scope is **SG + US only**. Do not silently expand it.
- Daily canonical output is `data/YYYY/MM/DD/trending.json` using schema v1.
- Prefer Google's public Trending Now RSS export for recurring collection. Do not replace it with Selenium/Playwright unless RSS becomes unusable and the tradeoff is documented.
- Missing fields stay missing; never infer exact search counts or timestamps from volume buckets/labels.
- Do not download or commit images, screenshots, page HTML, article bodies, browser profiles, cookies, or session state.
- Existing direct Google snapshots beat third-party historical backfills on date/geo overlap.

## Changes

- Parser/schema changes require deterministic tests.
- If `config.json` geos change, update `README.md`, deliberately migrate historical files with `prune_to_config.py` or an equivalent reviewed repair, and verify Action load with `python tools/check-repository-integrity.py --show`.
- `validate_archive.py` must pass after historical or schema maintenance.
- Historical import is deliberate maintenance, not a recurring scheduled job. Temporary backfill/repair workflows must be removed after success.
- Normal daily data commits should only touch `google-trends/data/**` and the dashboard block in `google-trends/README.md`.
