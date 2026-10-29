# Exact exclusion of the odd-perfect endpoint-defect-5 layer

Date: 2026-10-29

## Statement

For a length-100 odd-perfect binary sequence (`O=50`), let `d=min(d_L,d_R)` be the minimum number of nonzero odd autocorrelations in the two length-99 endpoint deletions. Reverse the sequence if necessary so that a minimum-defect endpoint is on the right.

The computation recorded here proves:

> There is no odd-perfect length-100 sequence with invariant endpoint defect `d=5` and total LABS energy `E<=574`.

In fact the defect-5 target arithmetic forces `E<=570`, and the search finds no such sequence.

Together with the exact near-skew result (`d=0`) and the completed defect-1 through defect-4 searches, any odd-perfect `E<=574` candidate must have invariant endpoint defect at least 6.

## Defect-5 target arithmetic

Let `R=s[0..98]`, and write the parity-half sums

```text
A = sum_i s_{2i},
B = sum_i s_{2i+1}.
```

For the right deletion,

```text
sum_{k odd} C_k(R) = A(B-s_99).
```

With defect 5, exactly five odd deletion correlations are nonzero and each is `+/-2`, so their sum is one of

```text
+/-2, +/-6, +/-10.
```

Odd-perfectness gives `AB=0`. The deletion sum is nonzero, hence `A!=0`, so necessarily

```text
B=0,
|A| in {2,6,10}.
```

All three nonzero half-sum magnitudes are `2 (mod 4)`. The product/energy congruence therefore places the sequence in the `E == 2 (mod 8)` class. For a target below 578, the largest possible energy in this class is 570, so

```text
even energy <= 570-50 = 520.
```

This is the exact energy cap used by the search.

## Why the old anchor representation was abandoned

There are

```text
C(49,5) = 1,906,884
```

five-lag supports. In the reflection-path representation, a support with five separated edges has ten bad reflection coordinates. The previous modular solver would normalize one bad coordinate and enumerate the remaining bad-coordinate signs, producing up to 512 anchor systems per support.

An exact combinatorial count over all defect-5 supports gives about

```text
666,348,057
```

anchor/gauge linear systems. This was the wrong search space to scale.

## Mod-4 Boolean linearization

Fix only the unsigned endpoint support, not the bad-coordinate anchor signs.

After reflection inversion, each exact odd-perfect equation is a signed sum of monomials of the form

```text
+/- x_i x_j
```

plus, on a supported lag, one signed endpoint monomial. Every variable is `+/-1`.

Write

```text
x_i = (-1)^{b_i},  b_i in GF(2).
```

Expand an integer coefficient of magnitude `m` as `m` identical unit terms. Suppose one exact equation has `M` unit `+/-1` terms and must sum to zero. Then exactly `M/2` terms are negative. Modulo 2, the parity of the number of negative terms is therefore fixed:

```text
xor_t negative_bit(t) = (M/2) mod 2.
```

For a signed monomial,

```text
negative_bit(+ x_i x_j) = b_i xor b_j,
negative_bit(- x_i x_j) = 1 xor b_i xor b_j.
```

Thus every integer quadratic equation yields a **linear affine equation over GF(2)**. The same construction applies to the exact `B=0` signed-sum equation.

This is only a necessary mod-4 filter. It cannot cause a false exclusion because the solver then enumerates the complete resulting affine GF(2) space and re-evaluates every original integer equation exactly.

## Exact symmetry gauge

Global negation fixes one bad reflection coordinate to `+1`. For odd endpoint defect, an even bad reflection coordinate must exist: if every bad path vertex were odd, edge 0 would be absent and every pair of edges `(1,2),(3,4),...,(47,48)` would have equal membership, forcing the support weight to be even, a contradiction.

Choose an even bad coordinate as the global-negation reference. The alternating-sign LABS symmetry leaves this even reference fixed but flips the endpoint sign, so fix

```text
x_ref = +1,
s_99 = +1.
```

This keeps exactly one representative of each relevant global-negation/alternation orbit.

## Full profile and exhaustion

A complete mod-4 profile over all 1,906,884 supports took one GF(2) elimination per support and produced

```text
affine assignments = 4,498,643,306
maximum nullity     = 24
```

This is comparable to the already-completed defect-4 free-assignment workload, despite defect 5 having almost nine times as many supports.

The exact search was then split into five contiguous ranges chosen by **affine workload**, not support count:

```text
[0,910000)          902,404,068 affine assignments
[910000,1460000)    905,549,268
[1460000,1670000)   848,528,446
[1670000,1760000)   892,755,976
[1760000,1906884)   949,405,548
```

Every range returned

```text
complete=1
found=0
```

Aggregate exact workload:

```text
supports                    1,906,884
mod-4 affine assignments    4,498,643,306
exact integer solutions     1,190,683,248
target-half-sum solutions   1,190,683,248
maximum affine nullity                 24
```

For defect 5, every exact solution of the reflection equations plus `B=0` automatically has the target support-sum magnitude `|A| in {2,6,10}`, hence `exact == target` in the transcript.

No exact solution had even energy at most 520. Therefore no defect-5 odd-perfect sequence has total energy at most 570, and a fortiori none has `E<=574`.

The clean per-range transcript is preserved in [`2026-10-29-endpoint-defect5-mod4-exhaustion.log`](2026-10-29-endpoint-defect5-mod4-exhaustion.log).

## Independent implementation checks

The new representation was cross-checked in two ways.

First, the mod-4 solver independently re-exhausted the **entire defect-3 layer**. It found exactly

```text
204,187,502
```

integer `+/-1` solutions, exactly matching the previous mod-257 anchor solver's independently obtained `+/-1` candidate count `204,187,502`. Both complete searches found no target sequence.

Second, four defect-5 supports were solved both ways:

```text
support             mod-257 exact   mod-4 exact
1,3,5,7,9                    38              38
1,5,9,13,17                  32              32
1,11,21,31,41              2054            2054
49,61,73,85,97             4098            4098
```

The full exclusion rests on the five complete mod-4 ranges; these comparisons validate the new representation against the older exact implementation.

## Reproducibility

The retained implementation is

```text
code/oddperfect_endpoint_mod4.cpp
```

It derives the GF(2) affine system from the original integer reflection equations, enumerates every affine solution, rechecks all integer equations exactly, reconstructs the length-100 sequence, applies the defect-specific half-sum condition, screens even energy with bit-parallel correlation code, and independently recomputes all original correlations before reporting any possible hit.

## Consequence

The exact odd-perfect endpoint picture is now

```text
d=0   near-skew manifold: exact minimum E=578
d=1   no E<=574
d=2   no E<=574
d=3   no E<=574
d=4   no E<=574
d=5   no E<=574
```

The next move should **not** be a mechanical defect-6 campaign. Defect 5 was made tractable only by changing representation. The more promising global reformulation is the parity-polynomial factorization of the complete odd-perfect condition, recorded separately, which removes endpoint support from the primary state space altogether.
