# Elementary source concentration bound from periodic logarithmic energy

Status: elementary lemma, independent of RH and independent of the detailed Weil operator. It gives a rigorous interpretation of the metrics in `source_escape_diagnostic.py`.

## Setup

Let

\[
T(s)=\sum_{k\in\mathbb Z}u_k e^{2\pi i k s}\in L^2(\mathbb T),
\qquad
\|T\|_2^2=\sum_k|u_k|^2=1,
\]

and define

\[
E_{\log}^{\mathbb T}(T)
=\sum_{k\in\mathbb Z}|u_k|^2\log(e+|k|).
\]

For a finite Galerkin source only finitely many coefficients are nonzero, but the lemma is stated for every source with finite logarithmic energy.

## Lemma

For every measurable set `I` in the unit circle of measure `ell`, every integer `K>=1`, and every normalized `T` as above,

\[
\boxed{
\|\mathbf 1_I T\|_2
\le
\sqrt{\ell(2K+1)}
+
\sqrt{\frac{E_{\log}^{\mathbb T}(T)}{\log(e+K)}}.
}
\]

Consequently

\[
\boxed{
\int_I|T|^2
\le
\left(
\sqrt{\ell(2K+1)}
+
\sqrt{\frac{E_{\log}^{\mathbb T}(T)}{\log(e+K)}}
\right)^2.
}
\]

The set `I` may be a union of the two endpoint strips; only its total measure matters.

## Proof

Split

\[
T=P_KT+R_KT,
\]

where

\[
P_KT=\sum_{|k|\le K}u_ke^{2\pi iks}.
\]

For the low-frequency part, Cauchy--Schwarz on the coefficient vector gives

\[
\|P_KT\|_\infty
\le\sum_{|k|\le K}|u_k|
\le\sqrt{2K+1}\,\|P_KT\|_2
\le\sqrt{2K+1}.
\]

Therefore

\[
\|\mathbf1_IP_KT\|_2
\le\sqrt\ell\,\|P_KT\|_\infty
\le\sqrt{\ell(2K+1)}.
\]

For the high-frequency part,

\[
\begin{aligned}
\|R_KT\|_2^2
&=\sum_{|k|>K}|u_k|^2\\
&\le
\frac1{\log(e+K)}
\sum_{|k|>K}|u_k|^2\log(e+|k|)\\
&\le
\frac{E_{\log}^{\mathbb T}(T)}{\log(e+K)}.
\end{aligned}
\]

Finally use the triangle inequality in `L2(I)`:

\[
\|\mathbf1_IT\|_2
\le
\|\mathbf1_IP_KT\|_2+\|\mathbf1_IR_KT\|_2
\le
\sqrt{\ell(2K+1)}
+
\sqrt{E_{\log}^{\mathbb T}/\log(e+K)}.
\]

This proves the claim.

## Corollary: fixed local mass forces logarithmic energy growth

Suppose

\[
\int_I|T|^2\ge m>0.
\]

Then for any `K` satisfying

\[
\ell(2K+1)\le m/4,
\]

the lemma implies

\[
\sqrt m
\le\frac{\sqrt m}{2}
+
\sqrt{E_{\log}^{\mathbb T}/\log(e+K)},
\]

and hence

\[
\boxed{
E_{\log}^{\mathbb T}(T)
\ge \frac m4\log(e+K).
}
\]

For sufficiently small `ell` one may choose `K` comparable to `m/ell`; therefore

\[
E_{\log}^{\mathbb T}(T)
\gtrsim_m \log(1/\ell).
\]

Thus a normalized Galerkin source carrying a fixed positive amount of mass in endpoint strips whose total width tends to zero must have diverging periodic logarithmic energy.

## Corollary: bounded logarithmic energy gives uniform anti-concentration

Choose for small `ell`, for example,

\[
K\asymp\frac1{\ell\log^2(e/\ell)}.
\]

Then

\[
\ell(2K+1)=O(1/\log^2(e/\ell))
\]

and

\[
\log(e+K)=\log(1/\ell)+O(\log\log(1/\ell)).
\]

Therefore every family with `E_log^T <= E` obeys

\[
\sup_T\int_I|T|^2
=O\!\left(\frac{E+1}{\log(1/\ell)}\right).
\]

This recovers, by an elementary Fourier split on the circle, the same logarithmic concentration scale that appeared from boundary Hardy/local-uncertainty arguments in the interval model.

## Sharpness in order

The logarithmic scale cannot be generically improved. Normalized trigonometric kernels concentrated on width `~1/N` use frequencies up to `N`; their logarithmic energy is of order `log N`, while a fixed fraction of their `L2` mass can remain in an interval of width `~1/N`.

So the lemma captures the correct order for generic source concentration.

## Use in the current experiment

For the CvS/CCM coefficient vector, the experiment records both

\[
E_{\log}^{\mathbb T}
\]

and exact endpoint-strip masses. The lemma means the two measurements are not unrelated heuristics:

- fixed/shrinking endpoint mass with increasing `N` mathematically forces logarithmic frequency growth;
- bounded logarithmic energy rules out genuine concentration on vanishing endpoint scales;
- a candidate mode with bounded energy is precompact in source `L2`, while a Bombieri-style weak-to-zero boundary escape cannot be.

This still does not certify the sign of the full Weil form. It is a compactness/escape diagnostic to be combined with independent finite-cutoff/tail certification.
