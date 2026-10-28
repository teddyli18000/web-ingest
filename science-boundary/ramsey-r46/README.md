# Ramsey R(4,6) lower bound

## Question

Can we construct a graph on at least 36 vertices with neither a 4-clique nor an independent set of size 6? A 36-vertex certificate would prove `R(4,6) >= 37`, improving the public lower bound.

This directory is the durable research workspace for Few Shots `p003-ramsey-r46`. Exploratory code, evidence, failures, and search artifacts stay here. Only a fully verified final `certificate.json` and `SHOT.md` belong in the Few Shots repository.

## Current state

- **Target:** first verified `(4,6)` graph on 36 vertices.
- **Few Shots record at start:** 35 vertices, epsilon +1; no merged p003 shot beyond the baseline.
- **Public state rechecked 2026-10-28:** `36 <= R(4,6) <= 40`; no public 36-vertex construction found. Radziszowski revision #18 (2026) and McKay's live Ramsey collection still describe Exoo's 35-vertex family as the largest known examples.
- **All 37 published Exoo 35-vertex graphs are exactly non-extendable by one frozen-core vertex.** Two independent exact solvers agree; see `results/extension-all-37.json`.
- **Every undirected circulant graph on 36 vertices is exactly ruled out.** Exhaustive scan of all `2^18=262144` masks found no solution. The best cyclic seed has mask `11459`, `K4=0`, `I6=72`, objective 72; frozen as `results/circulant36-best-seed.json`.
- **Few Shots baseline old-edge Hamming radius <=2 is exactly ruled out** with the new vertex free.
- **Best retained 36-vertex near-miss:** 14 defects = 10 K4 + 4 independent-6 sets, in `results/algorithm22-calibration-best-14.json`.
- **The complete labelled edge-Hamming ball of radius <=12 around that 14-defect near-miss is exactly UNSAT.** Radius 12 used CaDiCaL195, 11 separator iterations, 1198 learned Ramsey clauses, 248.30 s; see `results/nearmiss-14-radius12.json`. Hence any valid graph is distance at least 13 from this seed. Earlier independent enumeration also exhausts radii 6 and 7.
- **First all-37-core WalkSAT sweep:** best 15 defects, worse than the retained 14-defect seed.
- **Monolithic fixed-degree 11..17 Kissat sweep:** all branches timed out after four hours; this is inconclusive, not a negative proof.
- **Degree 17 is the main exact structural branch.** Seven complete `(3,6,17)` neighborhood types are known. Static SAT v1 is running as Actions run `40608016453`; a stronger v2 with exact safe degree bounds `11..17` and an exhaustively self-tested sequential counter is run `40610327410`.
- **Extended exact balls:** run `40609878390` has proved radius 12 UNSAT; radii 14, 16, 20 are still running.
- **Method-B / Algorithm-22 searches:** the first 12-lane shaped campaign from the 14-defect seed finished with no zero-defect hit; its collector is pending. Separate searches from the 15-defect all-core basin, randomized 15-regular basins, and the exhaustively best cyclic mask 11459 are active.
- **No valid 36-vertex certificate has been found yet.**

## Why this is frontier-level

Exoo raised the lower bound to 36 in 2012 by constructing 37 graphs on 35 vertices. Radziszowski's 2026 survey still lists the lower bound as 36, while the upper bound is 40. Nagda, Raghavan, and Thakurta (2026, arXiv:2603.09172v5) report that AlphaEvolve recovered the state of the art for `R(4,6)` but did not improve it.

Algorithm 22 of that work is particularly relevant: initialize from the best cyclic seed, minimize the unweighted objective `#K4 + #I6`, use exact common-neighborhood/common-nonneighborhood edge-flip deltas with tabu tenure about `N`, and apply a roughly 25% edge perturbation after low-cost stagnation. Exoo's earlier Method B also reports that induced four-vertex statistics, especially `P4`, were useful. `methodb36.cpp` combines exact defect deltas with optional `P4` or full 11-class induced-four-vertex shaping; its incremental bookkeeping is checked against complete recounts in randomized self-tests.

## Structural facts

A hypothetical `(4,6,36)` graph has degree between 11 and 17 at every vertex:

- `deg(v) <= 17` because `N(v)` is a `(3,6)` graph and `R(3,6)=18`;
- `deg(v) >= 11` because the non-neighborhood is a `(4,5)` graph and `R(4,5)=25`.

The degree-17 endpoint is rigid: `N(v)` must be one of exactly seven known `(3,6,17)` graphs. Fixing one representative on vertices `1..17` leaves 18 non-neighbors and a gluing problem. The degree-11 endpoint is also structured: the 24 non-neighbors must be one of McKay's complete catalogue of 352,366 `(4,5,24)` graphs.

## Exact one-vertex extension result

For a fixed 35-vertex `(4,6)` graph `G`, add a new vertex `x` and let `S=N(x)` among the old vertices. Then `G+x` is valid exactly when:

1. `S` contains no triangle of `G`;
2. `S` intersects every independent 5-set of `G`.

