# Google Trending 2026 gap audit

Generated: `2026-08-31T20:36:26+00:00`

## Candidate

- Repository: `fdciabdul/Google-Trends-Keywords-Scraper`
- Direct Google RSS endpoint found in collector source: **yes**
- README contains `All Rights Reserved`: **yes**
- Anchor dates with non-empty SG/US/GB/HK snapshots: **2/4**

## Anchor verification

| UTC date | Commit | SG | US | GB | HK |
| --- | --- | ---: | ---: | ---: | ---: |
| 2026-01-04 | `—` | — | — | — | — |
| 2026-04-15 | `—` | — | — | — | — |
| 2026-07-01 | `983b268851` | 10 | 10 | 10 | 10 |
| 2026-08-31 | `b71d206400` | 10 | 10 | 10 | 10 |

## Decision

This repository is strong **cross-validation evidence** that Google Trending RSS snapshots existed throughout the 2026 gap and that all four target regions were being captured in Git history.

It is **not approved as a bulk import source** for `web-ingest`: the repository itself advertises `All Rights Reserved`, so redistribution rights for copying its historical archive at scale are unclear. `web-ingest` should not copy the data unless the licensing/permission situation becomes explicit.

The canonical historical importer remains the CC-BY-4.0 `aurman/GoogleTrendArchive` raw daily archive. Later rankless/processed Google Trends datasets must not be converted into invented daily rankings.

This report is durable evidence; the script that produced it is temporary repository-management tooling.
