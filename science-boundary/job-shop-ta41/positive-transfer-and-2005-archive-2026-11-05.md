# 30x20 positive controls and the historical 2005 chain — 2026-11-05

## Research objective and prespecification

The priority is **constructive, independently verified improvements**, not an ever-growing infeasibility map of ta41. Test adaptive path-replacement coordination on 30x20 instances for which a better full machine-order solution already exists but is withheld from search. Compare genuine published N7 (not our N7-inspired code), same-initialization static/dynamic three-move, and tabu. Judge final legal makespan and cost with no oracle leakage.

## Completed first positive fixture benchmark

- Source: `ScheduleOpt/benchmarks` commit **8a6e36ef31263d36975e56fb481e0ba04e188d6f**, `jobshop/instances/json/ta42js..ta47js`, `jobshop/solutions/solutions.json`. Each reference 20x30 operation-ID machine order is checked for complete permutations, exact machine/route consistency and full 600-operation DAG-recomputed makespan.
- **6 distinct 30x20 instances, 24 independently verified starts**, each known to have a real strictly better schedule withheld from the search process. Twelve are easy (one or a few degrading adjacent exchanges). Twelve are **multi-machine perturbations**, 16 or 32 different adjacent edits spanning 16–20 machines, with oracle-relative makespan degradation 47–77. These are still **oracle-origin perturbations**—the evaluator must not generalize their recovery difficulty to genuinely distinct local-optimum basins.
- The search binary is supplied `<case>/start.txt` containing only 30×20 routing, durations and degraded machine orders. Hidden reference permutations were consumed only by fixture preparation and never written to the runtime input. The separate judge reads oracle makespan from `positive-control-data/manifest.json` **after** search.
- Algorithms: `predictive_cascade_search.cpp` N7-inspired full-DAG engine adapted by `benchmark_hidden_positive.py`: `tabu`, `static3`, `dynamic3`. Only ta41 hardcoded initial and stop constants are generalized at C++ compile; search generator and evaluation unchanged; 350,000 DAG candidate evaluation budget each. Two seeds **4107, 4113** per case. **48 trials per method**.
- Genuine published source **Ming Qi 2025 original N7 C++**, pinned `Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8`, original `find_move, approximate_evaluation, make_move, tabu` intact. Previous AGPL-compatible warmstart method injects the exact same test-case machine order; new thin driver merely removes ta41 score check and 2005 stop. **5 seconds of C++ search per case/seed**, not matched DAG evaluation count or wall time. All 600 start/end time records replayed against source durations, independent Python DAG score equals native reported score.
- All four method runs and the post-search judge completed successfully: `results/positive-cascade-{tabu,static3,dynamic3}/results.json`, `results/positive-original-n7/results.json`, `results/positive-joint-benchmark-judged.json`.

### Primary results — known better schedule score reached or beaten

| Policy | Multi-machine cases (24) | All cases (48) | Mean full score gain across 48 | Approx C++ time/trial |
| --- | ---: | ---: | ---: | ---: |
| dynamic3 | **24 / 24** | 47 / 48 | 69.4583 | 2.17 sec |
| tabu (N7-inspired) | 21 / 24 | 45 / 48 | 69.7292 | 1.19 sec |
| static3 | 19 / 24 | 43 / 48 | 68.9792 | 1.54 sec |
| authentic published N7 | 17 / 24 | 41 / 48 | 68.8542 | 5 sec |

All 48 trials per method improved their starting makespan (trivial positive rate), and many differences are small. Paired 48 trial score comparisons: dynamic3 vs tabu **3 wins / 44 ties / 1 loss**; dynamic3 vs static3 **5 wins / 42 ties / 1 loss**; dynamic3 vs true N7 **7 wins / 40 ties / 1 loss**. The *mean score across all cases* is actually 0.27 **worse** for dynamic3 than tabu, despite its higher target recovery count. **Thus the evidence is recovery-threshold-specific, not a comprehensive dominance claim**. The three original algorithms had matched exact candidate-evaluation budgets, but CPU times differ. Published true N7 had **5s** fixed time; cannot claim fully matched wall-time performance. No extra ta41 2005 was found in this study.

### Next independence test

The true risk is that perturbing the archived target creates artificially recoverable directions. `create_independent_n7_positive.py` and `original_n7_cold_30x20_driver.cpp` generate **12 source-faithful true N7 cold-initialized elite schedules** (6 instances, two seeds 1701/1711, 20s author N7 search each) with no oracle machinery used in their construction. The final generated schedules are only retained if independently DAG verified and actually worse than an archived full oracle—so positive answer exists without injecting its structure. Workflow `temp-ta41-independent-n7-elite-positives.yml`, run **42044442285**, launched and not yet confirmed complete in this note. Once complete, compare all 4 algorithms on these genuinely independent basins, with **matched search start, paired seeds and both wall-time and evaluation budgets**. Do not claim cross-basin transfer from oracle-origin mutations.


## Completed independent-elite basin benchmark — the decisive negative control

The `temp-ta41-independent-n7-elite-positives.yml` run **42044442285** completed successfully, generating and independently verifying **12 30×20 source-algorithm-created schedules** (ta42..47 × author N7 seeds 1701 and 1711, **20 seconds of the genuine native author search from random initial schedules per case**). Their known score gap to published machine-order witnesses is **16–42**, and their parent machine orders were NOT derived by perturbing the hidden answer. The authentic N7 source is pinned as previously; each of the 600 operation machine/start/end records was checked before extracting final machine order.

