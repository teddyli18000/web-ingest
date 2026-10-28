# Ramsey R(4,6) lower bound

## Question

Can we construct a graph on at least 36 vertices with neither a 4-clique nor an independent set of size 6? A 36-vertex certificate would prove `R(4,6) >= 37`, improving the public lower bound.

This directory is the durable research workspace for Few Shots `p003-ramsey-r46`. Exploratory code, evidence, failures, and search artifacts stay here. Only a fully verified final `certificate.json` and `SHOT.md` belong in the Few Shots repository.

## Current state

- **Target:** first verified `(4,6)` graph on 36 vertices.
- **Public state rechecked 2026-10-28:** `36 <= R(4,6) <= 40`; no public 36-vertex construction found. Radziszowski revision #18 (2026) and McKay's live collection still list Exoo's 35-vertex examples as the largest known.
- **Few Shots record:** 35 vertices, epsilon +1; no merged p003 shot beyond the baseline.
- **All 37 published Exoo 35-vertex graphs are exactly non-extendable with the old core frozen.** Two independent exact formulations agree; `results/extension-all-37.json`.
- **Few Shots baseline old-core shell is exactly UNSAT through radius 8** when the new vertex is completely free. Radius 16 and 32 timed out, so the proven statement is only `<=8`. Any solution based on that labelled core needs at least nine old-old edge changes.
- **All undirected abelian Cayley graphs on 36 vertices are exactly ruled out.** Two independent exhaustive implementations agree across all four abelian group types; 1,572,864 group-specific connection sets total, zero valid. `results/abelian-cayley36.json`.
- **Best retained 36-vertex near-miss:** 14 defects = 10 K4 + 4 independent 6-sets, `results/algorithm22-calibration-best-14.json`.
- **The complete labelled edge-Hamming ball through radius 14 around that near-miss is exactly UNSAT.** Radius 14 used CaDiCaL195, 19 separator iterations, 1760 learned Ramsey clauses, 2515.03 s; `results/nearmiss-14-radius14.json`. Therefore any valid labelled graph is at distance at least 15 from this seed. Radii 16 and 20 are still running in Actions run `40609878390`.
- **Semiregular cyclic automorphism SAT:** orders 18 and 12 are exactly UNSAT; orders 6 and 9 are still running in `40613531660`. `results/semiregular-sat-partial-12-18.json`.
- **Degree 17 remains the main exact endpoint.** Seven complete `(3,6,17)` neighborhood types are known. Static v1 `40608016453`, degree-bounded v2 `40610327410`, and the automorphism-aware v3 index-5 branch `40613113896` are active.
- **All-37 old-core radius-2 exact sweep** is running as `40614294523`.
- **Exoo core 37 V4 symmetry SAT** is queued as `40615812735`; it fixes the recovered `V4` action `4^6 2^5 1^2` on 36 vertices, leaving 180 edge-orbit variables.
- **No valid 36-vertex certificate has been found yet.**

## Why this may be frontier-level

Exoo raised the lower bound to 36 in 2012 by constructing 37 graphs on 35 vertices. Radziszowski's 2026 survey still lists the lower bound as 36 and the upper bound as 40. Nagda, Raghavan, and Thakurta (2026, arXiv:2603.09172v5) report that AlphaEvolve recovered the state of the art for `R(4,6)` but did not improve it.

Exoo's Method B is particularly relevant: an unusual valid 34-vertex graph `G1` had a high induced-`P4` count and favorable full four-vertex profile, then extended immediately to 35 vertices. The 37 known 35-vertex graphs are closely related to that basin. `methodb36.cpp` already embeds Exoo's full 11-class `G1` profile and supports defect-only, P4-shaped, and full-profile tabu search, so do not reimplement that objective without a materially new idea.

## Structural facts

Every hypothetical `(4,6,36)` graph has degree between 11 and 17:

- `deg(v) <= 17` because `N(v)` is a `(3,6)` graph and `R(3,6)=18`;
- `deg(v) >= 11` because the non-neighborhood is a `(4,5)` graph and `R(4,5)=25`.

At degree 17, `N(v)` must be one of exactly seven known `(3,6,17)` graphs. At degree 11, the 24 non-neighbors must be one of McKay's complete 352,366 `(4,5,24)` graphs. The seven degree-17 neighborhood representatives have automorphism-group sizes `[1,2,2,2,2,8,2]`; v3 therefore focuses its symmetry work on index 5.

Any valid 36-vertex graph also yields an **extendable valid 35-vertex core** after deleting any vertex. This makes searching for new 35-point cores principled. Preliminary local searches that perturb known cores and return to feasibility, however, collapsed back into the known 37 isomorphism classes even along a 21-edge path, so merely “find another nearby valid 35-core” is low priority unless novelty or extension potential is explicitly optimized.

## Exact negative results

### All 37 published 35-vertex cores

For a fixed valid 35-vertex graph `G`, a new vertex with neighborhood `S` is valid iff `S` contains no triangle of `G` and hits every independent 5-set of `G`. `extension_check.py` solves this both as CNF/DPLL and direct hitting-set branching.

