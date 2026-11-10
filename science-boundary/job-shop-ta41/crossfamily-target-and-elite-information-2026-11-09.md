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
