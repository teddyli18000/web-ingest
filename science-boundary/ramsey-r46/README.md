# Ramsey R(4,6) lower bound

## Question

Can we construct a graph on at least 36 vertices with neither a 4-clique nor an independent set of size 6? A 36-vertex certificate would prove `R(4,6) >= 37`, improving the public lower bound.

This directory is the durable research workspace for Few Shots `p003-ramsey-r46`. Exploratory code, evidence, failures, and search artifacts stay here. Only a fully verified final `certificate.json` and `SHOT.md` belong in the Few Shots repository.

## Current state

- **Target:** first verified `(4,6)` graph on 36 vertices.
- **Few Shots record at start:** 35 vertices, epsilon +1; no merged p003 shot beyond the baseline.
- **Public state rechecked 2026-10-27:** `36 <= R(4,6) <= 40`; no public 36-vertex construction found. Radziszowski's 2026 survey, McKay's collection, and the 2026 AlphaEvolve Ramsey paper all remain consistent with 35 vertices as the largest known construction.
- **All 37 published Exoo 35-vertex graphs are exactly non-extendable by one frozen-core vertex.** Two independent exact solvers agree for every graph; see `results/extension-all-37.json`.
- **Every undirected circulant graph on 36 vertices is ruled out.** `circulant36.cpp` exhausts all `2^18` distance masks; no solution exists in that family.
- **Few Shots baseline old-edge Hamming radius <=2 is exactly ruled out** by lazy SAT. Larger baseline shells are running in Actions.
- **A calibrated Algorithm-22-style local search reached a 36-vertex near-miss with 14 total defects = 10 K4 + 4 independent-6 sets.** Frozen candidate and metadata are `results/algorithm22-calibration-best-14.json` and `results/algorithm22-calibration-summary.json`.
- **The labelled Hamming ball of radius <=4 around that 14-defect near-miss is exactly ruled out.** Its 14 original conflicts require at least four repair flips; there are only three minimum 4-edge hitting sets, and exact recounts after those three give `(K4,I6)=(9,78),(4,70),(4,71)`. See `nearmiss_cover.py` and `results/algorithm22-nearmiss-cover.json`.
- **Running compute:** unrestricted direct SAT, degree-branched Kissat, larger baseline Hamming shells, exact frozen-core extension-MaxSAT ranking, a 37-core C++ WalkSAT sweep, and exact Hamming balls of radii 1,2,3,4,5,6,8,10 around the 14-defect near-miss.
- **No valid 36-vertex certificate has been found yet.**

## Why this is frontier-level

Geoffrey Exoo raised the lower bound to 36 in 2012 by constructing 37 graphs on 35 vertices. Radziszowski's dynamic survey revision 18 (2026) still lists the lower bound as 36, while the upper bound is 40. McKay's Ramsey graph collection likewise still describes Exoo's family as the largest known examples.

Nagda, Raghavan, and Thakurta (2026, arXiv:2603.09172v5) report that AlphaEvolve recovered the state of the art for `R(4,6)` but did not improve it. Their Algorithm 22 is especially relevant: it minimizes the unweighted objective `#K4 + #I6`, uses exact common-neighborhood/common-nonneighborhood edge-flip deltas, tabu tenure about `N`, and a roughly 25% edge perturbation after low-cost stagnation. This independently supports the structure of the current local-search route. Details and local calibration are in `notes/algorithm22-calibration.md`.

## Useful structural facts

The problem is to find a graph `G` with `omega(G) <= 3` and `alpha(G) <= 5`.

For any hypothetical `(4,6,36)` graph every vertex has degree between 11 and 17. The neighborhood is a `(3,6)` graph, giving degree at most `R(3,6)-1 = 17`; the non-neighborhood is a `(4,5)` graph, so it has at most 24 vertices, giving degree at least 11. These safe bounds are used in the SAT searches.

Exoo's 2012 search remains informative. Method A recolors individual edges under simulated annealing/tabu search. Method B starts directly at the target order and augments the objective with induced 4-vertex statistics; Exoo reports that increasing induced `P4` count was important. Method C starts from a symmetric near-solution and then breaks symmetry. The decisive 34-vertex precursor reported by Exoo was an outlier in both K4 and induced-P4 statistics and then extended immediately to 35 vertices.

## Exact one-vertex extension result

