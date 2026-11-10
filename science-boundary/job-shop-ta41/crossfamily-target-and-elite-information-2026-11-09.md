# Joint machine-order repair: falsification and next mechanism, 2026-11-09

## Scientific question

**Before completing a job-shop schedule, is there enough source-available, transferable information to identify a *joint* set of machine-order constraints to reopen, beyond what standard N7 search, random group release, and CP's own incumbent-distance objective already exploit?**

The primitive under test is a complete 30×20 CP-SAT with 600 operations, all fixed job precedences and 20 unconditional machine NoOverlap resources. A selected set of whole machine permutations may be reordered without restrictions; unselected original sequences remain fixed. Complete schedules are independently DAG rescored. An original 29-adjacent-pair reorientation objective favors small coordinated changes. If full CP proves infeasible under the target, a sufficient closed-machine assumption core teaches a valid necessary disjunction of machine groups. A machine-subset master reoptimizes jointly under these cores. `UNKNOWN` is exploration status only, never an exclusion.

All data and tests are under this same directory, reproducible at `Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8` for the original 2025 source N7, `ortools==9.14.6206` for CP. The second-stage 5s wall target is matched only approximately in CPU resources because the CP master uses up to four solver threads, whereas native N7 is single-threaded. Real CP wall may exceed 5s by tens of ms owing to final serialization. No universal performance superiority is claimed.

## Completed controlled experiments

### Taillard in-family, 2026-11-09

Original 12 genuine independently initialized N7 20-second elite schedules from ta42–ta47, two follow-up method seeds each = 24 paired trials. With 5-second source-only horizon:
- Whole-machine dynamic group/core selection: 15/24 improved; mean gain 0.6667; 10 wins / 13 ties / 1 loss against static full-machine CP group selection.
- Static group: 6/24, mean 0.25.
- Random group: 12/24, mean 0.5417.
- **Authentic original N7:** 9/24, mean 1.2083, with larger individual gains.

Entirely unused ta48–ta50: six other N7-20s starts (seeds 1801/1811), two followup seeds = 12 trials:
- Dynamic 9/12, mean 1.5; static 8/12, mean 1.1667; random 7/12, mean 0.9167; author N7 7/12, mean **2.0833**.
- On the same individual tasks, dynamic vs static 3W/9T/0L, dynamic vs random 4W/8T/0L. The unit of independence is **six elite starts**, not twelve trials.

Source: `results/machine-group-transfer-strict-{1701,1711}-{dynamic,static,random}/summary.json`; `results/holdout-machine-group-{1801,1811}-{dynamic,static,random}/summary.json`; authoritative true N7 `results/positive-independent-true-n7/results.json` and `results/holdout-original-n7/results.json`.

### Architecture and objective ablations

Oracle-informed *representation* controls (NOT blind search): if known changed machine sets are supplied, CP reconstructs independent N7 ta43 1888→1887 by opening 3 machines in 0.078s, and ta46 2044→2042 by opening 9 machines in 0.214s. `results/group-order-diagnostic-*/results.json`. No target solution passed to the blind search.

Crucially, if the group selection is held fixed but CP no longer minimizes original adjacent-pair reversals, instead merely seeks any schedule meeting C-1, **only 4/36** Taillard source-N7 first-improvement trials succeed, compared with **24/36** under the incumbent-aware minimal-change CP objective. This demonstrates a large **search heuristic/objective effect**, not a new feasible-set theorem. `results/group-feasibility-only-{development,heldout}-*/summary.json`.

A naive receding-horizon chain that partitions the same 5s into <=1.5s calls to group CP and repeats from each improved complete incumbent performed *worse* on ta48–ta50: dynamic 6/12 improved, total gain 15, versus single-stage dynamic 9/12, total gain 18; static 2/12, random 4/12. Hence blindly dividing the time into identical short restarts is **not** an improvement mechanism. `receding_machine_group_repair.py`, `results/receding-holdout-*/summary.json`.

### **True cross-family falsification**: DMU30×20

Untouched 10 DMU instances: dmu16–20 and dmu56–60 from ScheduleOpt. For each, create two independent N7 20s cold elites, yielding **20 distinct 600-operation starts**, and two later search seeds per start, giving 40 paired trials **per method** (same full source-compatible machine orders, with hidden superior reference solutions held out during all searches).

Same 5s budget, hard `target=incumbent-1`:
| Method | Strict improvements /40 | Mean makespan decrease |
|---|---:|---:|
| dynamic core-guided whole-machine CP | 29 | 1.425 |
| static whole-machine CP | 22 | 0.950 |
| random whole-machine CP | 28 | 1.400 |
| genuine source N7 | 28 | **8.800** |

Paired dynamic vs static: 10W /25T /5L; vs random: **4W /32T /4L**; vs N7: **9W /5T /26L**. Thus dynamic group selection *does not* demonstrate marginal structural information over random on DMU; general competitive quality **clearly fails** against true N7. A significant constructive primitive is not the same as a transferable superior selector.

