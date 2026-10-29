# C7^5 radius-6 closure and basin-recombination exclusions

Status: exact negative results on the pinned Polak/BPZ 367-word parent and on several unions of known 367-word basins. These results do **not** prove `alpha(C7^5)=367`; they only close the explicitly stated search spaces.

## Source objects

The pinned BPZ/Tandon data are from `tandonravi/C7-Shannon-Capacity-Heterogeneous-Recursion`, commit `c753408492dde92a239708986d16c15dbf6c3235`, `data/base_c7.json`.

- `I0`: the 367-word Polak/Schrijver-style parent in the BPZ/Tandon profile.
- `X`: the 367-word companion independent set in the same file.
- `F`: the public Family-F 367-word witness from `molind/c7-five`, commit `ae81e0d24b356aef3d388238f6fb4d02c4aa32a5`.
- Family-F has 36 size-367 states, common core size 360, total union size 374.

All words use the standard base-7 integer encoding in `[0,7^5)`.

## Exact blocker-support census around `I0`

For every outside vertex `v`, let `B(v)` be the set of incumbent `I0` words that conflict with `v`. The full outside-vertex support-size distribution is:

| support size | outside vertices |
|---:|---:|
| 1 | 8 |
| 2 | 254 |
| 3 | 1,505 |
| 4 | 3,039 |
| 5 | 3,712 |
| 6 | 3,897 |
| 7 | 2,842 |
| 8 | 921 |
| 9 | 199 |
| 10 | 61 |
| 11 | 2 |

There are no support-0 vertices. The support-at-most-6 universe contains 12,415 outside vertices in 12,100 distinct blocker-support groups.

Previously available exact work closes improving exchanges through deletion radius five. Therefore any hypothetical remove-6/add-7 witness must use exactly six incumbent owners, and its selected blocker-support hypergraph must be connected: a disconnected component with more additions than owners would itself give an improving exchange at smaller radius.

## Complete radius-6 partition

The radius-6 search is partitioned by the maximum blocker-support size among the seven selected additions. In every final six-owner set `U`, the solver reconstructs the **complete** candidate pool

`P(U) = { v outside I0 : B(v) subseteq U }`

and then performs an exact backtracking search for seven pairwise nonconfusable additions. Thus no final decision uses only an anchor-local approximation.

### Maximum support 6

Code: `code/c7p5_r6_direct.cpp`.

- distinct exact support-6 anchors: 3,719
- owner sets with complete pool size at least 7: 506
- largest complete pool: 14
- result: no independent 7-set
- reproduced wall time on the local 2026-10-29 environment: about 0.16 s

### Maximum support 5

Code: `code/c7p5_r6_c5.cpp`.

Completeness of generation: fix a selected size-5 support `A` and let `x` be the sixth owner. If `x` occurred in only one selected addition, the other six additions would be blocked by the five owners of `A`, contradicting the exact radius-5 negative result. Two independent singleton-support additions on the same owner are impossible in this construction, so some selected support contains `x` together with an owner already in `A`. It is therefore sufficient to attach `x` through real observed co-owner support incidence.

- distinct size-5 anchors: 3,650
- distinct generated six-owner sets: 532,048
- complete pools of size at least 7: 26,309
- largest complete pool: 14
- result: no independent 7-set
- reproduced wall time: about 11.7 s

### Maximum support 4

Code: `code/c7p5_r6_c4.cpp`.

Generation uses only real support crossings. From a selected size-4 anchor, the two missing owners are introduced either by two one-owner crossings or by one support that introduces both. Connectivity of the selected support hypergraph makes these cases complete.

- distinct size-4 anchors: 3,010
- distinct generated six-owner sets: 269,877
- complete pools of size at least 7: 31,620
- largest complete pool: 14
- result: no independent 7-set
- reproduced wall time: about 1.31 s

### Maximum support 3

Code: `code/c7p5_r6_connected.cpp` with argument `3`.

