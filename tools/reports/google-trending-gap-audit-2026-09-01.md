# Google Trending 2026 gap audit

Generated from the one-shot repository audit on `2026-09-01` (Asia/Singapore), with manual GitHub commit-search follow-up for older dense history.

## Candidate

- Repository: `fdciabdul/Google-Trends-Keywords-Scraper`
- Collector source directly requests Google Trending RSS: `https://trends.google.com/trending/rss?geo=<country>&hours=48`.
- Repository-generated README states **All Rights Reserved**.
- The candidate is therefore useful as historical **cross-validation evidence**, but is **not approved as a bulk import source** for `web-ingest` without clearer redistribution permission.

## Cross-validation

The temporary path-scoped REST audit automatically found complete SG/US/GB/HK snapshots on **2026-07-01** and **2026-08-31**, but returned false negatives for the older January/April anchors in this unusually large, high-frequency Git history.

A second GitHub commit-search + historical-file pass verified those older anchors directly:

| UTC date | Verification | SG | US | GB | HK |
| --- | --- | --- | --- | --- | --- |
| 2026-01-04 | GitHub commit search + direct historical file reads | present | present | present | present |
| 2026-04-15 | GitHub commit search + direct historical file reads | present | present | present | present |
| 2026-07-01 | one-shot automated audit | present | present | present | present |
| 2026-08-31 | one-shot automated audit | present | present | present | present |

Result: **4/4 anchor dates** confirm that all four target regions were being captured in the candidate repository during the 2026 gap. This validates that the gap is not caused by Google Trending Now being unavailable during those periods.

## Decision

Do **not** copy the candidate's historical JSON into `web-ingest` at scale while its redistribution terms remain unclear. Public visibility and technical recoverability are not treated as permission to republish an archive.

The canonical import source remains `aurman/GoogleTrendArchive` (CC-BY-4.0) for the dates where its raw daily CSV archive preserves original daily ordering. Its later processed dataset can establish that trends existed after January 2026, but it does not expose an original daily rank field and therefore must not be converted into invented rankings.

The remaining 2026 continuity gap is now classified as **recoverable in principle, but not currently importable under the repository's provenance/licensing rules**. Revisit only if a suitably licensed rank-preserving source or explicit permission becomes available.

The temporary audit script and one-shot workflow were removed after the repair; this report is the durable result.
