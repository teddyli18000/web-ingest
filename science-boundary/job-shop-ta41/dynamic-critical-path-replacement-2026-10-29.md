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