Exact scores in `results/dmu-blind-{dmu16-20,dmu56-60}-{1901,1911}-{dynamic,static,random}/summary.json`, `results/dmu-original-n7-*/results.json`, and source manifests `positive-n7-{dmu16-20,dmu56-60}/manifest.json`.

### Desired target decrease (independent of solution oracle)

A new controlled experiment changed ONLY the hard CP horizon from `C-1` to `C-d` for d=2,4,8, leaving the dynamic machine selection and 5s budget otherwise unchanged:

| d | Improve /40 | Mean actual gain | Max gain |
|---|---:|---:|---:|
| 1 | 29 | 1.425 | 7 |
| 2 | 27 | 2.125 | 8 |
| 4 | 21 | 2.800 | 8 |
| 8 | 10 | 2.225 | 16 |
| 4, **random groups** | 26 | **3.300** | 8 |

Source `results/dmu-target-*/summary.json`. This exposes the mismatch between `find any 1-point improvement` and producing N7-sized gains. It does **not** rescue dynamic selection: source-only random machine groups with d=4 were better on this data. Caution: the choices of d=4 etc have now been examined on DMU and cannot be treated as optimized on untouched evaluation data.

## ta41 boundary and logical proof scope

- Baseline officially verified makespan remains **2006**; no independently verifiable ta41 schedule <=2005 has been constructed, so no Few Shots submission.
- An independent full NoOverlap CP-SAT decision proof establishes any <=2005 completed schedule must change >=**15 of 20 full original machine permutations**: `results/machine-budget14/decision.json`.
- A second independently rebuilt 600-operation CP model proves any <=2005 schedule must reverse at least one of **21 original machine-adjacent precedences**: `results/ta41-mandatory-adjacent-gateways-independently-proved.json`.
- Full-machine model with k in {15,17,19,20} and source-verified group-core IHS: 3 policies × 26 open-group candidate trials, **0 ta41 breakthroughs**, many conditional UNSAT/UNKNOWN; does not exclude other groups.
- Full endogenous CP (580 orientation variables and 20 exact changed-machine booleans, some with 15-machine proof constraints): four models ×95s all status UNKNOWN; not a global exclusion.

A fixed original parent with high machine-distance lower bound suggests genuinely global reorientation; spending more time only enumerating its conditional UNSAT regions will not be productive.

## Literature and origin boundary

- Ba, Liu, Yuan, **2026**, `A batch approximate evaluation method for neighborhood solutions in job shop scheduling`, COR 195, 107610, DOI https://doi.org/10.1016/j.cor.2026.107610, accelerates true N7 tabus via slack recursion; not implemented here.
- Lin & Yang, **November 2026**, `An incumbent-aware selective-repair framework for dynamic flexible job shop scheduling`, CIE 112299, DOI https://doi.org/10.1016/j.cie.2026.112299, combines a dual-head GNN keep/release policy with incumbent-aware CP repair and OOD transfer; problem is **dynamic flexible JSSP**, not the static 30×20 ta41.
- Nagata & Ono **2018** IEBO partial insertion/ejection DOI https://doi.org/10.1016/j.cor.2017.09.017, earlier established coupled operation neighborhood.
- Standard CP-SAT, core IHS and large neighborhood search are prior art. We claim neither new global theory nor state of art.

## Research question opened after this falsification

Perhaps **information content from a SECOND genuinely independent elite** (not merely marginals of generated UNSAT cores) helps identify critical machine groups before full schedule construction. Controlled trial `temp-ta41-real-vs-fake-second-elite-dmu.yml`: each current A receives ONLY a source-real B same-instance 20s independently optimized machine order for **machine group priority**, never as parent solution or CP order. Compare against a fake B that matches the exact number of A-adjacent pair disagreements **on every machine** but assigns disagreements to uniformly randomized pair positions. Both get target-drop 4, 5s, same source A and seed; original A-only dynamic4/random4 are already recorded. If real B is no better than count-matched fake B, individual A–B orientation information has no demonstrated transferable added value.

**Next research direction after source-real/fake result:** If the source-real B improves validated hit-rate and quality, further test B-supplied branching/conditional compatibility rather than naively training a GNN. If not, shift to a construction that uses true N7's large-basin moves and CP's efficient small coordinated repairs, with strict 5s budget and full 600-operation independent schedule verification; no more marginal-score tuning on failed source family.

## Completed source-real versus count-matched fake second elite B (2026-11-09 PST)

The identical DMU 20 independent N7 elite A starts and 2 second-stage seeds each (40 paired searches per arm, target drop=4, 5 seconds) were rerun with:

- `real`: provide genuinely independent second 20-second-source-N7 elite B of SAME JSSP instance to **machine group priority scores only**; CP completion always starts from A; never uses B as a target or machine fixed order.
- `count-matched-fake`: for each machine preserve exactly the count of A-adjacent job-pair reversals observed in real B, but uniformly randomly assign which original adjacent positions carry that flag. Fake orientation positions need not correspond to a consistent complete schedule; only marginal counts are matched.
- `none`: no B signal, A-only dynamic source-group criticality, same 5-second timing and target drop=4.
- `random`: unchanged random group master, same CP completion with target drop=4.

