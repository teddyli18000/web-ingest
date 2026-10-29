# Taillard ta41 — separating distance from coordination, 2026-10-29

## Research question

The old explanation, "makespan 2006 is a deep local minimum requiring large perturbations", confuses two independent geometric properties:

1. **End-point distance**: (D(S_0,S_1)=\sum_m \#\{(a,b):\text{the baseline and target orders on machine }m\text{ disagree on }a,b\}\), the exact machine-pair Kendall tau distance (out of `20 * C(30,2) = 8700`).
2. **Coordination barrier**: (B_\mathcal{N}(S_0,S_1)=\min_{\text{valid local-move paths}}\max_t C_{max}(S_t)-\max(C_{max}(S_0),C_{max}(S_1))). This depends on the allowed move graph and is NOT determined by (D). Even a schedule only 15 inversions away may be inaccessible to a greedy single-swap improvement procedure if some useful moves must be preceded by enabling moves.

**Distinguish:** the unknown 2005 schedule's minimum Kendall distance is not yet known. The experiments below prove coordination effects between verified 2006 schedules; they do not establish the existence of a nearby 2005 schedule.

## Quantitative evidence

Official Few Shots-verified score-2006 neutral schedules relative to original baseline:

| Source | Machine orders changed | Kendall inversions | Reversed arcs in prior 21-arc consensus no-2005 core |
|---|---:|---:|---:|
| neutral-critical8 | 16/20 | 47 | 0 |
| neutral-mixed12 | 19/20 | 83 | 0 |
| neutral-mixed16 | 19/20 | 100 | 0 |
| neutral-mixed20 | 19/20 | 131 | 0 |
| warm-backbone-5 | 18/20 | 84 | 1 |
| warm-backbone-6 | 16/20 | 79 | 3 |
| continuation-7 | 20/20 | 126 | 3 |

Evidence `results/geometry-vs-coordination.json`. Thus a change in >=15 whole machine permutations (known necessary for an unknown 2005 schedule) need not mean a long distance in machine-pair orientation space.

### Atomic 15-pair counterexample to "large perturbations"

`synchronous_small_inversions.py` (OR-Tools 9.14.6206; no learned cuts) decided exact conditional NoOverlap neighborhoods. It restricts machine permutations to disjoint adjacent transpositions, with all nonadjacent baseline job pairs kept in original order. Selected swaps across machines are **simultaneous**; no intermediate makespan bound is imposed.

| Exact family | Deadline | Outcome |
|---|---:|---|
| <=1 adjacent swap/machine, 15..20 total and >=15 changed machines | 2006 | **FEASIBLE; 15 total machine-pair inversions on 15 machines**, independent DAG and Few Shots verifier `valid=true, score=2006` |
| same | 2005 | INFEASIBLE (0.168s, solver presolve) |
| <=2 disjoint adjacent swaps/machine, 15..30 total and >=15 changed machines | 2006 | **FEASIBLE; 18 inversions across 15 machines**, official verifier `valid=true, score=2006` |
| same | 2005 | INFEASIBLE (0.097s, presolve) |

Evidence under `results/synchronous-{single-2006,single-2005,double-2006,double-2005}/`. The exact 15-swap 2006 certificate has canonical hash `b415766203c999221eb60ffbec941aafa16f90d5839df19acca72de2197c9b39`.

### Complete, exact small-swap coordination lattice — strongest conceptual result

`exact_swap_lattice.py` exhaustively constructed **all 32768=2^15 subsets** of the 15 atomic swaps above and independently evaluated each full machine DAG. A minimax dynamic program over all monotone orders of the 15 swaps proves:

- Minimum possible **peak makespan along such a monotone order is exactly 2006**. One can reach the score-2006 endpoint by 15 sequential swaps without ever worsening the score, **if moves are ordered appropriately**.
- **15360** subsets have makespan <=2006 and are reachable from the zero-swap baseline by some monotone path staying <=2006; no cycle in any subset.
- However **two individual swaps look harmful in isolation**:
  - Machine 1, baseline positions 8/9: applying it alone gives makespan **2024**. First apply machine 4 position 10 and machine 2 position 10 (both neutral enablers), then the machine 1 swap keeps makespan **2006**. Exact minimal prerequisites in this 15-move lattice: **two other swaps**.
  - Machine 17, baseline positions 17/18: alone makespan **2047**. First apply machine 5 position 16, then it is feasible at **2006**. Exact minimum: **one other swap**.
- Therefore **negative single-move evaluations can be artifacts of missing coordination**, even where no literal uphill barrier exists. This is a rigorous instance-level example of multi-arc epistasis.
- These 15 swaps reverse **none** of the 21 baseline precedence relations in the proven consensus no-2005 core, so **no subset could reach 2005**. Avoid presenting the neutral lattice as a breakthrough candidate; use it as a diagnostic for move ordering and joint variable coupling.

Evidence: `results/exact-15-swap-coordination-lattice.json` (contains all chosen swaps, exact path, and minimal enabling predecessor sets).

### Larger neutral paths are not a proof of a necessary barrier

Heuristic monotone target-directed adjacent-swap beam search (width 100) found upper bounds on maximum intermediate makespan between two 2006 schedules: baseline->critical8 at 47 inversions had **2090** peak, baseline->reversed6 at 79 inversions **2032** peak. These are **UPPER bounds on optimal minmax barriers**, NOT lower bounds. All target-directed feasible first moves had minimum makespan 2006, so no positive barrier has been proved. Other paths, especially nonmonotone paths, could do better. Source `results/geometry-vs-coordination.json`.

### Direct distance to the unknown 2005 schedule

`exact_kendall_radius.py` explicitly orients baseline job pairs with Boolean variables, counts exactly all reversed machine-job pairs, and checks the 2005 horizon with full NoOverlap and **no learned cores**.

| Tested radius/representation | Result |
|---|---|
| Kendall radius<=20 with only original rank-gap<=2 pair reversals | INFEASIBLE (1.117s) |
| Kendall radius<=30, reversals only among original rank-gap<=3 | INFEASIBLE (175.617s) |
| Kendall radius<=47, reversals only among original rank-gap<=5 | UNKNOWN after 210s |
| **Fully unrestricted** Kendall radius<=20 (all 8700 pair orientations) | **UNKNOWN after 210s** |
| **Fully unrestricted** Kendall radius<=40 | **UNKNOWN after 210s** |

Important: Only fully unrestricted exact Kendall-ball infeasibility could certify a true global incumbent-relative distance radius; **neither global radius 20 nor 40 was solved**. Therefore there is still **no proven nearest-distance answer for 2005**. Narrow-window negatives exclude exactly their tested subfamilies, not all nearby solutions.


## Verified low-distance crossings of certified structural gateways

The three exact-Kendall, 8700-pair guided CP optimizations **completed** (OR-Tools 9.14.6206; 180s each) with new **Few Shots-officially verified** 2006 schedules:

| Forced reversal in mandatory 21-arc core | Best found Kendall inversions from original | Changed machine permutations | Reversed core relations | Status |
|---|---:|---:|---|---|
| Arc 124, machine 3, job 24 before job 16 in baseline | **30** | 13 | [124] | FEASIBLE, not OPTIMAL |
| Arc 120, machine 3, job 19 before job 25 in baseline | **36** | 13 | [120,124,125] | FEASIBLE, not OPTIMAL |
| Arc 127, machine 3, job 27 before job 5 in baseline | **43** | 17 | [127,181] | FEASIBLE, not OPTIMAL |

Source `results/gateway-{124,120,127}/gateway-cost.json` and respective `upstream-verdict.json`. The solver best objective bound stayed **2** at the deadline for all three, so these are **existence upper bounds**, not minimum distances.

**Meaning:** The previously known necessary 2005 *precedence gateway* can itself be crossed while keeping score 2006 with only **30** of 8700 machine-pair inversions; one example still differs on just **13 machine permutations**. Thus neither high machine-order distance nor structural gateway violation independently requires a remote basin. What extra coupled changes are needed to actually reach 2005 remains open. A follow-up exact small co-swapping repair from these gateway parents has been launched (`temp-ta41-gateway-coordinated-micro-repair.yml`), not claimed complete.

## Interpretation and decision

The evidence **falsifies the inference** that 15 changed machine permutations necessarily means a geometrically distant basin. It **directly demonstrates** that individually harmful micro-moves can have constructive, mutually enabling interactions. It does **not** determine whether a score<=2005 solution is geometrically near or far.

This is consistent with the established job-shop big-valley/path-relinking view (Nowicki and Smutnicki, J Scheduling 2005, doi:10.1007/S10951-005-6364-5) and modern disjunctive-graph neighborhoods; no generic novelty claim is made.

## Concrete next experiment with causal relevance to the record

1. Focus on the **21 mandatory consensus-core machine precedences**: any score<=2005 solution MUST reverse >=1, whereas the neutral 15-move cohort reverses 0. Relearn minimal prerequisite move clusters that enable one of those reversals while retaining score<=2006.
2. The launched `gateway_kendall_cost.py` computes a fully oriented 8700-pair exact-Kendall objective at the **2006** horizon, forcing one of core arcs 120/124/127 reversed and warming from official-verified 2006 parents. The result (when available) gives a feasible upper bound and/or solver lower bound for reaching that structural gateway. **No outcome claimed until `results/gateway-{120,124,127}/gateway-cost.json` exists.**
3. Use exact neutral reachable-subset DP and pairwise conflict learning to build **macro-moves** (many jointly timed micro-swaps) guided toward mandatory core reversals; reject blind random large moves. Compare best certified <=2005 score against same-budget single-swap/LNS baseline.
4. Treat exact unlimited Kendall-ball `UNKNOWN` correctly; CP-SAT search difficulty is evidence of solver/encoding limitation, not proof of a deep objective basin.

## Literature

- Nowicki & Smutnicki (2005), *An Advanced Tabu Search Algorithm for the Job Shop Problem*, doi:10.1007/S10951-005-6364-5 (big-valley/path relinking).
- *Necessary and Sufficient Conditions for Feasible Neighbourhood Solutions in the Local Search of the Job-Shop Scheduling Problem* (2023), https://link.springer.com/article/10.1186/s10033-023-00911-8.
- Soykan (2026), *Exploiting Edge Semantics in Job Shop Scheduling Problem With Heterogeneous Graph Transformers*, doi:10.1002/aisy.70522.
