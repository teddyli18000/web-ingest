# Odd-perfect `(18,0)`, `K=19`: an exact sparse near-NGP corner

Date: 2026-10-30

## Scope

This note identifies a sharply constrained branch of the next odd-perfect half-sum class after `(20,0)`. It is an exact structural reduction, not a LABS record claim and not yet an exclusion.

For an odd-perfect length-100 sequence normalize the parity-half sums to

```text
a=sum A_i=18,
b=sum B_i=0.
```

Write

```text
d_r = C_(2r)/2,              r=1,...,49,
W   = sum d_r^2,
m   = d_25 = C_50/2.
```

Since

```text
sum d_r = (a^2+b^2-100)/4 = 56,
E = 50 + 4W,
```

and the `(18,0)` product class has `E == 2 (mod 8)`, a breakthrough through `E<=574` actually satisfies

```text
W <= 130.
```

For the 24 opposite-lag pairs define

```text
U_r = (d_r+d_(50-r))/2,
V_r = (d_r-d_(50-r))/2,       r=1,...,24.
```

The universal opposite-lag parity makes `U_r,V_r` integers, and exactly

```text
56 = m + 2 sum U_r,
W  = m^2 + 2 sum (U_r^2+V_r^2).              (1)
```

## Order-25 norm

For the standard order-25 compression

```text
p_i=(A_i+A_(i+25))/2,
q_i=(B_i+B_(i+25))/2,
c=x^13 q,
```

let

```text
K = ||p||^2 + ||c||^2.
```

A direct calculation at lag 50 gives

```text
C_50 = 2K-50,
```

so

```text
m=K-25.                                      (2)
```

The most negative feasible center surviving the `W<=130` convex bound is

```text
m=-6,
K=19.
```

This is particularly attractive because it leaves almost no antisymmetric energy.

## Exact `K=19` classification

Putting `m=-6` in (1) gives

```text
sum U_r = 31,
W = 36 + 2 sum(U_r^2+V_r^2).
```

Among 24 integers with sum 31, the minimum square sum is uniquely

```text
sum U_r^2 = 45,
U multiset = 1^17 2^7.
```

Hence the minimum is `W=126`. Since only even `W` occur in this product class, the entire `K=19`, `E<=574` branch consists of just `W=126,128,130`.

The possibilities are exact:

```text
W=126:
  U = 1^17 2^7,
  V = 0.

W=128:
  U = 1^17 2^7,
  sum V^2 = 1,
  so exactly one V coordinate is +/-1.

W=130:
  either
    U = 1^17 2^7,
    sum V^2 = 2,
    so exactly two V coordinates are +/-1,
  or
    V = 0,
    sum U^2 = 47.
```

The last integer system has exactly two multisets:

```text
U = 0^1 1^15 2^8,
U = 1^18 2^5 3^1.
```

Thus the complete `K=19` target is a zero-, one-, or two-defect near-NGP problem.

## Order-25 common PAF types

The periodic cross equation remains

```text
p c* + c p* = 0  in Z[x]/(x^25-1).
```

Equivalently, with `x=p+c`, `y=p-c`, the two small-alphabet sequences are cyclically homometric.

For `j=1,...,12`, their common order-25 PAF is

```text
G_j = PAF_p(j)+PAF_c(j) = U_j + U_(25-j).      (3)
```

For the base multiset `U=1^17 2^7`, pairing the 24 values into the 12 pairs of (3) gives only four sorted PAF multisets:

```text
2^5 3^7
2^6 3^5 4^1
2^7 3^3 4^2
2^8 3^1 4^3
```

For the two zero-defect `W=130` alternatives, exhaustive multiset pairing gives only 12 distinct sorted PAF multisets in total:

```text
1^1 2^7 4^4
1^1 2^6 3^2 4^3
1^1 2^5 3^4 4^2
1^1 2^4 3^6 4^1
1^1 2^3 3^8
2^9 4^2 5^1
2^8 3^2 4^1 5^1
2^8 3^1 4^3
2^7 3^4 5^1
2^7 3^3 4^2
2^6 3^5 4^1
2^5 3^7
```

The exact census is implemented in

```text
code/oddperfect_h18_k19_spectral_types.py
```

with assertions for the unique square-sum multisets and all PAF pairing counts.

## Fibre channel reuse

For the original even correlations,

```text
C_(2r)-C_(100-2r) = 4 V_r.
```

Therefore the existing exact order-25 fibre-key machinery applies without modification:

```text
W126 -> defect 0,
W128 -> defect 1,
W130 -> defect 0 or defect 2,
```

where every nonzero fibre target is exactly `+/-4` in one or two coordinates.

The reusable implementations are

```text
code/oddperfect_order25_fibre_mitm.cpp
code/oddperfect_order25_fibre_witness.cpp
```

The second reconstructs a full binary length-100 witness and independently rescales all LABS correlations whenever a fibre key matches.

## Why this corner is the next exact target

The broader `(18,0)` class has a large energy interval, so generic CP-SAT or unrestricted order-10 quotient search is not sufficiently selective. `K=19` is qualitatively different: the center value forces the whole target into three energy layers, four base periodic spectral types, and at most two antisymmetric defects.

A useful exact attack should therefore enumerate the order-25 compressed `(p,c)` candidates for these finite PAF types, preserving affine/support symmetry, and feed every survivor immediately into the exact fibre oracle. The symmetric-difference/modular-kernel machinery developed for the `(20,0)` low11 closure is directly reusable because the mod-2 cross equation still reduces to

```text
P D* + D P* = 0,
D=P xor C.
```

No claim is made here that `K=19` is empty.
