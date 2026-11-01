# Odd-energy defect projection beyond odd-perfectness

Date: 2026-11-01

## Purpose

The exact `(18,0)` program has now closed three consecutive odd-perfect center layers `K=19,21,23` without producing a better candidate.  Rather than mechanically extend the same slice, this note changes the search space: it derives the first non-odd-perfect odd-energy layer `O=58` from first principles.

The main result is that `O=58` is not a generic relaxation.  It has a **one-sparse cyclic cross defect**, forces the parity-half sums to `(2,2)` up to energy-preserving sign symmetries, and turns the existing periodic/negacyclic zero equations into the even/odd parts of that same one-sparse defect.

## Paired odd correlations

Let

```text
D_r = C_(2r+1),   r=0,...,49,
O = sum_r D_r^2.
```

Every `D_r` is odd.  Pair opposite odd lags and define

```text
z_r = (D_r + D_(49-r))/4,   r=0,...,24.       (1)
```

### Integrality

Split the length-100 sequence into parity halves `A,B` of length 50, and let

```text
T_r = sum_i A_i B_(i+r mod 50)
```

be their cyclic cross-correlation.  Directly separating wrapped and non-wrapped terms gives

```text
D_r + D_(49-r) = T_r + T_(49-r).              (2)
```

For any shift `r`, write `T_r=50-2h_r`, where `h_r` is the number of negative products in that cyclic cross-correlation.  The parity of `h_r` is independent of `r`, because

```text
(-1)^h_r = product_i A_i B_(i+r)
          = (product_i A_i)(product_i B_i).
```

Hence all `T_r` are congruent modulo four.  Equation (2) therefore implies

```text
D_r + D_(49-r) == 0 (mod 4),
```

so every `z_r` in (1) is an integer.

## Exact odd-energy lower bound

For each pair write

```text
D_r       = 2 z_r + e_r,
D_(49-r)  = 2 z_r - e_r,
```

where `e_r` is odd.  Then

```text
D_r^2 + D_(49-r)^2
  = 8 z_r^2 + 2 e_r^2
  >= 8 z_r^2 + 2.
```

Summing the 25 pairs gives the global bound

```text
O >= 50 + 8 ||z||_2^2.                         (3)
```

More precisely,

```text
O - (50 + 8 ||z||_2^2)
  = 2 sum_r (e_r^2-1),
```

and because `e_r` is odd, the right-hand side is a nonnegative multiple of 16.

The standard identity

```text
sum_r D_r = a b,
```

with `a=sum A`, `b=sum B`, becomes

```text
ab = 4 sum_r z_r.                              (4)
```

Equation (4) immediately recovers the odd-perfect consequence `ab=0` when `z=0`.

## The first non-odd-perfect layer: `O=58`

If `O=58`, equation (3) and the mod-16 remainder force

```text
||z||_2^2 = 1,
```

with equality in every paired bound.  Therefore exactly one coordinate of `z` is `+1` or `-1`, all others are zero, and every `|e_r|=1`.

Equivalently, exactly one opposite odd-lag pair is

```text
(3,1) or (1,3),
```

up to simultaneous sign, while every other pair is `(1,-1)` up to sign.

Equation (4) then gives

```text
ab = +/-4.
```

Since length-50 half sums are even, the only absolute half-sum class is

```text
(|a|,|b|) = (2,2).
```

Global sign and a whole-half sign flip preserve LABS energy, so the `O=58` layer may be normalized to

```text
(a,b) = (2,2),
sum z_r = 1,
z = a positive unit vector.                    (5)
```

This collapses the first non-odd-perfect target from many apparent half-sum classes to one.

## Periodic / negacyclic channel split

Use the same order-25 decomposition as in the odd-perfect work:

```text
A=(1+x^25)p+(1-x^25)alpha,
B=(1+x^25)q+(1-x^25)beta,
c=x^13 q              in Z[x]/(x^25-1),
gamma=x^13 beta       in Z[x]/(x^25+1).
```

Let `P_s` be the coefficient of

```text
p c* + c p*            mod x^25-1
```

and `M_s` the coefficient of

```text
alpha gamma* - gamma alpha*   mod x^25+1.
```

Exact coefficient algebra gives

