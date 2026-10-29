# Eighteen optimal BPZ terminal basins and their common periphery problem

Status: the fixed-`BB` union of all 18 terminal-optimal basins is now **exactly closed analytically** at peripheral optimum 5,872. No verified score above 134,753 is claimed here. The active extension releases one or more `BB` points.

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

Reusable pair-union code is in `code/bpz_optimal_terminal_union_hall.py`.

## Common-core reduction

Every optimum contains the same square block

`BB`, of size `359^2 = 128,881`.

The remaining score in every optimum is therefore

`134,753 - 128,881 = 5,872`.

Let `Q=PH union PV` be the 16 private-pair endpoints and let `X` be the 367-point five-dimensional companion independent set. Exact materialization of all 18 record terminal codes gives

`P = (X x Q) union (Q x X)`

for their total peripheral union.

Every point of `P` is compatible with all of `BB`, so with the core fixed the ten-dimensional problem reduces to the induced conflict graph on `P`.

## Exact analytic closure: alpha(P)=5,872

The full peripheral SAT is no longer needed to establish the optimum of this union.

`Q` consists of the endpoints of eight disjoint private pairs, and the two endpoints of each private pair conflict. Therefore any independent subset of `Q` contains at most one endpoint from each pair, so

`alpha(Q) <= 8`.

On the other hand `PH` and `PV` are each eight-point independent subsets of `Q`, so

`alpha(Q) = 8`.

`X` is an independent set of size 367. Hence in `X x Q`, different first coordinates in `X` are mutually nonconfusable, and for each fixed `x in X` the remaining conflict graph is exactly the graph induced on `Q`. Therefore

`alpha(X x Q) = |X| alpha(Q) = 367 * 8 = 2,936`.

By symmetry,

`alpha(Q x X) = 2,936`.

For any independent `S subseteq P`,

`|S| <= |S intersect (X x Q)| + |S intersect (Q x X)| <= 2,936 + 2,936 = 5,872`.

The known terminal-optimal constructions attain 5,872 peripheral points. Thus

**`alpha(P) = 5,872` exactly.**

Consequently the entire fixed-`BB` union of all 18 record terminal basins is closed at total score

`128,881 + 5,872 = 134,753`.

This is stronger than the earlier pairwise Hall checks and makes the queued full-periphery SAT only an independent computational cross-check, not a necessary proof step.

## Pairwise union Hall theorem

For any two equal-score independent sets `J1,J2` among the 18 optima, all conflicts in `J1 union J2` lie across the symmetric difference

`L = J1 \ J2`, `R = J2 \ J1`.

Since the sets have equal size, `|L|=|R|`. If `nu` is the maximum matching size in this bipartite conflict graph, then

`alpha(G[J1 union J2]) = 134,753 + |L| - nu`.

Thus one maximum matching exactly decides every recombination of that pair at all exchange radii. The analytic `alpha(P)=5872` closure above subsumes all pairwise checks simultaneously for the full 18-basin union.

## Releasing the core: one-hole formulation

Because the fixed-core union is exactly saturated, any improvement must leave `P` or release some of `BB`.

For `z in C7^5`, define

`S(z) = N[z] intersect B`.

A ten-dimensional point `(u,v)` conflicts with exactly the core footprint

`S(u) x S(v)`

inside `BB`.

If one core point `(b,c)` is deleted, the newly compatible points whose entire core footprint is that single hole are exactly

`W_b x W_c`, where `W_b = {z : S(z)={b}}`.

Since `alpha(P)=5,872`, a one-hole breakthrough must contain at least **two genuinely new unlocked peripheral points**: deleting one `BB` point lowers the retained core to 128,880, so at least 5,874 peripheral points are required.

Two exact implementations are retained:

- `code/bpz_one_core_hole_periphery_sat.py` — solves selected core holes one at a time;
- `code/bpz_global_one_core_hole_sat.py` — global selector encoding over all holes, with optional exact sharding. A single selector is chosen and each unlocked point implies its unique core blocker selector.

The global-selector version is the preferred representation under severe GitHub Actions queueing because one acquired runner can process many hole choices without rebuilding the same search from scratch.

## Relation to earlier search spaces

This is not another bounded-radius local exchange. The 18-basin union permits coordinated changes of arbitrary radius while holding only the common `BB` core fixed, and the one-hole model then releases a core point while optimizing the whole peripheral union directly.

It also differs from the earlier strict ninth-port searches. Those attempted to enlarge one fixed Gao-style port gadget. Here the final ten-dimensional independence objective is enforced directly over the union of all terminal-optimal orientations, plus exactly characterized newly unlocked core-hole points.

If the complete one-hole family is negative, the next principled extension is two core deletions. For two holes `D`, a newly compatible point must satisfy

`S(u) x S(v) subseteq D`,

so only footprint shapes `(1,1)`, `(1,2)`, and `(2,1)` can occur. This gives a finite exact two-hole selector model rather than a return to ambient `7^10` enumeration.
