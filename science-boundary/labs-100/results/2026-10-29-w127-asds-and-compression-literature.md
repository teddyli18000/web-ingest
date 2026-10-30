# W127 as an even-order ASDS plus shifted cross constraint

Date: 2026-10-29

## Purpose

This note records a design-theoretic reformulation of the odd-perfect `(20,0)`, `W=127` branch and relates it to two relevant external lines: almost supplementary difference sets (ASDS) and the October 2026 exact compression/lifting method for complementary pairs.

No LABS improvement or impossibility theorem is claimed here.

## From parity halves to an ASDS on Z_50

Let `A,B` be the length-50 parity halves of an odd-perfect candidate, normalized by

```text
sum A = 20,
sum B = 0.
```

Let

```text
X = {i : A_i=-1}, |X|=15,
Y = {i : B_i=-1}, |Y|=25.
```

At `W=127`, the exact correlation multiset is

```text
d_r=C_(2r)/2 in {1,2},
d=1 x23,
d=2 x26,
```

and opposite-lag parity forces

```text
d_r=d_(50-r).
```

Hence the combined periodic autocorrelation of the two halves is

```text
PAF_A(r)+PAF_B(r)
 = C_(2r)+C_(100-2r)
 = 4 d_r
 in {4,8}.
```

For negative sets `X,Y`, if `lambda_X(r)` is the number of ordered differences `x-x'=r`, then

```text
PAF_A(r) = -10 + 4 lambda_X(r),
PAF_B(r) = -50 + 4 lambda_Y(r).
```

Therefore

```text
lambda_X(r)+lambda_Y(r) in {16,17},
```

with exactly 23 nonzero shifts taking 16 and 26 taking 17.

Thus `(X,Y)` is exactly an even-order

```text
2-{50;15,25;16;23}
```

almost supplementary difference-set pair in the terminology of Armario--Flannery.

The parameter count checks:

```text
15*14 + 25*24 = 810
23*16 + 26*17 = 810.
```

This ASDS condition is necessary but not sufficient for the LABS branch.

## The extra odd-perfect cross condition

Let

```text
n(r) = #{(x,y) in X x Y : y-x=r mod 50}.
```

The periodic cross factor from odd-perfectness is

```text
A B* + x B A* = 0  in Z[x]/(x^50-1).
```

In correlation form this is

```text
R_AB(r)+R_BA(r+1)=0.
```

Since

```text
R_AB(r)=-30+4 n(r),
R_BA(r+1)=-30+4 n(-r-1),
```

we obtain the exact shifted cross rule

```text
boxed: n(r)+n(-r-1)=15,  for all r in Z_50.       (1)
```

This is stronger than the ASDS property. It is also not the usual ASDS `amicability` condition `n(r)=n(-r)`: the involution is reflection about `-1/2`, and `1/2` does not exist in `Z_50`.

Writing `Z_50 ~= Z_2 x Z_25` makes the obstruction explicit. If

```text
n_even(t)=n(2t),
n_odd(t)=n(2t+1),
```

then (1) is

```text
n_even(t)+n_odd(-t-1)=15.
```

This is the set version of the order-25 cross-channel equation used by the current exact projection model.

## Relation to ASDS literature

Armario and Flannery introduced ASDS and proved that, for odd `m`, ASDS satisfying a symmetric cross-difference condition are equivalent to optimal quaternary sequences / quasi-orthogonal cocycles.

Reference:

- J. A. Armario and D. L. Flannery, *Almost supplementary difference sets and quaternary sequences with optimal autocorrelation*, Cryptography and Communications 12 (2020), 757--768; arXiv:1911.08828.

Their ASDS definition itself applies here, but their main equivalence theorem assumes odd `m`. Our parameter group is `Z_50`, and the shifted reflection (1) is not their ordinary amicability condition. Therefore that theorem cannot currently be used as a nonexistence result for W127.

The connection is still useful: it identifies the periodic part of W127 as a highly constrained design object rather than a generic LABS state, and suggests importing exact difference-family enumeration and cyclotomic-key techniques.

## Very recent compression/lifting result

A directly relevant new preprint appeared on 2026-10-24:

- S. D. Georgiou and S. Stylianou, *An exact compression-and-lifting procedure and D-optimal designs of orders 198 and 170*, arXiv:2610.33418.

The paper separates Fourier conditions retained by compression from the missing character channels. It then groups local lifts by exact integer spectral keys (cyclotomic/minimal-polynomial remainders) before generating full sequences. For the successful length-99 construction, the reported exact key removes 99.9888% of raw lift pairs while preserving every valid D-optimal lift.

The paper's general exact-key statement is especially relevant: for an integer sequence on `Z_m`, equality of PSD at primitive `m`th roots can be tested by reducing its autocorrelation polynomial modulo the cyclotomic polynomial `Phi_m`. Thus a real-field key of dimension `phi(m)/2` gives an exact integer class identifier.

This aligns with the current LABS route:

```text
length 50 binary A,B
    -> order-25 ternary compression
    -> exact cross/autocorrelation projection
    -> classify compatible lift channels by cyclotomic keys
    -> only then generate/test binary lifts.
```

The published result concerns D-optimal complementary pairs on odd-order groups, so its target equations are not identical to W127. The reusable part is the exact compression/channel/key methodology, not its D-optimal existence theorem.

## Current computational consequence

The committed order-25 CP-SAT projection

```text
code/oddperfect_w127_order25_cpsat.py
```

is an exact necessary-condition test on the compressed ternary pair. If it has survivors, the next implementation should not enumerate all binary lifts naively. Instead it should:

1. expose the nontrivial length-2 fibre channel (agreement/disagreement signs);
2. form exact `Phi_50` / `Phi_25` or real-subfield spectral keys for the missing periodic cross and NGP equations;
3. count/match compatible lift classes first;
4. run the full aperiodic odd-perfect check only inside matched classes.

A separate exact Boolean full model is also retained as

```text
code/oddperfect_e558_xor_cpsat.py
```

for independent verification or direct shard searches.
