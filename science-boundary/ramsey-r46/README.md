# Ramsey R(4,6) lower bound

## Question

Can we construct a graph on at least 36 vertices with neither a 4-clique nor an independent set of size 6? A 36-vertex certificate would prove `R(4,6) >= 37`, improving the public lower bound.

This directory is the durable research workspace for Few Shots `p003-ramsey-r46`. Exploratory code, evidence, failures, and search artifacts stay here. Only a fully verified final `certificate.json` and `SHOT.md` belong in the Few Shots repository.

## Current state

- **Target:** first verified `(4,6)` graph on 36 vertices.
- **Few Shots record at start:** 35 vertices, epsilon +1; no merged p003 shot beyond the baseline.
- **Public state rechecked 2026-10-28:** `36 <= R(4,6) <= 40`; no public 36-vertex construction found. Radziszowski's 2026 survey and McKay's live Ramsey collection still describe Exoo's 35-vertex family as the largest known examples.
- **All 37 published Exoo 35-vertex graphs are exactly non-extendable by one frozen-core vertex.** Two independent exact solvers agree for every graph; see `results/extension-all-37.json`.
- **Every undirected circulant graph on 36 vertices is ruled out.** `circulant36.cpp` exhausts all `2^18` distance masks; no solution exists in that family.
- **Few Shots baseline old-edge Hamming radius <=2 is exactly ruled out** by lazy SAT.
- **A calibrated Algorithm-22-style local search reached a 36-vertex near-miss with 14 total defects = 10 K4 + 4 independent-6 sets.** Frozen candidate and metadata are `results/algorithm22-calibration-best-14.json` and `results/algorithm22-calibration-summary.json`.
- **The complete labelled Hamming ball of radius <=10 around that 14-defect near-miss is exactly UNSAT.** `results/nearmiss-14-hamming-balls.json` records exact CaDiCaL results through radii 5,6,7,8,9,10; an independent explicit enumeration also exhausts radii 6 and 7 (`results/algorithm22-nearmiss-radius6.json`, `results/algorithm22-nearmiss-radius7.json`).
- **The first all-37-core WalkSAT sweep did not beat the local calibration:** best result was 15 defects versus the retained 14-defect near-miss; see `results/walksat-all-37.json` and `results/walksat-all-37-best.json`.
- **Unrestricted degree-branched Kissat remains inconclusive:** all degree branches 11..17 timed out after four hours; this is not a nonexistence result.
- **Degree 17 is now the main exact structural branch.** The first seven-catalog lazy-SAT sweep timed out in every branch. A replacement static encoding fixes each of the seven complete `(3,6,17)` neighborhood types, simplifies all global Ramsey clauses once, and lexicographically sorts the 18 unlabeled non-neighbors by their 17-bit cross-neighborhood rows. GitHub Actions run `40608016453` is executing the seven branches in parallel.
- **No valid 36-vertex certificate has been found yet.**

## Why this is frontier-level

Geoffrey Exoo raised the lower bound to 36 in 2012 by constructing 37 graphs on 35 vertices. Radziszowski's dynamic survey revision 18 (2026) still lists the lower bound as 36, while the upper bound is 40. McKay's Ramsey graph collection likewise still describes Exoo's family as the largest known examples.

Nagda, Raghavan, and Thakurta (2026, arXiv:2603.09172v5) report that AlphaEvolve recovered the state of the art for `R(4,6)` but did not improve it. Their Algorithm 22 is especially relevant: it minimizes the unweighted objective `#K4 + #I6`, uses exact common-neighborhood/common-nonneighborhood edge-flip deltas, tabu tenure about `N`, and a roughly 25% edge perturbation after low-cost stagnation. This independently supports the structure of the current local-search route. Details and local calibration are in `notes/algorithm22-calibration.md`.

## Useful structural facts

The problem is to find a graph `G` with `omega(G) <= 3` and `alpha(G) <= 5`.

For any hypothetical `(4,6,36)` graph every vertex has degree between 11 and 17. The neighborhood is a `(3,6)` graph, giving degree at most `R(3,6)-1 = 17`; the non-neighborhood is a `(4,5)` graph, so it has at most 24 vertices, giving degree at least 11. These safe bounds are used in the SAT searches.

The degree-17 endpoint is unusually rigid. If `deg(v)=17`, then `N(v)` is a `(3,6,17)` graph. McKay's complete public catalogue contains exactly seven such graphs. After relabeling, one of those seven neighborhood graphs can be fixed on vertices `1..17`; the remaining 18 non-neighbors must induce a `(4,5,18)` graph. This yields seven complete gluing/completion branches rather than one unrestricted 630-edge search.

