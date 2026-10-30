# Low11 symmetric-difference `t=4`: exact exclusion

Date: 2026-10-30

## Scope

This note closes the complete support-overlap layer `t=4` in the remaining odd-perfect `(20,0)` low11 order-25 projection.  As in the preceding symmetric-difference records, let `P,C` be the supports of ternary `p,c`, let

```text
kp=|P|, kc=|C|, kp+kc=26,
t=|P intersect C|,
D=P xor C.
```

For `t=4`, `|D|=18`; replacing `D` by its complement preserves the GF(2) support equation because `kp` is even, so the reduced difference support has weight 7.  There are exactly 974 affine orbits of seven-subsets of `Z_25`.

## Exact search

Implementation:

```text
code/oddperfect_low11_symdiff_rank_exact.cpp
```

For every reduced difference-support orbit and each norm split `(kp,kc)=(12,14),(14,12)`, the computation:

1. solves the exact GF(2) support equation `P D* + D P* = 0`;
2. keeps only support pairs with the requested weights and quotients them by the stabilizer of the fixed difference support;
3. enumerates every signed `p` with `sum p=10`;
4. uses a safe mod-3 full-rank test on the 14 integer equations for the `c` signs;
5. solves every surviving signed-`c` system exactly by meet-in-the-middle;
6. checks all original integer cyclic cross equations and then the complete low11 PAF target.

No SAT/CP solver or timeout appears inside the mathematical enumeration.

The hosted run partitioned all 974 affine difference-support orbits into 20 contiguous ranges per `kp` value and explicitly checked that the ranges form a disjoint cover of `[0,974)`.

Workflow evidence:

```text
run 41049581471
job 124042020765
artifact labs100-low11-symdiff-t4-rank
```

The job completed successfully.

## Exact aggregate counts

```text
kp=12, kc=14
support-pair orbits =    858,350
p-sign tests        = 10,300,200
mod-3 rank pass     = 10,300,200
integer H matches  =    215,416
compressed hits    =          0

kp=14, kc=12
support-pair orbits =    858,350
p-sign tests        = 78,109,850
mod-3 rank pass     = 15,194,911
integer H matches  =  2,193,852
compressed hits    =          0
```

The `kp=12` rank-pass count equalling the full `p` count is expected: the 14 equations have a universal integer row relation

```text
H_0 + 2 sum_{r=1}^{12} H_r = 20 sum_i c_i,
```

so the corresponding 14x14 matrix cannot have full rank.  This observation motivated the later projective modular-kernel solver, but it is not needed for correctness of this completed enumeration.

## Consequence

There is no low11 order-25 compressed target with support overlap `t=4` for either remaining norm split.  Therefore no W129-A, W131-A2 or W131-B1 full sequence can arise from this overlap layer.

Combined with the previously exact `t=2`, `t=10`, and `t=12` exclusions, the low11 branch is now reduced to only

```text
t = 6 or 8.
```

The next search uses the stronger projective modular-kernel representation, which can determine or reject most signed-`c` systems before any meet-in-the-middle work.
