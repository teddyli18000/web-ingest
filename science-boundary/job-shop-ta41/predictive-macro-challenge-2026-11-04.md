# Predictive critical-path replacement: constructive search challenge (2026-11-04)

## Objective
Produce a fully verified ta41 schedule with Cmax <=2005. Secondary question: with the same *exact-DAG evaluation budget*, does targeting newly created bottleneck arcs after speculative changes outperform targeting current, static, or certified core arcs?

## Diagnosis from earlier work
The previous critical-feedback N7-inspired pilot replaced critical edges often but found no <=2005 schedule. A subsequent fixed-survivor CP repair released up to 240/600 operations but remained infeasible in 64 tested subspaces. Independently rebuilt models found sufficient remaining pinned-precedence UNSAT cores of size 59–95 (results/dcprcp-independent-core-audit.json). This is evidence of an unsuitable fixed-survivor CP representation, **not** proof that the final schedule is distant. Avoid scaling that representation again.

## Literature and strong competitors
- Ba, Liu, Yuan (2026), *A batch approximate evaluation method for neighborhood solutions in job shop scheduling*, COR 195, 107610, DOI 10.1016/j.cor.2026.107610: faster batched N7 approximate evaluation; this is **not** the origin of predictive critical replacement, and we do not claim to implement its exact approximate algorithm.
- Liu, Li, Gao (2026), *Knowledge-Driven Decoupling and Coordinated Optimization Framework Based on Decision-Variable Parameterization and Release*: ScheduleOpt credits 17 improved bounds across Taillard/DMU, not ta41. Full code is not confirmed publicly available.
- Li, Hao, Wu (2025 online / IISE Trans. 2026), *Combining hash-based Tabu search and frequent pattern mining for job-shop scheduling*, DOI 10.1080/24725854.2025.2532071; author PDF https://leria-info.univ-angers.fr/~jinkao.hao/papers/LiHaoWuIISETrans2025.pdf. Reports 13 new upper bounds and is a serious modern baseline. The present in-house tabu control is **not** a faithful reproduction of the full population/frequent-pattern method; no SOTA victory claims without a certified same-instance comparison.
- https://github.com/ScheduleOpt/benchmarks/blob/main/jobshop/README.md currently lists ta41 bound [1926,2005], where historical 2005 lacks a publicly listed full machine-order certificate. Few Shots' independently graded baseline is 2006.

## New executable construction
`predictive_macro_search.py`: for each full feasible machine-order schedule, evaluate candidate operation insertions (<=4 positions). Retain some temporarily worse first moves. **Counterfactually** compute the *new critical machine arcs in the speculative candidate* before committing, then focus step 2 on those replacement arcs. Repeat this for step 3; choose an entire legal sequence as a macro-transition without requiring every intermediate move to improve the incumbent. This is *exact speculative lookahead*, not a learned forward predictor. Every proposed candidate uses the full independent 600-node DAG makespan evaluator.

Six policies: `replacement` (new critical arcs), `current` (all current critical arcs), `static` (original critical arcs), `core` (21 certified baseline-core arcs), `random`, and project-local `tabu` (one-step critical-path insertion with visited-state tabu). Equal 16,000 exact DAG candidate evaluations, paired seeds 4107/9241, parents baseline/gateway-124 (both officially verified 2006), same operation-insertion radius, uphill cap and restart threshold. Extra critical-state recomputations and wall seconds are reported to avoid claiming equal runtime. Macro arms have multi-step lookahead unlike tabu by design, so a better score must subsequently be verified under wall-time-matched comparison as well.

Workflow `.github/workflows/temp-ta41-predictive-macro-headtohead.yml` runs syntax/360-score smoke then 24 conditions. Results: `results/macro-{baseline,124}-{replacement,current,static,core,random,tabu}-{4107,9241}/constructive.json`. If candidate<=2005, write `certificate.json`, independently DAG-score, and run Few Shots official `verify/verify.py`. No improved score is claimed before that.

## Decision rules
- Primary: best officially verified score and anytime success at *matched exact candidate evaluations and wall time*. Secondary: legitimate critical replacement frequency, explored state diversity.
- If replacement has no advantage, don't just scale iterations. Inspect whether compounds *unlock a mandatory one-of-21 gateway arc* without returning to the prior bottleneck. Change candidate representation or use a complete stateful release interface.
- Additional comparison with an actually runnable modern hash-tabu/elite-pattern method remains necessary before a state-of-the-art claim.

Status: pilot launched; results pending verification.
