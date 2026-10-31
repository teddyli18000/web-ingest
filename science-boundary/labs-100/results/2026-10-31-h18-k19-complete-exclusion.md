# Odd-perfect `(18,0)`, `K=19`: complete exact exclusion

Date: 2026-10-31

## Claim

There is no odd-perfect length-100 binary sequence in the normalized half-sum class

```text
(sum A, sum B) = (18,0)
```

with order-25 compression norm

```text
K = ||p||^2 + ||c||^2 = 19
```

and LABS energy at most the breakthrough threshold.  In this product class the congruence sharpens the nominal `E<=574` threshold to

```text
E <= 570.
```

Equivalently, the complete `(18,0),K=19,W<=130` branch is empty.

This is an exact finite exclusion, not a heuristic search result.

## Arithmetic reduction

Write

```text
d_r = C_(2r)/2,
W = sum_{r=1}^{49} d_r^2,
m = d_25,
U_r = (d_r+d_(50-r))/2,
V_r = (d_r-d_(50-r))/2.
```

For `(18,0)`,

```text
sum d_r = 56,
E = 50 + 4W.
```

At `K=19`, `m=K-25=-6`, hence

```text
sum U_r = 31,
W = 36 + 2 sum(U_r^2+V_r^2).
```

The exact `W<=130` possibilities are therefore the sparse near-NGP cases recorded in
[`2026-10-30-h18-k19-sparse-near-ngp.md`](2026-10-30-h18-k19-sparse-near-ngp.md): the order-25 common PAF has one of twelve possible sorted spectra and the antisymmetric fibre has squared norm at most two.

Because

```text
sum p = 9,
sum c = 0,
||p||^2 + ||c||^2 = 19,
```

the only compression norm splits are

```text
(kp,kc) = (19,0),(17,2),(15,4),(13,6),(11,8),(9,10).
```

All six are now excluded.

## Exact compressed representation

For ternary length-25 compressed sequences `p,c`, the periodic odd-perfect projection is

```text
p c* + c p* = 0  in Z[x]/(x^25-1).
```

At support level, with `P=supp(p)`, `C=supp(c)`, `D=P xor C`, reduction modulo two gives

```text
P D* + D P* = 0.
```

The low-support branches are enumerated by affine orbits of `D`, the exact GF(2) kernel for `P`, and stabilizer quotienting.  Signed `c` is then solved from the complete periodic cross system plus `sum c=0`; modular rank is used only as a necessary-condition accelerator, and every survivor is rechecked in the original integer equations.

For `kp=17,kc=2`, the two nonzero `c` entries reduce up to affine symmetry to separations `1` and `5`, giving a direct exact RREF enumeration instead.

## Exact fibre representation

Write the two length-50 parity halves as

```text
A = (1+x^25)p + (1-x^25)alpha,
B = (1+x^25)q + (1-x^25)beta,
c = x^13 q.
```

The cyclic odd-cross equation splits exactly into periodic and negacyclic order-25 channels.  With

```text
gamma = x^13 beta  in Z[x]/(x^25+1),
```

the remaining fibre equation is

```text
alpha gamma* - gamma alpha* = 0  mod x^25+1.
```

For each compressed survivor, all binary `alpha` fibres are enumerated and every compatible binary `gamma` is found by exact meet-in-the-middle.  A full-length affine symmetry then covers all 500 compressed affine images without re-solving the fibre equation.

### Important sign audit

For `c=0`, the global symmetry `B -> -B` permits quotienting `gamma -> -gamma`.

For `kc>0`, once a compressed representative has fixed the sign of `c`, that quotient is **not** valid: the global flip sends `(c,gamma)` to `(-c,-gamma)`, not `(c,-gamma)`.  An initial `kp=15` prototype reused the `c=0` quotient and was retired.  The corrected verifier explicitly scores both gamma orientations.  The retired source is intentionally compile-disabled so it cannot be reused as a certificate.

## Branch results

### `kp=19,kc=0`

Two independent exact implementations exclude this branch.

The universal `q=0` fibre-table route processed 47,500 unique affine signed images and found no defect-0/1/2 lift.  Clean GitHub Actions reproduction:

```text
run 41097018181
artifact labs100-h18-k19-kp19-exact
```

An independent negacyclic affine-lift implementation enumerated

```text
95 compressed representatives
6,080 alpha choices
69,314 half-B cyclic lifts
34,657,000 affine transforms
0 target-V passes
```

Clean run:

```text
run 41097642110
```

Durable record: [`2026-10-30-h18-k19-kp19-exclusion.md`](2026-10-30-h18-k19-kp19-exclusion.md).

### `kp=17,kc=2`

The compressed layer already vanishes.  The exact RREF search tests

```text
3^13 + 3^15 = 15,943,230
```

free ternary assignments, finds 20,400 exact sum/norm/periodic-cross solutions, and zero K19 spectral targets.

