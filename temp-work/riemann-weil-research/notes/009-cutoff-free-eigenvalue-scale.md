# 009 — Cutoff-free finite-matrix eigenvalue scale

## Scope

This note records the first rigorous two-sided numerical brackets obtained in this workspace for the smallest eigenvalue of the **cutoff-free finite CvS/Groskin Galerkin matrix** at `c=100`.

This is **not** a proof of full compact-window Weil positivity: each `N` is only a finite-dimensional restriction, so its minimum is an upper bound for the true infinite-dimensional window minimum. The result is nevertheless useful because it removes the finite-`T` archimedean quadrature error entirely.

Public upstream verifier pinned at:

```text
akivag613/connes-cvs-
commit 5a66d0cd177ef8b8ad1c2c93165b8d56ca40292c
```

Method:

```text
build exact Arb cutoff-free interval matrix A_N
choose a search scale from the midpoint matrix only
certify A_N - lo I positive definite by interval LDL^T
certify A_N - hi I has exactly one negative direction by interval LDL^T
therefore lo < lambda_min(A_N) < hi
```

The midpoint eigensolve is not part of the certificate.

## Rigorous results at c = 100

The cutoff corresponds to compact-window half-width

```text
L_win = log(100)/2 ≈ 2.302585092994046.
```

Representative rigorous brackets:

| N | dimension | rigorous lambda_min scale |
|---:|---:|---:|
| 8 | 17 | `4.3443206784016509913e-32` |
| 12 | 25 | `2.2001845022108129895e-43` |
| 16 | 33 | `4.8600690151341071044e-53` |
| 24 | 49 | `3.5758283578644386378e-71` |
| 32 | 65 | `1.5843315816797568761e-87` |
| 48 | 97 | `2.0459132626766556916e-116` |

For every row, both endpoints are interval-certified. The adaptive brackets in the saved JSON have relative width about `1.24077e-24`.

Full machine-readable result:

```text
temp-work/riemann-weil-research/results/cutoff-free-lambda-brackets-c100.json
```

## Finite-T ladder was numerically misleading

The earlier finite archimedean-cutoff experiment at `c=100, N=16` produced

```text
T=120: lambda_T ≈ -6.77e-20
T=240: lambda_T ≈ -4.03e-47
T=480: lambda_T ≈ -1.25e-2
```

while the rigorous tail-order theorem gives

```text
0 <= Q_infty - Q_T <= B_T I
```

past the threshold. Therefore `Q_T` must increase in Loewner order with `T`, so its smallest eigenvalue must be nondecreasing. The observed `T=480` drop is incompatible with an accurate evaluation of the finite-`T` matrix and exposes quadrature failure.

The cutoff-free Arb result resolves the sign correctly at `N=16`:

```text
lambda_min(A_16) ≈ 4.8600690151341071e-53 > 0
```

rigorously.

Conclusion: do **not** infer Weil signs at deep spectral scales by merely increasing the archimedean quadrature cutoff.

## What the scale means

The finite minimum falls extremely rapidly toward zero as the Galerkin band grows. From the rows above, increasing `N` by a modest amount can lose tens of decimal orders in the positive margin.

This is consistent with the known spectral-plunge phenomenon and explains why generic compactness arguments are computationally useless: resolving the sign by a naive approximation requires precision that grows rapidly with the band.

But the small positive values themselves do **not** distinguish between two very different infinite-dimensional possibilities:

1. **Bombieri zero-mode / collapse channel** — the ground vectors converge to a structured limiting relation while the eigenvalue tends to zero.
2. **High-frequency escape** — the minimizing vectors keep using newly available modes and fail to converge strongly in the source space.

This distinction is now the next experiment.

## Immediate next diagnostic

Build the **cutoff-free** Arb matrices for the same nested sequence of bands, then use high-precision midpoints only for eigenvector diagnostics. For each ground vector record:

- logarithmic source energy `sum |u_k|^2 log(e+|k|)`;
- outer-frequency mass;
- endpoint-strip mass of the reconstructed trigonometric source;
- overlap with the padded previous-band ground vector;
- `L2` distance after sign alignment.

The eigenvector diagnostics are exploratory rather than interval-certified, while the associated finite-matrix eigenvalue signs remain independently certified by this note's Arb brackets.

A pattern

```text
overlap -> 1
log-energy bounded
outer-frequency mass -> 0
```

would support a genuine Bombieri-style zero-mode candidate worth analyzing through the exact variational equation.

A pattern

```text
overlap fails to stabilize
log-energy grows
outer-frequency mass stays substantial
```

would instead support escape to unresolved frequencies.
