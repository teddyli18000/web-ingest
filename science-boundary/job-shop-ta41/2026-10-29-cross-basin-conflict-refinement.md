# Cross-basin resource-conflict refinement (2026-10-29)

## Question

Does changing the *search interface* rather than expanding a static critical-path neighborhood expose new ways toward a valid ta41 score <=2005? Prior action-centric DCPRR changed critical-path identities but repeatedly preserved a large frozen partial order. Instead, use the intersection of distinct verified score-2006 machine orders to identify **still-invariant machine precedences**, extract independently certified no-2005 resource-conflict cores, and use these cores as global **soft disjunctive cuts** to synthesize new neutral 2006 counterexamples. Iterate only while the set of actually reachable oriented schedules expands.

## Source evidence and checked outcomes

- Live Few Shots baseline: valid score **2006**. ScheduleOpt lists historical 2005 but no full 2005 ta41 machine-order certificate. No <=2005 shot obtained.
- Five cohorts of independently graded score-2006 parent schedules were tested by `cross_basin_poset.py`: original five neutral parents plus new nine-core neutral, a set of neutral gateway parents, combined original+new, all **12** available parents, and a greedy seven-parent diversity selection.
- Exact same-machine pairwise consensus over 8700 possible pairs, with hard NoOverlap and job precedence at target 2005:

| Parent cohort | Retained agreed pairwise precedences | Released disagreements | Transitive cover arc count | Core extracted | Independent hard UNSAT recheck |
|---|---:|---:|---:|---:|---|
| original five + ninecore | 8526 | 174 | 687 | 23 | INFEASIBLE |
| gateways (baseline, 120/124/127, ninecore) | 8620 | 80 | 626 | 47 | INFEASIBLE |
| old five + three gateways + ninecore | 8483 | 217 | 720 | 37 | INFEASIBLE |
| all twelve | 8431 | 269 | 731 | 46 | INFEASIBLE |
| diversity-greedy seven | 8432 | 268 | 731 | 46 | INFEASIBLE |

Each independently rebuilt 600-interval hard-NoOverlap model returned **INFEASIBLE** within 0.011–0.031 sec for the extracted core alone. This proves a new necessary condition relative to each entire parent consensus: any target <=2005 schedule must reverse **at least one pair** in the relevant core. The cores have not been proved minimal; do not turn their cardinalities into a necessary number of reversed pairs.
- Importantly the **old five-parent 21-arc obstruction still has 16 cover arcs retained across all twelve 2006 parents**. This exposes low orientation diversity rather than a globally distant 2005 basin.
- **Independent precedence-only check (without machine NoOverlap):** the new extracted cores' longest-path lower bounds are **1878, 1858, 1823, 1846, 1846**, respectively, not >2005. So machine resource disjunction propagation is crucial to the observed obstruction. These numbers can be independently recomputed using the 600 job-route DAG plus the listed machine core arcs; this does not establish a globally new makespan lower bound.

## Experimental mechanism

`counterexample_poset_refinement.py` and one-shot workflow `temp-ta41-counterexample-poset-refinement.yml` were launched. Starting with the all12 independently audited 46-arc sufficient core and the nine earlier certified disjunctions:
1. use a globally complete NoOverlap+job model without hard-frozen survivor machine orders, allowing all 8700 machine-pair orientations to change;
2. require >=1 reversal per independently valid no-2005 disjunction and >=15 changed machine orders (necessary for a 2005 solution);
3. minimize Cmax first and total adjacent orientation distance to an official 2006 neutral parent second; keep Cmax <=2006 for an incumbent;
4. if a new neutral 2006 certificate emerges, independently score and officially verify its 20x30 machine-order certificate; append it to the parent ensemble and recompute its consensus poset;
5. for a new 2005 consensus UNSAT core, rebuild an independent unconditional hard NoOverlap model before promoting it to a necessary cut;
6. if 2005 is actually found, verify via official Few Shots and then publish.

A second independent one-shot `shrink_cross_poset_core.py` tests whether new 23/37/46/47-arc sufficient cores can be compressed by deleting assumptions and re-proving hard subproblems. UNKNOWN deletions are retained, so minimization completeness is **not claimed**.

Results of the two running Actions were **not yet retrieved at this note's creation**:
- `results/iterative-poset-refinement/iteration.json` and optional `neutral-*/upstream-verdict.json`
- `results/shrunk-poset-*/shrunk-core.json`

## Why this is distinct from the exhausted search

Old DCPRR freed operation identities but kept hundreds of other survivor precedences hard. The current model places no hard freeze on those survivor pair orientations. Learned cores are *necessary disjunctions* rather than a fixed neighborhood: 2005 remains in the modeled feasible space, and a 2006 counterexample cannot be mistaken for a record. The hypothesis is that repeatedly revising what stays invariant after crossing a genuine obstruction discovers coordinated orientation changes that static critical-path operators cannot represent.

## References

- [CP/DP partial orders, Legrand et al., 2026](https://arxiv.org/abs/2605.23569). Transfer is of the CP-returned precedence-information idea, not a faithful code replication.
- [Google OR-Tools official job-shop NoOverlap example](https://developers.google.com/optimization/scheduling/job_shop).
- [2026 CP solver benchmark](https://www.mdpi.com/2227-7390/14/12/2179).
- [Project literature reassessment](literature-reassessment-2026-10-29.md).
- [DCPRR prior attempted mechanism](dynamic-critical-path-replacement-2026-10-29.md).
