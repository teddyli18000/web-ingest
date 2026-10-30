# W127 order-25 projection: exact exclusion of `ka=20` and `ka=22`

Date: 2026-10-29

## Setup

For the odd-perfect `(20,0)` W127 branch, compress the parity halves to ternary length-25 sequences `p,c` as in the order-25 projection:

```text
sum p = 10,
sum c = 0,
||p||^2+||c||^2=26,
p c* + c p* = 0  in Z[x]/(x^25-1),
PAF_p(r)+PAF_c(r) in {2,3,4}, r != 0.
```

Let

```text
ka=||p||^2,
kc=||c||^2=26-ka.
```

This note gives exact, solver-independent exclusions of the two shards

```text
(ka,kc)=(22,4),(20,6).
```

The extreme `(24,2)` shard is proved separately in
`2026-10-29-w127-order25-ka24-exclusion.md`.

## Linearization for fixed c

For any even `ka`, a ternary `p` with support `ka` and sum 10 has

```text
#(+1) = (ka+10)/2,
#(-1) = (ka-10)/2,
#(0)  = 25-ka.
```

Let `z` be the zero indicator and `n` the negative-entry indicator. Then

```text
p = 1 - z - 2 n.                               (1)
```

For fixed `c`, the cross equation is linear in `p`. Let `M(c)` be its integer coefficient matrix, using the 13 independent cyclic coefficients `r=0,...,12`:

```text
M[r,j] = c_(j-r) + c_(j+r).                    (2)
```

Because `sum c=0`, the all-ones vector is in the kernel:

```text
M 1 = 0.
```

Substituting (1), the exact cross equation becomes the subset-sum identity

```text
boxed: M z + 2 M n = 0.                        (3)
```

This permits an exact meet-in-the-middle search: hash all allowed negative-position column sums, enumerate all zero supports, and look up the required vector `-Mz/2`. Disjointness of the two supports is checked explicitly.

Every hash hit is then reconstructed as a ternary `p` and independently checked against:

1. all 25 coefficients of the original integer cross equation, not only the 13 hashed coefficients;
2. all 12 independent combined cyclic autocorrelations;
3. the exact W127 requirements `2<=PAF_p(r)+PAF_c(r)<=4` and independent-shift sum 37.

Thus a hash collision or omitted symmetry assumption cannot itself create an exclusion.

## `ka=22,kc=4`

Here

```text
p: 16 plus, 6 minus, 3 zero,
c: 2 plus, 2 minus.
```

Common affine maps of `Z_25`,

```text
i -> a i+b, gcd(a,25)=1,
```

and an independent global sign flip of `c` preserve every projected equation. Exhaustive canonicalization of all

```text
C(25,2) C(23,2) = 75,900
```

raw `c` states gives exactly

```text
88 affine/sign orbits.
```

Implementation:

```text
code/oddperfect_w127_ka22_mitm.cpp
```

Exact exhaustive result:

```text
classes = 88
cross-compatible p = 30,542
W127 target survivors = 0
```

Therefore `(ka,kc)=(22,4)` is impossible.

## `ka=20,kc=6`

Here

```text
p: 15 plus, 5 minus, 5 zero,
c: 3 plus, 3 minus.
```

The raw `c` space has exactly

```text
C(25,3) C(22,3) = 3,542,000
```

states. The implementation constructs affine/sign orbits by explicit orbit marking rather than assuming generic orbit size. It verifies that all 3,542,000 raw states are covered and obtains

```text
3,586 orbits.
```

For each orbit representative, equation (3) is solved by hashing all `C(25,5)=53,130` negative supports and querying all 53,130 zero supports. The computation is parallelized across orbit representatives; each candidate is still independently checked with the original integer equations.

Implementation:

```text
code/oddperfect_w127_ka20_mitm.cpp
```

Exact exhaustive result on 5 CPU threads:

```text
raw c states = 3,542,000
visited by orbit construction = 3,542,000
classes = 3,586
cross-compatible p = 20,764
W127 target survivors = 0
```

The local full run completed in about 21 seconds; runtime is not part of the proof.

Therefore `(ka,kc)=(20,6)` is impossible.

## Consequence

The order-25 W127 support split originally had eight possible values

```text
ka = 10,12,14,16,18,20,22,24.
```

The exact non-CP-SAT exclusions now remove

```text
ka = 20,22,24.
```

so only

```text
ka = 10,12,14,16,18
```

remain.

The same direct orbit/MITM strategy grows substantially at `ka=18,kc=8` because the `c` orbit count and zero-support count increase sharply. That is the point where the running order-25 CP-SAT projection or a stronger cyclotomic/lift representation becomes preferable to mechanically scaling this enumeration.
