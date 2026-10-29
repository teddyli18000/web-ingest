# Dynamic critical-path replacement: CP obstruction replacement and the release-interface trap (2026-10-29)

## Hypothesis and actual experiment

Question: after a moving-critical-path CP neighborhood is shown infeasible at Cmax <=2005, is it enough to selectively release a *small set of operation endpoints that invalidates all currently visible CP UNSAT witnesses*, or do equally hard replacement obstructions appear?

Parent experiments: eight independently checked 240-operation released subspaces (four critical-path selection policies x two officially verified makespan-2006 parents: baseline and gateway124). Each keeps **all hard 20 machine NoOverlap** plus 570 job precedences, but preserves survivor relative machine orders as extra hard precedence arcs. Every original 2005 decision was independently UNSAT. Sufficient, not minimal, CP assumption cores contain **59–95** still-pinned machine precedence arcs, on 9–17 machines. Source: `results/dcprcp-independent-core-audit.json`.

## Exact finite combinatorial bridge

Build an 8-column incidence matrix: operation `u` covers core `i` if `u` is an endpoint of **at least one precedence** in that sufficient core. The distinct core-endpoint universe has **406** operations. Exhaustive exact subset dynamic programming over the 2^8 core coverage masks proves:

- **Minimum hitting-set cardinality: 2 operations**.
- One lexicographically selected solution: **operation IDs {7,30}**, indexed as job*20 + job-position. Another valid size-2 cover is {30,93}; the choice of tie breaker is not scientific evidence.
- No single operation hits all eight prior core witnesses.

This does **not** say two operations are enough for a schedule improvement or that each whole UNSAT core can be made feasible. Hitting a sufficient core invalidates only that specific proof witness. The eight old cores also belong to *different* conditioned partial-order subspaces, so simultaneous coverage is a structural diagnostic, not a global cut.

## Controlled intervention and exact outcomes

`dynamic_core_hinge.py` reconstructs each of the eight original 240-released-operation sets. It releases two additional nonreleased operations, comparing the global two-operation hitting-set (backfilling an already released item with a local high-degree core endpoint when required) versus a deterministic random two-operation control. After each release it recomputes the machine survivor precedence partial order and independently reconstructs a full CP-SAT model with hard NoOverlap.

All sixteen models returned **INFEASIBLE**, with no target-2005 certificate. Detailed result:
`results/dynamic-core-hinge-replacement.json`.

| Measure | Minimum-hinge intervention | Matched random 2-operation release |
| --- | ---: | ---: |
| Cases | 8 | 8 |
| Invalidate the previous sufficient core witness | **8 / 8** | **4 / 8** |
| Newly returned CP UNSAT core after release | 8 / 8 | 8 / 8 |
| New core contains precedence arcs absent from the prior core | **8 / 8** | **8 / 8** |
| New core size range | 66–102 | 61–99 |
| New 2005 certificate | 0 | 0 |

**Independent hard re-verification:** `verify_dynamic_core_hinges.py` independently re-ran the assumption-core extraction and then constructed a completely fresh 600-interval model with ONLY the new core precedence arcs hard, plus job chains and all machine NoOverlap constraints. All **16 / 16** returned independently **INFEASIBLE**, 0.024–0.033 s hard-model time each. This establishes that all reported replacement cores really suffice to exclude the <=2005 deadline; it does not make them minimum cores. Evidence `results/dynamic-core-hinge-independent-hard.json`.

## What this means, and what it does not

The old core witnesses are not irreducible bottlenecks of the entire optimization problem. They can be disabled at very low *witness-hitting cost*, yet another independent obstruction immediately emerges in each tested conditioned subspace. Thus *counting newly disabled UNSAT cores*, like merely counting new critical paths, is a misleading stand-in for *candidate quality*. Core feedback only has explanatory value if it alters the **set of possible complete machine orientations**, not just which partial proof the CP engine returns next.

Crucial caveat: because the current model still freezes survivor relative machine order, the new core could simply describe another consequence of that very strong representation. We should **not** continue scaling core-hitting release inside the same fixed-survivor space, or claim that an improved ta41 schedule has to be far away.

## Representation reassessment / next test criterion

The actual frontier remains **official Few Shots best feasible makespan 2006**, while historical literature has reported ta41=2005 without a publicly available machine-order witness (ScheduleOpt and optimizizer disagree on benchmark upper bound). No new official score claim is made.

The next constructive experiment should operate in **complete global machine-pair orientation space**, with no survivor order frozen; use multiple independently validated 2006 parents and test *connected critical-block/path-relinking macro-moves* across the conflicting old/new CP cores. Crucially, apply a coherent group of mutually enabling disjunctive arc changes **together** and use full makespan, not core count, as the objective. A sensible benchmark is to compare this with an established N7/N8 tabu/path-relinking method at matched full DAG evaluations before attributing any advantage to dynamic core feedback.

Relevant prior art for evaluating candidate algorithms:
- Ba, Liu, Yuan, 2026, *A batch approximate evaluation method for neighborhood solutions in job shop scheduling*, [doi:10.1016/j.cor.2026.107610](https://doi.org/10.1016/j.cor.2026.107610): speeds up approximate N7 candidate evaluation, not the present core-replacement hypothesis.
- *A new neighbourhood structure for job shop scheduling problems*, *IJPR* 2023, [doi:10.1080/00207543.2022.2060772](https://doi.org/10.1080/00207543.2022.2060772): N8 critical-operation neighborhood compared with N5/N6/N7 (no direct ta41 success claim).
- ScheduleOpt [jobshop benchmark](https://github.com/ScheduleOpt/benchmarks/blob/main/jobshop/README.md) describes a 2026 memetic elite-population path-relinking/N7 method by Hernan Diaz Rodriguez that improved DMU bounds; its individual ta41 performance has not been demonstrated.

## Reproduction

- `python science-boundary/job-shop-ta41/dynamic_core_hinge.py` (OR-Tools 9.14.6206).
- `python science-boundary/job-shop-ta41/verify_dynamic_core_hinges.py`.
- GitHub Actions runs `40882283462` and `40882630518` both completed and were validated by checking persisted result JSON files.
- All core IDs are operation IDs `20*job + operation_position`, zero-indexed, not machine IDs.
