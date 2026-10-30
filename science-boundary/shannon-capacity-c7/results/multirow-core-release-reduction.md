# Arbitrary multi-row / multi-column core release reduces to C7^5=368

Status: **structural closure of every pure multi-row and every pure multi-column replacement of the pinned 134,753 construction, conditional only on `alpha(C7^5) <= 367`.** Rows may use completely different replacement sets, arbitrary support sizes, and arbitrary shared terminal blockers. No score above 134,753 is claimed.

Pinned source: Tandon/BPZ commit `c753408492dde92a239708986d16c15dbf6c3235`.

## Construction facts

Write the 359-point core factor as `B`.  The pinned 367-point companion decomposes disjointly as

`X = N disjoint-union A disjoint-union D`

with sizes

`|N|=322, |A|=19, |D|=26`.

The three 8-point sets `O,H,V` are independent transversals completely nonconfusable with `B`; hence `B union T` is a 367-point independent set for each `T in {O,H,V}`.

There is an injective confusability matching

`m : B -> X`

with `m(a) in N[a]` for every `a in B`.  Thus all 359 core rows are matched to distinct companion points.  `code/bpz_multirow_matching_audit.py` reconstructs this matching deterministically from the pinned data and independently checks the terminal wiring.

For terminal orientation 0, the row-side periphery contains

`N x q  union  A x H  union  D x V`,

and for orientation 1 it contains

`N x q  union  A x V  union  D x H`,

where `q in {O,H,V}`.  Column-side blocks are the symmetric counterparts with `r` in place of `q`.

## One row: three simultaneous hit bounds

For a row `a in B`, let `Y_a` be any independent set of newly inserted second coordinates and let

`C_a = union_{y in Y_a} (N[y] intersect B)`.

Define its raw core gain

`g_a = |Y_a| - |C_a|`.

For any transversal `T in {O,H,V}`, let

`H_T(a) = {t in T : some y in Y_a is confusable with t}`.

Exactly as in the single-row reduction, the five-dimensional set

`(B \ C_a) union Y_a union (T \ H_T(a))`

is independent and has size

`367 + g_a - |H_T(a)|`.

Therefore, under `alpha(C7^5) <= 367`, every row satisfies all three inequalities

`g_a <= |H_O(a)|`,

`g_a <= |H_H(a)|`,

`g_a <= |H_V(a)|`.                                      (1)

Rows with `g_a <= 0` cannot help a score-improving construction: dropping such a row's additions removes nonpositive raw gain and cannot increase the required blocker set.  Hence it suffices to charge rows with positive `g_a`.

## Matching charge for arbitrarily many rows

Consider any collection of modified rows, each with its own unrelated `Y_a`.  Let the terminal orientation determine three row-side factor/transversal pairs:

- factor `N` uses transversal `q`;
- factor `A` uses `H` in orientation 0 and `V` in orientation 1;
- factor `D` uses `V` in orientation 0 and `H` in orientation 1.

For a modified row `a`, inspect its matched point `m(a)`.

### If `m(a) in N`

By (1), at least `g_a` distinct endpoints of `q` are hit by `Y_a`.  Choose any `g_a` of them.  For every chosen endpoint `t`, the terminal point

`(m(a), t) in N x q`

conflicts with a newly inserted point `(a,y)`: the first coordinates conflict because `m(a) in N[a]`, and the second coordinates conflict by the definition of a hit.  Thus those terminal points must be deleted.

### If `m(a) in A` or `D`

Use the analogous inequality in (1) for the transversal attached to that factor in the current orientation.  The terminal contains `(m(a),t)` in the corresponding `A x H/V` or `D x V/H` block, so again `g_a` existing periphery points are forced out.

### Charges cannot be shared away

The matching `m` is injective.  Therefore different rows use different first coordinates `m(a)`.  Within one row the charged endpoints `t` are distinct.  Consequently all charged ten-dimensional periphery points `(m(a),t)` are pairwise distinct, even if the original blocker sets of different rows overlap heavily.

Hence any pure multi-row replacement forces at least

`sum_a g_a`

distinct terminal-periphery deletions.

The core/addition contribution before terminal losses is exactly `sum_a g_a`, because core cells from different rows are disjoint.  The final score increment therefore satisfies

`Delta <= sum_a g_a - sum_a g_a = 0`.

Thus, under `alpha(C7^5) <= 367`, **no arbitrary pure multi-row replacement can beat 134,753**.

The proof for arbitrary pure multi-column replacements is identical using the symmetric column-side terminal blocks and the same injective `B -> X` matching.

## Scope and remaining mechanism

This closure is much stronger than fixed-defect amplification experiments:

- any number of rows, up to all 359;
- each row may use a different independent replacement set;
- arbitrary support size and exchange radius;
- arbitrary sharing of ordinary terminal blockers;
- no restriction to k5/k6/k7/k8 support pools or known defect modes.

It also explains why the earlier exact amplification searches repeatedly optimized to gain zero: the matching provides a private forced blocker budget for every row's raw gain.

The proof does **not** cover simultaneous mixtures of row and column replacements.  In a mixed construction, deleted core cells at row/column intersections are shared, so the raw core gains are no longer additive by row or by column.  This is precisely the higher-order nonrectangular/rectangular support-product mechanism that survives the reduction.

Therefore future pinned-core work should stop scaling pure row or pure column searches.  The remaining qualitatively different target is **mixed row-column release**, where core-deletion overlap can compensate the matching charges, or the direct five-dimensional 368 problem itself.
