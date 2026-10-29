# Dynamic Critical-Path Replacement Repair — mechanism pilot (2026-10-29)

## Exact hypothesis

Given the same ta41 incumbent, search operator, scoring budget and uphill envelope, selecting the *next* neighborhood based on the machine edges which became newly critical **after** the last accepted modification will (a) alter the sequence of bottleneck repairs, and (b) more often discover a schedule Cmax<2006 than selecting operations from static baseline bottlenecks, certified fixed-core arcs, or uniformly random positions.

This is an original testable synthesis, **not** a reproduction of either underlying paper.

## Primary sources, boundaries of what they establish

- Ba, Liu, Yuan (2026): [A batch approximate evaluation method for neighborhood solutions in job shop scheduling](https://doi.org/10.1016/j.cor.2026.107610), *Computers & Operations Research* **195**, 107610. A Sep 2025 SSRN draft is [SSRN 5527219](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5527219). The paper develops a slack-time recursive N7 neighborhood batch *approximate evaluation* with linear complexity in batch size, more efficient tabu search. It does **not** demonstrate the dynamic bottleneck-replacement feedback proposed here. Our first implementation uses **exact DAG scoring** and N7-inspired bounded critical-block insertion moves; no source-level N7 faithful implementation or their reported complexity is claimed.
- Liu, Li, Gao (2026): *A Knowledge-Driven Decoupling and Coordinated Optimization Framework Based on Decision-Variable Parameterization and Release for the Job-Shop Scheduling Problem.* [ScheduleOpt/benchmarks/jobshop/README.md](https://github.com/ScheduleOpt/benchmarks/blob/main/jobshop/README.md) lists **LLG2026, 17 bound contributions across ta and dmu**. A complete public methodology/implementation was not identified in the initial survey, so the implementation below **cannot claim** to reproduce their decision-variable parameterization; only the general idea of dynamically selecting coupled variables is transferred.
- The same ScheduleOpt source still lists ta41js bounds **[1926, 2005]**, the 2005 score is historical with no published full solution in `solutions.json`. Our official Few Shots baseline remains the verified **2006** certificate.
- Prior exact ta41 finding, [distance-vs-coordination-2026-10-29.md](distance-vs-coordination-2026-10-29.md): 15 independent tiny swaps can jointly preserve score 2006; particular harmful swaps become neutral after 1–2 enabling steps, verified by all `2^15` subsets. Thus feedback of newly critical arcs is a plausible mechanism, but not yet proven useful for **2005**.

## Controlled first pilot

Program `dynamic_critical_replacement.py` tests four policies and two independently verified starting schedules:

- **dynamic**: update all critical machine arcs after every accepted insertion; next attention set starts with *newly emerged* bottleneck arcs, falling back to the current critical set.
- **static**: position candidates around original 2006 critical and near-critical machine edges without updating the attention set.
- **core**: position candidates around 21 certified no-2005 machine precedence arcs from `results/consensus-five-parents/consensus-analysis.json`.
- **random**: position candidates randomly on all machine sequences.

The **same** N7-inspired single-operation insertion operator (up to five positions), independent full-DAG candidate scorer, 24 candidates per step, 18,000 candidate evaluations per trial, limit of best-score+65 for temporary uphill moves, restart every 220 no-best steps, and seeded random generator are applied to every policy. Parents: original Few Shots 2006 and independently Few Shots-verified `gateway-124` with just 30 Kendall inversions from original, already reversing a necessary core arc. Pilot matrix = 4 policies x 2 parents x one common seed 4107, eight jobs. Code/test workflow: `temp-ta41-dynamic-critical-replacement-pilot.yml`. No original paper batch evaluator implemented yet because the first question is whether feedback is valuable under **equal exact scoring cost**, not whether batch approximation is faster.

Primary outcome: independent valid machine-order certificate with makespan <=2005. Secondary outcomes: best/median makespan at fixed evaluation budget, viable candidate rate, number of accepted moves that replace critical machine edges, number of neutral/temporary-uphill moves, and time to threshold. The code records exact critical-edge replacements after every accepted move for **all** policies; only the dynamic arm feeds these edges back into candidate selection. This avoids conflating an instrumentation difference with a causal policy effect.

### Caveats and decision rule

- A single seed and a small pilot establish *feasibility* and detect broken mechanisms; no statistically defensible performance advantage should be claimed from this pilot.
- If all arms remain at 2006, inspect whether dynamic replacement events happened and whether critical arc targets actually changed; if replacements are numerous but no improvement, the next search should not simply increase epochs. Instead **jointly release** old and replacement bottleneck arcs in one coordinated CP/large-neighborhood operation and benchmark using matched budgets.
- If a policy improves to <=2005, validate `certificate.json` using Few Shots official `verify/verify.py`, recheck the current public 2005 historical value, and only then submit.
- Do not call N7-inspired bounded insertions the full N7 neighborhood, and do not attribute untested dynamic feedback to the 2026 articles.

## Results: first equal-evaluation pilot (eight controlled runs)

All eight pilot Actions completed successfully at **18,000 exact full-DAG candidate evaluations each**, seed 4107; all remained **makespan 2006**, with zero certificate at <=2005. The replacement-edge counts and number of accepted moves are:

| Starting verified parent | Policy | Accepted moves | Accepted moves with new critical edges | New critical edges counted | Best |
| --- | --- | ---: | ---: | ---: | ---: |
| baseline | dynamic | 307 | 296 | 3082 | 2006 |
| baseline | static | 629 | 181 | 2641 | 2006 |
| baseline | core | 593 | 449 | 5572 | 2006 |
| baseline | random | 659 | 94 | 1508 | 2006 |
| gateway-124 | dynamic | 679 | 662 | 5538 | 2006 |
| gateway-124 | static | 607 | 149 | 2281 | 2006 |
| gateway-124 | core | 594 | 445 | 5470 | 2006 |
| gateway-124 | random | 665 | 109 | 1569 | 2006 |

These counts **are not effectiveness metrics** in isolation: replacements per accepted move differ, some strategies accept more moves, and one seed does not establish a statistical advantage. They demonstrate that newly generated critical paths are being observed and fed into the dynamic move generator. The static/core/random ablations also generate replacement events because actual objective dynamics are observed even when the selector does not use them.

**Decision after pilot:** dynamic changes path geometry, but selecting the next isolated move still fails to improve makespan. Instead of simply multiplying iterations, run a second experiment with growing *operation-level CP release sets* constructed from the encountered replacement critical arcs, with matched release size, exact scorer and CP time caps. Implemented as `dynamic_critical_cp_repair.py` (eight jobs `temp-ta41-dynamic-critical-cp-repair.yml`); no result claimed until `results/dcprcp-*/dynamic-repair.json` exists.

## Previous launch reference

Pilot launched; results now verified. Inspect `results/dcpr-{baseline,124}-{dynamic,static,core,random}-4107/pilot.json` and any `upstream-verdict.json` before editing this section.

## Phase IV objective verification — completed

All six `optimize_core_feedback_subspaces.py` runs completed from the **actual** initial 240-operation released sets PLUS their subsequent CP-core-guided releases. The first run exposed a state-reconstruction bug (forgot the initial 240 released operations); repaired, rerun, and all six persisted with independently checked scores:

| Parent | Release strategy | Free operations | Solver status | Optimality lower bound | Independently scored feasible makespan | Runtime |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| baseline | degree | 312 | **OPTIMAL** | 2006 | 2006 | 102.341s |
| baseline | core_random | 288 | **OPTIMAL** | 2006 | 2006 | 0.451s |
| baseline | random | 336 | **OPTIMAL** | 2006 | 2006 | 5.220s |
| gateway-124 | degree | 288 | **OPTIMAL** | 2006 | 2006 | 70.726s |
| gateway-124 | core_random | 288 | **OPTIMAL** | 2006 | 2006 | 32.132s |
| gateway-124 | random | 336 | **FEASIBLE** | 1996 | 2006 | 105.008s |

These are full hard resource NoOverlap + all job-route constraints, with other survivor pairs fixed to the source 2006 schedule. Five subspace optimizations are rigorously **2006-optimal** (under CP-SAT's computational correctness); the sixth is still **undecided** (FEASIBLE 2006 does not exclude 2005, despite lower bound 1996). No target 2005 witness was found, so no shot was submitted.

**Causal conclusion:** dynamic path-replacement selects different candidate moves and produces many more replacement events, but *not* a better makespan at the matched budget. Greedy operation release—even guided by exact CP infeasibility cores—does not reliably dissolve the coupled 2005 barrier. Prematurely claiming core-guided success from earlier assumption UNKNOWN would have been wrong; full objective verification disproves that interpretation in five of six cases.

**Representation reassessment for next substantive effort:** remove the remaining survivor-pair **hard freezing** interface. Work instead with soft/selective precedence orientation variables plus objective-based repair that can reorient formerly frozen pairs jointly; crucially condition the repair on both old and newly emerged critical chains AND solver-derived conflict cores. Pre-register matched controls and inspect critical-path transitions, but prioritize official valid makespan improvements over the number of transitions. Do not merely scale the same fixed-survivor release search.

## Phase II and III verified: dynamic CP release versus core feedback

**Phase II — direct dynamic release is insufficient:** `dynamic_critical_cp_repair.py` accumulates newly critical operation endpoints over eight rounds, releases exactly 30 new operations per round, preserves the remaining jobs' relative machine order, and calls a full hard-NoOverlap 2005 decision oracle. Four policies x two verified parents x eight rounds = **64 separate exact CP-SAT decisions**, and **all 64 were INFEASIBLE** (zero UNKNOWN, zero target certificate) even after releasing 240/600 operations. All eight outcome logs: `results/dcprcp-{baseline,124}-{dynamic,static,core,random}-4107/dynamic-repair.json`.

This specifically tests operation identities selected adaptively from *successive* critical-path replacements, not a static time band. Yet the fixed-survivor partial-order interface remains restrictive. The solver usually rejects in presolve with zero conflicts. This is evidence about this representation, NOT a global ta41 makespan bound.

**Independent obstruction audit:** `audit_dynamic_repair_cores.py` reconstructed all eight final 240-operation neighborhoods using a fresh model, made every remaining successor precedence conditional on CP assumptions, and extracted sufficient UNSAT assumption cores (not necessarily minimal). The cores have **59, 66, 68, 83, 85, 86, 88, 95** pinned machine precedences across **9–17 machines**, even though all have already freed 240 operations. Source: `results/dcprcp-independent-core-audit.json`. Thus a moving critical path does not necessarily expose the still-fixed necessary resource relationships.

**Phase III — feedback from CP obstructions:** starting from the same 240 operations selected by the dynamic policy, `core_feedback_release.py` unlocks 24 more per round based on (a) maximum assumption-core endpoint incidence, (b) random core endpoints, or (c) uniform random operations; two parents. The first assumption-UNKNOWN radius occurred with additional releases:
- Baseline 2006: degree **312** total released; core-random **288**; unstructured random **336**.
- Gateway-124 2006: degree **288**; core-random **288**; unstructured random **336**.

**Critical caution:** in baseline core-random at 288 freed, a separate hard constraint solve returned **INFEASIBLE**, despite the assumption oracle returning UNKNOWN. The other five hard status checks were UNKNOWN after 12s. Neither a larger core nor first UNKNOWN is a proof of nearness to 2005 or evidence of an improved feasible schedule. Source: `results/core-feedback-{baseline,124}-{degree,core_random,random}/core-release.json`.

**Phase IV — actual objective check of these six subspaces:** `optimize_core_feedback_subspaces.py` uses the official 2006 starting schedules as full interval hints, minimizes makespan under the same partial survivor pinning with a 105s/four-worker CP budget, and records objective lower bounds / optimality / true certificates. Workflow `temp-ta41-core-feedback-objective.yml`. Do not claim results until `results/core-objective-*/objective-repair.json` exists. A score-2006 FEASIBLE result is not an optimality certificate, whereas OPTIMAL=2006 rules out its exact conditioned subspace.

**Mechanistic interpretation:** the first adaptive critical feedback implementation definitively changes critical-path identity much more often, but does not outperform controls on best makespan in the pilot. Its release interface still freezes hundreds of precedence arcs. The next qualitatively different idea, if all CP objective checks stagnate, is to jointly *reorient* relations via a soft baseline order with propagated conflicts rather than simply unlock more operation IDs in the same fixed-survivor model. The 2026 N7 batch paper accelerates evaluation, not this joint interaction, and the Liu-Li-Gao paper's exact parameterization release cannot be claimed reproduced from its ScheduleOpt citation alone.



## Phase V: counterfactual two-step coordinated critical-path replacement (complete)

To test the representation issue rather than simply release more operations, `replacement_macro_pilot.py` selects the **same first critical-path operation insertion candidate family** for every arm, applies a tentative move (its intermediate makespan may exceed 2006 by up to 180), recomputes the **new** critical path, and then chooses the **second** insertion according to either freshly created critical edges (dynamic), original fixed edges (static), 21-core precedence edges (core), or uniform random positions. Only the **final two-operation macro** is scored for acceptance, subject to a small final score envelope of 2006+24. No survivor precedences are fixed. This is an N7-inspired insertion, **not** a faithful full N7 implementation or the 2026 Ba–Liu–Yuan approximate evaluator.

Sixteen complete experimental runs (2 verified parents x 4 policies x seeds 4107/4113), exactly **22,000 full DAG evaluations per run, 352,000 total**, all stayed at makespan **2006**. Aggregated empirical behavior:

| Parent | Dynamic distinct visited states (two seeds) | Static | Core-guided | Random |
| --- | --- | --- | --- | --- |
| baseline | 71, 73 | 18, 29 | 18, 14 | 65, 87 |
| verified gateway-124 | 113, 118 | 23, 35 | 11, 20 | 55, 73 |

These are *distinct accepted schedules, including temporarily worse scores*, **not** unique 2006-equivalent optima. For instance baseline/dynamic seed4107 accepted 247 macros but only 16 ended exactly 2006; 231 ended above 2006, though no more than +24. Most accepted macros had an individually harmful first intermediate step, showing the macro is operational rather than simply cherry-picking separately good steps. Dynamic selection moves more frequently into alternate schedule geometry, especially from gateway124; no score improvement or statistical conclusion is claimed from two seeds.

The next *representation* test is **fully soft predecessor reorientation**, not operation release. The new `soft_reorientation_feedback.py` model makes **all 340 previously fixed survivor arcs reversible Boolean disjunctions**; no survivor order is hard-frozen. It keeps full job chains and NoOverlap, enforces one independently certified necessary 2005 core reversal, and minimizes makespan first, then policy-weighted reorientation costs. Policies dynamic/static/core/random and both 2006 parents have equal 130-second CP caps. The model is globally complete despite different optimization guidance; a score-2006 FEASIBLE outcome is not a global lower bound. Results pending at `results/soft-orientation-{baseline,124}-{dynamic,static,core,random}/soft-orientation.json`.



## Phase VI: full global model with soft rather than hard machine precedences

`soft_reorientation_feedback.py` made **all 340 previously hard survivor machine-order relations** explicitly reversible Boolean disjunctions, while retaining every job arc and all 20 full NoOverlap constraints. Its weighted policy choices were *objective guidance only*; the 2005 target remained reachable in principle. The model also required one reversal of an independently certified 2005 obstruction core as a necessary cut, and lexicographically prioritized makespan (10000x) over weighted flip count.

Eight 130-second CP-SAT runs (two verified 2006 starts x four policies) all returned **FEASIBLE at makespan 2006, never OPTIMAL**, and all found one core-reversing survivor-pair orientation. Reported best CP objective bounds were around 18710000–18750000, far too weak to prove anything about 2005. No exact score 2005 certificate exists. Source `results/soft-orientation-{baseline,124}-{dynamic,static,core,random}/soft-orientation.json`.

**Mechanistic diagnosis:** Simply softening all pinned arcs removes the earlier structural exclusion (no more immediate presolve INFEASIBLE), but the one-core cut is too weak to require a coordinated 2005-like repair: the solver can select a one-pair neutral gateway and stop at 2006. The remaining necessary structure comes from *multiple* independent UNSAT cores and the proven >=15-machine change theorem.

**Phase VII launched:** `all_core_orientation_repair.py` uses a fully unconstrained NoOverlap job-shop machine-order representation plus **nine separately verified necessary orientation cuts** (eight independently hard-checked cores + 21-arc consensus core) and the independently CP-SAT-proven >=15 changed machine orders condition. These conditions are necessary for any <=2005 schedule, not arbitrary heuristic hard freezes. The solver may still find 2006; FEASIBLE 2006 does not prove optimum. Four initial pilot arms (two parents x dynamic/core weighting) under equal 150-second limits. Only cite this as a *constructed test* until `results/allcores-*/all-cores-reorientation.json` exists and any strict improvement is officially validated.



## Phase VII result: nine independent conflict cuts can all be crossed at 2006

`all_core_orientation_repair.py` built a **globally complete** CP-SAT NoOverlap model (no hard survivor freezing) subject to (i) eight independently rebuilt sufficient 2005 UNSAT cores, (ii) the separate 21-arc consensus 2005 UNSAT core, and (iii) the independently proven necessary change to **at least 15/20 machine permutations**. Each cut is a disjunction of *true reversed pairwise orderings*, not a nominally removed assumption. All conditions are necessary for 2005, though far from sufficient.

Four 150-second pilots (baseline/gateway124 x dynamic/core soft-flip weighting) all returned **FEASIBLE score=2006**, never OPTIMAL. Each found **15 changed machine orders and exactly 21 reversed original adjacent relations**; each genuinely reversed at least one oriented relation in **every one of the nine certified core sets** (the independent cut-test counts were included per report). Solver objective lower bounds `187000000`–`187100000` still fall far short of proving 2005 infeasible.

This is a structural *existence* result: previously we knew a 15-inversion score-2006 neutral state that **did not** cross the 21-arc core, and a 30-Kendall neutral gateway state that crossed just one. The new 15-machine/21-baseline-adjacency candidates cross **all nine known necessary obstruction sets simultaneously** while keeping score 2006. They are not score breakthroughs; they could be useful neutral starting points for adaptive new-bottleneck repair.

**Reproducibility caveat:** The initial four pilots saved verified DAG scores and complete cut counts, not the resulting 20x30 permutations. A single replay with the same pinned solver version is launched via `temp-ta41-ninecore-neutral-certificate.yml` to retain a full `neutral-certificate.json` and have Few Shots officially validate score 2006; do not cite the *new* replay schedule as independently certified until the verdict file exists.

Next decision: only if this nine-cut neutral certificate is officially valid, resume new-critical-path macro search *from that exact orientation class*, rather than simply rerun the original baseline. The real open question remains reaching **2005**, not just crossing a growing collection of necessary disjunctions at score 2006.