For a fixed 35-vertex `(4,6)` graph `G`, add a new vertex `x` and let `S=N(x)` among the old vertices. Then `G+x` is valid exactly when:

1. `S` contains no triangle of `G`, otherwise that triangle plus `x` is a K4;
2. `S` intersects every independent 5-set of `G`, otherwise those five old vertices plus `x` form an independent 6-set.

`extension_check.py` solves this finite 35-variable problem independently as:

- CNF/DPLL: negative 3-clauses for triangles and positive 5-clauses for independent 5-sets;
- direct hitting-set branching with triangle-forbidden choices.

The complete GitHub Actions sweep of all 37 published Exoo graphs gives `extendable=0`, with both solvers agreeing. Source hashes and per-graph constraint counts are preserved in `results/extension-all-37.json`. This eliminates literal frozen-core extension, not general 36-vertex graphs with changed old-old edges.

`extension_maxsat.py` turns those extension clauses soft to compute the exact minimum frozen-core defect. Its role is ranking the 37 cores for destroy-and-repair search; the ranking campaign is running.

## Current search routes

1. **Unrestricted direct SAT.** `sat_search.py` uses all 630 edges, all K4/I6 constraints, safe degree bounds, and a lossless symmetry break. A separate `sat_r46.py` campaign branches on the degree of vertex 0 (`11..17`) and runs pinned Kissat.
2. **Exact local shells around known 35-vertex cores.** `lazy_shell_search.py` bounds changed old-old edges and lazily separates genuine Ramsey clauses. An UNSAT result rigorously excludes the complete labelled shell.
3. **Exact local balls around 36-vertex near-misses.** `lazy_ball36.py` constrains all 630 edge flips around a frozen 36-vertex candidate. `nearmiss_cover.py` provides a solver-independent conflict-hitting lower bound and already rules out radius <=4 around the best calibrated near-miss.
4. **High-throughput edge-flip search.** `walksat36.cpp` uses exact K4/I6 deltas and starts from each known Exoo core plus a new vertex. The first all-37-core campaign is running. A stronger Algorithm-22-style parameterization has been locally calibrated and should be applied to the best-ranked cores after the first campaign/ranking lands.
5. **Exoo Method-B shaping.** If raw defect minimization stalls, add induced `P4` as a tie-break/objective component rather than only increasing random search volume.
6. **Catalog-guided degree branches.** If direct SAT stalls, exploit the endpoint degree cases: degree 11 forces a 24-vertex `(4,5)` non-neighborhood, for which the full public catalogue is known; degree 17 forces a 17-vertex `(3,6)` neighborhood. These can turn a 630-variable search into a constrained gluing/completion problem.

## Evidence and exact negative results

### All 37 known 35-vertex graphs: direct extension UNSAT

- graphs checked: 37
- extendable: 0
- two independent exact solvers agreed on every instance
- triangle counts across seeds: 375..395
- independent-5 counts: 742..818
- complete data: `results/extension-all-37.json`

### Exhaustive 36-vertex circulant family

`circulant36.cpp` exhausts all 262,144 undirected circulant masks on `Z_36`. No `(4,6,36)` graph exists in this family. The restricted-family result is exact; it does not constrain asymmetric solutions.

### Few Shots baseline shell

`lazy_shell_search.py` proved no solution exists while changing at most two old-old edges of the Few Shots baseline and freely choosing the new vertex. Radius 2 became UNSAT after 13 separator iterations / 801 learned Ramsey clauses. Larger radii are running.

### Algorithm-22-style 14-defect near-miss

A local calibration using the Few Shots baseline plus one new vertex, exact edge-flip deltas, tabu tenure `24..48`, stagnation after `4*N*N=5184` steps, a 25% edge kick, and 12% random conflict repair reached:

- objective: 14
- K4: 10
- independent-6: 4
- seed: 4
- requested search: 200,000 steps, 4 restarts
- local runtime: about 7.25 s

The candidate is invalid and is preserved only as a search seed.

### Exact radius-4 exclusion around the 14-defect near-miss

Each original K4 must lose at least one edge and each original independent-6 set must gain at least one edge. The 14 repair constraints involve 68 distinct candidate edges. Exact set-cover enumeration gives minimum hitting number 4 and only three size-4 hitting sets. Applying each and exactly recounting all forbidden subgraphs produces totals 87, 74, and 75 respectively. Therefore no valid graph is within Hamming distance <=4 of this labelled near-miss.

## Ruled-out regions / dead ends