`extension_check.py` solves this finite 35-variable problem two ways: CNF/DPLL and direct hitting-set branching. All 37 published Exoo cores are UNSAT under both formulations. This rules out literal frozen-core extension only; a 36-vertex solution may require changing old-old edges.

`extension_maxsat.py` softens those clauses to rank frozen cores. A sequential exact RC2 campaign completed two cores before its two-hour workflow timeout; both optima are exactly 18 conflicts. Preserve but do not prioritize this expensive ranking; see `results/extension-maxsat-partial.json`.

## Exact negative results

### All 37 known 35-vertex cores

- graphs checked: 37
- direct one-vertex extensions: 0
- two independent exact formulations agree
- triangle counts: 375..395
- independent-5 counts: 742..818
- artifact: `results/extension-all-37.json`

### All 36-vertex circulants

`circulant36.cpp` exhausts all 262,144 undirected circulants on `Z_36`.

- valid: 0
- K4-free masks: 17,859
- best defect objective: 72
- best split: K4=0, I6=72
- best mask: 11459

This is an exact restricted-family exclusion. The best mask is nevertheless scientifically useful because Algorithm 22 explicitly starts from a best cyclic graph.

### Few Shots baseline shell

`lazy_shell_search.py` proves no solution exists while changing at most two old-old edges of the Few Shots baseline and choosing the new vertex freely. Radius 2 became UNSAT after 13 separator iterations / 801 learned Ramsey clauses.

### Full-edge ball around the 14-defect seed

The 14 original conflicts have repair hitting number at least four; `nearmiss_cover.py` independently enumerated the three minimum size-4 hitting sets and showed none repairs the graph. Lazy SAT then proved complete labelled Hamming balls through radius 10 UNSAT. The current stronger result is:

- radius: 12
- solver: CaDiCaL195
- status: UNSAT
- elapsed: 248.299951 s
- separator iterations: 11
- learned Ramsey clauses: 1198
- run: `40609878390`, job `122558552827`
- durable record: `results/nearmiss-14-radius12.json`

Therefore every valid `(4,6,36)` graph differs from this seed in at least 13 edge decisions.

## Current search routes

1. **Degree-17 catalogue SAT, v1.** `degree17_static_sat.py` fixes one of the seven complete `(3,6,17)` neighborhood types, emits every residual K4/I6 clause once, and lexicographically sorts the 18 unlabeled B vertices by their 17-bit cross-neighborhood rows. Run `40608016453`.
2. **Degree-17 catalogue SAT, v2.** `degree17_static_sat_v2.py` adds exact `11<=deg<=17` Sinz sequential counters after eliminating fixed branch edges. Its counter encoding is exhaustively projection-tested on small instances before every solver lane. Run `40610327410`.
3. **Exact near-miss balls.** `lazy_ball36.py` is running radii 14,16,20 after the radius-12 proof. Any SAT model is automatically sent to the Few Shots verifier.
4. **Algorithm-22 cyclic start.** `results/circulant36-best-seed.json` is the exact best cyclic mask from the exhaustive family scan. `.github/workflows/temp-ramsey-r46-methodb-cyclic.yml` runs defect-only, P4-shaped, and full-profile variants from that seed.
5. **Independent heuristic basins.** The same self-tested searcher is also running from the all-37-core 15-defect best graph and from randomized asymmetric 15-regular graphs generated by degree-preserving 2-switches.
6. **Degree-11 catalogue endpoint.** The complete 352,366-graph `(4,5,24)` catalogue is the natural opposite structural endpoint. A one-shot workflow authenticates the current McKay source and persists only source metadata/hash, not the 17MB third-party catalogue itself.

## Inconclusive or low-priority routes

- Full-CNF Kissat with only a fixed vertex-0 degree 11..17: every four-hour branch timed out.
- First degree-17 lazy separator: all seven catalogue branches timed out; it repeatedly enumerated all six-subsets in Python and left B labels symmetric.
- First all-37-core WalkSAT parameterization: best 15 defects, so repeating exactly that configuration is low priority.
- Continuing to optimize only P4 from the 14-defect seed is low priority: multiple long lanes returned to the same basin, and its P4 count is already unusually high.
- Blind random graph sampling is lower priority than structure-aware exact search or degree-controlled/tabu search.

## Verification discipline

A candidate counts only after all of the following:

1. exact internal K4 / independent-6 recount;
2. independent implementation or exact-solver recheck;
3. Few Shots p003 verifier returns `valid:true`, score at least `36`;
4. live literature/public-record recheck;
5. Few Shots `tools/check.py` returns exit code 0 against current `main`;
6. exact certificate and provenance are frozen before submission.

If a valid 36-vertex graph appears, stop exploratory optimization immediately and follow this verification/submission path.

## Next steps

