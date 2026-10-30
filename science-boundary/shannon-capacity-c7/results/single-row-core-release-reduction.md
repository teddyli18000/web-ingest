# Arbitrary single-row/column core release reduces to the open C7^5=368 problem

Status: **structural closure of the entire arbitrary single-row and arbitrary single-column replacement family, conditional only on the unresolved statement `alpha(C7^5) <= 367`.** No score above 134,753 is claimed.

Pinned construction: Tandon/BPZ data at commit `c753408492dde92a239708986d16c15dbf6c3235`.

## Setup

Let `B` be the 359-point core factor.  Write the pinned terminal periphery in a row orientation as

`N x q  union  A x H/V  union  D x V/H  union  (blocks with first coordinate in Q)`,

where `q` is one of the three 8-point transversals `O,H,V`, and `N=X0` has 322 points.  Every point of `B` is nonconfusable with every point of `O,H,V`, and each of those transversals is independent.  Thus

`B union q`

is a 367-point independent set for each `q in {O,H,V}`.

The pinned finite audit also gives

`min_{a in B} |N[a] intersect N| = 1`.

The full histogram is

| `|N[a] intersect N|` | rows `a in B` |
|---:|---:|
| 1 | 37 |
| 2 | 12 |
| 3 | 21 |
| 4 | 63 |
| 5 | 79 |
| 6 | 76 |
| 7 | 66 |
| 8 | 5 |

These construction-specific facts are independently replayed by `code/bpz_single_row_reduction_audit.py`.

## Arbitrary row replacement

Fix any row coordinate `a in B`.  Let `Y` be **any** independent set of five-dimensional second coordinates not already used as retained core points.  No support size, exchange radius, or previously enumerated defect family is assumed.

To insert the ten-dimensional points

`{a} x Y`,

the necessary deleted core columns are

`C = union_{y in Y} (N[y] intersect B)`.

Let

`H_q = {t in q : some y in Y is confusable with t}`.

Because the terminal contains the entire block `N x q`, and because `a` has at least one neighbor in `N`, every endpoint `t in H_q` forces deletion of at least one terminal-periphery point `(x,t)` with `x in N[a] intersect N`.  Different `t` give different ten-dimensional points, hence the actual periphery loss `L` obeys

`|L| >= |H_q|`.

Therefore the true ten-dimensional score increment of this arbitrary row move satisfies

`Delta <= |Y| - |C| - |H_q|`.                 (1)

Now consider the five-dimensional set

`S = (B \ C) union Y union (q \ H_q)`.

It is independent:

- `B \ C` is independent;
- `Y` is independent by assumption;
- the definition of `C` removes every core point confusable with `Y`;
- `q` is independent and completely nonconfusable with `B`;
- the definition of `H_q` removes every endpoint of `q` confusable with `Y`.

Its cardinality is exactly

`|S| = 359 - |C| + |Y| + 8 - |H_q|`

`     = 367 + |Y| - |C| - |H_q|`.             (2)

Combining (1) and (2):

> If an arbitrary single-row replacement has `Delta >= 1`, then `S` is an explicit independent set of at least 368 points in `C7^5`.

Thus, under `alpha(C7^5) <= 367`, **no arbitrary single-row replacement can beat 134,753**.

The column proof is identical using the terminal block `r x N`, where `r in {O,H,V}`.

## Scope

This is substantially stronger than the earlier k=5/k=6/k=7/k=8 row-defect censuses:

- no bound on support size `k`;
- no assumption that the replacement comes from a known support pool;
- no killer-color proxy;
- no local exchange-radius restriction;
- true terminal loss is lower-bounded directly by the mandatory `N x q` / `r x N` block.

It therefore closes **all single-row and single-column core-release mechanisms** as an independent route around the unresolved five-dimensional 368 problem.

It does **not** close genuinely multi-row/nonrectangular replacements, because different rows may share deleted terminal-periphery blockers.  That sharing is the remaining mechanism not captured by the rowwise inequality.  Future core-release work should optimize multi-row coupling directly rather than enumerate larger single-row support defects.

## Consequence for compute

Do not spend further compute mechanically extending single-row support-gap searches to k=9, k=10, etc.  A positive result there would already imply the much larger five-dimensional breakthrough `alpha(C7^5) >= 368`, whose square gives 135,424 points in `C7^10`.

The active directions after this reduction are:

1. direct search for a 368-word independent set in `C7^5` using a qualitatively different/global representation;
2. genuinely coupled multi-row/nonrectangular ten-dimensional core release, where terminal blockers can be shared across rows;
3. exact optimization over row interactions rather than isolated row defects.