| Arm | improvement /40 | mean Cmax decrease |
|---|---:|---:|
| Real B | 21 | 2.65 |
| Count-matched fake B | 22 | 2.85 |
| No B | 21 | 2.80 |
| Random machine group selection | **26** | **3.30** |

Paired real-vs-fake: **5 real wins /30 ties /5 real losses**, real vs no B **5/28/7**, real vs random **6/22/12**. **No transferable incremental value of these tested detailed A-B adjacent orientation signals is established.** This is a falsification of a feature, NOT of all cross-elite linkage or learned representations. Source runs completed with success (Action `42771937010`), results in `results/dmu-elite-information-{dmu16-20,dmu56-60}-{1901,1911}-{real,count-matched-fake}/summary.json` and matched baseline `results/dmu-target-*/summary.json`.

## Primary source for historical ta41=2005 and methodological pivot

Found and visually inspected original 2015 Vilím, Laborie, Shaw CPAIOR [`Failure-directed Search for Constraint-based Scheduling — Detailed Experimental Results`](https://vilim.eu/petr/cpaior2015-results.pdf), page 2: **tail41 LB1906 UB2005** in the authors' own table. The companion [primary research paper](https://vilim.eu/petr/cpaior2015.pdf) (DOI `10.1007/978-3-319-18008-3_30`) describes using LNS as plan A and FDS as plan B once LNS plateaus, with **binary start-time domain choices** that force a bound change and branch preference for likely failure. This avoids re-running the same limited local-neighborhood search when progress stalls. The table contains NO 600-operation order/time certificate; 2005 is a **published claim, not an independently verified Few Shots submission**. Do not conflate with available score-2006 valid schedule. Thomas Weise's independently maintained literature table also attributes 2005 to the same VLS 2015 appendix, not an independent valid raw witness.

New, concretely distinct construction underway: published source N7 as plan A for 4 seconds **then** CP group repair as plan B within remaining ~1 second, compared at matched starting A and source-N7 seed against published true N7 alone for 5 seconds. Distinct from prior neutral CP -> N7 studies. Source `n7_then_group_cp.py`, Action `temp-ta41-original-n7-then-constructive-cp.yml`. Demand positive out-of-family objective gains (not merely success counts), and keep exact 600-operation verifier before claiming anything. This simple hybrid is standard methods in combination, not yet a new FDS algorithm.

## Completed 4s native N7 then 1s CP constructive plan-B test

The first source-only hybrid full-score test completed, Action `42773231197`, 8 matrix jobs and 40 paired DMU trials. The original author N7 kernel was left unchanged, with its existing verified warm-start loading adapter; each initial 30x20 N7 elite A underwent native 4-second N7 search, then the resulting independently verified complete N7 incumbent was supplied **only as a current CP parent** (not an oracle) for a 1-second group joint repair at Cmax(parent)-1.

| Search strategy | 40 matched starts, mean score improvement from A |
|---|---:|
| Native N7 4s without last CP phase | 7.55 |
| Native N7 4s **then dynamic group CP 1s** | 8.00 |
| Native N7 4s **then random group CP 1s** | 7.80 |
| Native N7 alone 5s, same seed, independent runner | **8.80** |

- Dynamic CP improved the already optimized 4s N7 schedule **9/40** times, mean additional score decrease **0.45**, max additional gain **4**. Random CP had **7/40**, mean extra **0.325**.
- Paired hybrid against native 5s N7: dynamic **9 wins /27 ties /4 losses**, but overall mean makespan score **0.8 worse** than 5s N7; random **7/28/5**, mean 1.0 worse. Dynamic vs random hybrid **4/35/1**.
- Actual hybrid wall average 4.866s dynamic, 4.916s random; N7 source C++ uses one worker while CP master uses up to four, so 5s wall-time comparison is approximate not matched CPU. N7 four-second and five-second runs were on independent GitHub runners so can differ by hardware speed and time-based stopped iteration count despite same seed: interpret paired scores as comparative samples, not literal continuation from the identical internal N7 state.
- Full 600-operation time CSV from native source and the final CP machine order were independently DAG scored; all scores used in comparisons were verified.
- Raw `n7_then_group_cp.py`, `results/n7four-then-CPone-{dmu16-20,dmu56-60}-{1901,1911}-{dynamic,random}/summary.json`, original native N7 5s control `results/dmu-original-n7-*/results.json`.

**Decision:** There is genuine local complementarity (CP can complete additional joint improvements after original N7), but replacing one second of N7 by basic CP repair does not raise mean objective quality. This is a constructive *positive plus negative* under matched starts, not a newly competitive method. To test a cost-honest portfolio, run distinct techniques on separate cores against a two-native-N7 portfolio with equal total CPUs; do not claim single-core superiority or repeat ta41 95s UNKNOWN blind without a mechanism change.
