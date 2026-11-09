# Whole-machine resource-release transfer — 2026-11-08

## Research question and outcome

**Can a 30×20 job-shop scheduler predict necessary joint resource withdrawals before constructing a full schedule, and use those predictions to generate actual better schedules?**

Partial-order, single-machine-adjacent decisions and dynamic ejection chains showed a fundamental representation bottleneck. Earlier genuine source-independent elite tests found valid ta43/ta46 improvements only under an unrestricted full 580-soft-arc CP, or a hand-tuned minimum correction quartet; direct N7 source was stronger across independent basins.

This iteration made a falsifiable representation change: release **every original machine adjacency on a machine together**, while keeping every original job arc and all 20 machine NoOverlap constraints hard. A single CP-SAT assumption literal retains all 29 adjacency relations of one machine. An UNSAT sufficient assumption core is a necessary machine-release disjunction; an implicit hitting set (IHS) globally selects a new machine subset every iteration. In ta41, an independently verified CP-SAT theorem excludes all <=2005 completions differing from the 2006 baseline on <=14 complete machine orders; consequently at least 15 machine sequences must actually change in any winning schedule. Releasing >=15 machine groups is a **necessary relaxation capacity** (not a guarantee of actual change).

Generic machine-based decomposition, machine-group LNS, CP-SAT, and implicit hitting-set learning are all substantial established prior art: Pacino & Van Hentenryck, IJCAI 2011 (https://doi.org/10.5591/978-1-57735-516-8/IJCAI11-333), Kasapidis et al., EJOR 2025 (https://doi.org/10.1016/j.ejor.2024.08.010), Nagata & Ono IEBO 2018 (https://doi.org/10.1016/j.cor.2017.09.017), and Legrand et al. 2026 (https://arxiv.org/abs/2605.23569) all explore relevant machine decomposition/partial-order + constraint propagation ideas. We make **no novelty claim** for the general decomposition; the contribution is a specific source-backed negative-to-positive representation test and cross-basin transfer verdict.

## Verified source experiment: why "15 machines touched" was not 15 released machine sequences

1. `joint_conflict_hitting_repair.py` generated 21 certified 2005 gateway inversions, split into seven three-root GitHub Actions shards. All 21 explored using dynamic CP conflict cores, with root-specific 78s and 200 iteration caps, sometimes augmented releases of 12/24/48 isolated adjacent resource arcs. Results: **0/21 2005**; 10 root time limits, 9 iteration limits, 2 solver UNKNOWN. **No global exclusion**. Data `results/ihs-certified-21-shard0..6/results.json`. Independent exact 21-arc necessity proof in `results/ta41-mandatory-adjacent-gateways-independently-proved.json` is sound and reproducible but not a construction.
2. `machine_coverage_joint_ihs.py` then forced 15,17,19,20 *machines with at least 2 original adjacencies relaxed* (30–80 total original adjacency withdrawals). Nine trials (ta41, source-N7 independent ta43 and ta46, each dynamic/static/random), 80 full-resource CP attempts apiece: **720/720 conditionally INFEASIBLE; no improvement**. This representation still retains hundreds of original adjacency decisions across all supposedly opened machines and cannot express many coordinated reinsertions. The lower bound on **different machine permutations** does not imply sparse adjacent withdrawals suffice. Code/output under `results/machine-coverage-*/results.json`.
3. **Actual full-machine release IHS**: `whole_machine_release_ihs.py` uses 20 binary machine-open decisions and omits all 29 incumbent resource precedences on any opened machine, with hard 600 operation intervals, full job order, NoOverlap, fixed horizon incumbent-1. `INFEASIBLE` conditionally proves at least one fixed machine in a sufficient core must be opened; solver `UNKNOWN` only excludes the exact attempted mask from *subsequent exploration*, never from the mathematical feasible set. On ta41 it attempts 15,17,19,20 open machines. On source-independent positive controls, the release cardinalities are 2,3,4,5,7,10,15,20.

### First constructive positive controls, source-independent elite basins

Identical source N7-created (not oracle-degraded) elite starts:
- **ta43 (1888 → 1887)** with all three policies. Dynamic took **1.888 s, 23** CP subproblems; static 1.900 s/18; random 2.415 s/23. Each independently found complete machine orders with exactly the same necessary opened machine set **{5,6,8}**. Independently verified 600-operation DAG score. This is an oracle-blind construction (target reference schedule never read by the algorithm).
- **ta46 (2044 → 2043)** with all three policies. Dynamic took **6.763 s, 92** CP subproblems; static 17.158 s/99; random 9.604 s/97; each needed to free **15 machines** in its successful CP model. Independently verified 600-operation makespan.
- **ta41 (2006 → 2005)**: no improvement for any policy. Dynamic 56 trials/55.77s (19 CP INFEASIBLE, 37 UNKNOWN); static 56 trials/61.25s (15 INFEASIBLE, 41 UNKNOWN); random 56 trials/51.06s (21 INFEASIBLE, 35 UNKNOWN). The 20-free model is a fully unconstrained machine-order CP model; UNKNOWN is unsurprising and not global infeasibility. No valid ≤2005 Few Shots certificate found.

### Two-stage positive transfer: ta46 source 2044 → 2043 → 2042

The initial **2043** machine orders were produced by this constructive `whole_machine_release_ihs.py` dynamic policy, not copied from the archived oracle. A separate JavaScript topological scheduler reconstructed the 600 operation job+machine DAG and obtained exactly **2043**. Its 51-line startup file and complete provenance are under `positive-constructed-starts/ta46js-machine-2043/start.txt`.

The new start `2043` was given to all 3 policies × 2 previously unexposed seeds (20261108 and 20261117); all **6/6** runs produced a new complete **2042** schedule, with only two complete machine orders released and runtime **0.107–0.383 s**. All new machine orders independently rescored in Python. This confirms successive constructive improvements, not mere mutation undoing, but is not new published benchmark record and provides no ta41 2005 witness. Outputs: `results/multistage-ta46-2043-{policy}-seed{seed}/results.json` + `certificate.json`.

### Genuine external author N7 held-out paired comparison

All 12 starts were generated by original Ming Qi true N7 C++ at pinned `Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8` from independent native random initial schedules for 20 seconds, never from the archived hidden oracle. Exact same 12 starting schedules and two second-stage seeds **4107,4113** were tested with each method (24 paired trials). N7 comparison used actual original N7 code with **5.00 s** per trial. Our machine-group IHS was capped at roughly 5 s per trial, measured mean 4.05–4.34 s, but single CP calls sometimes cause **5.5–5.9 s max**.

| Method | Found further improvement / 24 | Mean makespan gain | Mean wall time/trial |
| --- | ---: | ---: | ---: |
| original source-faithful N7 | **9/24** | **1.2083** | 5.000 s |
| full-machine IHS randomized | 8/24 | 0.4167 | 4.287 s |
| full-machine IHS dynamic | 6/24 | 0.2500 | 4.342 s |
| full-machine IHS static | 6/24 | 0.2500 | 4.053 s |

Pairwise source-real N7 vs dynamic group IHS: **3 dynamic wins / 12 ties / 9 dynamic losses** (mean objective difference **+0.9583** against dynamic). Static and dynamic exact same final scores on all 24. Random selection yielded 2 wins over dynamic and 22 ties, zero losses. These scores contradict any claim that precompletion dynamic core weighting is currently a useful general improvement policy. Exact score audits, trial metadata, timing, and paired detail: `results/whole-machine-heldout-paired-judgment.json`.

## Scientific interpretation and next representation

**Positive:** The previously failing sparse arc-release interface hid attainable high-quality completions. Complete machine reordering is a materially better constructive operator and can repeatedly improve a modern algorithm's independent high-quality starting schedule. It makes improvement in ta43 and ta46 without oracle knowledge and can continue a discovered 2043 to 2042 in only two open machines.

**Negative:** Current conflict-weighted machine-group hitting-set selection does NOT outperform static or random weighting in 24 independent source-N7 elites, and the genuine original N7 remains stronger under a roughly comparable 5-second cap. Seven gateway shards, 720 sparse-arc trials, and the new unconstrained machine-group ta41 trials all found no 2005 certificate.

**Correct next mechanism** must not scale the identical machine-group IHS or add more exclusions. Candidate: use complete-machine free/reorder as a **constructive macro operator** interleaved with genuine N7 refinement and actual neutral elite diversification; machine selection should be conditioned on successful completion and new bottleneck structure, rather than just the earliest CP UNSAT core. Further positive controls must compare against the *source-faithful* N7 within total compute budgets and preserve diversity. The historical ta41=2005 result remains an unverified-by-certificate literature value (NO2013/CPO2015) until full machine order or timestamps can be independently checked.

## Links to inspect

- Source: `whole_machine_release_ihs.py`, `machine_coverage_joint_ihs.py`, `benchmark_whole_machine_transfer.py`, `judge_whole_machine_transfer.py`.
- Per-stage: `results/whole-machine-ta43js-n7elite1711-*/results.json`, `results/whole-machine-ta46js-n7elite1701-*/results.json`, `results/whole-machine-ta41-*/results.json`, `results/multistage-ta46-2043-*/certificate.json`.
- Full heldout: `results/whole-machine-transfer-{dynamic,static,random}-shard{0,1}-seed{4107,4113}/results.json`, `results/whole-machine-heldout-paired-judgment.json`.
- Official Few Shots submission requires a fully independently checked ta41 machine order with score <=2005 using the upstream verifier; nothing from this study qualifies.
