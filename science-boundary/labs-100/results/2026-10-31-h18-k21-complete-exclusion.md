# Odd-perfect `(18,0)`, `K=21`: complete exact exclusion through `E<=570`

Date: 2026-10-31

## Scope

This note closes the complete order-25 compression layer

```text
(a,b) = (18,0),
K = ||p||^2 + ||c||^2 = 21
```

for an odd-perfect length-100 LABS sequence with `E<=570`.

For this half-sum class the global product is `-1`, so an odd-perfect sequence with `E<578` can only have energies `... ,570,562,...`; consequently `E<=574` is equivalent here to `E<=570`.

The preceding `K=19` layer is closed in [`2026-10-31-h18-k19-complete-exclusion.md`](2026-10-31-h18-k19-complete-exclusion.md).

No unrestricted LABS improvement is claimed.  The public best remains `E=578`.

## Arithmetic reduction

Let

```text
d_r = C_(2r)/2,
U_r = (d_r+d_(50-r))/2,
V_r = (d_r-d_(50-r))/2,   r=1,...,24,
m = d_25.
```

For `(a,b)=(18,0)`,

```text
sum_{r=1}^{49} d_r = 56.
```

At `K=21`, `m=K-25=-4`, hence

```text
sum U_r = 30,
W = sum d_r^2 = 16 + 2(Q+R),
Q = sum U_r^2,
R = sum V_r^2.
```

Therefore

```text
E = 50 + 4W <= 570
iff
Q+R <= 57.                                      (1)
```

For the order-25 compressed pair `p,c`, define

```text
G_j = PAF_p(j)+PAF_c(j),  j=1,...,12.
```

Since `G_j=U_j+U_(25-j)`, the exact minimum possible `U`-norm for a fixed compressed spectrum is

```text
qmin(G) = sum_j ceil(G_j^2/2).                   (2)
```

Thus every target must satisfy `qmin(G)<=57`.  This avoids enumerating the `U` multisets themselves.

## Exact fibre split and `Q` identity

Write the two binary length-50 halves as

```text
A = (1+x^25)p + (1-x^25)alpha,
B = (1+x^25)q + (1-x^25)beta,
c = x^13 q,
gamma = x^13 beta.
```

Odd-perfect cyclic cross zero splits exactly into

```text
p c* + c p* = 0             mod x^25-1,
alpha gamma* - gamma alpha* = 0   mod x^25+1.
```

Let

```text
H_j = NPAF_alpha(j)+NPAF_gamma(j),
SG = sum_j G_j^2,
SH = sum_j H_j^2.
```

Then the full symmetric even-correlation norm is exactly

```text
2Q = SG + SH.                                      (3)
```

Hence the full fibre target is simply

```text
SG+SH <= 114.                                      (4)
```

The simultaneous affine action `AGL(1,Z_25)` on the two fibre supports preserves the attainable `SH` set.  The exact grouped solver therefore canonicalizes the support pair `(supp(alpha),supp(gamma))` and enumerates signs only on the smaller support, while checking every surviving modular solution in the original integer negacyclic equations.

Implementation:

- [`../code/oddperfect_h18_k21_compressed.cpp`](../code/oddperfect_h18_k21_compressed.cpp)
- [`../code/oddperfect_h18_k21_fullgamma.cpp`](../code/oddperfect_h18_k21_fullgamma.cpp)
- [`../code/oddperfect_h18_k21_qgroup.cpp`](../code/oddperfect_h18_k21_qgroup.cpp)
- [`../code/oddperfect_h18_k21_qgroup_affine.cpp`](../code/oddperfect_h18_k21_qgroup_affine.cpp)
- [`../code/oddperfect_h18_k21_kp15_witness.cpp`](../code/oddperfect_h18_k21_kp15_witness.cpp)
- [`../code/oddperfect_h18_k21_kp21_grouped.cpp`](../code/oddperfect_h18_k21_kp21_grouped.cpp)
- [`../code/oddperfect_h18_k21_affine_witness.cpp`](../code/oddperfect_h18_k21_affine_witness.cpp)

## Complete split coverage

The possible norm splits are

```text
(kp,kc) =
(21,0), (19,2), (17,4), (15,6), (13,8), (11,10), (9,12).
```

