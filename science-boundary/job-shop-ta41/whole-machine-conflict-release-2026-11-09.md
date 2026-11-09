# Whole-machine coordinated release and blind transfer — 2026-11-09

## Mechanism reformulation

**Question:** Can partial resource conflicts identify WHICH MACHINES should be jointly re-ordered before complete schedule construction, and can the resulting CP subproblem independently construct better full machine orders than a credible N7 reference? No global ta41 2005 record is claimed.

This reformulates earlier 21 mandatory adjacent ta41 machine precedence gateways and 15-machine lower bound. The earlier `machine_coverage_joint_ihs.py` released 30, 46, 60 or 80 isolated baseline adjacent decisions across >=15 machines; **all 9 × 80 trials** (ta41, independent source N7 ta43, source N7 ta46 × dynamic/static/random) produced no improvement. The 15-machine condition alone is insufficient if only 2 of the 29 adjacent decisions per machine are actually free.

New `machine_group_order_repair.py` opens **whole machines**, releasing all 29 baseline adjacency relations on every selected machine, with no restriction on its permutation. The other machine lists remain fixed. All 600 interval starts, all 570 job arcs, all 20 hard machine NoOverlap constraints, and strict deadline incumbent-1 are present in every CP subproblem. Every original adjacent orientation is a Boolean preference, reified both ways, minimizing the count of reversed original adjacencies, not imposing extra hard constraints. A single CP assumption per closed machine guards all 29 of its baseline arcs. If CP proves INFEASIBLE, a sufficient UNSAT core of closed machine guards gives a sound necessary clause requiring >=1 of those machines to be opened. The next master jointly reselects its entire group of open machines under all learned clauses. An UNKNOWN just skips this particular group set as an exploration tactic, never treated as a proof.

