# Precompletion resource-conflict inference and joint ejections — 2026-11-05

## Research question

Can a job-shop improvement algorithm identify, **before a complete new schedule exists**, which currently fixed machine precedence relations must be **jointly retracted and reoptimized** to achieve a smaller makespan?

**Short answer:** It can identify **sound necessary disjunctions** (not unique required individual edges), and on a real 30×20 independent N7 elite we now have a **constructive, exhaustively conditionally minimal 4-arc reorientation witness**. The generality and predictive superiority of the currently tested pairwise/energetic heuristics are **not** established; in preliminary tests the static critical-path heuristic is more effective. ta41 still has no official <=2005 certificate.

### Theory: conflicts exist before scheduling the remaining operations

Represent a *partial resource schedule* by all immutable job precedence arcs and a subset `E` of incumbent adjacent-machine precedence arcs. Other machine pairs are not ordered; full `NoOverlap` constraints are enforced only in final CP repair.

For target horizon `L`, compute longest-precedence-path head `h_u` (earliest start) and tail `t_u` (duration of u plus longest remaining path). Then for any two operations u,v sharing a machine, the choice u before v would impose `h_u + p_u + t_v <= L`. If this expression is larger than `L`, that order is impossible **while retaining E**. If **both** directions are impossible, every target-feasible completion must retract at least one **retained machine arc in the union of supporting head/tail paths**. This is a rigorous *disjunctive*, not singular, necessary condition. Standard disjunctive propagation, edge-finding and detectable precedence are prior art; it would be misleading to claim novelty for this test alone.

A higher-order certificate uses earliest/latest start bounds `ES_u=h_u`, `LS_u=L-t_u`. For any time interval [a,b] and a machine, each operation's compulsory overlap is `min(overlap(ES_u,p_u,[a,b]), overlap(LS_u,p_u,[a,b]))`. If the sum over that machine exceeds `b-a`, the partial schedule has **machine energetic overload**. Any improving completion must invalidate at least one supporting fixed resource-arc path. This is known resource-propagation theory, but its use as a *target-directed soft reorientation preference* is testable.

Third and strongest: add hard all-job arcs, full machine NoOverlap and deadline L to CP, but treat incumbent adjacent precedence relations as **assumptions**, not hard survivor constraints. A sufficient UNSAT assumption core gives a valid clause `OR(negate keep_arc_i)` in every improving target schedule. Follow-up cores after candidate arc removal reveal **replacement bottlenecks** before a full schedule is formed. Cores need not be minimal; repeated extraction is not a complete autonomous scheduling algorithm.

