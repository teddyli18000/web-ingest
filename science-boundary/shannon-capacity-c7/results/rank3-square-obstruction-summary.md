# Rank-3 square-obstruction structure

Date: 2026-10-27

This note records exact structural facts around the rank-3 neutral2 MaxSAT state at score 134,753.

## Fixed state

- neutral2 state: 18
- deleted parent indices: `60,160,231,244,250,267,330,344,364`
- square block size: `358^2 = 128,164`
- exact rank-3 port optimum in the original 18-endpoint family: 6,589
- total score: 134,753

## Conflict histograms against the retained 358-point parent set B

Among 5D endpoints outside B, the number with exactly `c` conflicts into B is:

| c | endpoints |
| ---: | ---: |
| 0 | 18 |
| 1 | 55 |
| 2 | 389 |
| 3 | 1,599 |
| 4 | 3,173 |
| 5 | 3,778 |
| 6 | 3,862 |
| 7 | 2,603 |
| 8 | 773 |
| 9 | 145 |
| 10 | 52 |
| 11 | 2 |

For the 367 companion points `x_i`, the B-conflict histogram is:

| conflicts into B | companions |
| ---: | ---: |
| 0 | 1 |
| 1 | 32 |
| 3 | 8 |
| 4 | 17 |
| 5 | 94 |
| 6 | 143 |
| 7 | 57 |
| 8 | 14 |
| 9 | 1 |

The unique zero-conflict companion is **`x_294`**.

## Consequence for one-square deletion

A horizontal port `(e,x_i)` conflicts with square vertices in the Cartesian product

`A_e × C_i`,

where `A_e` is the set of retained parent points conflicting with endpoint `e` and `C_i` is the set of retained parent points conflicting with `x_i`. A vertical port has the transposed product.

Therefore a new port conflicts with exactly one square vertex only when both factors have size one. The exact rank-3 statistics give 55 one-conflict endpoints and 32 one-conflict companions. These produce 3,520 touched oriented square vertices. Crucially, **each touched square vertex unlocks exactly one such additional port candidate**; the maximum unlock count per square vertex is 1.

Hence the threshold-1 square-relaxation family has the same optimum as the threshold-0 family. Given any threshold-1 solution deleting `k` square vertices, at most `k` selected ports depend on those deletions. Removing those ports and restoring the `k` square vertices gives a threshold-0 solution with score no smaller. The reverse inclusion is trivial, so the optima are equal.

This closes “delete one square vertex to unlock multiple ports” for the rank-3 state. Any improvement from square relaxation must arise at conflict radius at least 2, where different ports can share deleted square vertices.

## Unique zero-cost expansion

The only new freedom at threshold 0 comes from `x_294`: because `x_294` has no conflicts with B, a port `(e,x_294)` or `(x_294,e)` is square-safe for **any endpoint `e` outside B**, not only the 18 endpoints used by the earlier generalized-port model.

This makes the `x_294` fiber the current highest-priority subproblem. A dedicated exact MaxSAT search and local augmentation searches are being used to test this enlarged fiber.

## One-parent-swap result

The complete legal one-for-one parent neighborhood around this rank-3 state contains 10 moves. Re-optimizing the original port MaxSAT for every move gives score 134,753 for nine moves and 134,703 for the unique move at undeleted owner 294. Thus simple single-parent surgery does not improve the record.

## Provenance

- square-obstruction statistics: GitHub Actions run `40544591455`
- one-parent-swap exact sweep: run `40543763237`
- durable code: `code/rank3_square_stats.py`, `code/rank3_square_relax.py`, `code/rank3_parent1_maxsat.py`