Dynamic master weights machine choices using source-only initial criticality plus frequency of learned necessary closed-machine cores. Static uses only initial criticality; random uses unrelated seeded weights. Identical total open-machine-size stages and CP time caps for all methods. The original 2018 Nagata–Ono [IEBO paper](https://doi.org/10.1016/j.cor.2017.09.017) already contains partial schedules and ejection/reinsertion; the 2026 Lin/Yang [incumbent-aware selective repair](https://doi.org/10.1016/j.cie.2026.112299) emphasizes keep/release selection in dynamic flexible JSP. **Whole-machine LNS and conflict-guided CP are prior art; no generic novelty claimed.** The specific hypothesis is improvement by *joint machine-group release inference* rather than per-arc release.

## Exact first pilot results (completed)

**Known-group, oracle-informed representation CAPACITY controls (not blind research claims)**:
- ta43js-n7elite1711, source N7 makespan 1888: supply the known improved-schedule machine groups **5,6,8**; full CP completes 1887 in **0.078s** with exactly 4 adjacent pair reversals and 3 changed machine permutations; original static unrestricted 580-bit CP took 0.795s.
- ta46js-n7elite1701, source N7 makespan 2044: supply known improved machine groups **1,3,5,6,7,10,14,16,18**; CP completes **2042** in **0.214s**, with 10 adjacency reversals across 9 machines.
- Hidden archived reference order is NEVER loaded by blind selection; supplying these groups explicitly is an *oracle-aware positive representation calibration*, not a blind positive.

**Oracle-blind matched method pilot** (same source N7 starts):
| Independent source N7 start | dynamic group | static group | random group |
| --- | --- | --- | --- |
| ta43 elite makespan 1888 | 1887 after 9 group sets / 0.818s | 1887 after 19 / 1.735s | 1887 after 17 / 0.834s |
| ta46 elite makespan 2044 | 2043 after 27 / 1.941s | 2043 after 35 / 8.317s | 2043 after 33 / 3.275s |

All complete 20×30 machine schedules were DAG scored independent of the CP solver. None of these constitute a new ta41 p009 certificate.

**Larger six-instance blind transfer pilot**:
- 12 **independent** source-author N7 (pinned `Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8`) elite starts from 6 Taillard 30×20 problems **ta42–ta47**, constructed from *random* N7 initial schedules by 20 seconds of original author search each, not derived by mutating the hidden oracle. Two second-stage method seeds 4107/4113 per start yield 24 matched starts/trials per policy. Runtime search receives only `positive-n7-elite-data/<case>/start.txt`.
- Group policy first trial: target current score - 1, 5-second nominal internal search window with CP subcalls up to 0.7s and master group choice up to 0.15s. Because the first implementation could slightly overshoot 5s inside a subcall, these are **nominal** rather than strictly equal wall times. `machine_group_order_repair.py` was subsequently patched to cap each CP/master call by actual remaining elapsed time; strict replay is `temp-ta41-machine-group-strict-five-second-retest.yml`, not yet complete in this note.
- First nominal-window results:
| Method | Strict improvement rate | Mean score gain | Paired source N7 5s objective results |
| --- | --- | --- | --- |
| dynamic group/core | **15/24** | 0.667 | 7 better / 11 tied / 6 worse |
| random whole-machine groups | 12/24 | 0.542 | 7 better / 9 tied / 8 worse |
| static critical machine groups | 6/24 | 0.250 | 2 better / 13 tied / 9 worse |
| original **genuine** author N7 source | 9/24 | **1.208** | reference |

- Pairwise dynamic vs static within the identical group-CP model: **10 better / 13 tied / 1 worse**; dynamic vs random: **3 better / 20 tied / 1 worse**. Operational success-rate improvement does NOT imply better mean makespan: native N7 sometimes discovers larger improvements. The 24 trials share only 12 actual independent source starts, so do not treat them as 24 independent statistical samples. Four group master workers vs single-threaded original N7 can differ in total core consumption; the test primarily matches wall-clock time.

## ta41 source evidence and exact structural experiments

- `results/machine-budget14/decision.json` independently proved **any ta41 score <=2005 solution must differ on at least 15 of the 20 full machine order permutations** relative to the verified original 2006 parent, with complete NoOverlap and a direct cardinality decision model. It does not prove a 2005 solution exists.
- `results/ta41-mandatory-adjacent-gateways-independently-proved.json` rebuilt full 600-interval CP and proved the original 21 baseline-adjacent machine precedence constraints cannot all be retained under target 2005. Any improved target schedule must reverse at least one gateway.
- Two source-only generated machine group-core archives `results/machine-fast-{2026,4107}/machine-core-fast.json` supply **2,543 inclusion-minimal solver-proven necessary machine set clauses** (not exploratory UNKNOWN failures).
- Whole-machine group blind test at k∈{15,17,19,20} open machines, 8 candidates per stage and 3 policies, completed: **none found 2005**. All three returned INFEASIBLE on tested k15 masks, mostly UNKNOWN for k19 and unrestricted k20. This does not exclude any untested machine selections or the global target.
- `endogenous_machine_orientation.py` made all 580 reified original pair orientations and all 20 exact machine-change indicators endogenous to ONE CP model with every machine permutation free. Four 95s solvers were run (baseline/no-proof static objective, cardinality + gateway, cardinality + gateway + all source-verified machine cores under static weights, same full structure with feasibility-only objective). **All four status UNKNOWN after 95s**; no 2005 certificate. Proof constraints raised the objective lower bound in the weighted runs from 21 to 315 (not makespan bounds), but no successful candidate; do not mistake those weighted objective bounds for Cmax lower bounds.

## Independence test pending

To avoid overfitting to ta43 and ta46, a **fresh unseen Taillard ta48/49/50** (all 30×20) benchmark is being built under `temp-ta41-heldout-n7-elite-generator.yml`, with source N7 initialization seeds 1801/1811, 20 seconds cold N7 per start, 6 starts total. Source ScheduleOpt published full machine orders are verified only by preparation and withheld from method execution. Each of dynamic/static/random and the genuine N7 original C++ kernel will receive matching starts and two stage seeds under nominal 5-second internal search caps; the group CP code has already been frozen and strict capped before examining these cases. Recheck the new out-of-development results before claiming transfer.

## Scientific decision rule

Do not scale more local edge-release 80-move trials or ta41 CP 95-second UNKNOWN runs if merely adding failed starts. Positive heldout data should determine whether machine group selection feedback actually adds value beyond random grouping and original N7. If yes, next improve its root/group variable inference using independent interval overload, active machine closure, or better learned resource-conflict incidence. If no, revisit grouping interface, not just tweak weights. All final source-specific ta41 certificates must pass official Few Shots `p009` verifier before any submission.

Source files, workflows and results in `science-boundary/job-shop-ta41` on `main`.