Primary prior art:
- Nagata & Ono (2018), [IEBO: A guided local search with iterative ejections of bottleneck operations for the job shop scheduling problem](https://doi.org/10.1016/j.cor.2017.09.017). Explicitly works in partial schedule space, alternates insertions and ejects obstructive operations, DP enumerates feasible ejection patterns under improved deadline. We have NOT reproduced IEBO or invented iterative ejection.
- CP edge-finding, energetic propagators: [SAS Edge-Finding documentation](https://support.sas.com/documentation/cdl/en/orcpug/66101/HTML/default/orcpug_clp_details22.htm); [Juvin et al. CP 2023 disjunctive overload/edge finding](https://drops.dagstuhl.de/storage/00lipics/lipics-vol280-cp2023/LIPIcs.CP.2023.19/LIPIcs.CP.2023.19.pdf).
- Ba, Liu & Yuan (2026), [N7 batch approximate evaluation](https://doi.org/10.1016/j.cor.2026.107610): algorithmic acceleration, not proof that dynamic bottleneck replacement solves ta41.

## Controlled mechanism experiment: prediction accuracy is not enough

Reproducible scripts `partial_resource_pair_repair.py` and `audit_partial_resource_witnesses.py`, generated data `positive-n7-elite-data/ta42js..ta47js-*/start.txt` (12 independent genuine N7 elite 30×20 starts). Search sees only source schedule and target `L=Cmax(start)-1`; published stronger machine orders are read only during post-hoc independent audit.

For every start, first remove a minimum-critical-path cut of incumbent resource arcs until the remaining partial precedence DAG has longest path <= L. In the 12 withheld-answer controls:
- **8** double-forbidden operation pair witnesses and **56** machine-energetic window-overload witnesses were detected.
- All **64** witness disjunctions were independently consistent with an archived *complete legal improving schedule*: that schedule reversed at least one retained incumbent machine-arc from each witness's support set. Thus **no observed false necessary-condition claim**.
- Yet top-20 released incumbent arc predictions (12 controls aggregate) intersected known archived oracle reorientations: static critical-path `101`, pairwise `96`, energetic `90`. The reported precision is *relative to one hidden historical witness*, not a universal set of obligatory arc changes. The pairwise/energetic signals have low coverage, typically disappear after 20–40 releases, while complete full-NoOverlap models often remain UNSAT.
- A four-case matched test of 10 rounds × up to 20 newly released incumbent adjacent arcs per round (ta41, independent N7 ta42, ta43, ta46) found only one constructive gain: `ta43js-n7elite1711`, static policy `1888→1887`, independently DAG-verified. Pairwise, energetic, and random strategies were all still INFEASIBLE inside their conditioned partial-order subspaces after up to 201 arc releases. These are **subspace exclusions**, not global results.

Results:
- `results/partial-resource-oracle-audit.json`
- `results/partial-pair-{ta41,ta42js-n7elite1701,ta43js-n7elite1711,ta46js-n7elite1701}-{bidirectional,critical,random,energetic}/partial-repair.json`

**Diagnostic conclusion:** Two-operation and single-machine overload tests are valid but mostly explain only the *first* very tight resource obstruction. They do not capture the many transitive multi-machine conflicts that replacement resource paths cause. Changing the representation again is justified instead of increasing release counts.

## Constructive step: global joint resource decisions under the target

`joint_soft_pair_completion.py` models all 600 operations and 20 NoOverlap constraints under hard horizon `L=C(start)-1`; for each of 580 incumbent adjacent machine pairs a Boolean independently chooses original direction or reversed direction. **No survivor adjacency is held fixed.** It minimizes weighted reorientations with four initial-information conditions: `uniform`, `static`, `energetic`, `cp-core`.

Matched **3 starting examples × 4 variants = 12 trials** (60s CP budget each, 3s initial CP-core extraction where applicable), all independent DAG-scored:

| Instance and original incumbent | Uniform | Static | Energetic | Precompletion CP-core |
|---|---|---|---|---|
| true N7 elite ta43: 1888 | **1887** FEASIBLE, 4 reversed adjacent pairs, 60s | **1887** OPTIMAL weighted soft-pair cost 4, 4 reversals, **0.795s** | **1887** OPTIMAL weighted cost 18, 4 reversals, 17.2s | **1887** OPTIMAL weighted cost 25, 4 reversals, 53.7s (23-arc sufficient core) |
| true N7 elite ta46: 2044 | **2042**, 10 reversed original adjacent pairs, 60s | **2042**, 13 reversals, 60s | **2043**, 11 reversals, 60s | **2043**, 11 reversals, 60s (20-arc core) |
| ta41: 2006 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

**OPTIMAL refers to the minimum weighted pair-flip objective under a hard target deadline, not a proof of global JSSP makespan optimality.** The full-model CP can construct stronger positive schedules, but **simple static criticality has not been beaten** and ta41 has no <=2005 certificate.

Sources: `results/joint-global-{case}-{uniform,static,energetic,cp-core}/joint-completion.json` and `certificate.json` for successes. Actual native strong N7 had ta43 1888→1885 in one 5s trial and ta46 2044→2042 in one 5s trial; thus we must not call CP state of the art on these cases.

## Exact four-arc counterexample: explicit *joint necessity* and local-move barrier

Freeze a **genuine independent 20-second source-N7 ta43 elite** (`positive-n7-elite-data/ta43js-n7elite1711/start.txt`), independently validated `Cmax=1888`. The **oracle is hidden from the solver**. Global static-weighted CP returns a legally complete score **1887** schedule, differing in just **9 Kendall pair inversions on 3 machines**, and reversing exactly four incumbent-adjacent relations:

| Baseline adjacent-arc ID | Machine | Baseline predecessor job | Baseline successor job |
|---|---:|---:|---:|
| 168 | 5 | 24 | 11 |
| 199 | 6 | 13 | 21 |
| 257 | 8 | 13 | 18 |
| 258 | 8 | 18 | 5 |

**Exhaustive conditional minimal correction theorem:** Freeze the **other 576** original adjacent machine precedence arcs, allow only a subset of these four arcs to be released, and impose full NoOverlap, job routes and hard Cmax<=1887. Exhaustively test all `2^4=16` release subsets. **Every one of the 15 proper subsets is CP-SAT INFEASIBLE**, and all four released admit an independently scored **1887** schedule. This means these four are *jointly necessary and sufficient for the restricted family*; **not** that every globally improving schedule must reverse all four. `results/ta43-joint-4-arc-microstructure.json`.

**Exact local path barrier (same fixed endpoints):** Enumerate every complete machine-order state reachable by an adjacent transposition which *strictly reduces Kendall distance to the 1887 endpoint*. There are **80 feasible states over 9 distance levels** (by level: 1,4,8,12,15,15,12,8,4,1; no cycles). Exact minimax DP on all target-directed monotone paths proves **peak makespan 1920**, **+32 above the starting 1888**, although the endpoint is **1887**. Some first single moves score 1964 and 1920. This is a concrete example where *one atomic coordinated partial-order repair* crosses an objective barrier that every monotone one-swap route suffers, while total endpoint distance is only 9. **This is NOT a lower bound on paths that temporarily move away from the target**. Same JSON contains every intermediate move and the optimal minimax sequence.

**Independent second verification:** `independent_verify_joint_resource_quartet.py` independently rebuilt and rescored all 600 job+machine DAG operations (no reliance on `search.evaluate`), then rebuilt **16** separate full-NoOverlap assumption CP models. For all 15 infeasible strict subsets it extracted a fresh sufficient UNSAT core and re-solved an independent CP containing **only those core machine precedences**, again proving INFEASIBLE. All cores necessarily intersected at least one of the remaining corrective four arcs. All four removed gave an independent feasible improved machine order. `results/ta43-joint-4-arc-independent-audit.json`, run 42052446978 **success**.

### Exactly how replacement resource conflicts emerge *before* completion

From the validated 1888 parent:
- Initially keeping all 580 adjacency resource arcs yields an UNSAT core of **23** arcs, including corrective **257** but not the other three.
- After releasing 257, a new sufficient UNSAT core of **35** arcs contains corrective arcs **199 and 258**.
- After releasing 257 and 199, the new core of **39** arcs contains **258**.
- After releasing 257, 199 and 258, a **39**-arc core contains **168**.
- After releasing all four, the full NoOverlap CP produces the 1887 schedule.

Each new core was independently hard-model reverified; these core-replacement steps **exist before the improved complete schedule is computed**. BUT the particular sequence of 257→199→258→168 was reconstructed **post hoc using a known positive witness**, not yet autonomously selected by an oracle-blind policy. Replacing a core does not by itself tell us which of its many arcs to release.

This is the precise mechanism test for the user's hypothesis: **dynamic resource obstruction replacement can expose a coordinated correction set, but autonomous accurate selection remains unsolved.**

The initial core (size 23) includes only one corrective arc 257; simple static slack ranks the eventual quartet 257 / 258 / 199 / 168 at positions **8 / 9 / 59 / 82** of all 580 arcs. This explains why an algorithm which always selects only current top-critical arcs might miss needed secondary resource relations.

## Next discriminating test and representation direction

1. **Counterfactual core replacement ranking**: `counterfactual_core_replacement.py` constructs the exact partial-order assumption model and, for *each* candidate ejection in its current UNSAT core, simulates its removal to measure the replacement core's novelty and size **without ever constructing a full improved schedule or reading known solution arcs**. Three pre-stated stages probe R=empty, {257}, {257,199,258}, with true four-arc targets revealed only *after ranking*; workflow `temp-ta41-counterfactual-core-replacement-rank.yml`, run 42053010323. Status pending when this note was drafted. A useful predictor should rank true corrective arcs early *across other unseen genuine elite starts*, not only this one.
2. **Autonomous construction**: integrate small core-replacement lookahead in a partial-schedule ejection/repair procedure. Compare against simply sorting by original slack, CP-core degree, random and **genuine published N7**, at equal total wall-clock and CP cost, on *independently generated* ta42–ta47 N7 elites. Do not train on ta43 quartet and test on the same case.
3. **ta41 transfer**: only scale target 2005 searches if the autonomous predictor produces statistically meaningful constructive improvements on independent positive instances. On ta41 the four weighted full-global 60s CP trials returned UNKNOWN, no record. Historical reported 2005 still lacks a public machine-order witness.

## Software and data provenance

All code, runs and artifacts remain on `main` under `science-boundary/job-shop-ta41/`. OR-Tools CP-SAT pinned `9.14.6206`. Positive control start sources original 2025 Ming Qi published N7 20s runs, 30×20 ta43/ta46, independently validated from all machine/job start/end times; original instance sources ScheduleOpt archived public JSON. Exact machine orders stored in the winning `results/joint-global-*/certificate.json`. The improved candidate scorer is independent of the full resource CP model; further audit uses a separately rebuilt DAG and independent CP. No 2005 certificate has been produced or submitted.
