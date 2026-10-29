# Exact closure of the pinned BPZ one-core-hole mechanism

Status: **closed modulo the already-open five-dimensional 368 problem**. A one-point deletion from the common `BB` core cannot create a new ten-dimensional breakthrough unless `alpha(C7^5) >= 368` already holds, in which case squaring the 368-word five-dimensional set is itself a much larger breakthrough.

No score above 134,753 is claimed here.

## Setup

Use the pinned BPZ/Tandon five-dimensional data from `tandonravi/C7-Shannon-Capacity-Heterogeneous-Recursion`, commit `c753408492dde92a239708986d16c15dbf6c3235`.

Let

- `I0` be the 367-word parent;
- `R` be the eight private-pair owners;
- `B = I0 \ R`, so `|B|=359`;
- `BB = B x B`, so `|BB|=128,881`;
- `Q = {z : N[z] intersect B = empty}`.

The exact fixed-core audit gives `|Q|=16`; it is exactly the union of the eight private-pair endpoint pairs. Each private pair is an edge, and `alpha(Q)=8`.

The complete ten-dimensional universe compatible with all of `BB` is

`U0 = (Q x V5) union (V5 x Q)`,

where `V5=C7^5` has 16,807 vertices.

## Fixed-BB upper bound reduces to alpha(C7^5)

Partition `Q` into its eight conflicting private pairs `E_1,...,E_8`.
For an independent set inside `Q x V5`, the points whose first coordinate lies in one pair `E_i` project to an independent set of `V5`: because `E_i` is complete on two vertices, two selected points in `E_i x V5` conflict whenever their second coordinates conflict (including equality). Therefore

`alpha(Q x V5) <= 8 * alpha(C7^5)`.

By symmetry,

`alpha(V5 x Q) <= 8 * alpha(C7^5)`.

Consequently

`alpha(U0) <= 16 * alpha(C7^5)`.

If `alpha(C7^5) <= 367`, then `alpha(U0) <= 5,872`. The known record terminal construction attains 5,872 points in `U0`, so under that hypothesis the fixed-BB safe universe is exactly saturated.

Equivalently, any improvement while keeping the full `BB` core already implies `alpha(C7^5) >= 368`.

## Exact singleton-support census

For every `b in B`, define

`W_b = {z in V5 : N[z] intersect B = {b}}`.

The exact pinned-data census is:

| `|W_b|` | owners `b` |
|---:|---:|
| 1 | 309 |
| 2 | 50 |

No singleton-support class is larger than two.

The reusable checker is `code/bpz_one_core_hole_alpha_audit.py`.

## What one core deletion unlocks

Delete one core point `d=(b,c)` from `BB`. A ten-dimensional point not already in `U0` is compatible with the retained core exactly when its complete `BB` footprint is `{d}`. The newly unlocked layer is therefore

`T_d = (W_b x W_c) \ {(b,c)}`.

The exact size distribution over all `359^2=128,881` core holes is:

| `|T_d|` | holes |
|---:|---:|
| 0 | 95,481 |
| 1 | 30,900 |
| 3 | 2,500 |

The only nontrivial case is `|W_b|=|W_c|=2`, which produces three newly unlocked points. There are `50^2=2,500` such holes.

For every one of those 2,500 holes, all three unordered pairs among the three unlocked points were checked under the exact `C7^10` confusability relation. This is 7,500 exact pair tests. **Every pair conflicts.** Hence

`alpha(T_d) <= 1`

for every one of the 128,881 possible one-core holes.

The exact audit statistics are therefore:

- singleton classes: 309 of size 1, 50 of size 2;
- nontrivial three-vertex holes: 2,500;
- pair tests inside those holes: 7,500;
- independent unlocked pairs: 0;
- maximum unlocked-layer independence number: 1.

## One-hole theorem

Any independent set that retains `BB \ {d}` lies inside

`(BB \ {d}) union U0 union T_d`.

Therefore

`alpha <= 128,880 + alpha(U0) + alpha(T_d)`.

If `alpha(C7^5) <= 367`, the two exact bounds above give

`alpha <= 128,880 + 5,872 + 1 = 134,753`.

Thus a one-core-hole construction cannot beat the current 134,753 record unless `alpha(C7^5) >= 368`.

If a 368-word independent set in `C7^5` exists, its square already has

`368^2 = 135,424`

points in `C7^10`, far above the required 134,754. Therefore the one-core-hole family offers no independent path around the unresolved five-dimensional 368 problem.

## Consequence for ongoing compute

Earlier queued one-hole SAT and 2-SAT workflows remain useful only as independent computational cross-checks of smaller restricted formulations. They are no longer needed to establish the structural one-hole exclusion above.

The next core-release level with genuinely new combinatorics is **two core holes**. For two deleted points `D`, newly compatible footprints can have shapes `(1,1)`, `(1,2)`, and `(2,1)`; unlike the one-hole case, multiple newly unlocked points need not collapse to a clique. Any two-hole work should start from this footprint decomposition rather than scaling the superseded one-hole SAT.
