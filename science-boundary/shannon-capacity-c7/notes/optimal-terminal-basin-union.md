# Eighteen optimal BPZ terminal basins and their common periphery problem

Status: active exact search. No verified score above 134,753 is claimed here.

## Discovery

For the pinned BPZ five-dimensional profile

`B=359, N=322, A=19, D=26, O=H=V=8`,

the exact binary terminal-code enumeration has 15,149 maximal compatible codes. At the BPZ8 x BPZ8 profile the maximum score is 134,753, and there are exactly **18** maximal terminal codes attaining that score.

All 18 contain `BB`. They are parameterized by

- `q in {O,H,V}` for the block `Nq`,
- `r in {O,H,V}` for the block `rN`,
- one of two orientations:
  - orientation 0: `AH, DV, HD, VA`,
  - orientation 1: `AV, DH, HA, VD`.

Thus

- orientation 0: `BB, Nq, AH, DV, rN, HD, VA`,
- orientation 1: `BB, Nq, AV, DH, rN, HA, VD`.

The count is `3 x 3 x 2 = 18`.

The reusable exact pair-union implementation is
`code/bpz_optimal_terminal_union_hall.py`.

## Common-core reduction

Every optimum contains the same square block

`BB`, of size `359^2 = 128,881`.

The remaining score in every optimum is therefore

`134,753 - 128,881 = 5,872`.

Every peripheral vertex that appears in any one of the 18 optima is compatible with all of `BB`, because it occurs together with `BB` in a valid terminal code. Therefore `BB` may be fixed wholesale when optimizing over the union of the 18 basins.

Let `P` be the union of all peripheral vertices appearing in these 18 optima. Then a breakthrough inside this basin-union family is exactly an independent set of size at least

`5,873`

inside the induced real `C7^10` conflict graph on `P`.

Equivalently,

`BB union S`, with `S subseteq P`, is a 134,754-point construction iff `S` is independent and `|S| >= 5,873`.

This removes the 128,881 frozen vertices from the combinatorial search and turns the record-boundary question into a roughly ten-thousand-vertex peripheral MIS/SAT problem.

The exact implementation is
`code/bpz_optimal_terminal_periphery_sat.py`.
It builds the actual ten-dimensional conflict graph on `P` and asks MiniCard for at least 5,873 selected vertices. SAT materializes a Few Shots certificate; UNSAT exactly closes the entire 18-basin peripheral union.

## Pairwise union Hall theorem

For any two equal-score independent sets `J1,J2` among the 18 optima, all conflicts in `J1 union J2` lie across the symmetric difference

`L = J1 \ J2`, `R = J2 \ J1`.

Since the sets have equal size, `|L|=|R|`. If `nu` is the maximum matching size in this bipartite conflict graph, then

`alpha(G[J1 union J2]) = 134,753 + |L| - nu`.

Thus one maximum matching exactly decides every possible recombination of that pair at all exchange radii. Positive Hall deficiency gives a breakthrough; saturation exactly closes that pair union.

This pairwise search is weaker than the full peripheral SAT, because a winning set may combine vertices from three or more record basins even when every two-basin union is Hall-saturated.

## Relation to earlier search spaces

This is not another radius-7/radius-8 local exchange. The 18-basin union permits coordinated changes of arbitrary radius while holding only the common `BB` core fixed.

It also differs from the earlier strict ninth-port searches. Those attempted to enlarge one fixed Gao-style port gadget. Here the search recombines vertices from **all terminal-optimal eight-port orientations and `N`-port choices simultaneously**, with the final ten-dimensional independence objective enforced directly.

If the full peripheral SAT is UNSAT, the next reformulation should release part of the common `BB` core rather than merely add more variants inside the same fixed-core union. In particular, allowing a small number of `BB` deletions while optimizing the peripheral union gives a direct net-score extension:

`gain = selected_periphery - 5,872 - deleted_BB`.

That extension should be formulated on the same reduced conflict graph, with explicit blocker variables for `BB`, rather than returning to ambient `7^10` enumeration.
