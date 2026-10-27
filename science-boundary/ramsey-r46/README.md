# Ramsey R(4,6) lower bound

## Question

Can we construct a graph on at least 36 vertices with neither a 4-clique nor an independent set of size 6? A valid 36-vertex graph would prove `R(4,6) >= 37` and improve the current public lower bound.

This directory is the durable workspace for Few Shots problem `p003-ramsey-r46`. Exploratory code, evidence, negative results, and search artifacts stay here; only a fully verified final `certificate.json` and `SHOT.md` belong in a Few Shots shot.

## Why this may be a frontier

The current published interval is `36 <= R(4,6) <= 40`. Geoffrey Exoo raised the lower bound to 36 in 2012 by finding 37 graphs on 35 vertices. Radziszowski's dynamic survey revision 18 (2026) still lists 36 as the lower bound, and a current public-source check on 2026-10-27 found no 36-vertex construction. A valid 36-vertex `(4,6)` graph is therefore a genuine frontier result if the record state is rechecked at submission time.

Recent automated work is directly relevant: Nagda, Raghavan, and Thakurta (2026, arXiv:2603.09172) report that AlphaEvolve recovered the state of the art for `R(4,6)` from cyclic initialization and discovered a heuristic structurally similar to Exoo's search. That supports structured seeds plus aggressive search, not blind random sampling.

## Current state

- **Target:** first verified `(4,6)`-graph on 36 vertices.
- **Few Shots baseline/current record:** 35 vertices; epsilon is +1. No merged p003 shot existed at start.
- **Public state checked 2026-10-27:** `36 <= R(4,6) <= 40`.
- **All 37 published Exoo 35-vertex graphs are not directly one-vertex extendable.** `extension_check.py` independently solves each 35-variable extension instance by CNF/DPLL and direct hitting-set branching. GitHub Actions ran all 37; both solvers agreed on all inputs and `extendable=0`. Exact per-graph source SHA-256 values and constraint counts are in `results/extension-all-37.json`.
- **All undirected circulant graphs on 36 vertices are ruled out.** `circulant36.cpp` exhausts all `2^18 = 262,144` distance masks. Action re-verification found 17,859 K4-free circulants and zero valid `(4,6,36)` graphs. The best simple objective `#K4 + #independent-6` is 72 at mask 11459, with 0 K4 and 72 independent 6-sets.
- **The Few Shots baseline has no solution within old-edge Hamming radius 2.** `lazy_shell_search.py` used a complete lazy-SAT separation loop with safe degree bounds and proved radius `<=2` UNSAT after 13 iterations / 801 learned Ramsey clauses. Larger radii 4, 8, 16, 32 are running in Actions.
- **Four unrestricted direct-SAT workers are running** on the complete 36-vertex encoding (`cadical195`, `glucose42`, `maplesat`; cyclic/mixed/random phase biases), with safe degree bounds `11 <= deg(v) <= 17`.
- **Exact frozen-core MaxSAT ranking of all 37 Exoo seeds is running** to identify which 35-vertex core is closest to extendable and should seed destroy-and-repair search.
- **No 36-vertex certificate has been found yet.**

## Workspace boundary

The upstream Few Shots repository is the authoritative scoring/submission target. Do not put exploratory code or logs there. Any claimed improvement must pass the p003 verifier and `tools/check.py` against current Few Shots `main` before submission.

## What is known / useful structure

The problem is to maximize `n` for a simple graph `G` subject to `omega(G) <= 3` and `alpha(G) <= 5`.

Exoo's 2012 paper describes three heuristic search families. Method A recolors individual edges under simulated annealing/tabu search to reduce bad monochromatic subgraphs. Method B starts directly at the target order and augments the objective with counts of induced 4-vertex graph types; Exoo reports that maximizing induced `P4` count was the key ingredient. Method C begins with a highly symmetric coloring that has useful single-edge improving moves, then breaks symmetry and proceeds as in Method A.

