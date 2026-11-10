# Exact CP resource cores vs exploration novelty — 2026-11-09

## Current question and practical frontier

Can full job-shop CP-SAT extract *genuinely informative, small necessary cross-machine resource conflicts before constructing a better complete 30×20 schedule*, and can those conflicts deliver **incremental constructive improvements** over machine-selection diversity under matched CPU/time budgets? The ta41 record remains **2006**, no verified <=2005 certificate.

## Method, primary sources and no novelty overclaim

The key implementation issue is **documented OR-Tools behavior**, not a new theorem: [original CP-SAT CpSolverResponse source](https://github.com/google/or-tools/blob/stable/ortools/sat/cp_model.proto) states `sufficient_assumptions_for_infeasibility` is minimized only in single-threaded **feasibility**, not optimization; otherwise it includes all assumptions. [OR-Tools troubleshooting](https://github.com/google/or-tools/blob/stable/ortools/sat/docs/troubleshooting.md) recommends separately debugging infeasible assumption models. Thus our incumbent-change-minimizing CP model, despite using one solver worker, could **never meaningfully minimize its infeasibility explanation** without removing its objective. Our former phrase *dynamic conflict learning* was misleading: the feedback was effectively machine selection novelty.

In pinned [OR-Tools v9.14 Python](https://github.com/google/or-tools/blob/v9.14/ortools/sat/python/cp_model.py), `CpModel.clear_objective()` exists and removes the integer and floating-point objective. This permits two correct explanations modes:
1. `precise-core`: reconstruct a full feasibility-only 600-interval job-shop model with unchanged hard NoOverlap, job-chain, retained machine-order guard assumptions and makespan target, to extract a smaller sufficient machine-core. Source `machine_group_order_repair.py`.
2. `precise-inline`: reuse the SAME model, call `clear_objective()`, and solve again at a secondary capped budget. This avoids Python model rebuilding. A core is accepted only if the second solver independently returns **INFEASIBLE**, not UNKNOWN. Source/metadata in each trial's `completion.explanation_probe_*`.

Neither standard CP assumption explanation nor incumbent-aware CP ALNS is claimed as new: [Kasapidis et al. 2025 ALNS-CP](https://doi.org/10.1016/j.ejor.2024.08.010) uses long-term operation-pair solution history and CP repairs; [Lin and Yang, Nov 2026](https://doi.org/10.1016/j.cie.2026.112299) uses selective keep/release and CP in dynamic flexible job shop. [Ba, Liu and Yuan 2026](https://doi.org/10.1016/j.cor.2026.107610) materially advances N7 batch evaluation, so genuine modern N7 remains the principal comparator.

## Correctly sourced independent basins and 5-second comparison

Public source-N7 C++ kernel pinned to `Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8`; **20 seconds native N7 cold search** from random per-instance starts, then two independent stage seeds, search input contains only instance and independent 20x30 machine-order parent (not hidden ScheduleOpt full witness). Exact targets are confirmed *only after* runs against separately verified ScheduleOpt archived 600-operation machine orders.

| Family | Original-N7 independent starts | Paired trials | dynamic CP-core success/gain | true author N7 success/gain |
| --- | ---: | ---: | ---: | ---: |
| Taillard ta42–47 (development) | 12 | 24 | 15/24, mean +0.667 | 9/24, mean +1.208 |
| Taillard ta48–50 (held out) | 6 | 12 | 9/12, mean +1.500 | 7/12, mean +2.083 |
| DMU dmu16–20 + dmu56–60 (different family) | 20 | 40 | 29/40, mean +1.550 | 30/40, mean **+10.650** |

DMU genuine N7 vs group dynamic: group **8 better / 5 ties / 27 worse** in pairwise final score, despite similar rate of *any* improvement. DMU N7 gets large improvements, while the present group CP stops at first score-1 improvement.

### Fundamental control: no-core *novelty-only* machine selector

`novelty` does NOT read the CP returned core at all. It prioritizes a machine based on how often it was **closed in previously tested machine groups**, normalized by `1/sqrt(number closed)`. Same full resource repair, initial criticality, seed and time budget. It is compared to `dynamic`, which weights a machine by membership frequency in `sufficient_assumptions_for_infeasibility` from the incumbent-disruption MINIMIZING CP.

Across all **76 paired trials / 38 independent starts**:
- dynamic **better 2**, **equal 71**, **worse 3** than simple novelty;
- total net dynamic objective gain over novelty just **+1 makespan unit across 76 trials**. No demonstrated structural conflict-learning advantage.
- Independent audit of 20 DMU starts, first second-stage seed: **441/441 source minimization-model sufficient UNSAT machine cores were exactly the complement of the opened machines**—ZERO smaller-than-complement. The source-core weight is therefore essentially search exposure/novelty in this setting, not an informative resource dependency predictor.

Primary evidence: `results/novelty-only-<family>-<seed>/summary.json`, per-start `results.json`, and `results/machine-group-crossfamily-judged-<family>.json`.

### Why simply adding a second full CP was a poor 5-second algorithm

A full feasibility-only re-solve **does** extract informative small machine-core proofs: `audit_machine_core_information.py` on independent ta43/ta46/DMU17/ta41 starts returned original **15–17 closed machine assumptions**, refined to **3–9** in independently confirmed INFEASIBLE full resource models, without using any hidden target schedule.

But `precise-core` reconstructed a second 600-interval model within a strict 5-second wall-clock search budget and only improved **26/76** compared with novelty's **56/76**. It did not recover sufficient small cores in selected sample traces: many second calls returned UNKNOWN after exhausting the 0.2s probe cap. Performance was strictly worse; correct explanation is not automatically an effective search strategy, and cost parity matters.

The `precise-inline` same-model approach was verified in a 7-second smoke test: with 0.35s explanation probe, DMU17 extracted **17/18** smaller fully proved cores, and DMU60 **16/17**; Taillard ta43 probe was UNKNOWN **17/17** under this small budget. None of the three smoke runs generated a better complete schedule during their respective 7-second caps. This is a negative result for *per-attempt* expensive explanation, not for the soundness of the cores.

**Running next**: `temp-ta41-amortized-precise-core-transfer.yml` tests sparse same-model core extraction every fourth failed group, 0.35s probe, strict total 5s, across the 76 matched source-N7 trials and novelty controls. Only the final independent full-DAG scores count as constructive progress.

## Does target depth explain the poor N7 mean quality?

One 5-second DMU experiment per fixed hard deadline depth (not an ex-post best-of-many combined run; thresholds examined after seeing the development discrepancy):
- `Cmax <= incumbent - 1`: success **29/40**, mean makespan gain **1.55**.
- `Cmax <= incumbent - 5`: success **19/40**, mean gain **2.775**.
- `Cmax <= incumbent - 10`: success **6/40**, mean gain **1.65**.
- `Cmax <= incumbent - 20`: success **0/40**, mean gain **0**.

Thus arbitrary one-unit stopping explains *some* but not all of the original N7 gap; the group-CP family still lacks a way to propagate multi-stage improvements through changing resource bottlenecks within a 5-second search.

Evidence: `results/dmu-target-drop{5,10,20}-dmu{16-20,56-60}-{1901,1911}/summary.json`.

## Exact ta41 structural preconditions and constructive status

For original verified ta41 Cmax 2006:
- Independent full NoOverlap CP `results/machine-budget14/decision.json` proves all <=2005 schedules differ in **>=15 of 20 original machine order permutations**.
- Independently rebuilt full CP `results/ta41-mandatory-adjacent-gateways-independently-proved.json` proves any <=2005 schedule must invert >=1 of 21 specified original adjacent machine-order relations.
- These conditions are **necessary, not sufficient**. Full 20-machine group CP and reified 580-orientation models under 5s–95s yielded UNKNOWN/no 2005 witness; do not interpret as proof of infeasibility. No Few Shots submission.

## Future research decision

The exact and reproducible evidence supports **reformulating the search state**, not making the learned-core score more complicated:
- The current iterative keep/release selector makes a complete CP repair under a fixed target then stops at the first witness, so it cannot naturally pursue long N7-style improvement trajectories. A stateful incumbent-updating or replacement-critical-path repair with multi-machine *joint* ejection is the next constructive mechanism hypothesis, not simply more core collection.
- A core is an informative constraint only if the independently scored search policy gets incrementally better than a no-core selection-memory control under the same search cost.
- Preserve the public 20x30 complete machine certificates and independent DAG score checks; avoid ta41 2005 claims without official Few Shots verification.

All implementation, results and negative tests committed under `science-boundary/job-shop-ta41` on `main`; no unpublished/private data.