Exoo's 2012 search remains informative. Method A recolors individual edges under simulated annealing/tabu search. Method B starts directly at the target order and augments the objective with induced 4-vertex statistics; Exoo reports that increasing induced `P4` count was important. Method C starts from a symmetric near-solution and then breaks symmetry. The decisive 34-vertex precursor reported by Exoo was an outlier in both K4 and induced-P4 statistics and then extended immediately to 35 vertices.

## Exact one-vertex extension result

For a fixed 35-vertex `(4,6)` graph `G`, add a new vertex `x` and let `S=N(x)` among the old vertices. Then `G+x` is valid exactly when:

1. `S` contains no triangle of `G`, otherwise that triangle plus `x` is a K4;
2. `S` intersects every independent 5-set of `G`, otherwise those five old vertices plus `x` form an independent 6-set.

`extension_check.py` solves this finite 35-variable problem independently as:

- CNF/DPLL: negative 3-clauses for triangles and positive 5-clauses for independent 5-sets;
- direct hitting-set branching with triangle-forbidden choices.

The complete GitHub Actions sweep of all 37 published Exoo graphs gives `extendable=0`, with both solvers agreeing. Source hashes and per-graph constraint counts are preserved in `results/extension-all-37.json`. This eliminates literal frozen-core extension, not general 36-vertex graphs with changed old-old edges.

`extension_maxsat.py` turns those extension clauses soft to compute the exact minimum frozen-core defect. Its role is ranking the 37 cores for destroy-and-repair search.

## Current search routes

1. **Degree-17 catalogue completion (current exact priority).** `degree17_static_sat.py` fixes each of the seven complete `(3,6,17)` neighborhood types, writes the complete residual K4/I6 CNF, and adds a lossless B-vertex lexicographic symmetry break. This replaces the slower `degree17_catalog_sat.py` lazy separator, whose seven branches all timed out.
2. **Unrestricted direct SAT.** `sat_search.py` uses all 630 edges, all K4/I6 constraints, safe degree bounds, and a lossless symmetry break. `sat_r46.py` separately branched on vertex-0 degree `11..17`; the first four-hour Kissat sweep timed out in all seven branches.
3. **Exact local shells around known 35-vertex cores.** `lazy_shell_search.py` bounds changed old-old edges and lazily separates genuine Ramsey clauses. An UNSAT result rigorously excludes the complete labelled shell.
4. **Exact local balls around 36-vertex near-misses.** `lazy_ball36.py` constrains all 630 edge flips around a frozen 36-vertex candidate. The current 14-defect seed is completely excluded through radius 10, so further work should use a genuinely different near-miss rather than expand this ball mechanically.
5. **High-throughput edge-flip search.** `walksat36.cpp` uses exact K4/I6 deltas and starts from each known Exoo core plus a new vertex. The first all-37-core sweep bottomed out at 15 defects and therefore did not improve the retained 14-defect candidate.
6. **Exoo Method-B shaping.** A next heuristic campaign should add induced `P4` as a tie-break/objective component rather than only increasing random search volume.
7. **Other catalog-guided endpoint branches.** Degree 11 forces a 24-vertex `(4,5)` non-neighborhood, for which McKay's complete extremal catalogue is public. This is the natural next exact endpoint if degree 17 is resolved or remains solver-hard.

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

`lazy_shell_search.py` proved no solution exists while changing at most two old-old edges of the Few Shots baseline and freely choosing the new vertex. Radius 2 became UNSAT after 13 separator iterations / 801 learned Ramsey clauses.

### Algorithm-22-style 14-defect near-miss

A local calibration using the Few Shots baseline plus one new vertex, exact edge-flip deltas, tabu tenure `24..48`, stagnation after `4*N*N=5184` steps, a 25% edge kick, and 12% random conflict repair reached:

- objective: 14
- K4: 10
- independent-6: 4
- seed: 4
- requested search: 200,000 steps, 4 restarts
- local runtime: about 7.25 s

The candidate is invalid and is preserved only as a search seed.

### Exact radius-10 exclusion around the 14-defect near-miss

The original 14 conflicts already imply a repair hitting number of at least four; `nearmiss_cover.py` independently enumerated the three minimum size-4 hitting sets and showed none repairs the graph. The stronger lazy-SAT campaign then proved the complete labelled Hamming balls of radii 5, 6, 7, 8, 9, and 10 UNSAT. The radius-10 proof terminated after 7 separator iterations and 749 learned Ramsey clauses. An independent explicit enumeration also exhausted radii 6 and 7. Therefore no valid graph lies within Hamming distance <=10 of `results/algorithm22-calibration-best-14.json`.

### First all-37-core WalkSAT sweep

