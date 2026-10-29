# Literature-first strategy reassessment — 2026-10-29

Scope: Taillard ta41 (30 jobs x 20 machines), Few Shots p009. **No new ≤2005 certificate has been found**. This note is a literature-driven change in research strategy, not another bulk experiment.

## Critical archival discovery: reported historical 2005 vs downloadable 2006

[ScheduleOpt benchmark](https://github.com/ScheduleOpt/benchmarks/blob/main/jobshop/README.md) lists **ta41js LB=1926 (OptalCP, 2026) and UB=2005 (CPO2015)**. Its source-of-truth JSON at [bks.json](https://github.com/ScheduleOpt/benchmarks/blob/main/jobshop/solutions/bks.json) says:
- UB=2005 in **2013 (NO2013)** and again in **2015 (CPO2015)**, but both entries have `certificate: "no"`.
- LB=1926 credited to OptalCP in 2026, with `certificate: "no"`.
- [solutions.json](https://github.com/ScheduleOpt/benchmarks/blob/main/jobshop/solutions/solutions.json) **does contain ta41js, but only makespan 2006**, as a 20x30 array of operation IDs. Thus it is *not* the missing 2005 machine-order certificate.

Coupvent des Graviers et al. (2025) [Gra25; https://doi.org/10.48550/arXiv.2504.16106] explicitly report 1915–2006 and **do not** publish a ta41 2005 schedule. Distinguish the historical published value from a reproducible witness. **Highest initial payoff is archival / contact original solvers / test alternative open code**; numerical ≤2004 would improve the publicly reported UB; reproducing 2005 would improve Few Shots' certified record only.

## Key genuinely new (to this project) papers and transfer hypotheses

1. **Zago et al. (July 2026), Neural Deconstruction Search for Flexible Job Scheduling**, *Machine Learning*. DOI [10.1007/s10994-026-07116-9](https://doi.org/10.1007/s10994-026-07116-9); official open code [dawoz/NDS-S](https://github.com/dawoz/NDS-S).
   - Instead of freezing the survivor machine order and using CP as a repair, NDS-S uses an *activity-list representation* of operation scheduling. Autoregressive policy removes selected operations (Q=10 in reported training) and reinserts in multiple orders with job precedence repaired. It evaluates complete schedules. The paper gives code and C++ schedulers; training is ~5–10 days, so start with **provided heuristics or pretrained models** if compatible, not a bespoke training run.
   - **Why it matters:** prior project release-by-jobs/time-band neighborhoods always preserved large survivor subsequences and were often UNSAT in ~0.03s. Activity-list repairs can change induced relative orders among many other operations as a byproduct, avoiding the very fixed-survivor interface causing the known obstruction. This is a *testable representation change*. First verify JSSP ta41 instance parser and job/operation convention against Few Shots; benchmark existing public code using an official certificate converter. No unverified score claims.
   - The paper reports Taillard performance by size group 30x20, *not individual ta41 scores*; do not claim it already attains 2005.

2. **Kasapidis et al. (2025), A unified solution framework for flexible job shop scheduling problems with multiple resource constraints**, *European Journal of Operational Research*, DOI [10.1016/j.ejor.2024.08.010](https://doi.org/10.1016/j.ejor.2024.08.010).
   - CP-based Adaptive LNS guided by *long-term memory of operation and operation-pair machine assignments* across high-quality, diverse schedules, reporting 39 new BKS in its more general flexible-resource benchmarks.
   - **Transfer limitation:** classical ta41 has a *fixed machine assignment*. Machine-assignment memory is degenerate here. Transfer the idea at the right semantic level: record **relative machine precedence pairs** and their joint frequency/anti-frequency over equal-score 2006 schedules; release disagreeing, high-entropy paired precedences in a connected cluster rather than freeze a machine subset. This is a new synthesis hypothesis, not the paper's tested claim. Monitor whether resulting interface actually differs from the 21-arc shared unsatisfiable core.

3. **Legrand, Kameugne & Schaus (May 2026), CP or DP? Why Not Both: A Case Study in the Partial Shop Scheduling Problem**, DOI [10.48550/arXiv.2605.23569](https://doi.org/10.48550/arXiv.2605.23569).
   - Hybrid dynamic programming over partial schedules + CP propagator feeds **newly forced precedence arcs** back into DP state; LNS reuses these constraints, with paper-reported JSP LNS restart schedule initially pinning 70% of additional precedences, dropping 5 percentage points per 100 failures and resetting below 20%.
   - **Transfer:** CP's forced precedence *closure* should be fed back to a stateful search decoder; previous CP-SAT jobs tried fixed subsets without such dynamic propagation feedback. Preserve only **provably forced** orderings; guessed edges are hypotheses, not global constraints. Authors themselves do not claim state-of-art in this case study.

4. **Yuraszeck, Werner & Rossit (June 2026), A Comprehensive Benchmark of Constraint Programming Solvers for the Makespan-Minimisation Job Shop Scheduling Problem**, *Mathematics*, DOI [10.3390/math14122179](https://doi.org/10.3390/math14122179).
   - Four engines, 332 instances, 600 seconds each, #optima: **OptalCP 191, CP Optimizer 166, OR-Tools 144, Hexaly 116**. Best engine is instance-dependent; optimum counts are **aggregate, not ta41 success claims**. Same paper reports 22 new UB on *other* mostly large Da Col–Teppan instances; ScheduleOpt benchmark notes some paper BKS were preempted by older/prior results.
   - **Major project mistake:** hundreds of CP-SAT variants do not cover solver diversity. First validate whether OptalCP preview, Hexaly or IBM CPO can be lawfully run in available environment and whether their APIs/limits can handle ta41; run a **small controlled, independent baseline** rather than speculative methods.

5. **Tsogbetse et al. (2024), Influence of encoding and neighborhood in landscape analysis and tabu search performance for job shop scheduling problem**, *EJOR*, DOI [10.1016/j.ejor.2024.07.028](https://doi.org/10.1016/j.ejor.2024.07.028). Different encoding changes locality/landscape. This is directly consistent with the observed >=15 machine changes and <=3 released-job exclusion: the problem is not necessarily far in a *better representation*.

6. **Gui et al. (2024), Domain Knowledge Used in Meta-Heuristic Algorithms for the Job-Shop Scheduling Problem: Review and Analysis**, DOI [10.26599/tst.2023.9010140](https://doi.org/10.26599/tst.2023.9010140). Strong concrete older principles: critical block insertions with feasibility tests, Nowicki–Smutnicki tabu search, large neighborhood variants and **path relinking / big-valley** across good but distant schedules. This suggests *connected, conflict-driven partial-order path relinking* between 2006 parents rather than naive per-machine independent crossovers (previous exhaustive crossovers failed). Historical prior art must be credited.

7. **Fernandez-Viagas, Talens & Prata (2025), A speed-up procedure and new heuristics for the classical job shop scheduling problem: A computational evaluation**, *EJOR*, DOI [10.1016/j.ejor.2024.11.026](https://doi.org/10.1016/j.ejor.2024.11.026). Acceleration for insertion construction, critical-based local search and composite heuristics—more directly relevant to ta41 than flexible assignment approaches.

## Current project evidence and mechanism

- Baseline makespan 2006, 600 operations, 20 machines.
- An independent CP-SAT no-core decision model proves <=2005 solution cannot differ from the 2006 baseline in <=14 machine permutations; >=15 changed machines are required. This says **nothing** about the distance in an activity-list sequence or dynamic partial-order schedule.
- All 4525 global job-reinsertion neighborhoods freeing <=3 jobs but keeping all other job relative machine orders were fully excluded, and independently audited (653 DAG and 60 sample hard-CP rechecks).
- Multistart fixed-survivor 6/8/10/12/15 job LNS produced 30 INFEASIBLE, 15 UNKNOWN; 45 optimization trials remained at 2006. Temporal time-band 60 trials yielded 43 INFEASIBLE, 17 UNKNOWN. Core reversal uncovered multiple verified 2006 schedules with different orientations, but no Cmax improvement.
- **Diagnosis:** repeated failures might be due primarily to the fixed-survivor precedence interface and common solver engine, NOT because target 2005 is intrinsically impossible. Time to switch both the *decoder/representation* and (when available) the *solver portfolio*, and to prioritize archival 2005 retrieval.

## Decision order before any new substantial Action runs

1. **Reproduction:** try the official open NDS-S implementation (including baseline destroy/repair) on exactly ta41; first test its instance convention and derive official 20x30 machine-order certificate. Compare against 2006. No custom RL training until a baseline demonstrates promise.
2. **Archival record:** search NO2013/CPO2015 supplementary solutions and/or authors; verify any available 2005 schedule with the Few Shots verifier. ScheduleOpt `solutions.json` only contains 2006, so don't waste time re-reading it.
3. **Alternate engines:** run minimal controlled ta41 on available OptalCP/Hexaly/CPO if accessible, with scores checked by the same official verifier and matched time/worker budget. Report licensing/access constraints honestly.
4. **Novel hypothesis (only after above):** construct a learned/dynamically updated disjunctive partial-order repair over *connected machine-pair conflict clusters*, using operation-pair memory from 2006 diverse schedules and partial-order CP propagation. This combines the Kasapidis memory idea, Legrand CP→DP propagation, and Zago activity-list deconstruction, but is not already established to beat ta41.
5. Maintain a score-first scoreboard: **validated best makespan**, official certificate hash, diversity/distance and time. Negative proofs are diagnostic, not the primary objective.

## Sources

- https://github.com/ScheduleOpt/benchmarks/blob/main/jobshop/solutions/bks.json
- https://github.com/ScheduleOpt/benchmarks/blob/main/jobshop/solutions/solutions.json
- https://www.mdpi.com/2227-7390/14/12/2179
- https://github.com/dawoz/NDS-S
- https://doi.org/10.1007/s10994-026-07116-9
- https://doi.org/10.1016/j.ejor.2024.08.010
- https://doi.org/10.48550/arXiv.2605.23569
- https://doi.org/10.1016/j.ejor.2024.07.028
- https://doi.org/10.26599/tst.2023.9010140
- https://doi.org/10.1016/j.ejor.2024.11.026
- https://doi.org/10.48550/arXiv.2504.16106

## Direct upstream method reproduction (2026-10-29)

- **Pinned official NDS-S source:** `dawoz/NDS-S@c58783b0271f95d9a56252d8841fa2a78535a4d2`. Its `data/jssp/30_20 __ta41__lb1906_ub2005.csv` matches all **600** Few Shots machine assignments and processing times. Its original pybind11 C++ `JSSP.Solution` activity-list scheduling reconstructs the verified 2006 baseline exactly; no surrogate/reimplementation used for the native search.
- **Native authors' destroy/recreate operators, starting score 2006:** `results/nds-cpp-random/nds-reproduction.json` and `nds-cpp-heuristic/`: 100,000 iterations **each**, Q=10 selected operations, 16 rollouts, 6 repairs, ~230 and ~269 seconds. Best score both **2006**, no improvement. Source `reproduce_nds_cpp.py`; upstream C++ uses `std::random_device` so exact pseudorandom search stream is not replayable from Python seed; retain result files and any official certificate as evidence.
- **Important directly extracted original paper code artifact:** Author's own `results/jssp/nds/ta/ta41/` contains per-model `results.csv`, unlike the article's grouped tables. Scores: model **jssp15x15 = 2220**, **jssp20x20 = 2310**, **jssp30x20 = 2325**, **jssp50x20 = 2321** (each 60 seconds). Do **not** claim the authors attained ≤2006 on ta41. These are cold-start results.
- **Own reproduced unmodified pretrained NDS-S jssp30x20 inference:** `results/nds-neural30x20/neural-eval.json`: official model `checkpoint-1000.pt`, original `ndss.eval`, CPU, 125 seconds, best **2439** (independent C++ activity-list replay and independent Few Shots DAG agree). Different from authors' published cold-start 2325, plausibly due stochastic initialization and runtime/hardware; no controlled equivalence claim. First run failed on missing `matplotlib`, dependency was fixed before successfully rerunning. An **official 2006-warm-started pretrained model** is separately under test (`reproduce_nds_neural_warmstart.py`), results pending until saved.
- **Second solver engine baseline:** `results/optalcp-preview.json`: OptalCP Preview, full interval NoOverlap model with 600 tasks, 180s, best **2061**. All solution-variable starts unavailable in Preview; this is an *objective-only* comparison and never a validated certificate. Academic/full license would be required to obtain a machine-order schedule. Preview result does not imply OptalCP cannot beat 2006 with longer search or alternate settings.
- **Methodological lesson:** Although activity-list deconstruction is flexible across many machines and neural policy is superior in grouped training benchmarks, its unmodified pretrained policy and published heuristic operators have not crossed ta41's 2006 plateau. Stop equating method reputation or aggregate benchmark scores with instance-level success. Future effort should be directed at a new **repair interface informed by ta41's demonstrated common resource conflicts** and score-first official validation.


**NDS-S warmstart result now verified (2026-10-29):** `results/nds-neural-warmstart/neural-eval.json` reports original jssp30x20 pretrained policy from exact verified 2006 activity-list bootstrap, 120s CPU, **best 2006**. Original C++ activity-list replay and independent Few Shots DAG both agree 2006. This closes the controlled checkpoint test without a new certificate. The prior author's original `ndss.eval` cold-start run obtained 2439 and the authors' archived ta41 30x20 cold-start result is 2325; results depend on initialization. **No <=2005 score was produced in any upstream NDS-S test.**

