# Exact seven-owner support-gap frontier

Status: **no verified score above 134,753**. This note freezes the exact seven-owner support-graph census, its irreducibility reduction, and the completed downstream global-union prize optimization so later work does not repeat the 8.7-million-state enumeration.

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

The 12 irreducible complete support pools have sizes 22 through 26. Their audited union is small enough for a direct global ten-dimensional prize optimization rather than another radius-style census.

## Completed global irreducible-union optimization

GitHub Actions run **`40996847699`**, job **`123871843359`**, completed successfully. It replayed the 611-to-12 irreducibility reduction, optimized the union of all 12 irreducible support pools against all 18 record terminal scenarios, verified the resulting optimum upstream, and then continued unrestricted local search from the returned record-tie mother.

Exact global prize result:

- irreducible owner sets: **12**;
- union factor pool: **89** five-dimensional vertices after complete-pool union used by the optimizer;
- terminal scenarios: **18**;
- best selected noncore points: **26**;
- corresponding deleted blockers/core points: **26**;
- exact gain: **0**;
- candidate score: **134,753**;
- candidate variables in the winning scenario: **7,480**;
- conflict edges: **403,401**;
- touched blockers: **1,913**.

The resulting 134,753-point ten-dimensional set was accepted by the Few Shots p004 verifier with canonical hash

`8de1e3357cdec564c3a189f2d903ff46bbee82e64517a6febb0d1cbba1b6646c`.

The global optimization used four worker processes and finished its prize stage in about 6m56s wall time at about 368% CPU, peak RSS about 0.93 GiB. This is an exact record tie, not an improvement.

## Exact local search from the new tie mother

The same runner continued with unrestricted ten-dimensional net-+1 searches.

Radius through 4:

```json
{"kind":"none","method":"exact-unrestricted-net1-r4-complete","baseline_size":134753,"coverage0":0,"coverage1":4313,"coverage2":149855,"coverage3":997983,"coverage4":2127628,"support2_groups":141029,"support3_groups":968112,"support4_groups":2074502,"owner4_checked":10791510,"eligible_owner4":596248,"max_supported_pool":16}
```

Radius 5, direct support-5 stratum:

```json
{"kind":"none","method":"exact-unrestricted-net1-r5-direct-c5","baseline_size":134753,"coverage0":0,"coverage1":4313,"coverage2":149855,"coverage3":997983,"coverage4":2127628,"coverage5":2556156,"coverage2_groups":141029,"coverage3_groups":968112,"coverage4_groups":2074502,"coverage5_groups_checked":2490333,"eligible_groups":152782,"max_supported_pool":21}
```

Radius 5, connected lower-support stratum:

```json
{"kind":"none","method":"exact-unrestricted-net1-r5-connected-lower-support","baseline_size":134753,"coverage0":0,"coverage1":4313,"coverage2":149855,"coverage3":997983,"coverage4":2127628,"coverage2_groups":141029,"coverage3_groups":968112,"coverage4_groups":2074502,"generated_calls":252961219,"unique_owner5_checked":108273120,"eligible_owner5":7869646,"max_supported_pool":21}
```

Therefore this new k7-union record-tie basin is also exactly closed against unrestricted net-+1 exchanges through radius 5.

## Consequence / next step

The isolated k7 irreducible-union family is closed at gain zero, and its returned tie mother has no unrestricted local improvement through radius 5. The useful next representation is not a larger radius inside this same family. Current active work instead jointly optimizes multiple qualitatively different support families (`k=5`, all 32 `k=6` cover-gap pools, and the 12 irreducible `k=7` pools) against the full terminal union, while a separate line attacks the unresolved `C7^5` 368 problem directly.
