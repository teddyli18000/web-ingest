# Global polynomial factorization for the odd-perfect layer

Date: 2026-10-29

## Purpose

Endpoint-support searches have now excluded invariant endpoint defects `d=0,1,2,3,4,5` for an odd-perfect `E<=574` breakthrough. Continuing defect by defect is not a satisfactory global representation. This note rewrites the **entire** odd-perfect condition in parity-polynomial form and derives an exact energy identity that removes endpoint support from the objective.

## Parity polynomials

For a length-100 sign sequence split the even and odd positions into two length-50 Littlewood polynomials

```text
A(x) = sum_{i=0}^{49} s_{2i}   x^i,
B(x) = sum_{i=0}^{49} s_{2i+1} x^i.
```

For any degree-at-most-49 polynomial define its reversal

```text
A^R(x) = x^49 A(x^-1),
B^R(x) = x^49 B(x^-1).
```

Define the degree-at-most-99 cross polynomial

```text
G(x) = A(x) B^R(x) + x B(x) A^R(x).
```

A direct coefficient calculation gives

```text
[x^(50+r)] G = C_{2r+1},             r=0,...,49,
[x^r]      G = C_{99-2r},            r=0,...,49.
```

Thus the two halves of `G` are the odd autocorrelations in opposite orders.

## Odd-perfect factorization

For length 100, every odd autocorrelation is odd, and the universal opposite-lag congruence is

```text
C_k + C_{100-k} == 0 (mod 4).
```

If the sequence is odd-perfect, all odd correlations are `+/-1`, so the congruence sharpens to the exact relation

```text
C_{100-k} = -C_k       for odd k.
```

Let

```text
Q(x) = sum_{r=0}^{49} C_{2r+1} x^r.
```

Then every coefficient of `Q` is `+/-1`, and

```text
Q_r = -Q_{49-r}.
```

The coefficient description of `G` therefore becomes the exact factorization

```text
A B^R + x B A^R = (x^50 - 1) Q.          (1)
```

So the full odd-perfect layer is equivalently a factorization problem involving three Littlewood polynomials, with `Q` anti-palindromic and only 25 independent signs.

This is more global than endpoint support: no deletion defect or near-skew assumption appears in (1).

## Spectral phase consequence

At every 50th root of unity `z`, equation (1) gives

```text
A(z) conjugate(B(z)) + z B(z) conjugate(A(z)) = 0.
```

Whenever both factors are nonzero, the phase of `A(z)/B(z)` is therefore fixed modulo pi by `z`; only its real amplitude ratio remains free. This is a strong cross-spectral phase constraint imposed by odd-perfectness.

## Lagrange identity and the even-energy objective

Define

```text
D(x) = A(x)^2 - x B(x)^2.
```

On the unit circle, let

```text
P = |A|^2 + |B|^2,
H = A conjugate(B) + x B conjugate(A).
```

The elementary complex Lagrange identity gives pointwise

```text
P^2 = |D|^2 + |H|^2.                    (2)
```

On the unit circle, multiplication by `x^49` converts `H` to `G`, so `|H|=|G|`. Under odd-perfectness, (1) gives

```text
G = (x^50-1)Q.
```

Taking coefficient `l2` norms / Parseval in (2):

- `|A|^2+|B|^2` has constant coefficient 100 and off-zero coefficients `C_{2r}=C_A(r)+C_B(r)`, hence

```text
||P||_2^2 = 10000 + 2 V,
V = sum_{r=1}^{49} C_{2r}^2.
```

- `Q` has 50 coefficients of magnitude one, and the two copies in `(x^50-1)Q` have disjoint supports, hence

```text
||G||_2^2 = 100.
```

Therefore

```text
10000 + 2V = ||D||_2^2 + 100,
```

or equivalently

```text
boxed:  ||A^2 - x B^2||_2^2 = 9900 + 2V.          (3)
```

This identity was independently checked numerically on the public E578 incumbent, the E678 near-skew basin representative, and the reproducible E1162 outside-near-skew representative:

```text
sequence energy   V     ||A^2-xB^2||^2   9900+2V
578               528   10956              10956
678               628   11156              11156
1162              1112  12124              12124
```

## Target thresholds

On the odd-perfect layer, total energy is `E=50+V`. Hence a breakthrough satisfies

```text
E <= 574   <=>   V <= 524   <=>   ||D||_2^2 <= 10948.
```

For the global-product-minus class relevant to exact E570,

```text
E <= 570   <=>   V <= 520   <=>   ||D||_2^2 <= 10940.
```

The E578 incumbent has

```text
||D||_2^2 = 10956,
```

only 8 above the E574 threshold and 16 above the E570 threshold. Thus the remaining odd-perfect question can be stated as a very sharp norm gap for the factor pair `(D,Q)` satisfying (1).

## Universal coefficient lattice for D

There is another exact simplification independent of odd-perfectness. For any length-50 Littlewood polynomial `L`, the coefficient of `L(x)^2` is congruent modulo 4 to the number of ordered pairs contributing to that coefficient: off-diagonal terms occur in equal pairs and contribute `+/-2 == 2 (mod 4)`, while a diagonal term contributes `+1`.

Applying this to

```text
D(x)=A(x)^2-xB(x)^2 = sum_{n=0}^{99} d_n x^n
```

gives the universal lattice constraint

```text
d_n == +1 (mod 4),   0 <= n <= 49,
d_n == -1 (mod 4),  50 <= n <= 99.       (4)
```

In particular every coefficient of `D` is odd. The target is therefore not an arbitrary small-norm integer polynomial; it lies in the fixed 100-dimensional residue lattice (4) and must additionally factor as

```text
D(x^2) = S(x) S(-x),
S(x) = A(x^2) + x B(x^2),
```

where `S` is the original length-100 Littlewood polynomial.

## Relation to current literature

Recent LABS work continues to emphasize heuristic region prioritization and GPU search; it does not supply an exact N=100 classification. The 2025/2026 literature on base, normal and near-normal sequences uses the same Laurent-polynomial/norm language and exhaustive canonical-form methods, but its defining condition is a sum of autocorrelation norms, not the cross factorization (1). It is therefore methodologically relevant rather than a theorem that can simply be imported here.

Relevant public references reviewed while deriving this representation include:

- Xu Wang and Jiayi Zhu, *On Base, Normal and Near-normal Sequences*, arXiv:2506.20296.
- Blaž Pšeničnik et al., *Prioritizing Search Space Regions in the Low Autocorrelation Binary Sequences Problem*, arXiv:2607.09688.
- classical Littlewood/L4-merit-factor formulations in the LABS literature.

## Research direction

Equation (1) plus the norm threshold (3) is a better first-principles target than mechanically extending endpoint defect.

Useful next attacks include:

1. derive arithmetic/congruence restrictions on `D` and anti-palindromic `Q` jointly from (1);
2. exploit the prescribed cross-spectral phase of `A/B` at all 50th roots of unity;
3. search directly in the `D` coefficient lattice near norm 10948 and test Littlewood factorability of `D(x^2)=S(x)S(-x)`;
4. adapt canonical-form / quad-decomposition ideas from base-sequence enumeration to the cross factorization (1);
5. seek a proof that every factorization (1) has `||D||_2^2 >= 10956`, which would rule out the **entire odd-perfect layer** at once.

No such global lower bound is claimed yet.