The decisive 34-vertex precursor `G1` in Exoo's paper was an outlier: in the color-two graph it had only 1586 induced `K4`s versus at least 1780 in comparison colorings, and 9553 induced `P4`s. It extended to 35 vertices immediately, and all 37 resulting 35-vertex colorings were closely related.

For any hypothetical `(4,6,36)` graph, every vertex has degree between 11 and 17. Its neighborhood must be a `(3,6)` graph, so degree is at most `R(3,6)-1 = 17`; its non-neighborhood must be a `(4,5)` graph, so degree is at least `35-(R(4,5)-1) = 11`. These safe bounds are included in the SAT searches.

## Exact one-vertex extension formulation

For a fixed 35-vertex `(4,6)` graph `G`, add a new vertex `x` and let `S` be the old vertices adjacent to `x`. Then `G+x` is again a `(4,6)` graph exactly when:

1. `S` contains no triangle of `G`; otherwise that triangle plus `x` is a `K4`.
2. `S` intersects every independent 5-set of `G`; otherwise those five vertices plus `x` form an independent 6-set.

`extension_check.py` solves this exact feasibility problem two independent ways. The complete 37-graph Action sweep agrees with Lehavi's 2024 one-vertex-extension result and eliminates literal frozen-core extension as a search direction.

`extension_maxsat.py` keeps the same frozen core but makes every extension clause soft with unit weight. Its exact optimum is the minimum number of forbidden subgraphs involving the new vertex; this is used only to rank seeds for later searches where old-old edges are allowed to move.

## Search routes

1. **Lazy SAT Hamming shells around known cores.** `lazy_shell_search.py` constrains the number of changed old-old edges, solves a relaxation, finds every actual K4 / independent-6 in the model, adds only those globally valid clauses, and repeats. UNSAT is rigorous for the entire shell because all learned clauses are genuine Ramsey constraints.
2. **Unrestricted direct SAT.** `sat_search.py` materializes the complete 630-variable encoding: 58,905 negative K4-blocking clauses and 1,947,792 positive independent-6-blocking clauses, plus safe degree bounds and a lossless `edge(0,1)=1` symmetry break.
3. **Destroy-and-repair around ranked Exoo cores.** Use exact extension-MaxSAT cost to pick the closest known cores, then allow old edges to move as well.
4. **Exoo Method-B objective shaping.** Combine exact forbidden-subgraph count with induced 4-vertex statistics, especially `P4`, to avoid known local minima.
5. **Structured seeds only as starts.** Circulant symmetry is fully ruled out as the final answer at n=36, but the best circulant can still seed unrestricted symmetry-breaking search, consistent with Exoo Method C / AlphaEvolve.

## Evidence and experiments

### 2026-10-27 — all 37 known 35-vertex graphs: direct extension UNSAT

Action result:

- graphs: 37
- extendable: 0
- independent exact solvers agreed: true
- triangle counts across seeds: 375..395
- independent-5 counts across seeds: 742..818
- complete per-source SHA-256 and statistics: `results/extension-all-37.json`

This does **not** prove that no 36-vertex `(4,6)` graph exists, because the 37 known 35-vertex graphs are not an exhaustive list of all possible induced 35-vertex subgraphs of a hypothetical solution.

### 2026-10-27 — exhaustive 36-vertex circulant search

`circulant36.cpp` enumerates every undirected circulant graph on `Z_36` (18 binary distance classes). Independent local and GitHub Actions runs agree:

- checked: 262,144
- K4-free: 17,859
- valid `(4,6,36)`: 0
- best simple violation objective: 72
- best mask: 11459
- best split: 0 K4 + 72 independent-6 sets

This is a complete negative result only for the circulant class.

### 2026-10-27 — Few Shots baseline Hamming shell

