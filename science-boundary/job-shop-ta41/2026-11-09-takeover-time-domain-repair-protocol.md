# 009 takeover: prospective time-domain coordinated repair protocol (2026-11-09)

## Status and boundaries
This is an **experiment specification**, not a completed experiment or improved schedule. Continue on `main` in this topic. Current independently verified ta41 score is 2006; a 2015 VLS appendix reports historical 2005 without a machine-order certificate.

## Why representation changes
Independent 20-second native-N7 elites in 10 DMU 30x20 instances showed that full-machine-group CP is constructive but native N7 yields larger average improvements. Dynamic core weights tied random release; real second-elite A/B adjacency flags tied count-matched fake flags. Native N7 4s + CP 1s yielded complementary improvements but lower mean improvement than 5s native N7. Therefore do **not** retune the same whole-machine priority score, or claim novelty for CP cores, ejection, or FDS.

## New falsifiable hypothesis
Given a tight horizon `H=Cmax-δ`, *partial scheduling time-domain failures* reveal a **joint set of operations and resource orientations** whose simultaneous reconsideration can open an improving route; this information is more actionable per CPU second than static critical path, random matched-size operation release, and native N7 continued search.

Unlike prior machine-group release, the decision variables are a coupled **resource arc plus start-time-bound** frontier. Model full intervals, job precedences and NoOverlap, with an incumbent machine order used as reversible assumptions. Start from a limited set of time-domain decisions derived **solely from original incumbent, instance, and propagation** (never reference target). Record each conflict as a sound conditional implication or sufficient infeasibility core under its exact assumptions. Grow the repair set by re-propagating after each proposed release and admitting newly affected resource arcs. Reoptimize all admitted arcs and time variables jointly. Completion returns a full feasible schedule or UNKNOWN, never a claimed proof of nonexistence.

## Constructive baselines (same starts)
1. Original native N7 5 seconds, unchanged source kernel.
2. Native N7 4 seconds then random matched-size CP operation/arc release 1 second.
3. Native N7 4 seconds then static slack/critical-block CP release 1 second.
4. Native N7 4 seconds then failure-driven time-domain joint release 1 second.
5. Optional native N7 4 seconds + ordinary unrestricted CP solver 1 second, and CPU-matched two-N7 portfolio.

Prespecify evaluation on independent N7 elites not used to tune parameters: prefer genuinely untouched Taillard and DMU starts beyond the already consumed dev/holdout sets. Within each instance, cluster repeated method seeds as one unit of statistical independence. Separate wall time from actual summed CPU-core seconds; use 1 solver worker for primary fairness, or compare equal CPU budgets. Include orchestration cost and run under identical hardware whenever feasible. Fixed `δ` must be chosen on a training partition only; test δ=1 and an unmodified deeper-target arm if tunable on development.

## Measurements / acceptance
Primary: best verified final Cmax decrease across starts under equal CPU and wall budgets; paired difference against original N7, with per-instance bootstrap confidence intervals. Secondary: strict improvement rate, time to first and best improvement, distinct improved basins, resource release count, arc inversion/Kendall distance, conditional conflict precision, solver UNKNOWN percentage, and independent 600-operation DAG verification.

**Stop/go rule:** if proposed failure-driven feature cannot beat the random and static controls prospectively and produce an aggregate gain competitive with native N7 (or a clearly defined equal-CPU portfolio), treat the current representation as falsified and redesign the joint variable interface instead of scaling ta41 hours. Any ta41 2005 claim requires a full machine-order certificate and independent verifier.

## Primary sources and prior art
- Vilím, Laborie, Shaw (2015), *Failure-directed Search for Constraint-based Scheduling*: https://vilim.eu/petr/cpaior2015.pdf
- VLS primary appendix, historical tail41 2005: https://vilim.eu/petr/cpaior2015-results.pdf
- Nagata and Ono, IEBO (2018): https://doi.org/10.1016/j.cor.2017.09.017
- Ba et al., N7 batch approximate evaluation (2026): https://doi.org/10.1016/j.cor.2026.107610
- Local controls and evidence: `crossfamily-target-and-elite-information-2026-11-09.md`, `cross-family-dmu-transfer-and-core-information-2026-11-09.md`, `n7_then_group_cp.py`.

## Immediate implementation checkpoint
First implement/verify a source-only **time-domain decision log** on an existing ta43 1888->1887 positive control, keeping its 1887 witness inaccessible to the search. Compare blind first-pass release choices with the hidden witness *only offline*. Only then expand to untouched independent N7 elite starts. This protocol is prospective; no such execution is claimed here.
