# O=58, K=16: exact exclusion of four extreme compression splits

Date: 2026-11-04

## Scope

For length-100 LABS, odd-energy O=58 is normalized to parity-half sums (a,b)=(2,2). At compression norm K=16 (m=-9) the exact breakthrough-energy condition E<=574 requires Q+R<=24, hence Q<=24, where Q=sum(U_r^2), R=sum(V_r^2).

This note **excludes the four splits** (kp,kc)=(1,15),(3,13),(13,3),(15,1). It does **not** claim the entire K=16 layer is excluded; the central four splits remain.

## Clean GitHub Actions reproduction

- Workflow: `.github/workflows/temp-labs100-o58-k16-extremes-20261104.yml`
- Commit: `96904d8e2d064621902f368a8deabb033f82a4ff`
- Run: `41719753889`, job `126209086296`, completed **success**
- Artifact: `labs100-o58-k16-extremes`
- Tools: `code/o58_k16_compressed_exact.cpp`, `code/o58_k16_qgroup_exact.cpp`, and `code/odd_energy_defect_projection.py`
- Runner: one `ubuntu-latest`; independent branch processes via `xargs -P $(nproc)`, with one OpenMP thread each.

The 18 enumerated branches consist of 3 for kp=1, 6 for kp=3, 6 for kp=13, and 3 for kp=15. Every compressed producer line `qhits=` was checked against the actual emitted `HIT` line count before the fibre oracle ran, so no retained-candidate cap affected this campaign.

The program enumerates support-difference affine orbits, signed compressed periodic equations with the exact one-sparse RHS, and the qmin<=24 bound. For each compressed survivor support orbit, the second program enumerates all negacyclic binary fibres modulo the common sign, using the corresponding sparse RHS, and computes the necessary identity

    2Q = SG + SH,

where SG is the sum of squared 12 independent periodic PAF coefficients and SH is the corresponding negacyclic fibre sum. For each support group it uses min SG over its compressed candidates. Consequently, groupwise min SG + any SH>48 is a conservative exact exclusion even though the minimizing compressed candidate and the given fibre need not be compatible.

## Frozen full run summary

| kp | kc | t | defect | compressed hits | fibre groups | Q passes | minimum SG+SH-48 |
|---:|---:|---:|---|---:|---:|---:|---:|
| 1 | 15 | 0 | unit | 76 | 69 | 0 | 38 |
| 1 | 15 | 0 | five | 20 | 16 | 0 | 62 |
| 1 | 15 | 1 | center | 18 | 8 | 0 | 38 |
| 3 | 13 | 0 | unit | 790 | 667 | 0 | 50 |
| 3 | 13 | 0 | five | 185 | 164 | 0 | 34 |
| 3 | 13 | 1 | center | 238 | 124 | 0 | 34 |
| 3 | 13 | 2 | unit | 1414 | 1246 | 0 | 34 |
| 3 | 13 | 2 | five | 446 | 365 | 0 | 34 |
| 3 | 13 | 3 | center | 132 | 55 | 0 | 22 |
| 13 | 3 | 0 | unit | 790 | 667 | 0 | 50 |
| 13 | 3 | 0 | five | 185 | 164 | 0 | 34 |
| 13 | 3 | 1 | center | 238 | 124 | 0 | 34 |
| 13 | 3 | 2 | unit | 1414 | 1246 | 0 | 34 |
| 13 | 3 | 2 | five | 446 | 365 | 0 | 34 |
| 13 | 3 | 3 | center | 132 | 55 | 0 | 22 |
| 15 | 1 | 0 | unit | 76 | 69 | 0 | 38 |
| 15 | 1 | 0 | five | 20 | 16 | 0 | 62 |
| 15 | 1 | 1 | center | 18 | 8 | 0 | 38 |

Minimum reported necessary-budget margin was **22** (the target SG+SH cap is 48). No Q pass occurs; therefore no full-length witness rescore is needed for these four splits.

## Independent check and research implication

`code/o58_k16_singleton_census.cpp` directly enumerates every normalized support/sign pattern at kp=1, kc=15 without the main compressed solver's affine quotient. It finds nonzero periodic qmin survivors in all three defect types, so the periodic equations alone cannot exclude the split. The fibre-Q exclusion is an actual additional obstruction.

Current next work: examine central splits (kp,kc)=(5,11),(7,9),(9,7),(11,5) using a producer that cannot truncate emitted compressed hits; exploit exact p/c-swap symmetry only for necessary Q-level exclusion, but retain both orientations for any full aperiodic witness search. If the middle combinatorics grows too fast, switch to the dual K34 sparse-fibre representation rather than replaying the same enumeration at larger budget.

No E<=574 candidate was found.