A generic connected-hypergraph expansion starts from every observed exact support-3 anchor and repeatedly crosses the current owner cut using a real observed support of size at most three. Owner-set states are deduplicated exactly.

- exact support-3 anchors: 1,469
- observed support hyperedges of size 2 or 3: 1,713
- visited owner-set states: 503,207
- distinct six-owner finals: 432,432
- finals with complete pool size at least 7: 63,594
- largest complete pool: 14
- result: no independent 7-set
- reproduced wall time: about 2.87 s

### Maximum support 2

Code: `code/c7p5_r6_connected.cpp` with argument `2`.

Here the support hypergraph is an ordinary graph. The same exact connected-state expansion enumerates every connected six-owner set supported by observed support-2 edges.

- support-2 anchors / graph edges: 244
- visited owner-set states: 32,971
- distinct six-owner finals: 23,758
- finals with complete pool size at least 7: 14,551
- largest complete pool: 14
- result: no independent 7-set
- reproduced wall time: about 0.15 s

### Radius-6 conclusion

All possible maximum-support strata `6,5,4,3,2` are negative. A support-1-only seven-addition witness cannot be connected across six owners, and the one-owner pools do not contain the needed independent multiplicity. Together with the earlier exact radius-at-most-5 exclusion, this closes **all improving exchanges deleting at most six words from this specific `I0` parent**.

This is a local exclusion around one 367-word basin, not a global upper bound on `alpha(C7^5)`.

## Exact recombination of known 367 basins

Several cheap arbitrary-radius recombination tests were also run before deciding not to scale the same family further.

### Pairwise Hall checks

For two size-367 independent sets, the conflict graph on their union is bipartite after identifying common physical vertices. Maximum independent set size is therefore obtained exactly from a maximum matching / minimum vertex cover calculation.

Direct pair checks were Hall-saturated at 367 for:

- `I0` versus `X`;
- `I0` versus one Family-F representative;
- `X` versus one Family-F representative.

For `I0` versus every relative translation of `X`, all **16,807** translations were checked exactly; every bipartite conflict graph had a perfect 367 matching. The same complete translation sweep was run for `I0` versus the Family-F representative and for `X` versus that representative; every translation remained saturated at 367.

For `I0` versus `X` with no translation, all `5! * 2^5 = 3,840` signed coordinate orientations were also Hall-saturated. The full orientation-times-translation Cartesian product was deliberately not scaled after candidate quality remained flat; that larger unsearched family must not be described as excluded.

The `molind/c7-five` archive already reports a completed translation-hybrid exclusion for its chosen C/F parents. The local sweeps here are recorded mainly to prevent repeating the same basin-pair mechanism.

### Multi-basin union MIS

Pairwise Hall saturation does not imply that three or more basins cannot recombine. We therefore solved the actual conflict graph on their physical union as a binary maximum independent-set MILP with SciPy/HiGHS; HiGHS returned a proven integer optimum with zero MIP gap.

1. `I0 union X union F`:
   - physical vertices: 1,053
   - conflict edges: 5,748
   - exact optimum: 367
   - local solve time: about 0.29 s

2. `I0 union X union (union of all 36 Family-F states)`:
   - Family-F total union: 374 vertices
   - total physical vertices: 1,060
   - conflict edges: 5,843
   - exact optimum: 367
   - local solve time: about 1.77 s

Thus arbitrary recombination inside this complete known-basin union still does not produce 368.

## Why we changed search space

The exact radius-6 extension did not improve the best 5D candidate, and the known-basin union remained pinned at 367. Per the project search policy, the next work should not simply extend the same local radius or multiply the same automorphism family indefinitely.

Current higher-leverage directions are instead:

- the reduced one-`BB`-hole model in ten dimensions, especially `code/bpz_one_core_hole_zero_deficit_2sat.py`;
- a controlled one-periphery-deficit extension of that 2-SAT formulation if zero-deficit is excluded;
- or a genuinely different 5D construction representation escaping the tested Polak/BPZ and Family-F basins.
