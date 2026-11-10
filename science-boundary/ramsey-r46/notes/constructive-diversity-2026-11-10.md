# p003 constructive search update — 2026-11-10

## Verified incumbent

- The verified 36-vertex near miss is still **12 K4, zero independent 6-sets, 260 edges**: `results/compound-repair-36-12-defects.json`.
- Action [42504813562](https://github.com/teddyli18000/web-ingest/actions/runs/42504813562) **completed successfully**, deterministically reproducing the 14→13 (iteration 135)→12 (iteration 136) transition with a separate full-graph recount. This is a real improvement in *candidate defect count*, not a new Ramsey bound.
- [42504776739](https://github.com/teddyli18000/web-ingest/actions/runs/42504776739) tested twelve selected vertex-regrowth neighborhoods for an exact `K4 + I6 <= 11` target. Seven specified frozen-core neighborhoods returned UNSAT and five larger neighborhoods returned UNKNOWN / timeout. There was **no new witness**. Do not generalize fixed-neighborhood UNSAT or solver timeouts to the complete 36-point problem.
- The public lower/upper range remains 36–40 in Radziszowski's 2026 survey and the current Ramsey problem overview.

## New constructive diagnosis and experiments

**Why three-edge and short-compound moves plateau.** A local independent C++ polynomial evaluator derives the exact defect count under any up-to-three-edge flip from the original graph: for every potential forbidden K4 or independent-six subset, its indicator is expanded in the edge-flip variables through degree three. Coefficients are summed across all subsets. Thirty random triple changes were independently compared with full K4/I6 recount and agreed. Among **11,256,105 distinct three-edge sets that include an edge of an existing K4**, no resulting score was below 12. Any score-improving triple must include such an edge because the base graph has I6=0. This is an exact *local* fact, not the goal or a global impossibility result. An exploratory beam seeded by low-defect triples made coordinated 4–12-edge changes but likewise did not improve 12 within its sampled frontier.

**Neutral-network search.** Despite the triple barrier, some **five-edge joint changes** reach different full 36-vertex graphs with the same 12 defects. A beam over up to eleven changes found a score-12 graph **11 edge flips from the original** and independently recounted it. Recentring on that graph returned to score 12 within the tested beam. The next mechanism should preserve **genuinely different high-quality parents** across iterations rather than repeatedly selecting very close equivalents of the same elite.

**Core recombination feasibility check.** The 12 K4s have a five-vertex hitting set; there are 64 five-tail sets whose removal leaves a legal 31-vertex core. Only a small fraction of these cores allowed even a single individually legal new tail (typical legal-tail catalogue zero, largest observed 54). Jointly assembling five new individually legal tails from the 54-mask domain yielded high defects (~181 in a short search), so this particular fixed-31-core recombination is not competitive. There are also 1,984 six-tail hitting sets leaving a legal 30-core; a pilot from a domain of 160 legal masks reached only 91 defects. These *construction quality* measurements do not exclude all other core decompositions.

**Coordinated repair ILP pilot.** Deleting a minimum seven-edge cover of all 12 K4s creates 138 independent six-sets. Adding edges while forbidding the seven deleted edges and insisting on K4-free and I6-free was infeasible under one selected fixed-edge formulation. Allowing other internal edges to change produced 0-K4 but hundreds of I6 (e.g. 616) and no improvement. The failure is evidence about the frozen-cover representation; simply adding more deletion-only trials is not presently justified.

## New active construction family

- `compound_repair_diverse.py` implements structural diversification of the successful delayed-acceptance K4/I6 conflict-cascade move. It retains elites only if they differ by a meaningful undirected-edge Hamming distance, permits crossover between distinct elites before the repair cascade, randomizes repair depth, and saves both strict defect improvements and independently auditable same-score candidates far from the initial graph.
- The eight-job experiment [42855098306](https://github.com/teddyli18000/web-ingest/actions/runs/42855098306) starts independently from **both** the former 14-defect graph and the verified 12-defect graph, with multiple seeds/depths. Each emitted 36x36 matrix is independently recounted for exact K4/I6; zero-defect output is additionally passed to the Few Shots official verifier.
- Success criterion: either an independently recounted **score <= 11** full graph, or a diverse parent set that materially differs in structure and provides a new, reproducible constructive basin. A green GitHub job alone is not a mathematical breakthrough.

## Next decision

Once the eight jobs finish, compare exact candidate scores **and** parent diversity. If none beats 12 and diverse parents collapse to near-identical structures, stop expanding this same compound-swap parameter grid; explore a different jointly optimized graph representation instead. No claimed lower-bound improvement until a 36-point zero-defect certificate passes the official verifier.

## Primary references

- Few Shots p003: https://github.com/few-shots/few-shots/tree/main/problems/p003-ramsey-r46
- Exoo, *On the Ramsey Number R(4,6)* (2012), https://doi.org/10.37236/2102
- Radziszowski, *Small Ramsey Numbers* (2026 revision): https://www.cs.rit.edu/~spr/ElJC/sur.pdf