```text
run 41098098183
```

Implementation: `code/oddperfect_h18_k19_kp17_exact.cpp`.

### `kp=15,kc=4`

The corrected exact compressed search has 88 signed `c` affine orbits and returns exactly one spectral survivor:

```text
K19_KP15_COMPRESSED
orbits=88
rank11=8
rank13=80
tested=80,779,032
exactvalid=92,501
spectral=1
base=0
alt=1
```

Because it is an alternative `W=130` spectrum, it requires `V=0`.  The corrected full-gamma audit gives

```text
alphas=1,024
half_gamma_solutions=32,780
full_gamma_solutions=65,560
affine_transforms=32,780,000
V0_pass=0
```

Clean reproduction and raw artifact:

```text
run 41182406285
artifact labs100-h18-k19-kp15-exact-corrected
```

The artifact was downloaded and the two summary lines above were checked directly.

Implementations:

```text
code/oddperfect_h18_k19_kp15_compressed.cpp
code/oddperfect_h18_k19_kp15_fullgamma.cpp
```

### `kp=13,kc=6`

All overlap layers `t=0,2,4,6` leave only 13 compressed spectral representatives in total, exactly one of which has the lower-square base spectrum.  The full-gamma audit gives

```text
reps=13
alphas=53,248
half_gamma_solutions=440,968
full_gamma_solutions=881,936
affine_transforms=440,968,000
Vbudget_pass=0
```

### `kp=11,kc=8`

The five overlap layers leave 14 compressed spectral representatives.  Full fibre audit:

```text
reps=14
alphas=229,376
half_gamma_solutions=164,692
full_gamma_solutions=329,384
affine_transforms=164,692,000
Vbudget_pass=0
```

### `kp=9,kc=10`

Here `sum p=9` forces all nine nonzero `p` entries to be `+1`, so there is no `p`-sign search.  The five overlap layers leave 16 compressed spectral representatives.  Full fibre audit:

```text
reps=16
alphas=1,048,576
half_gamma_solutions=428,062
full_gamma_solutions=856,124
affine_transforms=428,062,000
Vbudget_pass=0
```

The last three branches were reproduced together on one four-core hosted runner.  Every expected compressed count was asserted in the workflow, every HIT stream was frozen, and every full-gamma count was asserted:

```text
run 41182753353
artifact labs100-h18-k19-remaining-exact
```

The downloaded artifact independently contains

```text
kp13: Vbudget_pass=0, oddperfect_pass=0, E_le_570=0
kp11: Vbudget_pass=0, oddperfect_pass=0, E_le_570=0
kp9:  Vbudget_pass=0, oddperfect_pass=0, E_le_570=0
```

Implementations:

```text
code/oddperfect_h18_k19_remaining_compressed.cpp
code/oddperfect_h18_k19_fullgamma.cpp
```

## Consequence

Every feasible order-25 norm split at `K=19` has now been exhausted.  Therefore

```text
odd-perfect (18,0), K=19, E<=570: impossible.
```

This is a structural exclusion only.  It does not exclude the remaining `(18,0)` center values `K=21,23,...` and does not exclude odd-energy layers above the odd-perfect minimum.

## Next representation: `K=21`

At `K=21`, `m=-4`, so

```text
sum U = 30,
W = 16 + 2 sum(U^2+V^2),
sum(U^2+V^2) <= 57.
```

A simpler target representation avoids enumerating dozens of `U` multisets.  For each periodic pair sum

```text
G_j = U_j + U_(25-j),
```

the minimum possible square contribution of the two integers is

```text
min_{u+v=G_j}(u^2+v^2) = ceil(G_j^2/2).
```

Hence define

```text
q_min(G) = sum_{j=1}^{12} ceil(G_j^2/2).
```

Since `sum G_j=30` is automatic from `sum p=9`, `sum c=0`, and `K=21`, the complete arithmetic energy condition is simply

```text
q_min(G) <= 57,
sum V^2 <= 57 - q_min(G).
```

As a regression, applying the same formula at `K=19` with budget `47` reproduces exactly the twelve previously enumerated K19 spectral multisets and their fibre budgets.  This is the preferred representation for the next exact attack.

## Literature scope checked

Before extending the computation, current public work was rechecked.  The 2026 LABS paper by Pšeničnik et al., *Prioritizing Search Space Regions in the Low Autocorrelation Binary Sequences Problem* (arXiv:2607.09688), concerns heuristic partitioned/skew search and new records at long lengths `450..527` and `573`; it does not supply an N=100 exact classification.  Lumsden, Kotsireas and Bright, *New Results on Periodic Golay Pairs* (arXiv:2408.15611), gives exhaustive periodic-complementary methods through length 72 and is methodologically relevant to compression, but does not settle this length-50 near-negaperiodic fibre problem.

No novelty claim beyond the exact computation recorded here is inferred from that literature check.