1. Consume degree-17 runs `40608016453` and `40610327410`. Any SAT model gets immediate independent recount + Few Shots verification. If all seven catalogue branches are UNSAT under a sound encoding, record that every hypothetical 36-vertex graph has maximum degree at most 16.
2. Consume exact-ball run `40609878390`. Preserve every new UNSAT radius immediately; any SAT result is a direct candidate.
3. Consume the best-cyclic Algorithm-22 campaign before spawning more heuristic parameter sweeps. The cyclic seed is the main literature-faithful heuristic experiment still missing from earlier work.
4. Authenticate the McKay `(4,5,24)` catalogue source, then design degree-11 gluing by catalog partition/structure rather than launching 352,366 monolithic jobs blindly.
5. Freeze and verify any zero-defect candidate immediately; otherwise preserve exact exclusions and solver statistics so later agents do not repeat them.

## Durable artifacts

- `extension_check.py`, `results/extension-all-37.json` — exact direct-extension sweep.
- `extension_maxsat.py`, `results/extension-maxsat-partial.json` — partial exact frozen-core defect optimization.
- `circulant36.cpp`, `results/circulant36-best-seed.json` — exhaustive cyclic family scan and best cyclic seed.
- `sat_search.py`, `sat_r46.py` — unrestricted / degree-branched direct SAT encodings.
- `degree17_catalog_sat.py`, `results/degree17-catalog-sat.json` — first lazy degree-17 attempt; timeout evidence.
- `degree17_static_sat.py` — static degree-17 catalogue CNF with B-label lex symmetry breaking.
- `degree17_static_sat_v2.py` — v2 static encoding with exact safe degree counters.
- `lazy_shell_search.py` — exact old-edge shells around 35-vertex cores.
- `walksat36.cpp`, `results/walksat-all-37.json` — first all-core local-search sweep.
- `methodb36.cpp` — self-tested defect/P4/profile tabu search.
- `random_regular36.py` — deterministic asymmetric 15-regular seed generator.
- `notes/algorithm22-calibration.md` — literature-derived Algorithm-22 calibration.
- `results/algorithm22-calibration-best-14.json` — frozen invalid 14-defect near-miss.
- `nearmiss_cover.py`, `results/algorithm22-nearmiss-cover.json` — exact repair-cover analysis.
- `lazy_ball36.py`, `results/nearmiss-14-hamming-balls.json`, `results/nearmiss-14-radius12.json` — exact all-edge Hamming-ball exclusions.
- `results/algorithm22-nearmiss-radius6.json`, `results/algorithm22-nearmiss-radius7.json` — independent explicit local enumerations.

## Sources

- Few Shots p003: https://github.com/few-shots/few-shots/tree/main/problems/p003-ramsey-r46
- S. Radziszowski, *Small Ramsey Numbers*, EJC Dynamic Survey DS1, revision #18 (2026).
- G. Exoo, *On the Ramsey Number R(4,6)*, EJC 19(1) (2012), P66, DOI 10.37236/2102.
- G. Exoo public 37-coloring collection: https://cs.indstate.edu/ge/RAMSEY/R46/index.html
- B. McKay, Ramsey graph collection: https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
- A. M. Lehavi, *Ramsey Number Counterexample Checking and One Vertex Extension Linearly Bound by s and t*, arXiv:2411.04267 (2024).
- A. Nagda, P. Raghavan, A. Thakurta, *Reinforced Generation of Combinatorial Structures: Ramsey Numbers*, arXiv:2603.09172v5 (2026).

## Work log

### 2026-10-28

- Rechecked the live public record: still `36 <= R(4,6) <= 40`, no public 36-vertex construction.
- Consolidated all-37 direct extension UNSAT, all-circulant exclusion, old-edge baseline radius 2, and the first all-core heuristic sweep.
- Proved the 14-defect near-miss's complete labelled Hamming ball through radius 12 UNSAT; launched radii 14,16,20.
- Replaced the slow degree-17 lazy separator with static v1; launched all seven catalogue branches.
- Added degree-17 v2 with explicit exact degree bounds `11..17` and exhaustively self-tested Sinz counters; launched all seven branches.
- Implemented `methodb36.cpp`; randomized delta/profile self-tests agree with full recounts.
- Ran a 12-lane P4/profile campaign from the 14-defect seed; no zero-defect lane was found. Launched independent searches from a 15-defect all-core basin and randomized 15-regular basins.
- Recovered the exhaustive best cyclic mask `11459` (`K4=0`, `I6=72`) and launched the literature-faithful Algorithm-22 cyclic-seed campaign.
- Preserved two exact extension-MaxSAT optima (both 18 conflicts) from the earlier sequential campaign; deprioritized finishing all 37 cores because each exact instance costs about one hour.
- Started authentication of McKay's complete 352,366-graph `(4,5,24)` catalogue as groundwork for a degree-11 endpoint search.

### 2026-10-27

- Read and followed Few Shots plus `science-boundary` repository rules; established this durable topic on `main`.
- Exhausted direct extension of all 37 Exoo 35-vertex graphs with two independent exact formulations.
- Exhausted all 36-vertex undirected circulants.
- Proved old-edge Hamming radius <=2 around the Few Shots baseline contains no solution.
- Calibrated Algorithm-22-style local search and found the retained 14-defect near-miss.
- Froze that near-miss, proved its first local repair balls impossible, and started progressively larger exact Hamming-ball searches.
