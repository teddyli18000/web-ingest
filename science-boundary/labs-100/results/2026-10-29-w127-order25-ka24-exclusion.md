# W127 order-25 projection: exact exclusion of the `ka=24` shard

Date: 2026-10-29

## Statement

Consider an odd-perfect length-100 LABS candidate in normalized half-sum class

```text
(sum A, sum B) = (20,0)
```

at the minimum even-energy budget

```text
W = E_even/4 = 127.
```

Compress the parity halves modulo 25:

```text
p_i = (A_i + A_(i+25))/2,
q_i = (B_i + B_(i+25))/2,
```

and shift the second compression by the inverse of 2 modulo 25,

```text
c = x^13 q.
```

Then `p,c` are ternary sequences in `{-1,0,1}^25` satisfying

```text
sum p = 10,
sum c = 0,
p c* + c p* = 0  in Z[x]/(x^25-1),
||p||^2 + ||c||^2 = 26,
PAF_p(r)+PAF_c(r) in {2,3,4}  for every r != 0.
```

Let

```text
ka = ||p||^2,
kc = ||c||^2 = 26-ka.
```

This note proves exactly that

```text
ka=24, kc=2
```

is impossible.

## Normalize the two-point `c`

Since `c` has support 2 and sum zero, after a cyclic shift and global sign it has the form

```text
c = delta_0 - delta_d,
```

for some nonzero `d mod 25`.

The cross equation becomes

```text
p c* + c p* = 0.
```

Substituting the two-point `c` and factoring in `Z[x]/(x^25-1)` gives

```text
(1-x^(-d)) (p - x^d p*) = 0.                 (1)
```

There are only two cases because `25=5^2`.

## Case 1: `gcd(d,25)=1`

Multiplication by `d` generates the whole cyclic group. Therefore the kernel of

```text
1-x^(-d)
```

on length-25 cyclic sequences consists exactly of constants.

The sequence

```text
g = p-x^d p*
```

has coefficient sum zero, so (1) forces

```text
p = x^d p*.
```

Thus `p` is invariant under the reflection

```text
i -> d-i mod 25.
```

A reflection of an odd cycle has exactly one fixed coordinate. Because `ka=24`, `p` has exactly one zero. From

```text
sum p=10,
#supp(p)=24
```

its nonzero entries consist of

```text
17 copies of +1,
7 copies of -1.
```

The unique zero must occupy the reflection fixed point. Every other coordinate occurs in an equal-value reflection pair, so the numbers of `+1` and `-1` entries must both be even. But they are `17` and `7`, contradiction.

Hence no unit-distance two-point `c` is possible.

## Case 2: `gcd(d,25)=5`

A unit multiplier normalizes `d` to 5, so take

```text
c = delta_0-delta_5.
```

Equation (1) says

```text
g = p-x^5 p*
```

is invariant under cyclic shift by 5.

The reflection in this expression is

```text
i -> 5-i mod 25.
```

It has one fixed point and twelve 2-cycles. The shift-5 invariance of `g`, together with

```text
p_i in {-1,0,1},
#supp(p)=24,
sum p=10,
```

leaves a tiny finite integer system.

The dependency-free verifier

```text
code/oddperfect_w127_ka24_exact.py
```

enumerates this system directly. It finds exactly

```text
28
```

candidate `p` sequences satisfying the complete order-25 cross equation.

Every candidate is then independently rechecked against all 25 cross coefficients. For each one the combined cyclic autocorrelation at shift 5 is

```text
PAF_p(5)+PAF_c(5) = 14  (20 candidates),
or
PAF_p(5)+PAF_c(5) = 18  (8 candidates).
```

But W127 requires this quantity to belong to

```text
{2,3,4}
```

at every nonzero shift. Therefore none survives.

Expected verifier summary:

```text
KA24_GCD5_CANDIDATES 28
KA24_SHIFT5_VALUES {14: 20, 18: 8}
KA24_W127_SURVIVORS 0
EXACT_RESULT W127_ORDER25_KA24_INFEASIBLE
```

## Conclusion

Both possible distance classes are impossible, so the W127 order-25 projection has no solution with

```text
(ka,kc)=(24,2).
```

This removes one of the eight support-size shards independently of CP-SAT and without any timeout qualification.

The remaining possible `ka` values are

```text
10,12,14,16,18,20,22.
```

The same small-support algebra may be useful next for `ka=22,kc=4` before spending more general-purpose search effort.