`walksat36.cpp` searched from every known 35-vertex Exoo core plus a new vertex. The best campaign output has 15 forbidden subgraphs, so this sweep did not beat the 14-defect calibration seed. This is a heuristic negative result, not an exhaustive exclusion.

## Inconclusive exact campaigns

- Direct full-CNF Kissat with fixed vertex-0 degree 11,12,13,14,15,16,17: every branch timed out after four hours (`results/sat-degree-*-run-40558674423.json`). No branch is proved SAT or UNSAT.
- First degree-17 seven-catalog lazy-SAT sweep: all seven branches timed out (`results/degree17-catalog-sat.json`). The lazy implementation repeatedly enumerated all 6-subsets in Python and left the 18 B-vertex labels symmetric, motivating the current static encoding.

## Ruled-out regions / dead ends

- Literal one-vertex extension of any of Exoo's 37 public 35-vertex graphs.
- Every undirected 36-vertex circulant graph.
- Old-edge Hamming radius <=2 around the Few Shots baseline (new vertex free).
- Full-edge Hamming radius <=10 around `algorithm22-calibration-best-14.json`.
- Repeating the first all-37-core WalkSAT parameterization is low priority; it produced a best defect count of 15, worse than the retained 14.
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

1. Consume GitHub Actions run `40608016453`. If any degree-17 catalogue branch is SAT, immediately freeze the model and run the authoritative Few Shots verifier plus an independent clique/independence recount. If all seven are UNSAT, record the structural theorem that a hypothetical 36-vertex graph has maximum degree at most 16.
2. If the static branches still time out, inspect Kissat statistics and add only sound branch-specific symmetry/structure (for example automorphisms of the fixed A catalogue representatives) rather than rerunning equivalent jobs.
3. Move next to the opposite endpoint: degree 11 with a fixed 24-vertex `(4,5)` non-neighborhood from McKay's complete 352,366-graph extremal catalogue, using catalogue partitioning/gluing rather than a monolithic degree-11 CNF.
4. For heuristic search, stop expanding the excluded 14-defect Hamming ball; instead implement Exoo Method-B induced-`P4` shaping to seek a qualitatively different basin.
5. Freeze and verify any zero-defect candidate immediately; otherwise preserve exact exclusions and solver statistics so later agents do not repeat them.

## Durable artifacts

- `extension_check.py` — independent exact one-vertex extension solvers.
- `results/extension-all-37.json` — complete 37-core extension sweep with source hashes.
- `extension_maxsat.py` — exact frozen-core extension-defect ranking.
- `circulant36.cpp` — exhaustive 36-vertex circulant checker.
- `sat_search.py`, `sat_r46.py` — unrestricted / degree-branched direct SAT encodings.
- `degree17_catalog_sat.py`, `results/degree17-catalog-sat.json` — first lazy seven-catalog degree-17 attempt; all branches timed out.
- `degree17_static_sat.py` — complete static residual CNF for the seven degree-17 catalogue branches plus lossless lexicographic B-label symmetry breaking.
- `lazy_shell_search.py` — exact old-edge Hamming shells around a 35-vertex core.
- `walksat36.cpp`, `results/walksat-all-37.json` — incremental exact-delta local search and first all-core sweep.
- `notes/algorithm22-calibration.md` — literature-derived parameter calibration and local result.
- `results/algorithm22-calibration-best-14.json` — frozen invalid 14-defect near-miss.
- `nearmiss_cover.py`, `results/algorithm22-nearmiss-cover.json` — exact conflict-cover analysis.
- `lazy_ball36.py`, `results/nearmiss-14-hamming-balls.json` — exact all-edge Hamming-ball exclusions through radius 10.
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

- Rechecked the live public state: Radziszowski revision 18 and McKay's Ramsey collection still give `36 <= R(4,6) <= 40` and no 36-vertex construction.
- Consolidated exact near-miss results: the complete Hamming ball around the 14-defect seed is UNSAT through radius 10; independent enumeration also exhausts radii 6 and 7.
- Consolidated the all-37-core WalkSAT campaign: best defect count 15, so it did not improve the retained 14-defect seed.
- Confirmed the monolithic degree 11..17 Kissat sweep and the first seven-catalog degree-17 lazy-SAT sweep were timeouts, not negative proofs.
- Replaced the degree-17 lazy encoding with `degree17_static_sat.py`: complete residual Ramsey clauses are generated once, and the 18 unlabeled B vertices are lexicographically ordered by their 17-bit cross rows. Local generation for catalogue branch 0 yields 919 variables and 706,705 clauses in about 3.4 s. Launched seven parallel branches in Actions run `40608016453`.

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
