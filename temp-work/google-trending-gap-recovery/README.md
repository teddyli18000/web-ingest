# Google Trending gap recovery

One-shot recovery workspace for Google Trending archive gaps.

## Scope

- Re-check the unresolved historical gaps on `2025-03-24` (SG/US/GB/HK) and `2025-03-27` (HK) against additional GitHub mirrors/derivatives of `fdciabdul/Google-Trends-Keywords-Scraper`.
- Recover the missed `2026-10-07` snapshot from the primary GitHub RSS mirror if the live collector did not commit the day.
- Preserve exact source repository, commit SHA, source file, RSS endpoint, source order, and rights notice.
- Never synthesize a missing day from adjacent snapshots.

## Lifecycle

`.github/workflows/google-trending-gap-recovery.yml` runs this workspace once, validates the archive, refreshes the Google Trending README dashboard, commits any verified recovery, and then removes both the temporary workflow and this workspace.

Only validated archive data and durable provenance in `google-trending/mirror-manifest.json` should remain after completion.
