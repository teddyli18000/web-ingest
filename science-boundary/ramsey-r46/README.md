# Ramsey R(4,6) lower bound

## Question

Can we construct a graph on at least 36 vertices with neither a 4-clique nor an independent set of size 6? A valid 36-vertex graph would prove `R(4,6) >= 37` and improve the current public lower bound.

This direction corresponds to Few Shots problem `p003-ramsey-r46`.

## Current state

- **Target:** first find a verified `(4,6)`-graph on 36 vertices.
- **Few Shots baseline/record:** 35 vertices; the repository baseline is one of Exoo's 2012 35-vertex graphs.
- **Few Shots acceptance rule:** final certificate must pass `problems/p003-ramsey-r46/verify/verify.py`; the score is the vertex count.
- **Public mathematical state checked at start:** the Few Shots problem statement, citing Radziszowski's 2026 dynamic survey, reports `36 <= R(4,6) <= 40`. Thus a 36-vertex `(4,6)`-graph would be a genuine lower-bound advance if independently verified and still absent from current literature at submission time.
- **Merged Few Shots p003 shots at start:** none; `FEWSHOT.md` contains only the 35-vertex baseline.
- **No breakthrough has been found yet.**

## Workspace boundary

All ongoing research state for this problem belongs here: code, literature notes, experiment definitions, negative results, candidate graphs, and reproducibility material.

The upstream Few Shots repository is treated as the scoring/submission target. Do not place exploratory code or logs there. Only create a Few Shots shot after a candidate passes the authoritative verifier and current-record check.

## What is known

The problem is to maximize `n` for a simple graph `G` on `n` vertices subject to:

- `omega(G) <= 3` (no `K4`), and
- `alpha(G) <= 5` (no independent 6-set).

A 35-vertex construction by Geoff Exoo underlies the currently published lower bound `R(4,6) >= 36`. The Few Shots baseline certificate is a 35-vertex, 248-edge graph drawn from Brendan McKay's public collection of 37 such graphs.

Exoo's 2012 paper describes heuristic search for Ramsey graphs and reports that a method favoring certain induced 4-vertex subgraph statistics, especially unusually high induced-`P4` counts in a precursor, led to the 35-vertex constructions. This suggests structure-aware local search is more promising than uninformed Erdős–Rényi sampling.

## Initial hypotheses / routes

1. **Exact one-vertex extension test.** For each known 35-vertex `(4,6)` graph, ask whether there is a neighborhood for a new vertex that preserves both forbidden-subgraph constraints. This is a small exact Boolean feasibility problem and can decisively rule out direct extension of a seed.
2. **Destroy-and-repair around 35-vertex seeds.** If direct extension is impossible, add a 36th vertex and recolor a small set of old/new edges, using SAT/MaxSAT or custom local search to repair all `K4` and independent-6 conflicts.
3. **Structure-guided objective.** Reproduce useful statistics from Exoo's successful search (especially induced 4-vertex patterns) and use them as secondary objectives while maintaining or approaching feasibility.
4. **Symmetry/structured constructions.** Check circulant, Cayley, block, and algebraic families only when they reduce the search enough to justify their rigidity; do not assume the record graph is highly symmetric.
5. **Independent exact encodings.** Maintain at least one validation path independent from any heuristic generator so a promising candidate is not trusted because of a bug in the search code.

## Planned first experiments

### A. Baseline reproduction

Re-run the Few Shots verifier on its 35-vertex baseline and preserve the exact verifier output here.

### B. Exhaustive one-vertex extension of all public 35-vertex seeds

For a fixed 35-vertex graph `G`, let Boolean variable `x_v` mean the new vertex is adjacent to `v`.

Constraints are immediate:

- For every triangle `{a,b,c}` of `G`, forbid `x_a = x_b = x_c = 1`, otherwise the new vertex plus that triangle forms a `K4`.
- For every independent 5-set `{a,b,c,d,e}` of `G`, require at least one of the corresponding `x` variables to be `1`, otherwise those five vertices plus the new vertex form an independent 6-set.

This exact SAT instance has only 35 variables. Run it against all 37 public Exoo/McKay 35-vertex graphs. A complete UNSAT result for every seed rules out direct one-vertex extension of the known family, while any SAT assignment immediately yields a 36-vertex candidate for authoritative verification.

### C. Near-extension search

If B is UNSAT for all seeds, quantify how far each seed is from extendability by allowing a bounded number of flips among old edges and solving/optimizing the resulting conflict set. Use this to rank seeds and neighborhoods before broader stochastic search.

## Verification discipline

Any claimed improvement must satisfy all of the following before it is described as a breakthrough:

1. exact internal check for `K4` and independent 6-sets;
2. Few Shots authoritative verifier returns `valid: true` with score at least `36`;
3. independent re-check with a separate implementation or exact solver;
4. current literature / public-record re-check;
5. Few Shots `tools/check.py` returns exit code `0` against current `main` before submission.

## Sources

- Few Shots p003 problem statement and verifier: https://github.com/few-shots/few-shots/tree/main/problems/p003-ramsey-r46
- S. Radziszowski, *Small Ramsey Numbers*, Electronic Journal of Combinatorics Dynamic Survey DS1, revision #18 (2026): https://www.combinatorics.org/ojs/index.php/eljc/article/view/DS1
- G. Exoo, *On the Ramsey number R(4,6)*, Electronic Journal of Combinatorics 19(1) (2012), P66: https://www.combinatorics.org/ojs/index.php/eljc/article/view/v19i1p66
- B. McKay, Ramsey graph collection: https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
- Public 35-vertex `(4,6)` graphs: https://users.cecs.anu.edu.au/~bdm/data/r46_35some.g6

## Next steps

1. Reproduce the Few Shots baseline verifier result locally.
2. Fetch the 37 public 35-vertex graphs and preserve provenance/checksums.
3. Implement an exact one-vertex-extension solver and independently validate its output.
4. If all 37 seeds are non-extendable, preserve the UNSAT evidence/results and begin bounded destroy-and-repair search around the most promising seeds.

## Work log

### 2026-10-27 — direction opened

- Read the Few Shots `take-a-shot` procedure, repository rules, p003 problem metadata, verifier, baseline certificate, and generated `FEWSHOT.md`.
- Read the `web-ingest` root and `science-boundary` workspace rules.
- Established `science-boundary/ramsey-r46/` as the sole durable research workspace for p003.
- Recorded the initial exact-extension formulation and validation requirements above.
