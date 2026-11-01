# Odd-perfect `(18,0)`, `K=23`: complete exact exclusion

Date: 2026-11-01

## Claim

There is no odd-perfect length-100 binary sequence in the normalized half-sum class

```text
(sum A, sum B) = (18,0)
```

with order-25 compression norm

```text
K = ||p||^2 + ||c||^2 = 23
```

and LABS energy at most the breakthrough threshold.  In this global-product class the congruence sharpens `E<=574` to

```text
E <= 570.
```

Thus the complete `(18,0), K=23` layer is empty through the target energy.

## Arithmetic reduction

For

```text
d_r = C_(2r)/2,
U_r = (d_r+d_(50-r))/2,
V_r = (d_r-d_(50-r))/2,
m=d_25=K-25,
```

we have at `K=23`

```text
m=-2,
sum U_r = 29,
W = sum d_r^2 = 4 + 2(Q+R),
Q=sum U_r^2,
R=sum V_r^2.
```

Since `E=50+4W`, the target is exactly

```text
Q+R <= 63.
```

For the order-25 compressed spectrum

```text
G_j = PAF_p(j)+PAF_c(j),
SG = sum G_j^2,
```

the exact arithmetic lower bound is

```text
qmin(G) = sum_j ceil(G_j^2/2) <= Q.
```

For binary fibres `alpha,gamma`, define

```text
H_j = NPAF_alpha(j)+NPAF_gamma(j),
SH = sum H_j^2.
```

The exact fibre identity is

```text
2Q = SG+SH,
```

so every target must satisfy

```text
SG+SH <= 126.
```

The possible compression norm splits are

```text
(kp,kc) =
(23,0),(21,2),(19,4),(17,6),
(15,8),(13,10),(11,12),(9,14).
```

All eight are exhausted below.

## Exact pipeline

The compressed stage enumerates the complete periodic odd-perfect equation

```text
p c* + c p* = 0  mod x^25-1
```

using support-orbit reduction, GF(2) support kernels or the signed-`c` exact solver, exact integer regression, and the necessary `qmin(G)<=63` filter.

The fibre stage quotients simultaneous `AGL(1,Z_25)` support symmetry and solves

```text
alpha gamma* - gamma alpha* = 0  mod x^25+1
```

exactly.  Any `SG+SH<=126` survivor is reconstructed to binary length-100 parity halves, expanded through every matching compressed affine image and all 500 induced full-length affine transforms, then rescored in the original LABS objective.

No CP/SAT timeout or heuristic result is used as an exclusion.

## High splits

Clean high-split reproduction:

```text
run 41316165820
artifact labs100-h18-k23-highsplits
```

The exact counts are

| `(kp,kc)` | compressed hits | affine-canonical fibre-support groups | Q-feasible half-fibres |
|---|---:|---:|---:|
| `(23,0)` | 2,930 | 2 | 0 |
| `(21,2)` | 1 | 1 | 0 |
| `(19,4)` | 323 | 270 | 0 |
| `(17,6)` | 9,281 | 6,169 | 64 |

For `(23,0)` there is also an independent support-class check.  The two zero positions of `p` have only the affine separation classes `d=1` and `d=5`.  Their exact compressed minima are

```text
min SG = 79, 91,
```

while independent negacyclic fibre enumeration gives

```text
min SH >= 111, 67,
```

respectively.  Hence

```text
SG+SH >= 190 or 158 > 126,
```

independently excluding that split.

### Final `(17,6)` audit

The 64 Q-level survivors were rebuilt and directly rescored in a separate clean run:

```text
run 41316397780
artifact labs100-h18-k23-kp17-witness
```

Exact final summary:

```text
QHITs                     64
mapped compressed         152
fibre orientations        608
affine transforms         304,000
V-budget passes           0
odd-perfect transforms    10,560
E<=570                    0
minimum V                 22
minimum odd energy        50
minimum full energy       1106
```

Thus all four high splits are empty.

## `(15,8)`

A dedicated exact campaign gives

```text
compressed hits                 34,248
affine-canonical support groups 24,519
Q-feasible half-fibres              204
mapped compressed candidates       416
fibre orientations                1,664
affine transforms               832,000
V-budget passes                       0
odd-perfect transforms           30,880
E<=570                                 0
minimum V                            16
minimum full energy                1098
```

Producer/final run:

```text
run 41187521385
artifact labs100-h18-k23-kp15-exact
```

The sharded final-witness implementation introduced below exactly reproduces this complete frozen summary before being used on the remaining lower splits.

## Lower splits `(13,10),(11,12),(9,14)`

The frozen compressed + fibre-Q producer run is

```text
run 41187536482
artifact labs100-h18-k23-lower-qgroup
```

Its exact counts are

| `(kp,kc)` | compressed hits | canonical fibre-support groups | Q-feasible half-fibres |
|---|---:|---:|---:|
| `(13,10)` | 128,420 | 74,998 | 976 |
| `(11,12)` | 41,594 | 35,436 | 234 |
| `(9,14)`  | 16,261 | 13,442 | 86 |

A naive final verifier would rescan every compressed candidate for every QHIT.  To remove that redundant Cartesian join without changing the mathematical search space, `code/oddperfect_h18_k_witness_shard.py` expands only the QHIT support orbits under the 500-element affine group, hashes raw compressed candidates into those orbits, and emits independent exact witness shards.

The sharder was first regression-checked on `(15,8)` and reproduced exactly

```text
QHITs=204,
mapped=416,
orientations=1664,
transforms=832000,
Vpass=0,
oddperfect=30880,
E<=570=0,
minV=16,
minOdd=50,
minE=1098.
```

Only then was it used on the lower three splits.  Clean final run:

```text
run 41316938369
artifact labs100-h18-k23-lower-sharded-witness
```

Exact summaries:

```text
kp=13:
  selected support groups   869
  QHITs                     976
  mapped candidates         2,233
  fibre orientations        8,932
  affine transforms         4,466,000
  V-budget passes           0
  odd-perfect transforms    171,688
  E<=570                    0
  min V / min odd / min E   17 / 50 / 1074

kp=11:
  selected support groups   211
  QHITs                     234
  mapped candidates         488
  fibre orientations        1,952
  affine transforms         976,000
  V-budget passes           0
  odd-perfect transforms    38,088
  E<=570                    0
  min V / min odd / min E   17 / 50 / 938

kp=9:
  selected support groups   83
  QHITs                     86
  mapped candidates         172
  fibre orientations        688
  affine transforms         344,000
  V-budget passes           0
  odd-perfect transforms    13,440
  E<=570                    0
  min V / min odd / min E   24 / 50 / 1114
```

No `CANDIDATE` line occurs in the complete final transcript.

## Consequence

Every feasible order-25 norm split at `K=23` is exactly exhausted.  Combining this result with the previous `K=19` and `K=21` closures gives

```text
odd-perfect (18,0), K in {19,21,23}, E<=570: impossible.
```

Therefore any surviving odd-perfect `(18,0)` breakthrough has

```text
K >= 25.
```

This does **not** exclude other half-sum classes or odd-energy layers above the odd-perfect minimum.

## Search-space reassessment

Three consecutive center layers have now been closed without producing a better candidate.  Continuing mechanically through `K=25,27,...` would grow only the excluded region unless the survivor geometry remains unusually sparse.

A separate first-principles direction is therefore warranted before scaling the same program: relax odd-perfectness by one odd-correlation defect (`O=58`) and express that defect in the same cyclic cross representation.  The paired odd correlations have a mod-4 structure that makes this next layer sparse rather than generic; that formulation should be derived and tested before committing major compute to further `K` layers.
