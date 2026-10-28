# Job-shop scheduling — Taillard ta41 (Few Shots p009)

## Current state (2026-10-28)
- **Goal:** Find feasible machine orders with makespan <=2005 (prefer <=2004 for unambiguous literature novelty) against Few Shots' independently reproducible **2006** baseline. Benchmark is 30 jobs x 20 machines.
- Official [problem and verifier](https://github.com/few-shots/few-shots/tree/main/problems/p009-job-shop-ta41), [baseline certificate](https://github.com/few-shots/few-shots/blob/main/problems/p009-job-shop-ta41/baseline/certificate.json).
- Published lower bound **1915** (Coupvent des Graviers et al. 2025, arXiv:2504.16106). Do not confuse it with a feasible upper bound.
- **Important historical-record conflict:** Weise's 2020 JSSP literature aggregation and older scheduling references claim **ta41 UB=2005**, attributed to Vilím, Laborie & Shaw (2015) or earlier literature; the raw 2005 schedule is not available in these tables. Conversely the published certificate-based 2025/2026 tables use **2006**. A reproduced 2005 certificate would beat the Few Shots verifiable baseline but **must not be presented as an unambiguous first-ever mathematical record**. Primary references: https://github.com/thomasWeise/jsspInstancesAndResults, https://zerothesis.com/challenges/jobshop-taillard-open?tab=brief, https://link.springer.com/article/10.1007/s10472-026-10007-3, https://doi.org/10.2139/ssrn.4938242.
- [Few Shots record chain](https://github.com/few-shots/few-shots/blob/main/problems/p009-job-shop-ta41/FEWSHOT.md) had no merged improvements at initial read.
- No new result is claimed until verified using the upstream verifier and `tools/check.py`.

## Approach / reproducibility
`search.py` downloads immutable-shape upstream instance and baseline (instance SHA256 checked), asserts baseline makespan 2006, and evaluates a candidate by topologically sorting all 600 operations with job and machine arcs; cyclic candidates are rejected. It explores adjacent critical-path machine swaps, tabu tenure and diversified restarts. Local output includes `certificate.json` and `search-result.json`.

```sh
python3 science-boundary/job-shop-ta41/search.py --seconds 300 --seed 41 --output science-boundary/job-shop-ta41/results/run
# Independent verification, from a clone of few-shots:
python3 problems/p009-job-shop-ta41/verify/verify.py /path/to/web-ingest/science-boundary/job-shop-ta41/results/run
```

The one-shot GitHub Action `temp-ta41-search.yml` runs fixed-seed experiments and uses the upstream verifier independently before publishing output. Its successful run is not itself a new record. On any breakthrough, also run Few Shots `tools/check.py` on the correctly packaged shot with the live record.

## First-principles reformulation (2026-10-28)
Rather than only vary local-swap parameters, ask the **binary feasibility** question: Does any schedule exist with makespan <= 2005? The incumbent's 580 adjacent machine precedences are individually optional clauses. We impose 600 true intervals, 20 global `NoOverlap` constraints, and job precedence unconditionally. The incumbent machine arcs become reified assumptions (keep or relax). Every UNSAT core produced under a subset of those assumptions is a **sufficient obstruction**: any better schedule must violate at least one retained machine-arc assumption in the core. The problem of minimally relaxing the incumbent therefore becomes a **hitting-set problem over learned cores**, followed by an exact CP-SAT feasibility check with the remaining 580 - |relaxed| arcs pinned. This is a falsifiable approach, not a claim of a novel general algorithm or a proof of infeasibility.

`core_guided_lns.py` implements that mechanism with deterministic seed, exact processing times, independent DAG rescore, and persisted evidence. An UNSAT response with assumptions only proves infeasibility **within that fixed-arc subspace**; UNKNOWN proves nothing. When a candidate is found, the Few Shots verifier is invoked on the result before it is trusted. See the one-shot `temp-ta41-core-guided.yml` action. This program requires OR-Tools CP-SAT 9.14.6206 (installed and pinned by the Action).

The hypothesis being tested is **coupled structural rigidity**: many incumbent arcs form mutually protecting sets, so moving one critical block alone cannot reduce makespan. If learned cores remain dense and the derived hitting set grows without producing improvements, change decomposition (partition jobs/machines by cut structure, or search start-time freedom directly), rather than extending the same search blindly.

## Results / negative evidence
- Two 720-second independent random-seed runs of critical-path tabu moves yielded 2006 (63,288 / 63,312 iterations). Their validated status applies only to the explored local neighborhood, not all schedules.
- Core-guided CP-SAT run: submitted to the workflow; results/status must be read from `results/core-seed4107/core-analysis.json` after it is actually committed. Do not assume success from code being committed.

## Evidence / literature
- Taillard (1993), *Benchmarks for basic scheduling problems*, EJOR.
- Reijnen et al. (2026), *Job shop scheduling benchmark: environments and instances for learning and non-learning methods*, Ann. Math. Artif. Intell., table lists 2006.
- Fernandez-Viagas, Talens & Prata (2025), *A speed-up procedure and new heuristics for the classical job shop scheduling problem*, EJOR, showing critical-path local search remains an active baseline; not itself the novelty here.
- Shylo & Pardalos (2008), published upper bound 2006, machine order reproduced in Few Shots baseline.
- Coupvent des Graviers et al. (2025), arXiv:2504.16106, improved LB 1915.
- [Optimizizer benchmark record](https://optimizizer.com/TA.php).
- [JSPLIB ta41 instance](https://github.com/tamy0612/JSPLIB/blob/master/instances/ta41).
- [ZeroThesis challenge brief](https://zerothesis.com/challenges/jobshop-taillard-open) summarizes historical algorithms, but is not an authoritative Few Shots record.

## Verified structural evidence (2026-10-28)

All numbers below refer to the official verified baseline schedule, not to the unknown global optimum.

- `results/critical-cut.json`: DAG dynamic programming enumerates **six** critical paths of length 2006, **69** critical operations, and **53** critical machine-precedence edges. A **minimum cardinality cut of one machine edge** (machine 16, job 26 -> job 9, edge ID 471) hits all six longest paths. Releasing that *partial-order edge* reduces the longest-path lower bound to **2005**. It does not produce a feasible permuted machine order.
- `results/coupled-precedence.json`: for all 53 critical edges, deleting that edge alone makes its literal reversal DAG-acyclic (`additional_cuts=0`). This is a **negative** for the hypothesis that alternate paths structurally force same orientation. But the partial relaxed graph omits the *new* machine-adjacency arcs created by real swaps: reversing edge 472 suggests a partial-order longest-path of 2005, yet the actual swap yields 2047. Reversing edge 471 yields 2065 in a partially constrained graph but the actual swap is **2081**. Therefore the main obstacle is not cycle closure alone; it is **new critical paths generated by replacement machine adjacencies**.
- `results/swap-probe/single-swap.json`: complete test of **all 580** adjacent swaps from the 2006 baseline. Exactly **zero** improve the score, **81** preserve 2006, **one** creates a cycle; all remaining feasible swaps worsen it. Exact neighborhood exclusion for **this incumbent only**.
- `results/core-seed4107/core-analysis.json`: CP-SAT with makespan **<=2005** (OR-Tools 9.14.6206) learned **1,433 distinct infeasible assumption cores**, core sizes **20–74**, across a 630-second campaign. A greedy hitting-set relaxation released up to **11** incumbent machine-adjacency constraints but did not reach a feasible candidate. Each core proves a necessary changed-precedence disjunction; none alone establishes global infeasibility.
- `results/machine-interfaces/machine-subsets.json`: exact CP-SAT checks unlock all operations on selected machines while pinning orders on the others. Sets `{16}`, `{1,16}`, `{1,3,11,16}`, all **8 machines** that host the 53 incumbent critical machine arcs `{1,2,3,5,6,11,15,16}`, and a set of 12 machines all returned **INFEASIBLE**, with the solver taking ~0.015–0.018s and zero conflicts. Thus changing **only the critical-arc machines cannot achieve 2005**; a noncritical-machine order must also change. This is a *specific-subspace* exclusion and should be independently rechecked via a second formulation if used in a formal paper.
- `core_hitting_set.py` separately seeks an exact minimum hitting set over the 1,433 core hyperedges; this would lower-bound the number of original adjacency precedences any 2005 schedule must violate. `exact_radius2.py` exhaustively enumerates 168,470 distinct two-adjacent-swap expressions, including noncommuting overlapping same-machine swaps; pending its committed result. Neither pending experiment is reported as a completed result.

### Key interpretation
The single-edge critical cut is a **lower-bound relaxation**; the machine permutation creates replacement edges and nonlocal delays. The structural research question is therefore **coupled replacement of resource-order constraints**, not merely selection of an old bottleneck edge to delete. The exact machine-subset exclusions demonstrate a hidden dependency on machines that carry no longest-path machine arcs in the incumbent. A solution route worth testing next is to let a solver identify a small set of **whole machines** (group assumptions), rather than individual adjacent arcs, that jointly must be released, and to solve coupled time windows over those machines.

## Search limitations / next research
Critical-path N1 adjacent moves can stall in local optima; a lack of improvement says nothing about global optimality. Next: richer N5/N6 block moves, path-relinking and elite pool, time-window CP-SAT/LNS, and stronger backbone/cut analysis. Avoid repeating identical seeds/tenures without changing the representation.

## Work log
- 2026-10-28: Read all repository and Few Shots instructions; inspected source instance, verifier and baseline. Implemented first reproducible critical-path tabu exploration. Outcome pending Action execution and official independent verification.

- 2026-10-28 (second pass): Cross-checked 2005 historical literature claim against later verifiable-2006 record; shifted from tabu-only heuristics to CP-SAT deadline feasibility and UNSAT-core-guided hitting-set relaxation. Code and Action committed. Await independent runtime evidence before claiming any result.

- 2026-10-28 (deep exploration): Launched/examined exact critical-path cut, coupled-reorientation, all 580 N1 swaps, machine-interface CP-SAT exclusions, and 1,433 UNSAT-core campaign; initiated exact core hitting-set lower bound and exhaustive two-swap search. See evidence files listed above. Do not infer a global impossibility result from any of these restricted computations.