- graphs checked: 37
- direct frozen-core extensions: 0
- independent exact formulations agree
- triangle counts: 375..395
- independent-5 counts: 742..818
- artifact: `results/extension-all-37.json`

`extension_maxsat.py` softens the clauses to rank cores; two completed RC2 instances both have exact optimum 18 conflicts. This is expensive and currently low priority.

### Few Shots baseline old-core shells

`lazy_shell_search.py` keeps the new vertex free while bounding changes among the original 35 vertices.

- radius 2: UNSAT
- radius 4: UNSAT
- radius 8: UNSAT, about 4302 s / 55 separator rounds
- radii 16 and 32: timed out, inconclusive

The corresponding durable logs are `results/shell-baseline-r02.txt`, `r04.txt`, `r08.txt`, `r16.txt`, and `r32.txt`.

### Complete abelian Cayley exclusion

`abelian_cayley36.cpp` and independent `abelian_cayley36_check.py` exhaust all undirected Cayley connection sets on all abelian groups of order 36:

| group | inverse orbits | connection sets | K4-free | valid |
| --- | ---: | ---: | ---: | ---: |
| `C36` | 18 | 262144 | 17859 | 0 |
| `C4 x C3 x C3` | 18 | 262144 | 25614 | 0 |
| `C2 x C2 x C9` | 19 | 524288 | 25529 | 0 |
| `C2 x C2 x C3 x C3` | 19 | 524288 | 34340 | 0 |

The two implementations agree exactly on every row. See `results/abelian-cayley36.json`.

### Semiregular cyclic symmetry

`semiregular_sat.py` fixes a cyclic automorphism consisting only of equal-length cycles and identifies edge variables by its orbits; the K4/I6 CNF is otherwise complete.

- order 18: 36 variables, 105705 clauses, UNSAT, about 3.02 s
- order 12: 54 variables, 162808 clauses, UNSAT, about 6m23s
- orders 6 and 9: still running in `40613531660`

This is strictly wider than the cyclic Cayley scan because the action need not be regular.

### Full-edge ball around the 14-defect seed

The original 14 conflicts have repair hitting number four. Independent explicit local enumeration exhausted radii 6 and 7; lazy SAT then proved progressively larger complete labelled Hamming balls UNSAT.

- radius 12: UNSAT, 248.30 s, 11 separator iterations, 1198 learned clauses
- radius 14: UNSAT, 2515.03 s, 19 iterations, 1760 learned clauses
- radii 16 and 20: active in `40609878390`

Durable records: `results/nearmiss-14-radius12.json` and `results/nearmiss-14-radius14.json`.

## Active exact routes

1. **Degree-17 static SAT.** v1 fixes each of the seven complete `(3,6,17)` neighborhoods; v2 adds exact safe degree bounds `11..17`; v3 adds a sound Aut(A) lex leader and currently targets index 5, whose neighborhood automorphism group has order 8.
2. **Near-miss Hamming balls.** Finish radii 16 and 20. Any SAT model is automatically sent to the Few Shots verifier.
3. **All-37 exact old-core shells.** `40614294523` applies radius 2 to every authenticated Exoo core instead of only the Few Shots baseline. If all are UNSAT, radius 4 is the natural next exact sweep.
4. **Semiregular automorphism SAT.** Finish orders 6 and 9; if both are UNSAT, consider orders 2, 3, and 4 when compute slots free.
5. **Exoo core-37 V4 action.** `core37_v4_sat.py` uses the recovered order-4 action from the most symmetric public 35-point core, with the added vertex as a second fixed point. The resulting exact 36-point family has 180 edge-orbit variables and about 499k distinct Ramsey clauses; run `40615812735`.

## Heuristic routes and dead ends

- `walksat36.cpp` all-37 sweep performed about 23.1 billion full-graph steps and reached best 15 defects, not better than the retained 14.
- A second Method-B basin starting from the all-core 15-defect graph also remained at 15 after long defect/P4/profile lanes.
- Randomized 15-regular and cyclic-seed Method-B campaigns have not produced a zero-defect graph.
- Tatarevic's 2014 structured 35-point near-miss was reconstructed as `K4=0`, `I6=7`; a quick 36-point repair search underperformed the current seed, so it is low priority without a stronger formulation.
- Full-CNF Kissat with only fixed degree 11..17 timed out in every four-hour branch; this is inconclusive, not a proof.
- The first degree-17 lazy separator timed out because it repeatedly enumerated six-subsets and left B labels symmetric; static encodings supersede it.
- Degree-11 catalogue statistics contain 30,395 `(3,6,11)` types and 352,366 `(4,5,24)` types. A simple total-cross-edge filter rejects none, so naive all-pairs gluing is not viable.
- Preliminary **core-preserving** 36-point tabu, where the first 35 vertices are forced to stay valid and only extension defects are optimized, reached best 15. Preserve the idea but do not prioritize unless it yields a basin below 14.

## Verification discipline

A candidate counts only after all of the following:

1. exact internal K4 / independent-6 recount;
2. independent implementation or exact-solver recheck;
3. Few Shots p003 verifier returns `valid:true`, score at least `36`;
4. live literature/public-record recheck;
5. Few Shots `tools/check.py` returns exit code 0 against current `main`;
6. exact certificate and provenance are frozen before submission.

