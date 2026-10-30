# Exact seven-owner support-gap frontier

Status: **no verified score above 134,753**. This note freezes the exact seven-owner support-graph census and its irreducibility reduction so later work does not repeat the 8.7-million-state enumeration.

All supports are against the pinned BPZ/Tan `B` of size 359 at source commit `c753408492dde92a239708986d16c15dbf6c3235`.

## Exact connected k=7 census

GitHub Actions run `40994390874` used `code/bpz_support_clique_cover_gap_census.py` with all available runner cores. It enumerated every connected seven-owner support set reachable by the exact support-extension state graph and computed exact support-pool independence number and clique-cover number.

Result:

- connected owner sets: **8,708,726**;
- sufficiently large pools (`|Y_C| >= 8`): **2,829,398**;
- maximum support-pool size: **34**;
- maximum exact independence number: **8**;
- clique-cover-gap cases: **611**;
- every one of the 611 gap cases has `alpha(Y_C)=8`.

The exact cover-gap histogram is therefore concentrated entirely at the raw `7 -> 8` boundary; there is no stronger single seven-owner defect in this census.

## Exact irreducibility audit

The completed census artifact was audited independently with `code/bpz_gap_irreducibility_audit.py`. For every one of the 611 gap cases, the audit recomputes a maximum independent set and minimizes how many deleted owners are re-used by a maximum set.

Intersection histogram:

| Minimum reused owners in a maximum 8-set | Cases |
|---:|---:|
| 0 | **12** |
| 1 | 131 |
| 2 | 468 |

Thus only **12** cases are genuinely outside-only irreducible `7 -> 8` support defects. The other 599 raw gap cases immediately re-add one or two deleted owners and reduce to lower-support geometry.

The 12 irreducible complete support pools have sizes 22 through 26. Their union contains only **73 distinct five-dimensional vertices**, so the meaningful seven-owner frontier is small enough for a direct global ten-dimensional prize optimization rather than another radius-style census.

## Current next step

A packed exact workflow (`40996847699`) consumes the already-completed census artifact, replays the 611 -> 12 irreducibility reduction, unions the 12 complete support pools, and jointly optimizes arbitrary independent subsets of `U x U` against all 18 record terminal baselines with shared core/periphery deletion costs. Its primary objective is true score gain; if the optimum is zero, its secondary objective returns the largest neutral record-tie mother and continues unrestricted net-+1 search through radius 5 in the same runner.

No result from that downstream workflow is claimed here until it completes and, for any score above 134,753, passes the upstream Few Shots verifier.
