# Mixed row/column release cannot exploit core intersections

Status: **conditional structural closure of every pinned-core modification whose newly inserted points all have at least one coordinate in `B`.** Under `alpha(C7^5) <= 367`, arbitrary mixtures of row and column replacements cannot beat 134,753. A genuine pinned-core breakthrough must therefore insert a point `(u,v)` with both `u` and `v` outside `B`, or else solve the five-dimensional 368 problem itself.

This note extends `multirow-core-release-reduction.md`.

## Row/column core-deletion overlap is forbidden by independence

A row addition has form `(a,y)` with `a in B`.  Its required core deletions include `(a,b)` exactly when `y` is confusable with `b in B`.

A column addition has form `(z,b)` with `b in B`.  Its required core deletions include the same `(a,b)` exactly when `z` is confusable with `a`.

If both additions required deletion of the same core cell `(a,b)`, then

- `a` is confusable with `z`, and
- `y` is confusable with `b`.

Therefore the two ten-dimensional additions `(a,y)` and `(z,b)` are confusable in the strong product.  They cannot both belong to an independent set.

Hence, in any valid mixed row/column construction, the core-deletion cells required by row additions and those required by column additions are **disjoint**.  The apparent possibility of saving score by paying for a row/column intersection only once does not exist.

## Matching periphery charges from rows and columns are also disjoint

The multi-row reduction fixes an injective confusability matching

`m : B -> X`,

where the companion factor `X=N disjoint-union A disjoint-union D` has 367 points.

For a row modification, the matching proof charges forced terminal deletions of the form

`(m(a), t) in X x Q`,

where `t` is one of the 16 private-pair endpoints.

The column proof symmetrically charges points of the form

`(t, m(b)) in Q x X`.

The pinned finite geometry satisfies

`X intersect Q = empty`.

Consequently a charged row point can never equal a charged column point.  Thus the lower bounds on forced periphery losses from arbitrary row and arbitrary column modifications add without double counting.

`code/bpz_multirow_matching_audit.py` checks `X intersect Q = empty`, reconstructs the 359-point saturating matching, verifies all three 367-point transversals, and replays the exact row/column terminal wiring for all 18 public terminal configurations.

## Combined reduction

Under `alpha(C7^5) <= 367`, the multi-row matching argument gives

`row periphery loss >= row raw core/add gain`,

and symmetrically

`column periphery loss >= column raw core/add gain`.

The two raw gains are additive because their required core deletion cells cannot overlap in a valid independent set.  The two forced periphery-loss charges are additive because `X x Q` and `Q x X` are disjoint.

Therefore every construction obtained solely from

- retained baseline core/periphery points,
- arbitrary new points in `B x (V5\B)`, and
- arbitrary new points in `(V5\B) x B`,

has final score at most 134,753 unless `alpha(C7^5) >= 368` already holds.

## What remains

This isolates the genuinely new pinned-core mechanism:

> Any independent route around the current record must introduce at least one new point `(u,v)` with `u notin B` and `v notin B`.

Such a point has a two-dimensional core footprint

`(N[u] intersect B) x (N[v] intersect B)`,

so the remaining search is intrinsically a union-of-support-rectangles problem.  This includes the previously studied support-graph products and genuinely nonrectangular combinations of multiple outside-outside points.

Row/column additions may still appear as auxiliaries in a construction that also contains outside-outside points, because they can then share deletions created by those two-sided footprints.  The reduction only says they cannot constitute the breakthrough mechanism by themselves.

Future compute should therefore prioritize the joint optimization of **outside-outside support rectangles**, with any row/column auxiliary variables introduced only after a positive or nearly positive two-sided footprint has been identified.