Every split is now excluded exactly.

### `(19,2)`

The complete compressed search has no `qmin<=57` target.  The two overlap layers `t=0,2` contain respectively 2,388 and 7,220 exact integer-cross sign solutions after support reduction, but zero spectral targets.

Clean reproduction: run `41183879257`.

### `(17,4)`

The complete compressed search leaves 293 representatives over `t=0,2,4`.  Exhausting every negacyclic fibre gives

```text
alpha states                 75,008
half-gamma solutions      4,033,322
full-gamma solutions      8,066,644
Q <= 57                         0
```

So no affine lift is needed.

Clean reproduction: run `41183879257`.

### `(15,6)`

The compressed search leaves 1,840 target hits grouped into 1,747 fibre-support pairs.  Exact fibre-Q enumeration leaves exactly one half-fibre with `Q<=57`:

```text
half-gamma solutions     11,358,884
Q-feasible half-gamma             1
minimum margin                    -6
```

The final witness verifier expands its four independent fibre sign orientations and all 500 induced affine images:

```text
affine transforms       2,000
V-budget passes             0
odd-perfect passes          80
E <= 570                     0
minimum V^2                 39
minimum energy            1434
```

Clean corrected reproduction: run `41185066943`.

### `(21,0)`

The compressed search has 3,933 hits but only 30 fibre-support groups.  The exact grouped fibre computation gives

```text
alpha states                480
half-gamma solutions    149,828
Q-feasible half-gamma         0
minimum margin               26
```

Clean reproduction: run `41184237885`.

### `(11,10)`

The complete compressed census has 6,846 `qmin<=57` hits, reduced by simultaneous affine support canonicalization to 6,649 groups.  Exact negacyclic fibre enumeration gives

```text
outer sign states        54,468,608
half-second solutions    31,012,274
Q-feasible half-pairs             0
minimum margin                     2
```

Clean runs: compressed `41185379285`; fibre-Q `41185885170`.

### `(13,8)`

The complete compressed census has 12,160 hits, giving 10,184 affine-canonical support groups.  Exact fibre-Q enumeration leaves only three half-pairs, all with

```text
Q = 54,
R <= 3 required by (1).
```

The final verifier maps every compressed hit in each support orbit to the exact canonical Q survivor, restores both independent global fibre signs, and exhausts all 500 induced full-length affine images.  It directly recomputes the original length-100 correlations and energy:

```text
Q survivors                         3
mapped compressed candidates        7
fibre orientations                 28
affine transforms              14,000
V-budget passes                     0
odd-perfect passes                480
E <= 570                            0
minimum V^2                        23
minimum odd energy                 50
minimum full energy              1386
```

### `(9,12)`

The complete compressed census has 3,644 hits, giving 3,527 affine-canonical support groups.  Exact fibre-Q enumeration leaves only one half-pair, again with `Q=54` and required `R<=3`.

Direct final expansion gives

```text
Q survivors                         1
mapped compressed candidates        2
fibre orientations                  8
affine transforms               4,000
V-budget passes                     0
odd-perfect passes                160
E <= 570                            0
minimum V^2                        30
minimum odd energy                 50
minimum full energy              1314
```

The `(13,8)` and `(9,12)` final clean verifier is run `41186505561`.  Its uploaded transcript contains no `CANDIDATE` line.

The affine support quotient itself was independently regression-tested against the previously frozen `(15,6)` unique Q-survivor and `(21,0)` zero-survivor cases in run `41185747958`; it preserves both exact outcomes.

## Consequence

All seven `K=21` norm splits are empty for odd-perfect `(a,b)=(18,0)` sequences with `E<=570`.

Together with the complete `K=19` exclusion, any surviving odd-perfect breakthrough in the `(18,0)` half-sum class must therefore lie at

```text
K >= 23.
```

The appropriate next layer is `K=23`, where

```text
m = -2,
sum U = 29,
W = 4 + 2(Q+R),
E<=570  iff  Q+R<=63.
```

The `qmin(G)` compression bound and exact fibre identity `2Q=SG+SH` carry over unchanged; the search should therefore continue in that representation rather than returning to generic CP-SAT or unrestricted LABS search.