`lazy_shell_search.py` around the 35-vertex Few Shots baseline proved no 36-vertex solution exists while changing at most two old-old edges. Radius 2 became UNSAT after 13 separator iterations and 801 learned Ramsey clauses. Larger shells are running.

## Dead ends / ruled-out regions

- Literal one-vertex extension of **any of the 37 known Exoo graphs**: exactly ruled out.
- Exact 36-vertex undirected circulant family: exhausted, no solution.
- Hamming radius `<=2` around the Few Shots baseline old-old edge set: exactly ruled out.
- Blind random graph sampling: low priority relative to structure-aware exact/local search.

## Verification discipline

Any claimed improvement must satisfy all of the following before being described as a breakthrough:

1. exact internal check for K4 and independent 6-sets;
2. independent re-check with a separate implementation or exact solver;
3. Few Shots authoritative verifier returns `valid:true` with score at least `36`;
4. current literature/public-record re-check;
5. Few Shots `tools/check.py` returns exit code `0` against current `main`;
6. freeze the exact certificate and preserve enough provenance to reproduce it.

## Next steps

1. Monitor the running direct-SAT and Hamming-shell Actions; immediately freeze and verify any zero-conflict candidate.
2. Persist the extension-MaxSAT ranking and use the best cores for new lazy-shell / edge-repair campaigns instead of treating all 37 seeds equally.
3. Implement a fast C++ unrestricted edge-flip search with exact K4 / independent-6 deltas and Exoo-style induced-`P4` tie-breaking; run many independent Action seeds.
4. If the baseline shells are exhausted without a hit, repeat shells around the best-ranked Exoo cores and around the best circulant only after symmetry is broken.

## Durable artifacts

- `extension_check.py` — two independent exact one-vertex-extension solvers.
- `results/extension-all-37.json` — complete 37-seed exact sweep with source hashes.
- `circulant36.cpp` — exhaustive 36-vertex circulant checker/objective scan.
- `sat_search.py` — complete direct-SAT encoding for n=36.
- `lazy_shell_search.py` — counterexample-guided SAT for Hamming shells around a 35-vertex seed.
- `extension_maxsat.py` — exact frozen-core extension-cost ranking.

## Sources

Primary/authoritative sources checked:

- Few Shots p003 statement/verifier: https://github.com/few-shots/few-shots/tree/main/problems/p003-ramsey-r46
- S. Radziszowski, *Small Ramsey Numbers*, Electronic Journal of Combinatorics Dynamic Survey DS1, revision #18 (2026).
- G. Exoo, *On the Ramsey Number R(4,6)*, Electronic Journal of Combinatorics 19(1) (2012), P66, DOI 10.37236/2102.
- G. Exoo public 37-coloring collection: https://cs.indstate.edu/ge/RAMSEY/R46/index.html
- B. McKay, Ramsey graph collection: https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
- A. M. Lehavi, *Ramsey Number Counterexample Checking and One Vertex Extension Linearly Bound by s and t*, arXiv:2411.04267 (2024).
- A. Nagda, P. Raghavan, A. Thakurta, *Reinforced Generation of Combinatorial Structures: Ramsey Numbers*, arXiv:2603.09172 (2026).

## Work log

### 2026-10-27

- Read Few Shots rules, p003 problem/verifier/baseline, and `science-boundary` rules.
- Rechecked current literature/record state and reviewed Exoo's successful heuristic structure.
- Implemented and independently validated exact one-vertex-extension logic.
- Exhausted all 37 published Exoo seeds: none directly extend to 36 vertices.
- Exhausted every undirected 36-vertex circulant: none is a solution; best violation count is 72 at mask 11459.
- Proved Hamming radius `<=2` around the Few Shots baseline old-edge set contains no solution.
- Launched unrestricted direct-SAT workers and larger lazy-SAT Hamming shells in GitHub Actions.
- Launched exact MaxSAT ranking of the 37 known cores to choose better destroy-and-repair seeds.
