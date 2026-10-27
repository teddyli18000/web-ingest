# Ramsey R(4,6) lower bound

## Question

Can we construct a graph on at least 36 vertices with neither a 4-clique nor an independent set of size 6? A valid 36-vertex graph would prove `R(4,6) >= 37` and improve the current public lower bound.

This direction is the durable workspace for Few Shots problem `p003-ramsey-r46`. Exploratory code, evidence, negative results, and search artifacts stay here; only a fully verified final `certificate.json` and `SHOT.md` belong in a Few Shots shot.

## Why this may be a frontier

The current published interval is `36 <= R(4,6) <= 40`. Geoffrey Exoo raised the lower bound to 36 in 2012 by finding 37 graphs on 35 vertices. Radziszowski's dynamic survey revision 18 (24 April 2026) still lists 36 as the lower bound; McKay's Ramsey graph collection likewise still describes Exoo's 37 graphs as the largest known examples. A valid 36-vertex `(4,6)` graph is therefore a genuine frontier result if the record state is rechecked at submission time.

## Current state

- **Target:** first find a verified `(4,6)`-graph on 36 vertices.
- **Few Shots baseline/current record:** 35 vertices; epsilon is +1. `FEWSHOT.md` had no merged p003 shot at the start of this work.
- **Public state checked on 2026-10-27:** `36 <= R(4,6) <= 40` in the 2026 survey and current public tracking sources.
- **Exact local result:** the Few Shots 35-vertex baseline is **not directly one-vertex extendable**. Its extension instance contains 383 triangles and 784 independent 5-sets. Two independent exact solvers in `extension_check.py` (CNF/DPLL and direct hitting-set branching) both returned UNSAT.
- `extension_check.py` is now durable on `main`; the next reproducible experiment is the same exact test on all 37 public Exoo graphs through GitHub Actions.
- **No 36-vertex certificate has been found yet.**

## Workspace boundary

All ongoing research state for this problem belongs here: code, literature notes, experiment definitions, negative results, candidate graphs, and reproducibility material.

The upstream Few Shots repository is treated as the scoring/submission target. Do not place exploratory code or logs there. Any claimed improvement must pass the authoritative p003 verifier and `tools/check.py` against current Few Shots `main` before submission.

## What is known

The problem is to maximize `n` for a simple graph `G` subject to `omega(G) <= 3` and `alpha(G) <= 5`.

Exoo's 2012 paper describes three heuristic search families. Method A recolors individual edges under simulated annealing/tabu search to reduce the number of bad monochromatic subgraphs. Method B starts directly at the desired order and augments the objective with counts of induced 4-vertex graph types. Exoo reports that maximizing induced `P4` count was the key ingredient. Method C begins with a highly symmetric coloring that has useful single-edge improving moves, then breaks symmetry and proceeds as in Method A.

The decisive 34-vertex precursor `G1` reported by Exoo was an outlier among otherwise good 34-vertex colorings. In the color-two graph it had only 1586 induced `K4`s versus at least 1780 in the previously seen examples, and 9553 induced `P4`s, substantially more than the comparison colorings. Exoo reports that it extended to 35 vertices immediately, and all 37 resulting 35-vertex colorings were closely related.

The displayed 35-vertex graph in the paper has color-one degrees between 11 and 16. These are close to elementary neighborhood limits coming from `R(4,5)=25` and `R(3,6)=18`, so degree shaping is also a plausible secondary search constraint.

## Exact one-vertex extension formulation

For a fixed 35-vertex `(4,6)` graph `G`, add a new vertex `x` and let `S` be the old vertices adjacent to `x`. Then `G+x` is again a `(4,6)` graph exactly when:

1. `S` contains no triangle of `G`; otherwise that triangle together with `x` is a `K4`.
2. `S` intersects every independent 5-set of `G`; otherwise five old non-neighbors of `x` together with `x` form an independent 6-set.

This is a 35-variable finite feasibility problem. `extension_check.py` solves it independently in two ways:

- **CNF/DPLL:** every triangle gives a negative 3-clause and every independent 5-set gives a positive 5-clause.
- **Direct hitting-set branching:** branch on an uncovered independent 5-set while forbidding future choices that would create a triangle inside `S`.

The program also detects whether a published matrix must be complemented to match the Few Shots `(4,6)` orientation. Any SAT witness is rebuilt as a 36-vertex graph and directly checked for forbidden cliques. A negative result is accepted only when the two exact solvers agree.

## Hypotheses / routes

