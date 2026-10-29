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

## Completed evidence and representation reassessment

All five cross-basin consensus queries independently proved INFEASIBLE at 2005. Four deletion-shrink workflows retained hard-verified sufficient cores reduced **23→21**, **47→37**, **37→33**, **46→38**. Deletion testers had **42–76 UNKNOWN** verdicts, so do not claim exact minimal cores.

The two-step counterexample-guided orientation loop (each 150s full global CP + fast consensus recheck) constructed TWO new **Few Shots-officially verified** Cmax=2006 machine-order certificates:
- `results/iterative-poset-refinement/neutral-01/certificate.json`, official hash `79eb117a0adc0ac2757013976e5b6cece3fb545033ab937e3956c90101c86be4`
- `results/iterative-poset-refinement/neutral-02/certificate.json`, official hash `2ab834d14f448695b64a36339cfe04196d90b406a2666720eeb25514ed8034bd`.

But the union of neutral-parent disagreements improved by only FOUR original pairwise coordinates: **8431 shared orders among 12 parents→8429 among 13→8427 among 14**. Both new solutions were 2006; neither CP objective produced a better schedule. A 48-arc then a 41-arc sufficient 2005 UNSAT core was independently hard-certified. The original Action failed to serialize their *actual* core triples; separate `archive_refined_poset_cores.py` reran both from the verified full neutral certificates and saved all 48/41 exact machine order pairs, with independent hard-NoOverlap checks, and simple precedence-only longest-path lower bounds of **1868** and **1803**, respectively. These exact reproduced arcs are at `results/refined-poset-{1,2}-core.json`.

**Negative test of stronger coordinated necessary conditions:** `core_simultaneous_reversal_lb.py` asks whether a target<=2005 schedule can reverse at most 1 or 2 pairwise relations in the original 21, new all12 46, or independently reconstructed refined14 core. All **six** complete full-NoOverlap CP-SAT tests returned **UNKNOWN after 130s each**; no lower bound beyond >=1 per core is certified. Do not infer that multiple core flips are required. See `results/core-multiflip-*/cardinality-core-decision.json`.

**First-principles pivot:** the previous iterative 2006-neural generator *minimized* orientation edits as a secondary objective, almost guaranteeing low diversity and making the consensus core loop repeatedly hit the same obstruction. Candidate quality stayed exactly 2006 while only the excluded/conflicting structure grew. Do not spend more compute on this objective. A qualitatively different global model `maxmin_neutral_orientations.py` now uses exact full NoOverlap and maximizes **minimum distance from every one of the 12 pre-existing 2006 parents** over all 580 baseline adjacent machine-pair orientations. Two controlled arms: unguided, and requiring the ten independently certified 2005 necessary core disjunctions. Unlike fixing operation groups or releasing a time band, this model can reorder any of the 8700 machine pairs. The measure of success is (a) official <=2005 certificate, or if neutral, (b) objectively larger min-distance to *all* known parents and genuinely decreased intersection-poset invariants after adding the witness. Workflow `temp-ta41-neutral-orientation-maxmin.yml`; its results were pending at the creation of this paragraph. This is a diversity objective, **not** a new makespan theorem.

