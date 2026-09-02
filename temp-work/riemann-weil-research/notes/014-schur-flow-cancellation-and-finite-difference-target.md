# Schur-flow cancellation and the finite-difference theorem target

Status: research note; no RH claim.

## Executive conclusion

For the cutoff-free even Connes--van Suijlekom matrix `E_N(u)` with `u=log c`, the last Schur pivot

\[
s_N(u)=\frac{\det E_N(u)}{\det E_{N-1}(u)}
\]

has a threshold-free logarithmic derivative

\[
g_N(u)=\frac{d}{du}\log s_N(u).
\]

At `c=100`, direct high-precision finite differences give a moderate scalar flow even though the full matrix relative derivative is catastrophically ill-conditioned:

| N | `g_N(100)` | matrix-wide generalized derivative scale |
|---:|---:|---:|
| 16 | `-101.61406926766...` | about `9.9e21` |
| 24 | `-93.76271392723...` | about `9.7e31` |
| 32 | `+80.68193793951...` | about `3.7e40` |
| 48 | `+67.40204265133...` | not needed for this comparison |

Thus the Schur recursion is a dramatically better dynamical variable than the full matrix condition number or minimum eigenvalue.

The surprising part is *why* `g_N` is moderate.  Writing the pinned cutoff-free matrix formula as

\[
E_N=W_{02}-W_R-W_p,
\]

the three contributions to the Schur-normal directional derivative are individually enormous and cancel to dozens of decimal orders.

## Schur-normal derivative identity

Write

\[
E_N=\begin{pmatrix}B&b\\b^T&c\end{pmatrix},\qquad
x=B^{-1}b,\qquad
w_N=\binom{-x}{1}.
\]

Then

\[
s_N=c-b^TB^{-1}b=w_N^T E_N w_N
\]

and for a differentiable threshold-free path,

\[
s_N'=w_N^T E_N'w_N,
\qquad
g_N=\frac{w_N^T E_N'w_N}{s_N}.
\]

Equivalently,

\[
g_N=\operatorname{tr}(E_N^{-1}E_N')-
\operatorname{tr}(E_{N-1}^{-1}E_{N-1}').
\]

The second formula explains how two huge trace responses can have a moderate discrete difference, but it does not by itself provide a bound.

## Deep component decomposition at `c=100`

The base pivots are rigorous Arb balls.  The derivatives below are high-precision midpoint finite differences with the active prime-power set frozen.  The step-size ladder was pushed far below the ordinary numerical scale because the component directional derivatives are extremely ill-conditioned.

### N = 16

At the smallest tested step `h=1e-24`, the three normalized directional contributions are approximately

\[
+1.0359950731666556\times10^{52},\quad
-5.504270870676989\times10^{51},\quad
-4.855679860989568\times10^{51}.
\]

Their sum is `-101.61489067...`, while the direct Schur-pivot finite difference is `-101.61406927...`.  The residual decreases by the expected centered-difference `O(h^2)` factor as `h` shrinks.  The cancellation ratio

\[
\frac{|G_{02}|+|G_R|+|G_p|}{|G_{02}+G_R+G_p|}
\]

is about `2.0e50`.

### N = 24

At `h=1e-34`, the individual contributions are of order `1e70`, while the sum is `-93.76328008...` and the direct value is `-93.76271393...`.  The cancellation ratio is about

\[
2.66\times10^{68}.
\]

### N = 32

At `h=1e-44`, the contributions are approximately

\[
\begin{aligned}
G_{02}&\approx +2.6205780223423025\times10^{86},\\
G_R&\approx -1.6389395537713353\times10^{86},\\
G_p&\approx -9.816384685709672\times10^{85},
\end{aligned}
\]

while

\[
G_{02}+G_R+G_p\approx80.68193723826...
\]

and the direct pivot difference gives `80.68193793951...`.  Again the remaining discrepancy is consistent with the centered-difference truncation ladder.  The cancellation ratio is about

\[
6.50\times10^{84}.
\]

## What this kills

A proof strategy of the form

\[
|w^T E'w|\le |w^TW_{02}'w|+|w^TW_R'w|+|w^TW_p'w|
\]

is unusable.  It destroys between roughly 50 and 85 decimal orders already at `N=16..32`.

Likewise, matrix-wide inequalities such as

\[
E'(u)\succeq-C(u)E(u)
\]

with a manageable `C` are not supported by the computed generalized derivative norms.

## Why finite differences are now the natural target

The Schur normals observed in the even Fourier basis approach centered finite-difference/binomial stencils.  On the full symmetric frequency grid define

\[
d_m=(-1)^{N-m}\binom{2N}{N+m},\qquad -N\le m\le N.
\]

Then

\[
\sum_{m=-N}^N d_m m^j=0\qquad(0\le j<2N)
\]

and

\[
\sum_{m=-N}^N d_m z^m
=(-1)^N z^{-N}(1-z)^{2N}.
\]

For exponential phases,

\[
\sum_{m=-N}^N d_m e^{im\theta}
=(-1)^N e^{-iN\theta}(1-e^{i\theta})^{2N},
\]

so its magnitude is exactly

\[
(2|\sin(\theta/2)|)^{2N}.
\]

For Cauchy kernels there is the exact identity

\[
\sum_{m=-N}^N
\frac{d_m}{z-m}
=(-1)^N\frac{(2N)!}{\prod_{j=-N}^N(z-j)}.
\]

These two identities are tailored respectively to the trigonometric prime term and the Cauchy/Loewner archimedean structure.

## Current theorem target

Do **not** estimate `W02`, `WR`, and `Wp` separately.  Instead seek a representation of the *combined* threshold-free derivative kernel

\[
K_u'(m,n)
\]

such that applying the centered finite-difference operator in both discrete variables kills the low-order jets before absolute values are taken.

A useful schematic target is

\[
\sum_{m,n=-N}^N d_m d_n K_u'(m,n)
=\Delta_m^{2N}\Delta_n^{2N}K_u'(\xi,\eta)
\]

or a contour-integral/divided-difference analogue with a directly bounded remainder.

Then split the actual Schur normal as

\[
w_N=d_N^{\mathrm{even}}+r_N
\]

and prove a quantitative stability estimate for the correction `r_N`.

The desired route is therefore:

1. exact finite-difference evaluation/bound for the **combined** CvS derivative kernel;
2. quantitative approximation of the Schur normal by the centered stencil;
3. a bound on the correction terms that is measured relative to `s_N`, not relative to the full matrix condition number;
4. only after that, incorporate the exact negative rank-one prime-edge jumps.

This is presently a concrete lemma program, not a proof of the Riemann Hypothesis.
