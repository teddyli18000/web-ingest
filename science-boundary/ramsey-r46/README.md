# Ramsey R(4,6) lower bound

## Question

Can we construct a graph on at least 36 vertices with neither a 4-clique nor an independent set of size 6? A 36-vertex certificate would prove `R(4,6) >= 37`, improving the public lower bound.

This directory is the durable research workspace for Few Shots `p003-ramsey-r46`. Exploratory code, evidence, failures, and search artifacts stay here. Only a fully verified final `certificate.json` and `SHOT.md` belong in the Few Shots repository.

## Current state

**NEW construction record within this workspace (2026-11-08): 36 vertices, 12 forbidden subgraphs (12 K4, 0 I6), 260 edges.** The prior near miss was 14 defects (10 K4 + 4 I6), 263 edges. The new candidate \`results/compound-repair-36-12-defects.json\` was found by conflict-cascade delayed-acceptance macro-moves and independently enumerated over all 36-vertex 4/6-subsets; it is **NOT** a valid Ramsey witness and does **NOT** change the established \(R(4,6)\) lower bound. A fixed-seed source \`compound_repair_search.py\` reproduces 14→13 at step 135 and 13→12 at step 136. This is the first verified candidate improvement across the last several rounds. To exploit it, \`elite12_lns_sat.py\` jointly resynthesizes selected vertex neighborhoods with an explicit SAT budget of **at most 11 total violations**; twelve diverse concurrent cases in [42504776739](https://github.com/teddyli18000/web-ingest/actions/runs/42504776739), subject to independent full-graph recount. Reproduction Action: [temp-ramsey-r46-repro12.yml](https://github.com/teddyli18000/web-ingest/actions/workflows/temp-ramsey-r46-repro12.yml). See \`notes/compound-repair-breakthrough-2026-11-08.md\` for full evidence, limitations, and handoff.


**Construction-first update (2026-11-08).** Verified record **unchanged**: 35 vertices; best retained 36-vertex near miss **14 forbidden sets** (10 K4 + 4 I6). The latest search changes its decomposition, not merely its random seed: vertex 3 of the near miss has a valid 13-vertex triangle-free neighborhood and a valid 22-vertex K4-free/I5-free antineighborhood; **all 14 violations cross the interface**. A corrected root-aware SAT encoding passed two explicit 35-point known-answer tests ([42501506877](https://github.com/teddyli18000/web-ingest/actions/runs/42501506877)); a direct fixed 286-edge root repair returned UNKNOWN, not UNSAT. New construction campaigns jointly rewire the A/B interface *and* selected interior edges using full static CNF ([42501283478](https://github.com/teddyli18000/web-ingest/actions/runs/42501283478)), try different rooted partitions ([42501739284](https://github.com/teddyli18000/web-ingest/actions/runs/42501739284)), and use weighted MaxSAT to search for an exact defect count **below 14** ([42502080443](https://github.com/teddyli18000/web-ingest/actions/runs/42502080443)). Earlier fixed-half and lazy variants repeatedly timed out without improving the candidate, so do not scale them blindly. The original root-aware CardEnc auxiliary-variable bug has been fixed. Reproducible current handoff: \`notes/constructive-rooted-interface-2026-11-08.md\`.


**Construction-first reassessment (2026-11-07):** No valid 36-vertex witness yet; the verified best 36-vertex near-miss remains **14 forbidden sets** (10 K4 + 4 I6). The exact 46-way 30-core / 6-tail representation is now implemented (\`cross_core_six_tail_repair.py\`) and its 276,000-proposal six-runner campaign [42455217975](https://github.com/teddyli18000/web-ingest/actions/runs/42455217975) completed without improving 14. This is a sampled construction experiment, not an exhaustive exclusion. **Positive-control breakthrough in method:** a new CaDiCaL195 independent-halves constructor (\`independent_halves_cadical.py\`) recovered valid 35-vertex graphs from two 17/18-point halves with **all 306 cross edges hidden**; Actions [42456135866](https://github.com/teddyli18000/web-ingest/actions/runs/42456135866) confirmed at least two SAT/recount successes (247 and 248 edges). That experiment also tests independently sampled **18+18 halves** (324 cross edges) from distinct public 35-point parents. A second running Action [42456264481](https://github.com/teddyli18000/web-ingest/actions/runs/42456264481) tests two overlapping 18-point halves from the same 35-point graph with its shared vertex duplicated.  A third constructive Action [42456461164](https://github.com/teddyli18000/web-ingest/actions/runs/42456461164) joins 17+18 cores from **distinct** public 35-point graphs to create new valid 35-point parents, immediately testing each for an exact 36-point extension and novel triangle/I5 fingerprint. The current objective remains a constructive n=36 SAT certificate, **not further nonexistence exclusions**. Full current reproducible handoff: \`notes/construction-reassessment-2026-11-07.md\`.


**Construction-first campaign (2026-11-06):** A new *joint vertex-regrowth* SAT searcher, \`constructive_regrow.py\`, is committed and live on two seed families in Actions run [42255847873](https://github.com/teddyli18000/web-ingest/actions/runs/42255847873). Rather than certifying more nonexistence ranges, this campaign fixes distinct 22–26-vertex induced cores from the published valid 35-vertex graph or our 14-defect 36-vertex seed, and jointly regenerates all edges incident on 10–14 selected vertices. Two parallel matrix jobs schedule 96 randomized full-graph synthesis attempts each, using three solver processes per job. **Only a found and independently recounted 36-vertex certificate counts as progress to the target.** A toy six-vertex SAT case returned a witness and independent recount passed. Local full-size tests: 2, 3, 4, 6, and 8-vertex repairs returned UNSAT for specified frozen cores; 10-vertex repairs timed out. Neither observation constitutes a new global Ramsey bound. The full 36-vertex run is active; no new witness yet. See \`notes/takeover-low-interface-2026-11-06.md\` for prior handoff.


**New post-audit seq2 filter (2026-11-06).** At m=220 and degree sequence `11^6 12^17 13^12 14`, the complete B88 low-anticomplete scan forbids **every degree-13 vertex with S=164**: its B88 component would contain >=4 other high vertices anticomplete to all six lows, but the verified maximum is 3. Consequently the 137 integer degree-class matrices reduce to 18. The unique degree-14 vertex has at most eight high neighbors (triangle-free neighborhood + R(3,4)=9 and alpha(high)<=3), reducing this to **8 matrices** (6 for low boundary R=22, 2 for R=24). Furthermore each degree-12 vertex sees at least two lows; if exactly two, it necessarily sees five degree-13 vertices, no degree-14 vertex, and has S=147. This forces at least 7 or 9 such middles for R=22 or 24. Script: `m220_n11_6_seq2_structural_verify.py`; output: `results/m220-n11-6-seq2-structural-post-audit.json`. **These are necessary conditions, not an exclusion.** Seq2 remains the sole unresolved n11=6 sequence; other m220 n11 layers remain open. No new 36-point witness.


**New exact exclusion (2026-11-05): m=220, n11=6 seq1 is impossible.** For the post-audit R=22/24 low-graph orbits, the six degree-11 lows have no neighbours among the fourteen degree-13 highs, and send respectively 44/42 edges to sixteen degree-12 middle vertices. Therefore some middle vertex meets at most two lows. The independently certified no-lucky-d12 bound S<=147 then forces at least nine high non-neighbours; the middle vertex also misses at least four lows. R(4,3)=9 and K4-freeness produce an independent triple among the high non-neighbours and an independent pair among the low non-neighbours; adding the middle vertex gives an independent 6-set, contradiction. Standalone stdlib verifier: `m220_n11_6_seq1_pigeonhole_verify.py`; certificate: `results/m220-n11-6-seq1-pigeonhole-post-audit.json`. With independently re-proved seq3/4/5 and seq6–14 exclusions, **only seq2 (11^6 12^17 13^12 14) remains unresolved within the n11=6 layer**. Other m=220 degree-11-count layers remain open. This is not a new Ramsey bound or a 36-point construction.


**Latest exact progress (2026-11-04):** The m=220, n11=6 **seq3 is now fully excluded** by a short post-audit extreme B88 packing / high-subgraph capacity contradiction. Independent Python and C++ bitset verifiers agree (170 -> 10 -> 0 class matrices); see \`m220_n11_6_seq3_high_packing_verify.py\`, \`m220_n11_6_seq3_independent.cpp\`, \`results/m220-n11-6-seq3-high-packing-post-audit.json\`, and \`notes/m220-seq3-high-packing-2026-11-04.md\`. **Only seq1 and seq2 remain within the six-degree-11-vertex layer**; other m=220 layers remain open and there is no 36-vertex certificate.


**Latest exact progress (2026-11-04):** m=220, n11=6 **seq5 is now fully excluded**, independently of the withdrawn row-domain CSP. The complete B88 low-set packing bound forces each extreme d13 vertex to have exactly one d14 neighbor, contradicting all 84 class-edge matrices (smallest gap 1). See `m220_n11_6_seq5_extreme_packing_verify.py`, `m220_n11_6_seq5_independent.cpp`, `results/m220-n11-6-seq5-extreme-packing-post-audit.json`, and `notes/m220-seq5-extreme-packing-2026-11-04.md`. **Only seq1, seq2, seq3 remain within the n11=6 layer.** Other m=220 layers remain open; there is no 36-vertex witness.


**Post-audit frontier (2026-11-04).** The older 2026-10-28 status bullets below are historical; current exact evidence excludes every 36-vertex edge count through 219. At 220 edges, the independently certified degree-11 low-graph and class-edge arguments exclude n11=1..5; among the fourteen n11=6 degree sequences, indices **4 and 6–14 are excluded**; only **1, 2, 3 remain open**. Other n11 layers are not covered by these n11=6 statements. See `notes/frontier-post-audit-2026-10-30.md` and `results/m220-n11-6-class-boundary-post-audit.json`.

**Seq4 is now fully excluded (post-audit exact finite proof).** The prior high-anchor certificate left four degree-class matrices. The complete R(3,4,7/8) catalogue (9 and 3 types) plus exhaustive 12-high-vertex enumeration reduces these to three high-only cases. Their 13,647, 708 and 2,256 K4/independence-feasible labelled configurations have **zero** survivors under the independently audited B88 extreme-pair support constraint. The C++ verifier and independent Python catalogue checker were run locally and their byte-identical source files are committed: `m220_n11_6_seq4_high_exact.cpp`, `m220_n11_6_seq4_t_catalog_verify.py`; see `results/m220-n11-6-seq4-high-exact-post-audit.json` and `notes/m220-seq4-high-exact-2026-11-04.md`. This closes only seq4, **not** all 220-edge graphs. No new Few Shots witness.

**New verified seq4 necessary condition.** For degree sequence `11^6 12^18 13^11 15`, at least four degree-13 vertices have `S(v)=164`; every nonadjacent pair of these extreme vertices forces the unique B88 graph type #0 at both endpoints, with exactly six common neighbors. The three complete B88 graphs give induced-neighborhood compatibility counts `[4,0,0]`, independently checked by two isomorphism routines. This **does not** eliminate seq4. Reproduce with `m220_n11_6_seq4_b88_embed_verify.py`; exact output: `results/m220-n11-6-seq4-b88-embedding-post-audit.json`. Do not use the withdrawn old row-domain `tf()` results.


> **Post-audit frontier — 2026-11-04.** The 2026-10-28 Action/run-status bullets
> below are historical, not the current queue status. A corrected row-domain
> predicate was audited in commit `e99119c`; all proof claims depending on
> the old predicate were withdrawn. Independent post-audit certificates restore
> a complete **m <= 219** edge-count exclusion. For **m=220**, all sequences
> with 1–5 degree-11 vertices have sound recursive exclusions. With exactly
> six degree-11 vertices there are 14 structural degree sequences; exact
> universal low-graph/class bounds plus separate sound proofs eliminate
> seq6–14 (historical snapshot). **The newer proof also excludes seq4; only seq1,2,3 remain unresolved.** New verifier
> `m220_n11_6_seq4_high_anchor_verify.py` reduces seq4 from 32 class-edge
> matrices to **four** without SAT or the withdrawn row predicate; see
> `results/m220-n11-6-seq4-high-anchor-post-audit.json` and
> `notes/m220-seq4-high-anchor-2026-11-04.md`. No verified 36-vertex
> witness has been found. The topic still targets a *lower-bound construction*;
> these exclusions only guide the search and are not a new upper bound.
>
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
