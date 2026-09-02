# 011 — Schur pivots, Loewner matrices, and a Pick-function target

## 1. Scalarizing finite positivity

Let `E_N` be the cutoff-free CvS Weil matrix restricted to the even trigonometric sector with ordered orthonormal basis

```text
1, sqrt(2) cos(2 pi t), ..., sqrt(2) cos(2 pi N t).
```

Because increasing the band by one adds exactly one basis vector,

```text
E_N = [[E_{N-1}, b_N],
       [b_N^T,     c_N]].
```

If `E_{N-1}` is positive definite, the block criterion gives

```text
E_N > 0
iff
s_N := c_N - b_N^T E_{N-1}^{-1} b_N > 0.
```

The scalar `s_N` is exactly the last diagonal pivot in an unpivoted `LDL^T` factorization in this nested basis.

Therefore

> positivity of every finite even-sector truncation is equivalent to positivity of a scalar Schur-pivot sequence `s_0,s_1,...`.

The odd sector has the analogous sequence and must ultimately be treated separately.

This does not by itself prove positivity of the completed infinite-dimensional form, but it is a much sharper finite problem than controlling `lambda_min(E_N)`, whose scale is already below `1e-100` at modest N.

## 2. Why this matches the observed cancellation

The ground-vector experiment shows that adding modes with essentially zero norm can change the optimized old coefficients and drive the minimum down by many orders.

The Schur formula explains precisely how:

```text
new mode self-energy       = c_N
feedback through old block = b_N^T E_{N-1}^{-1} b_N
remaining positive margin  = s_N
```

When `E_{N-1}` is extremely ill-conditioned, a very small coupling vector `b_N` can have a large effect through `E_{N-1}^{-1}` even when the final coefficient in the new mode is tiny.

Thus the correct object is not new-mode mass but the near-cancellation

```text
c_N ≈ b_N^T E_{N-1}^{-1} b_N.
```

## 3. Loewner structure

The CvS matrix is built from a divided-difference source function `psi`:

```text
Q[m,n] = (psi(m)-psi(n))/(m-n),  m != n,
Q[n,n] = psi'(n).
```

This is a confluent Loewner matrix.

For a Pick/Herglotz function with representation

```text
psi(z) = a + b z + integral (1/(t-z) - t/(1+t^2)) dmu(t),
```

with `b >= 0` and `dmu >= 0`, one has on real nodes away from the support

```text
(psi(x)-psi(y))/(x-y)
  = b + integral dmu(t)/((t-x)(t-y)),
```

so every finite Loewner matrix is a Gram matrix and hence positive semidefinite.

This suggests a crisp target:

> can the fixed-window CvS source data `{psi(n), psi'(n)}` be realized by a Pick/Herglotz interpolant on the integer nodes?

If yes, all finite confluent Loewner matrices would be positive automatically.

Important caution: this is currently a **candidate reformulation**, not an established equivalence for our infinite boundary-node interpolation problem. The precise infinite/confluent Nevanlinna–Pick theorem and its boundary hypotheses must be checked before claiming equivalence.

## 4. Relation to prime-cutoff dynamics

Groskin's corrected 2026 matrix-valued von Mangoldt work studies the finite path with `u = log c` and proves that at a prime-power threshold `u=log q` the first derivative has the rank-one jump

```text
-2 Lambda(q)/(sqrt(q) log(q)) * 11^T.
```

The same work develops Sherman–Morrison / Weyl-function formulas for the rank-one path but explicitly does **not** prove the missing Stieltjes/positivity structure needed for a genuine Krein-string interpretation.

That missing positivity is suspiciously close to the present target:

```text
Loewner positivity <-> positive Schur pivots <-> positive Weyl/Schur data.
```

So there are now two compatible axes:

1. **band axis N:** prove every new-mode Schur pivot `s_N(c)` is positive;
2. **prime-cutoff axis c:** understand how each `s_N(c)` changes between and across prime-power thresholds through rank-one updates.

## 5. Immediate experiment

Build one rigorous cutoff-free Arb matrix at a moderately large `N_max`, transform it to the even orthonormal basis, and perform interval `LDL^T` in nested order.

One factorization returns all scalar pivots

```text
s_0, s_1, ..., s_Nmax
```

simultaneously.

Record for each N:

- rigorous pivot interval;
- `log10(s_N)`;
- ratio to the corresponding diagonal `c_N`;
- where possible, ratio to the rigorously known `lambda_min(E_N)`;
- empirical first/second differences of `log s_N`.

Questions:

1. Is `s_N` vastly better scaled than `lambda_min(E_N)`?
2. Does `s_N/c_N` follow a regular asymptotic law?
3. Does the pivot sequence expose a Stieltjes / continued-fraction pattern?
4. Can positivity of `s_N` be reduced to an integral or arithmetic inequality with a fixed sign?

## Research priority

This is now the main analytic target. A proof of RH is still far away; the actionable subproblem is:

```text
understand and prove the sign of the nested Schur pivots of the Weil Loewner matrix.
```
