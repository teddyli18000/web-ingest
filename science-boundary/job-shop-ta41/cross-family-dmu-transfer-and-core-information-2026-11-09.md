# DMU 30×20 genuinely held-out transfer and conflict-core falsification — 2026-11-09

## Research decision

**Current best-supported mechanism is whole-machine sequence opening + a soft preference to preserve original N7 elite pair orientations, not machine-group UNSAT-core content.** This is *constructive* in multiple genuinely independent 30×20 instances but **does not currently beat original author N7 in mean makespan**. Ta41 remains 2006; no <=2005 certificate.

The exact hypothesis that dynamic replacement/conflict-core feedback *adds cross-instance predictive information beyond source-only criticality and exploration diversity* is **not supported** by the accumulated data. In particular, a near-information-free novelty-only comparator broadly replicates dynamic outcomes, and genuine short feasibility-only CP cores are more informative but much costlier.

## Strong external N7 test: different DMU family

The source-generator `create_independent_n7_positive.py` built 20 N7 elite schedules: dmu16–dmu20 and dmu56–dmu60, each with two genuinely independent 20-second random-initialized runs (source `Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8`). The 20 original machine orders are not derived from archived known-good orders and have independently cross-checked 600-operation job+machine DAG scores. Archived ScheduleOpt reference solutions were accessed by data **preparation only**, not search. Input `positive-n7-dmu16-20/`, `positive-n7-dmu56-60/` `start.txt` files contain only the instance and the source-N7 elite orders.

Each independent elite is passed to three *unchanged* whole-machine group selectors, 5-second total internal wall-clock target, two second-stage method seeds 4107 and 4113. Candidate completion retains all 600 hard operation intervals, all job precedence, 20 full machine NoOverlap; inside each selected machine all 29 original adjacency precedences are released, with cost-minimizing soft reified orientations. Full certified better machine orders have been independently DAG-rescored by the executable benchmark.

Original author N7 also received the exact same starts and seeds, and ran 5 actual seconds in the original native C++ author implementation (only a warmstart input hook is added; core search unchanged).

| Method | Strict-improvement count / 40 | Aggregate makespan gain | Mean gain | Paired vs genuine N7 |
| --- | ---: | ---: | ---: | --- |
| **Source-original native N7** | 28/40 | **320** | **8.00** | reference |
| Whole-machine + dynamic/unshrunk CP core weighting | **29/40** | 59 | 1.475 | 10 wins, 5 ties, 25 losses |
| Whole-machine + random choice | 27/40 | 53 | 1.325 | 9 wins, 5 ties, 26 losses |
| Whole-machine + static criticality | 22/40 | 38 | 0.950 | 8 wins, 7 ties, 25 losses |

The 40 paired trials contain **20 independent elite starts**; two second-stage seeds on one source schedule are correlated. Dynamic vs static: 10 better, 26 ties, 4 worse; dynamic vs random: 6 better, 31 ties, 3 worse. A higher rate of +1 improvements is NOT equivalent to stronger optimization; actual N7 generated several +7…+20 score improvements that an incumbent-1 first-success CP subproblem never pursued.

Evidence paths: `results/cross-family-dmu-{dmu16-20,dmu56-60}-{1901,1911}-{dynamic,static,random}/summary.json`, `results/cross-family-dmu-{dmu16-20,dmu56-60}-original-n7/results.json`, `.github/workflows/temp-ta41-cross-family-dmu-machine-transfer.yml`. All jobs completed successfully.

## Critical mechanism falsification: core vs exploration-only

A second source-only policy `novelty` uses the same group master and full CP model, but updates scores from machines *not opened* in previous failed attempts, **rather than weighting machines by returned solver core membership**. It still adds returned UNSAT clauses to the master, so this is a control of the *core weighting signal*, not a control with zero CP-core use. When CP returns the entire closed machine set, this clause simply excludes the previous exact open mask at that group size — no machine-specific conflict information.

Against the same 76 trials pooled over Taillard dev 24, Taillard unseen holdout 12, DMU external family 40:
- novelty-only **56/76 improved**, sum of makespan gains **95**
- dynamic/unshrunk solver core **53/76 improved**, sum of gains **93**
- precise short feasibility-only core reproof **26/76 improved**, sum of gains **39**; extra explanation computation takes from the same 5-second per trial budget, so this is *not* evidence that precise information is intrinsically bad.

Source artifacts `results/novelty-only-{taillard-dev-1701,taillard-dev-1711,taillard-holdout-1801,taillard-holdout-1811,dmu16-20-1901,dmu16-20-1911,dmu56-60-1901,dmu56-60-1911}/summary.json`, with matching `results/precise-core-*/summary.json`; `.github/workflows/temp-ta41-novelty-versus-core-historical-holdouts.yml` and `temp-ta41-precise-machine-core-dualsolver-transfer.yml`.

Independent fixed-group source-only diagnostic `results/audit-machine-core-information-{ta43js-n7elite1711,dmu17-n7elite1901,dmu60-n7elite1911,ta41}.json` found that the optimization model's naive sufficient machine UNSAT core often simply lists **every closed machine** (e.g. all 17 when 3 opened). A separate feasibility-only CP reproof shrinks that to 3–9 machine guards, demonstrating genuine structural knowledge is available but expensive to extract. Whether that precision has enough *value of information per CPU-second* to guide stronger construction remains open; current 5-second control does not establish it.

**Scientific inference:** the observed dynamic > static improvement likely derives largely from adaptive diversification and repeatedly avoiding known failed group masks, not an identifiable predictive CP core mechanism. This refutes the stronger previous causal interpretation.

## 2026 literature relationship and next representation change

- Nagata–Ono 2018 IEBO already conducts ejections in partial schedules: https://doi.org/10.1016/j.cor.2017.09.017.
- Xiong–Liu 2026 logic-based Benders for distributed FJSP combines master/subproblem separation, exact CP and strong subproblem relaxations: https://doi.org/10.1016/j.ejor.2025.08.039.
- Lin–Yang November 2026 *incumbent-aware selective repair* learns keep/release using a dual-head GNN and CP-SAT active-window repair: https://doi.org/10.1016/j.cie.2026.112299.
- Pacino–Van Hentenryck 2011 machine/hybrid LNS, earlier proof of prior art: https://doi.org/10.5591/978-1-57735-516-8/IJCAI11-333.

The fruitful next experimental distinction is **improvement depth rather than first +1 success**. Matched prospective target-depth ablations (drop 2/4/8/10/20), receding repeated +1 repairs, and genuine N7-after-CP hybrids have already been implemented in this shared topic by sibling work; **do not repeat** these experiments. Judge whether deeper target-aware machine selection, quality/time tradeoff or conditioned CP completion actually outperforms source N7 on genuinely unseen starts. Only after positive transfer should allocate large Ta41 computation. A 2005 historical table entry without its 20×30 operation order is not a valid Few Shots submission.

## Reproduction limitations

All starts are 30×20. One trial uses CP-SAT single worker under assumptions and a 4-worker master CP; native N7 uses 1 worker, so **wall time is matched but total CPU-core budgets are not identical**. CP solver subcalls are capped by remaining deadline; measured runtime can exceed nominal 5 seconds slightly due to interpreter/setup. The means and rates are empirical on a small, clustered sample, not claims of statistically decisive superiority. No literature priority/novelty claim beyond the exact synthetic comparison is made.