If a valid 36-vertex graph appears, stop exploratory optimization immediately and follow this path.

## Next steps

1. Consume `40615812735`, `40614294523`, `40613531660`, `40609878390`, `40613113896`, and the degree-17 v1/v2 runs. Persist every exact UNSAT result immediately; verify any SAT model immediately.
2. If semiregular orders 6 and 9 are UNSAT, extend the same exact family to orders 2, 3, and 4.
3. If all 37 cores are UNSAT at old-edge radius 2, launch radius 4 across the family rather than expanding only the first core again.
4. If degree 17 is completely UNSAT under a sound encoding, record the structural consequence `Delta <= 16` and redirect exact work toward degree 11/16 endpoints.
5. Freeze and submit any zero-defect certificate immediately after the full verification chain.

## Durable artifacts

- `extension_check.py`, `results/extension-all-37.json` — exact direct-extension sweep.
- `extension_maxsat.py`, `results/extension-maxsat-partial.json` — partial exact frozen-core soft optimization.
- `lazy_shell_search.py`, `results/shell-baseline-r*.txt` — exact old-core shells.
- `circulant36.cpp`, `results/circulant36-best-seed.json` — cyclic exhaustive scan and best cyclic seed.
- `abelian_cayley36.cpp`, `abelian_cayley36_check.py`, `results/abelian-cayley36.json` — complete abelian Cayley exclusion.
- `semiregular_sat.py`, `results/semiregular-sat-partial-12-18.json` — wider exact symmetry search.
- `core37_v4_sat.py` — exact V4 action derived from Exoo core 37.
- `degree17_static_sat.py`, `degree17_static_sat_v2.py`, `degree17_static_sat_v3.py` — degree-17 exact encodings.
- `degree11_catalog_stats.py`, `results/degree11-catalog-stats.json` — degree-11 endpoint catalogue statistics.
- `methodb36.cpp`, `walksat36.cpp`, `random_regular36.py` — self-tested heuristic searchers.
- `results/algorithm22-calibration-best-14.json` — retained invalid 14-defect near-miss.
- `nearmiss_cover.py`, `lazy_ball36.py`, `results/nearmiss-14-radius12.json`, `results/nearmiss-14-radius14.json` — exact local exclusions.
- `notes/algorithm22-calibration.md`, `notes/symmetry-search-2026-10-28.md` — literature calibration and symmetry-search handoff.

## Sources

- Few Shots p003: https://github.com/few-shots/few-shots/tree/main/problems/p003-ramsey-r46
- S. Radziszowski, *Small Ramsey Numbers*, EJC Dynamic Survey DS1, revision #18 (2026).
- G. Exoo, *On the Ramsey Number R(4,6)*, EJC 19(1) (2012), P66, DOI 10.37236/2102.
- G. Exoo public 37-coloring collection: https://cs.indstate.edu/ge/RAMSEY/R46/index.html
- B. McKay, Ramsey graph collection: https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
- M. Tatarevic, public R(4,6) construction note (2014): https://mtatar.wordpress.com/2014/08/21/ramsey46/
- A. M. Lehavi, *Ramsey Number Counterexample Checking and One Vertex Extension Linearly Bound by s and t*, arXiv:2411.04267 (2024).
- A. Nagda, P. Raghavan, A. Thakurta, *Reinforced Generation of Combinatorial Structures: Ramsey Numbers*, arXiv:2603.09172v5 (2026).

## Work log

### 2026-10-28

- Rechecked the live public record: still `36 <= R(4,6) <= 40`, with no public 36-point construction found.
- Consolidated exact direct-extension UNSAT for all 37 public cores and discovered the baseline old-core shell was already exhausted through radius 8.
- Exhausted every undirected abelian Cayley graph on 36 vertices with two independent implementations.
- Proved the retained 14-defect seed's complete labelled Hamming ball through radius 14 UNSAT; radii 16 and 20 continue.
- Launched/continued degree-17 static SAT v1/v2/v3.
- Proved semiregular cyclic automorphism orders 18 and 12 UNSAT; orders 6 and 9 continue.
- Launched exact radius-2 old-core shells across all 37 authenticated Exoo cores.
- Recovered the V4 action of public core 37 (`4^6 2^5 1`) and launched an exact 36-vertex V4-invariant SAT with the new vertex fixed.
- Re-read Exoo Method B and confirmed `methodb36.cpp` already encodes the full G1 four-vertex profile; local searches for new feasible 35-point cores fell back into known isomorphism classes.
- Preserved multiple heuristic negative results rather than repeating the same 14/15-defect basins.

### 2026-10-27

- Read and followed Few Shots plus `science-boundary` repository rules; established this durable topic on `main`.
- Exhausted direct extension of all 37 Exoo 35-vertex graphs with two independent exact formulations.
- Exhausted all 36-vertex circulants.
- Calibrated Algorithm-22-style local search and found the retained 14-defect near-miss.
- Froze that near-miss, proved its first local repair balls impossible, and started progressively larger exact Hamming-ball searches.