`temp-ta41-independent-elite-transfer-benchmark.yml` run **42045369980** then completed all **four policy × 12 starts × 2 second-stage seeds = 96** search trials, independent full-score replays, and `judge_independent_elite_transfer.py` produced `results/positive-independent-elite-judged.json`. All four method results were compared on *exactly the same starting schedules*, with the same 350k exact candidate-score budget for the three original arms; genuine N7 was given 5 CPU seconds per trial, which is NOT an equal wall-time budget.

| Policy | Improvement found / 24 | Recovered known archived target / 24 | Mean score improvement | Mean CPU seconds per trial |
|---|---:|---:|---:|---:|
| **Genuine original N7** | **9 / 24** | 0 | **1.2083** | 5.00 |
| dynamic3 | 5 / 24 | 0 | 0.2917 | 2.11 |
| static3 | 5 / 24 | 0 | 0.2917 | 1.45 |
| N7-inspired tabu | 4 / 24 | 0 | 0.3333 | 1.14 |

Paired dynamic3 against genuine N7: **3 better / 14 tied / 7 worse**, mean dynamic minus genuine N7 final objective **+0.917** (larger is worse). Against static3: **2 better / 20 tied / 2 worse**. No transferable improvement advantage is established for dynamic3 on these deliberately independent strong-search basins.

**Causal interpretation:** The earlier 24/24 oracle-recovery result was about **undoing damage to archived elite schedules**. This matched-start controlled independent-elite test exposes that as an insufficient proxy for cross-basin constructive ability. Do NOT train on or scale the current three-step full machine-permutation representation. Move to a distinct partial schedule search representation and compare genuine original N7, not only in-house approximations.

**Novelty boundary:** The exact IEBO 2018 method (Nagata & Ono) already uses alternation of insertions and ejections in partial schedules, target-constrained partial makespan lower bounds, and dynamic programming over minimal ejections. The next hypothesis must add *prediction of replacement conflicts, then release/interference closure conditioned on that prediction* beyond IEBO, not claim invention of ejection chains.

## Historic 2005: evidence, provenance, and unsolved archival question

- [ScheduleOpt historical `bks.json`](https://github.com/ScheduleOpt/benchmarks/blob/main/jobshop/solutions/bks.json) records **ta41js upper bound 2005**, attributed to **NO2013 (2013)** and **CPO2015 (2015)**, **both `certificate:no`**. Its machine-order `solutions.json` contains ta41 only at **2006**, independently scored against Few Shots. [Optimizizer](https://optimizizer.com/TA.php) also publicly provides a **2006** ta41 `(sol)`, not a 2005 certificate. The widely circulated 2005 number is a credible literature report, but not a usable/inspectable machine order.
- The original 2015 authors are Petr Vilím, Philippe Laborie and Paul Shaw, *Failure-directed Search for Constraint-based Scheduling*, CPAIOR 2015, doi:10.1007/978-3-319-18008-3_30. [Detailed experimental results PDF](https://vilim.eu/petr/cpaior2015-results.pdf) and an independent [Weise survey](https://github.com/thomasWeise/jsspInstancesAndResults) corroborate the 2005 makespan, **not** the full starting-time vector.
- **Important correction/identified NO2013 source:** The independent 2016 van Hoorn thesis benchmark appendix [Table B.7](https://research.vu.nl/files/42163578/complete%20dissertation.pdf) cites ta41 upper bound **2005 [88]** and explicitly identifies reference **[88] Nagata and Ono (2013)**. This provides a second historical provenance path beyond IBM/CPO2015.
- The Nagata/Ono 2018 published study [IEBO](https://doi.org/10.1016/j.cor.2017.09.017), *A guided local search with iterative ejections of bottleneck operations for the job shop scheduling problem*, is **critical antecedent** to the proposed dynamic bottleneck-replacement mechanism: it searches in **partially specified schedules**, repeatedly ejects sets of obstructing operations, and uses dynamic programming to enumerate minimal ejection combinations under the *best complete makespan* constraint. We must NOT market generic dynamic bottleneck ejection as new. A novel contribution would need to predict resource-conflict replacement **beyond** IEBO and show positive gains against authentic N7 and, if source becomes available, IEBO.
- [Nagata author publications](https://yokaisen1994.wixsite.com/nagata/publications) and university records confirm relevant research, but today's searchable public materials **did not reveal the full 2005 machine orders nor a downloadable original 2013 solver execution log**. Retrieval alternatives: inspect archived lab download attachments / datasets, original 2013 Nagata–Ono report or personal communication details, and inquire about a surviving raw `ta41` list of 20×30 machine orders or 600 integer starts. The 2015 IBM CP Optimizer log may similarly survive in supplementary archival files. Do not report success without independent Few Shots `verify.py` output.

## Quality controls / open caveats

- Archived ScheduleOpt `solutions.json` provides a complete ta45 schedule independently scoring **1997**, while its ranking README currently lists UB **1999**; the reference fixture uses the actual independently scored **1997** certificate and records a source/version discrepancy rather than cherry-picking a weak target.
- `positive-control-data` contains **no oracle order**, only its runtime degraded `start.txt` and target makespan/hash in a manifest. This is a blinded algorithm run, not a secret or cryptographically committed pre-registration.
- The 2018 IEBO paper emphasizes alternation of orientation addition and ejection, a qualitatively different interface from our complete fixed 20×30 permutations. If independent-basin controls invalidate dynamic3, **change representation** rather than running tens of millions more insertion moves.