```text
P_0 = 2 z_12,
M_0 = 0,
```

and for `s=1,...,12`,

```text
P_s = z_(12+s) + z_(12-s),                    (6)
M_s = z_(12+s) - z_(12-s).                    (7)
```

Indices are ordinary integers in `0,...,24` in (6)-(7).  The remaining coefficients satisfy

```text
P_(25-s)= P_s,
M_(25-s)=-M_s.
```

Thus the two order-25 channels are exactly the even and odd parts of the same vector `z` about the center index 12.

The old odd-perfect equations

```text
p c* + c p* = 0,
alpha gamma* - gamma alpha* = 0
```

are simply the special case `z=0`.

### `O=58` defect shapes

Under normalization (5), only two forms occur.

If the nonzero `z` entry is the center `z_12=1`, then

```text
P_0=2,
P_s=M_s=0 for s=1,...,12.
```

If the nonzero entry is `z_(12+s)=1` for some `s=1,...,12`, then

```text
P_s=1,
M_s=1,
```

with all other independent coefficients zero.  If instead the nonzero entry is `z_(12-s)=1`, then

```text
P_s=1,
M_s=-1.
```

So the first odd-energy defect remains one-sparse in both channels.  Among nonzero lag locations, multiplication by units modulo 25 has only the `gcd(s,25)=1` and `gcd(s,25)=5` location classes; the sign/orientation of the negacyclic defect should be retained until the corresponding full-sequence symmetry is explicitly proved.

## Even-energy target arithmetic for `O=58`

After normalizing `(a,b)=(2,2)`,

```text
sum_r d_r = (a^2+b^2-100)/4 = -23,
```

where `d_r=C_(2r)/2`.  As before let

```text
m=d_25=K-25,
U_r=(d_r+d_(50-r))/2,
V_r=(d_r-d_(50-r))/2.
```

Because each half has 24 negative signs, the global product is `+1`.  Hence `m` is odd, `K` is even, and `E==6 (mod 8)`.  The target `E<=574` is therefore exact at 574, giving

```text
4W <= 516,
W <= 129,
W = m^2 + 2 sum(U_r^2+V_r^2),
sum U_r = (-23-m)/2.
```

Integer convexity leaves exactly the center values

```text
K = 16,18,20,22,24,26,28,30,32,34.
```

For each such `K`, with `m=K-25`, define

```text
B_K = (129-m^2)/2.
```

Then the exact even-energy condition is

```text
sum(U_r^2+V_r^2) <= B_K.
```

The resulting budgets are

| `K` | `m` | `sum U` | `B_K` |
|---:|---:|---:|---:|
| 16 | -9 | -7  | 24 |
| 18 | -7 | -8  | 40 |
| 20 | -5 | -9  | 52 |
| 22 | -3 | -10 | 60 |
| 24 | -1 | -11 | 64 |
| 26 |  1 | -12 | 64 |
| 28 |  3 | -13 | 60 |
| 30 |  5 | -14 | 52 |
| 32 |  7 | -15 | 40 |
| 34 |  9 | -16 | 24 |

The existing compressed even-correlation lower bound `qmin(G)` and the `SG+SH` fibre identity do not depend on odd-perfectness and can therefore be reused, but the two cross equations must use the sparse right-hand sides (6)-(7) rather than zero.

## Regression

`code/odd_energy_defect_projection.py` independently computes the original length-100 odd correlations, both parity-half channel decompositions, and checks equations (1)-(7), the energy lower bound, and `ab=4 sum z` on the public E578 incumbent plus 500 deterministic pseudo-random binary sequences.

This regression is an index/sign audit; the proof is the algebra above.

## Consequence for the research program

The next exact search should **not** simply continue `(18,0)` odd-perfect center layers by default.  The first non-odd-perfect layer has unexpectedly strong structure:

```text
O=58
=> canonical half sums (2,2)
=> one-sparse z
=> one-sparse coupled periodic/negacyclic cross defects
=> only ten convex-feasible even center values K=16,18,...,34.
```

This gives a qualitatively new candidate family while retaining the successful order-25 compression/fibre interface.  It is the preferred next representation to test against the remaining odd-perfect `K>=25` route.
