# Low11 exact method: symmetric-difference supports and modular nullspace fibres

Date: 2026-10-30

## Scope

This note records the representation change that made the remaining odd-perfect `(20,0)` low11 order-25 branches tractable. It is a method note rather than a new global LABS bound by itself.

The compressed variables are ternary length-25 sequences

```text
p,c in {-1,0,1}^25,
sum p = 10,
sum c = 0,
||p||^2 + ||c||^2 = 26,
```

with the exact cyclic cross equation

```text
p c* + c p* = 0 in Z[x]/(x^25-1).                    (1)
```

For the remaining norm splits

```text
(kp,kc)=(12,14) or (14,12),
kp=||p||^2, kc=||c||^2.
```

The target periodic autocorrelation condition is

```text
G_r = PAF_p(r)+PAF_c(r) in {2,3,4},  r=1,...,12,
sum_r G_r = 37.
```

## 1. Lag zero fixes the support-overlap parity

Let

```text
P=supp(p), C=supp(c), t=|P intersect C|.
```

The lag-zero coefficient of (1) is

```text
2 sum_i p_i c_i = 0.
```

Every nonzero overlap term is `+1` or `-1`, so the overlap contains equally many same-sign and opposite-sign positions. Hence

```text
t is even.
```

Because `|P|+|C|=26` on 25 coordinates, `t>=1`, leaving exactly

```text
t in {2,4,6,8,10,12}.
```

## 2. Symmetric-difference support linearization

Reduce (1) modulo 2. Signs disappear and only support masks remain:

```text
P C* + C P* = 0.                                      (2)
```

Put

```text
D = P xor C.
```

Since `C=P+D` over GF(2), the quadratic terms cancel:

```text
P D* + D P* = 0.                                      (3)
```

For fixed `D`, equation (3) is a homogeneous linear system in the 25 bits of `P`.

Its weight is

```text
|D| = |P|+|C|-2t = 26-2t.
```

If `|D|>12`, replace `D` by its complement `E=D+J`, where

```text
J=1+x+...+x^24.
```

Because `|P|=kp` is even,

```text
P J* + J P* = 0,
```

so (3) is unchanged. The six overlap layers therefore reduce to difference-support weights

```text
t                  2  4  6  8 10 12
reduced |D|        3  7 11 10  6  2
```

This changes the support search from two coupled 25-bit masks into:

1. an affine orbit of one small difference support;
2. a GF(2) kernel for `P`;
3. exact weight checks for `P` and `C=P+D`;
4. quotienting by the stabilizer of the fixed difference support.

The resulting exact support-pair orbit counts are

```text
t=2       4,374
t=4     858,350
t=6   7,153,384
t=8   5,145,510
t=10    285,602
t=12        788
```

for each of the two norm splits.

## 3. Signed `c` is a small homogeneous integer system

After fixing a signed `p` and the support positions of `c`, all remaining cross constraints are linear in the signs of `c`.

Use the 13 independent cyclic equations

```text
H_r=0, r=0,...,12,
```

plus

```text
sum c=0.
```

This is a homogeneous integer system

```text
M c = 0,
```

with `M` of size `14 x kc`, where `kc` is 12 or 14.

There is a universal exact row relation

```text
H_0 + 2 sum_{r=1}^{12} H_r = 20 sum_i c_i.           (4)
```

Consequently the rational rank is at most 13. In particular, the `kc=14` case cannot be eliminated by a naive full-column-rank test.

## 4. Exact modular-nullspace enumeration

Choose an odd prime, currently `q=3`, and row-reduce `M` over `F_q`.

Any genuine integer solution has

```text
c_j in {-1,+1},
```

so modulo 3 every coordinate is in

```text
{1,2}.
```

Suppose the modular nullspace dimension is `d`. RREF gives `d` free coordinates and uniquely determines every pivot coordinate from them.

Therefore all possible integer `±1` solutions can be enumerated exactly as follows:

1. enumerate the `2^d` assignments of the free coordinates to `{1,2}`;
2. derive the pivot coordinates using the RREF equations;
3. reject if any derived coordinate is `0 mod 3`;
4. convert `1 -> +1`, `2 -> -1`;
5. quotient the exact global `c -> -c` symmetry;
6. verify `sum c=0` and every original integer `H_r=0` equation.

This procedure is complete: every integer `±1` solution reduces to one enumerated modular nullspace assignment, and every retained assignment is rechecked in the original integer system.

It therefore replaces the generic signed meet-in-the-middle search rather than merely pruning it.

Implementation:

```text
code/oddperfect_low11_symdiff_mod3_enum_exact.cpp
```

The code was regression-tested against previously audited exact counts on the closed `t=2`, `t=4`, and `t=12` layers before being used for the full `t=6` campaign.

## 5. Projective one-dimensional shortcut

A complementary solver uses several odd primes `3,5,7,11`.

If `rank_q(M)=kc`, there is no nonzero modular solution and hence no `±1` integer solution.

If `rank_q(M)=kc-1`, the modular nullspace is one-dimensional. After normalizing one free coordinate, every coordinate of the unique projective null vector must be `+1` or `-1 mod q`; otherwise no integer `±1` solution exists. If it is, the full sign vector is fixed up to global negation and can be checked directly in the integer equations.

Only modular nullity at least two needs a general fallback.

Implementation:

```text
code/oddperfect_low11_symdiff_modular_exact.cpp
```

This projective route was especially effective for the `kc=12` branch and was used in the running full `t=8` campaign.

## 6. An exceptional `t=8` support orbit

The GF(2) support kernels normally have dimension 13 or 15. In the `t=8` layer there is exactly one reduced-difference orbit with dimension 23:

```text
D = {0,1,5,6,10,11,15,16,20,21}
  = {0,1} + 5 Z_5.
```

Equation (3) degenerates to two residue-parity conditions for this orbit. Treating it separately and quotienting its large affine stabilizer leaves only 13,454 support-pair orbits for either norm split.

A complete signed search of this exceptional orbit found zero low11 compressed targets for both `kp=12` and `kp=14`. Thus it is not an unresolved long-tail case.

## 7. Current exact overlap status

At the time of this note:

```text
t=2    exact exclusion
t=4    exact exclusion
t=6    full exact campaign running
t=8    full exact campaign running
t=10   exact compressed exhaustion; two survivors, both fibre-incompatible
t=12   exact exclusion
```

The remaining campaigns use one hosted job each and exploit all available runner CPUs internally; they do not rely on a large GitHub Actions matrix.

## 8. Why this representation matters

The earlier generic CP-SAT models remained `UNKNOWN` after adding order-10 quotient tables and longer search time. The useful progress came from changing the representation:

- support coupling became a GF(2) linear equation after moving to the symmetric difference;
- sign solving became a low-dimensional modular nullspace enumeration;
- rare compressed survivors can be tested independently against the exact binary order-25 fibre defect by `code/oddperfect_order25_fibre_mitm.cpp`.

The computational exclusions are therefore tied to explicit finite covers and exact arithmetic, not solver timeout behaviour.
