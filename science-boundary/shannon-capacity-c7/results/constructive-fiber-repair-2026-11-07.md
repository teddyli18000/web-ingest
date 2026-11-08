# p004 constructive full-endpoint fiber search — 2026-11-07

**Objective:** Find a verifier-valid independent set with at least **134,754** vertices in `C7^⊠10`. The upstream Few Shots p004 board still gives **134,753**. This experiment constructs new *legal* ten-dimensional sets and optimizes their **actual cardinality**; no new record is claimed yet.

## Exact construction

Take a parent independent set `I⊂C7^5` of size 367, a deletion set `R⊂I` with size `t`, the retained core `B=I\R`, and any independent 367-point auxiliary `X`.

Define the **complete** safe endpoint pool

`E(R)={e∈C7^5:N[e]∩I≠∅ and N[e]∩I⊆R}.`

For each `x∈X` choose independently two arbitrary subsets `H_x,V_x⊆E(R)`. Require each chosen fiber to be independent and impose the full row/column compatibility condition:

`¬(e~y and x~f)` for all `e∈H_x, f∈V_y`.

Then the union

`S=(B×B) ∪ ⋃_(x∈X)(H_x×{x}) ∪ ⋃_(x∈X)({x}×V_x)`

is a legitimate independent set in `C7^10`. Because `X` is independent, two different row fibers cannot conflict, and similarly for column fibers. Safe endpoints cannot conflict with any core point in `B`.

The complete pool `E(R)` matters: it includes **every** 5D endpoint whose support is contained in the deleted owners, rather than only the two members of each private pair. Each endpoint may be used or discarded separately for every auxiliary word. This strictly generalizes a fixed PH/PV orientation.

For every auxiliary `x` with no confusable endpoint in `E(R)`, it is safe to fix `H_x=V_x=R`, contributing exactly `2t` points; no such fiber can cross-conflict with any active fiber. All other words are modeled exactly with binary H/V variables, within-fiber conflict edges, and cross-orientation conflict edges. The objective is **directly** the count of selected 10D points.

The implementation independently replays each fiber, all row-column interactions, core compatibility, and the exact final point count before writing a candidate certificate:

- [Reusable solver](../code/c7p004_full_endpoint_direct_milp.py)
- [Frozen SHA-checked 367-word parent](../data/circular-port12-port12a-2026-11-05.json)
- [Frozen nine-port case](../data/c7p004-direct-nine-port-case.json)
- [Frozen ten-port case](../data/c7p004-direct-ten-port-case.json)

## Constructive results — independently replayed locally

| Input case | Safe endpoints | Active auxiliary words | Exact MILP status | Constructed ten-dimensional points | Difference to record |
| --- | ---: | ---: | --- | ---: | ---: |
| 9 ports, original translated 367-word auxiliary | 20 | 32 | OPTIMAL | **134,704** | −49 |
| 10 ports, original translated 367-word auxiliary | 23 | 43 | OPTIMAL | **134,684** | −69 |
| 9 ports, auxiliary neutral swap `4848→4898` | 20 | (recomputed) | OPTIMAL | **134,705** | −48 |

The one-point neutral swap changes the *auxiliary itself* while preserving its exact 367-point five-dimensional independence. It was found by prioritizing the **full ten-dimensional MILP score** rather than a forbidden-hit metric. A score-guided search visited **216 distinct 367-word auxiliary states** and improved the starting score from 134,704 to 134,705. This is a genuine new **constructed-candidate quality improvement**, not a record and not a general upper bound.

Independent bitset checker `/mnt/data/science-p004/constructive/verify_independent_10d.py` (local working tree, distinct from the optimizer) separately regrouped all 10D points by 5D prefix and replayed neighborhood-bitset intersections:

- 9-port original: `valid=True, score=134704` (743 prefix groups)
- 10-port original: `valid=True, score=134684` (698 prefix groups)
- 9-port neutral auxiliary: `valid=True, score=134705` (742 prefix groups)

The local checker is supporting evidence; the **Few Shots authoritative verifier is still required** for the final official verdict. One-shot [GitHub Actions run 42457228288](https://github.com/teddyli18000/web-ingest/actions/runs/42457228288) was submitted to replay all three frozen inputs through the upstream p004 verifier; at the time of this note, the run was **pending due to repository Actions queue**, not claimed passed.

## Additional constructive exploration

- Exactly optimized all 672 valid nine-private-pair endpoint orientations of `port12a` for one translated parent auxiliary phase. Best direct score 134,704.
- Exactly optimized all 48 valid ten-private-pair endpoint orientations of the same parent at that phase. Best score 134,660.
- On the nine-port case, screened 250 phases ranked by possible endpoint activation using a cyclic FFT, then solved the direct 10D MILP: 240 exact OPTIMAL statuses and 10 time-limited; highest feasible score 134,704. Timeouts are not negative results.
- Reoptimizing the *same fixed 5D auxiliary* by exact forbidden-aware two-layer MILP (105 t10 and 140 t9 block solves), and arbitrary joint-release neighborhood MILP (65 t10 and 120 t9 solves), yielded no improvement of those auxiliaries. This does not prove the target auxiliaries impossible; it shows those fixed-core moves failed to recover the five-dimensional points.
- Independent two-for-two neutral search from the 134,705 auxiliary was started but a bounded exploratory execution did not return a better candidate; **no negative proof** claimed.

## Reassessment and next constructive mechanism

The best new construction currently has **134,705**, still **48** short of the public record. Simply scaling more fixed-orientation cases or filtering by forbidden intersection is not the next choice: 5D auxiliary reconfiguration raised the score by only one after the initial 26-point constructive lift from earlier adaptive-fiber incumbents.

**New parameterization to explore:** change the retained core itself jointly with `X` and with the 5D endpoint domains, rather than fix `R` and optimize only fibers. Equivalently, create a small family of core states whose changes make new outside–outside ten-dimensional candidates usable, then solve an exact prize-collecting independent-set repair over **all** changes in one go. Candidate evaluation must remain the *actual independently replayed 10D score*, and any score above 134,753 must immediately run the Few Shots p004 verifier.

No shot is ready.
