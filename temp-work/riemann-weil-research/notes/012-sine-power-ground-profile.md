# 012 — A sine-power model for the cutoff-free ground profile

## Status

This note records a new empirical/algebraic model for the **shape** of the cutoff-free `c=100` ground vectors. The vectors are high-precision midpoint diagnostics; their finite-matrix eigenvalue signs are certified separately by the Arb interval work in note 009.

This is not an RH claim and not yet a theorem about the continuum minimizer.

## 1. Empirical identification

For the real even Fourier source

```text
T_N(s) = sum_{k=-N}^N u_k exp(2 pi i k s),   0 <= s <= 1,
```

the cutoff-free ground coefficients alternate in sign and are almost exactly centered-binomial.

Compare against the normalized model

```text
S_m(s) = C_m sin(pi s)^(2m).
```

Its Fourier coefficients are exactly

```text
b_k = (-1)^k 4^(-m) binom(2m, m-k),   |k| <= m,
b_k = 0,                               |k| > m.
```

Searching integer `m` to maximize the padded coefficient overlap gives:

| N | m from `|u_1/u_0|` | best integer m | overlap with normalized `sin^(2m)` |
|---:|---:|---:|---:|
| 8  | 6.7208 | 7  | 0.999938 |
| 12 | 9.1061 | 9  | 0.999981 |
| 16 | 10.9996 | 11 | >0.9999998 |
| 24 | 13.7765 | 14 | 0.999965 |
| 32 | 15.6842 | 15 | 0.999936 |
| 48 | 18.0472 | 18 | 0.999951 |

The first-coefficient estimator is exact for the model because

```text
|b_1/b_0| = m/(m+1),
```

so

```text
m = r/(1-r),  r = |u_1/u_0|.
```

## 2. Independent spatial check

The coefficient match is not the only evidence.

For large `m`,

```text
integral_0^1 sin(pi s)^(4m) ds
  = binom(4m,2m) / 4^(2m)
  ~ 1/sqrt(2 pi m).
```

Hence the L2-normalized model has center height

```text
S_m(1/2) ~ (2 pi m)^(1/4).
```

Examples:

- `N=8`, best `m=7`: prediction about `2.58`; observed `T_N(1/2)=2.57`.
- `N=48`, best `m=18`: prediction about `3.26`; observed `T_N(1/2)=3.235`.

Thus the same model matches both Fourier coefficients and the real-space peak.

Near the center `s=1/2+x`,

```text
sin(pi s)^(2m) = cos(pi x)^(2m) ~ exp(-m pi^2 x^2),
```

so its spatial width is of order `m^(-1/2)` and its Fourier width is of order `m^(1/2)`.

This explains why, over the current low-N range, the source becomes more concentrated near `1/2` while the newly available outermost Fourier modes carry essentially no mass.

## 3. The apparent low-N drift

Over `N=8..48`, the coefficient-ratio estimate is fitted unusually well by

```text
m_N ~= 6.43 log N - 6.73
```

on these six points (this is only a local empirical fit).

If taken literally, that would imply extremely slow sharpening:

```text
spatial width ~ 1/sqrt(log N),
log-frequency energy ~ (1/2) log log N + O(1).
```

That mechanism would reconcile all three observations:

1. adjacent padded overlaps approach one;
2. outer-fraction frequency mass goes to zero;
3. the full sequence can still drift on a slowly increasing intermediate frequency scale.

However, **do not extrapolate this to N=infinity yet**.

The current Groskin c=100 sweep at `N=100,150,200,250` gives

```text
log10 lambda_N ~= -190.92, -247.19, -294.31, -333.68,
```

and two Aitken extrapolations of the finite-N sequence give roughly `-536.8` and `-533.7`, approaching the Connes 2026 section 6.4 heuristic continuum scale near `-530.4`. Therefore a finite, astronomically small positive continuum ground value is a serious competing interpretation.

The next experiment extends the **cutoff-free** midpoint profile to `N=64,80,96,128` to see whether the effective `m_N` continues its low-N logarithmic growth or starts to saturate.

## 4. Exact Cauchy-transform identity

The binomial model is algebraically useful, not merely visually convenient.

Let

```text
w_k = (-1)^k binom(2m,m-k),   -m <= k <= m.
```

For

```text
P_m(z) = product_{j=-m}^m (z-j),
```

partial fractions give the exact identity

```text
sum_{k=-m}^m w_k/(z-k)
  = (-1)^m (2m)! / P_m(z).
```

Reason: the residue of `1/P_m(z)` at `z=k` is

```text
1/P_m'(k) = (-1)^(m-k) / ((m+k)!(m-k)!),
```

which is the binomial weight up to the common factor and sign.

This is directly relevant to note 011. If a piece of the CvS source function admits a Herglotz/Pick representation, its Loewner quadratic form on these binomial vectors becomes a positive-measure integral of the explicit rational kernel

```text
|(2m)! / P_m(t)|^2.
```

That gives a concrete bridge

```text
sine-power profile
    -> centered finite-difference / binomial weights
    -> closed Cauchy transform
    -> Loewner / Schur-pivot analysis.
```

## 5. Important correction: do not revive the withdrawn Paley-Wiener argument

The current 2026 revision history of Groskin's `High-Precision Approximation of Riemann Zeros via the Truncated Weil Form` explicitly withdraws its former Section 8.2 Paley-Wiener mechanism after the paper's own preregistered test. The measured Sobolev exponent at `c=23` was essentially insensitive to the archimedean cutoff `T` (about `46.140, 46.031, 45.934` at `T=400,800,1600`), invalidating that proposed mechanism.

So the present sine-power observation must stand on its own. In particular:

- do not infer continuum convergence from Paley-Wiener zero-density heuristics alone;
- do not identify the empirical Galerkin regularity exponent with `2m` without a separate test;
- use the upcoming cutoff sweep only as a diagnostic comparison, not an identity claim.

## Immediate targets

1. Extend the cutoff-free profile to larger N and test saturation of `m_N`.
2. Sweep `c` at fixed N and compare the effective `m(c)` across prime cutoffs.
3. Compute the Weil Rayleigh quotient of the exact `sin^(2m)` family and compare it to the certified ground scale.
4. Exploit the explicit rational Cauchy transform inside the Schur/Loewner program.