1. **Exhaust direct extension.** Test every one of Exoo's 37 public 35-vertex graphs exactly. If all are UNSAT, stop spending search budget on choosing only the 36th vertex while freezing the old 35 vertices.
2. **Destroy-and-repair near known cores.** Add a 36th vertex but permit old-old edges to move as well. Rank seeds by how cheaply extension conflicts can be repaired.
3. **Exoo Method B objective shaping.** Use a weighted/lexicographic objective containing forbidden `K4` and independent-6 counts plus induced 4-vertex statistics, especially `P4`, to avoid collapsing into the known 35-vertex basin.
4. **Full edge-flip local search.** Run simulated annealing/tabu search on all 630 edges of `K36`, seeded both from perturbed 35-vertex cores and from structured near-solutions.
5. **SAT/MaxSAT completion.** A full 36-vertex CNF has 630 edge variables, one 6-literal negative clause for each 4-set, and one 15-literal positive clause for each 6-set (about two million clauses). Pure unrestricted SAT may be expensive, but fixed-core or symmetry-broken completion may be practical.
6. **Symmetric constructions only as seeds.** Circulant/Cayley restrictions are too rigid to be the primary bet, but Exoo's Method C gives a reason to use highly symmetric near-solutions as starting points before individual-edge symmetry breaking.

## Evidence and experiments

### 2026-10-27 — Few Shots baseline one-vertex extension

`extension_check.py` was syntax-checked locally and run on the Few Shots 35-vertex baseline adjacency matrix. The relevant graph orientation contains 383 triangles and 784 independent 5-sets. Both exact solvers returned UNSAT. The solver's internal analysis phase took about 1.65 seconds in that local run; end-to-end Python process time was a few seconds.

This rules out only extensions that freeze every edge among the existing 35 vertices. It does **not** rule out a 36-vertex `(4,6)` graph that differs on old-old edges.

## Dead ends

- **Single-vertex extension of the Few Shots baseline:** exactly ruled out as above.
- **Blind random graphs:** not competitive with the structure found in Exoo's successful search; use explicit conflict and induced-subgraph objectives instead.
- **Pure circulant/difference-graph family as the sole search space:** public searches have not reached the 35-vertex record in this restricted family. Keep such graphs only as possible Method-C seeds.

## Verification discipline

Any claimed improvement must satisfy all of the following before it is described as a breakthrough:

1. exact internal check for `K4` and independent 6-sets;
2. independent re-check with a separate implementation or exact solver;
3. Few Shots authoritative verifier returns `valid: true` with score at least `36`;
4. current literature / public-record re-check;
5. Few Shots `tools/check.py` returns exit code `0` against current `main`;
6. freeze the exact certificate and preserve enough provenance to reproduce it.

## Next steps

1. Run `extension_check.py --fetch-all` on GitHub Actions against Exoo's 37 public matrices and persist the exact result plus source SHA-256 values.
2. If all 37 are non-extendable, implement a fast 36-vertex edge-flip search seeded from those cores plus one new vertex. Track exact bad-subgraph counts and add Exoo-style induced-`P4` shaping.
3. Launch many independent Action seeds/workers. Persist only meaningful best states, configuration, and reproducible summaries rather than bulk logs.
4. Convert every zero-conflict candidate immediately to the Few Shots certificate format and run the authoritative verifier.

## Sources

Primary and authoritative sources checked:

- Few Shots p003 statement/verifier: https://github.com/few-shots/few-shots/tree/main/problems/p003-ramsey-r46
- S. Radziszowski, *Small Ramsey Numbers*, Electronic Journal of Combinatorics Dynamic Survey DS1, revision #18 (24 April 2026): https://www.combinatorics.org/ojs/index.php/eljc/article/view/DS1
- G. Exoo, *On the Ramsey Number R(4,6)*, Electronic Journal of Combinatorics 19(1) (2012), P66, DOI 10.37236/2102: https://www.combinatorics.org/ojs/index.php/eljc/article/view/v19i1p66
- G. Exoo's public 37-coloring collection: https://cs.indstate.edu/ge/RAMSEY/R46/index.html
- B. McKay, Ramsey graph collection: https://users.cecs.anu.edu.au/~bdm/data/ramsey.html

## Work log

### 2026-10-27 — direction opened

- Read the Few Shots `take-a-shot` procedure, repository rules, p003 problem metadata, verifier, baseline certificate, and generated `FEWSHOT.md`.
- Read the `web-ingest` root, workflow, and `science-boundary` workspace rules.
- Reviewed Exoo 2012 in detail and checked the current 2026 public bound state.
- Established `science-boundary/ramsey-r46/` as the durable research workspace for p003.
- Implemented `extension_check.py`, with two independent exact formulations.
- Locally ruled out direct extension of the Few Shots baseline (383 triangle constraints, 784 independent-5 constraints).
- Next: complete the 37-graph exact extension run in Actions, then move to unrestricted 36-vertex destroy-and-repair/local search.