- Literal one-vertex extension of any of Exoo's 37 public 35-vertex graphs.
- Every undirected 36-vertex circulant graph.
- Old-edge Hamming radius <=2 around the Few Shots baseline (new vertex free).
- Full-edge Hamming radius <=4 around `algorithm22-calibration-best-14.json`.
- Blind random graph sampling is low priority compared with structure-aware exact/local search.

## Verification discipline

A candidate counts only after all of the following:

1. exact internal K4 / independent-6 recount;
2. independent implementation or exact-solver recheck;
3. Few Shots p003 verifier returns `valid:true`, score at least `36`;
4. live literature/public-record recheck;
5. Few Shots `tools/check.py` returns exit code 0 against current `main`;
6. exact certificate and provenance are frozen before submission.

## Next steps

1. Consume running SAT / MaxSAT / shell / WalkSAT / near-miss-ball results as soon as they land; freeze and verify any zero-defect candidate immediately.
2. Use exact extension-MaxSAT ranking plus the first 37-core WalkSAT sweep to select a small set of best Exoo cores.
3. Run the calibrated Algorithm-22-style variant on those selected cores: tabu tenure near `N`, medium 25% perturbations, exact deltas, multiple independent seeds.
4. For strong nonzero near-misses, use `nearmiss_cover.py` first to get a cheap exact Hamming lower bound, then `lazy_ball36.py` beyond that radius.
5. If unrestricted SAT remains hard, move to catalog-guided degree-11 / degree-17 completion rather than merely adding more equivalent SAT workers.

## Durable artifacts

- `extension_check.py` — independent exact one-vertex extension solvers.
- `results/extension-all-37.json` — complete 37-core extension sweep with source hashes.
- `extension_maxsat.py` — exact frozen-core extension-defect ranking.
- `circulant36.cpp` — exhaustive 36-vertex circulant checker.
- `sat_search.py`, `sat_r46.py` — unrestricted / degree-branched direct SAT encodings.
- `lazy_shell_search.py` — exact old-edge Hamming shells around a 35-vertex core.
- `walksat36.cpp` — incremental exact-delta local search.
- `notes/algorithm22-calibration.md` — literature-derived parameter calibration and local result.
- `results/algorithm22-calibration-best-14.json` — frozen invalid 14-defect near-miss.
- `nearmiss_cover.py`, `results/algorithm22-nearmiss-cover.json` — exact conflict-cover analysis excluding radius <=4.
- `lazy_ball36.py` — exact all-edge Hamming balls around a 36-vertex near-miss.

## Sources

- Few Shots p003: https://github.com/few-shots/few-shots/tree/main/problems/p003-ramsey-r46
- S. Radziszowski, *Small Ramsey Numbers*, EJC Dynamic Survey DS1, revision #18 (2026).
- G. Exoo, *On the Ramsey Number R(4,6)*, EJC 19(1) (2012), P66, DOI 10.37236/2102.
- G. Exoo public 37-coloring collection: https://cs.indstate.edu/ge/RAMSEY/R46/index.html
- B. McKay, Ramsey graph collection: https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
- A. M. Lehavi, *Ramsey Number Counterexample Checking and One Vertex Extension Linearly Bound by s and t*, arXiv:2411.04267 (2024).
- A. Nagda, P. Raghavan, A. Thakurta, *Reinforced Generation of Combinatorial Structures: Ramsey Numbers*, arXiv:2603.09172v5 (2026).

## Work log

### 2026-10-27

- Read and followed Few Shots plus `science-boundary` repository rules; established this durable topic on `main`.
- Rechecked current public record and primary literature.
- Exhausted direct extension of all 37 Exoo 35-vertex graphs with two independent exact formulations.
- Exhausted all 36-vertex undirected circulants.
- Proved old-edge Hamming radius <=2 around the Few Shots baseline contains no solution; launched larger shells.
- Launched unrestricted SAT, degree-branched Kissat, and exact frozen-core extension-MaxSAT campaigns.
- Implemented and self-tested incremental C++ K4/I6 edge-flip deltas; launched an all-37-core WalkSAT campaign.
- Calibrated against AlphaEvolve Algorithm 22 and reached a 14-defect 36-vertex near-miss.
- Froze that near-miss, proved its full-edge Hamming radius <=4 contains no solution by exact conflict-cover enumeration, and launched larger exact Hamming-ball searches.
