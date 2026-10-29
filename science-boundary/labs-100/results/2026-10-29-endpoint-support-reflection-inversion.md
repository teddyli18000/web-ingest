# 2026-10-29 endpoint-defect support determines the reflection pattern

## Statement

For a length-99 endpoint deletion of an odd-perfect N=100 sequence, every odd autocorrelation is `0` or `+/-2`. The **support** of those nonzero odd correlations uniquely determines which mirror pairs violate length-99 skew symmetry.

This generalizes the defect-1 reduction. In particular, endpoint defect `d` lies in a reflection layer with at most `2d` violated mirror pairs. Low endpoint-defect layers are therefore finite low-complexity deformations of the skew manifold rather than generic 99-bit spaces.

## Setup

Let `R=(r_0,...,r_98)` and `m=49`. Define reflection signs

```text
rho_j = (-1)^(m-j) r_j r_(98-j),
z_j   = (1-rho_j)/2 in {0,1}.
```

Then

```text
z_j = z_(98-j),
z_49 = 0.
```

The sequence is skew-symmetric exactly when every `z_j=0`.

For `q=1,...,49`, put `k=99-2q`. Pair the `2q` products in `C_k(R)` by `i <-> 2q-1-i`. The paired contribution is zero if the two reflection signs agree and `+/-2` if they disagree. Therefore

```text
C_(99-2q)(R)/2 == sum_(j=0)^(2q-1) z_j  (mod 2).
```

For an endpoint deletion of an odd-perfect N=100 sequence, `C_k(R)` is either zero or `+/-2`, so the left side is exactly the indicator that lag `k` is a defect, modulo two.

Define

```text
p_q = 1  iff C_(99-2q)(R) is nonzero,
      0  otherwise.
```

Then the known support gives the 49 linear equations

```text
p_q = z_0 + ... + z_(2q-1)  (mod 2).
```

## Why the inversion is unique

It is enough to show that the homogeneous system has only `z=0`.

If every `p_q=0`, subtract consecutive prefix equations. This gives

```text
z_(2q-2) = z_(2q-1),   q=1,...,49.
```

The middle pair is `(48,49)`, so `z_48=z_49=0`. Reflection gives `z_50=z_48=0`; the next adjacent-pair equation gives `z_51=0`; reflection then gives `z_47=0`. Continuing outward forces every reflection bit to zero.

Thus the linear map from the symmetric reflection vector `z` to the odd-defect support vector `p` is invertible over GF(2). Every support set has exactly one reflection pattern.

## Useful constructive form

Because the map is linear over GF(2), the reflection pattern for an arbitrary defect support is the XOR of the patterns for its individual defect lags.

For one defect at odd lag `h`, the nonzero left-half reflection bits are

```text
h < 49:  {h-1, h}
h = 49:  {48}
h > 49:  {98-h, 99-h}.
```

Therefore a support of size `d` has reflection Hamming weight at most `2d` in the left half; cancellations can make it smaller.

Equivalently, after flipping one sign in each violated mirror pair, the length-99 deletion becomes exactly skew-symmetric using at most `2d` sign changes.

## Defect-sign constraints from half sums

Under the standard odd-perfect normalization `b=0`, the right deletion `R=s[0..98]` has parity-half sums

```text
A_R = a,
B_R = -s_99.
```

Hence

```text
sum_(k odd) C_k(R) = -a s_99.
```

If its defect support has size `d` and we write each nonzero correlation as `C_k(R)=2 t_k`, `t_k in {+1,-1}`, then

```text
sum t_k = -(a/2) s_99.
```

This immediately recovers the exact necessary conditions

```text
d >= a/2,
d == a/2 (mod 2).
```

It also fixes the defect-sign multiplicities. Examples:

- `d_R=1` forces `a=2` and the unique `t=-s_99`;
- `d_R=2, a=0` forces one `+1` and one `-1`;
- `d_R=2, a=4` forces both `t=-s_99`.

For every defect lag, full N=100 odd-perfectness additionally fixes the corresponding endpoint product because

```text
C_k(s) = 2 t_k + s_(99-k) s_99 = +/-1,
```

so necessarily

```text
s_(99-k) s_99 = -t_k.
```

## Computational consequence

The exact search can be organized by:

1. a small defect-support set;
2. its uniquely determined reflection pattern;
3. the small set of defect-sign assignments allowed by the half sums;
4. roughly 50 free reflection coordinates rather than 100 unrestricted signs.

The defect-1 solver `code/oddperfect_defect1_reflect_bnb.cpp` is the first implementation of this representation. The same inversion supplies the natural next representation for defect 2 and higher sparse endpoint-defect layers.
