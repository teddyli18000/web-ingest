# Squared-node Loewner reduction of the even CvS sector

Status: exact finite-dimensional algebraic reduction; **no RH claim**.

This connects the even-sector Schur pivots directly to the squared-node confluent-Vandermonde structure already present in the finite CvS prime-edge dictionary.

## 1. Odd source to a function of `z^2`

The explicit global source `Phi_C` of notes 017--018 is odd:

\[
\Phi_C(-z)=-\Phi_C(z).
\]

Therefore

\[
\boxed{
G_C(x):=\sqrt{x}\,\Phi_C(\sqrt{x})
}
\]

is single-valued and analytic wherever the corresponding even continuation is analytic: if

\[
\Phi_C(z)=z\,H_C(z^2),
\]

then simply `G_C(x)=x H_C(x)`.

Let

\[
x_k=k^2,\qquad k=0,1,\dots,N.
\]

## 2. Exact congruence with an ordinary Loewner matrix

Let `Q_Phi` be the full confluent Loewner matrix on integer nodes `-N,...,N`, and let `E_N` be its symmetric/even compression in the orthonormal basis

\[
e_0,\qquad \frac{e_k+e_{-k}}{\sqrt2},\quad k=1,\dots,N.
\]

For `k,l>0`, using oddness of `Phi`,

\[
\begin{aligned}
(E_N)_{kl}
&=Q_\Phi(k,l)+Q_\Phi(k,-l)\\
&=\frac{\Phi(k)-\Phi(l)}{k-l}
+\frac{\Phi(k)+\Phi(l)}{k+l}\\
&=2\frac{k\Phi(k)-l\Phi(l)}{k^2-l^2}\\
&=2\frac{G_C(k^2)-G_C(l^2)}{k^2-l^2}.
\end{aligned}
\]

On the diagonal,

\[
(E_N)_{kk}=\Phi'(k)+\frac{\Phi(k)}k=2G_C'(k^2),\qquad k>0.
\]

At zero,

\[
(E_N)_{00}=\Phi'(0)=G_C'(0),
\]

and for `k>0`,

\[
(E_N)_{0k}=\sqrt2\,\frac{\Phi(k)}k
=\sqrt2\,\frac{G_C(k^2)-G_C(0)}{k^2}.
\]

Hence, if `L_N(G_C)` denotes the ordinary confluent Loewner matrix of `G_C` on

\[
\{0,1^2,2^2,\dots,N^2\},
\]

then

\[
\boxed{
E_N=D_N L_N(G_C)D_N,
\qquad
D_N=\operatorname{diag}(1,\sqrt2,\dots,\sqrt2).
}
\]

This is an exact congruence, so the two matrices have the same inertia.

## 3. Schur pivot scaling

Let `sigma_N` be the last Schur pivot of `L_N(G_C)` and `s_N` the last even-sector pivot of `E_N`. Since the last diagonal scaling is `sqrt(2)` for `N>=1`,

\[
\boxed{s_N=2\sigma_N.}
\]

Thus the finite even-sector positivity problem is exactly

\[
\boxed{\sigma_N>0\quad\text{for all }N.}
\]

## 4. Rational Hermite meaning on the squared grid

Apply the standard Loewner--barycentric argument now to `G_C` on only `N+1` nodes.

Let `rho_N(x)` be the rational interpolant associated with the last Schur normal of `L_N(G_C)`, normalized at the endpoint `x_N=N^2`. Then

\[
\rho_N(k^2)=G_C(k^2),\qquad 0\le k\le N,
\]

and

\[
\rho_N'(k^2)=G_C'(k^2),\qquad 0\le k<N.
\]

The only unmatched confluent datum is the endpoint derivative, and

\[
\boxed{
\sigma_N=G_C'(N^2)-\rho_N'(N^2),
}
\]

hence

\[
\boxed{
s_N=2\left[G_C'(N^2)-\rho_N'(N^2)\right].
}
\]

This is the squared-grid version of notes 015--016, but with half as many geometric nodes and no explicit `+/-` duplication.

## 5. Squared-grid Hermite error factorization

Put

\[
\Delta_N(x)=\prod_{k=0}^N(x-k^2).
\]

The same residual argument gives a factorization of the form

\[
\boxed{
G_C(x)-\rho_N(x)
=
\frac{(x-N^2)\left[\prod_{k=0}^{N-1}(x-k^2)\right]^2
\,\mathcal H_N(x)}{\mathcal P_N(x)},
}
\]

where `mathcal P_N` is the barycentric denominator numerator and `mathcal H_N` is analytic near the interpolation nodes.

The endpoint product has the closed form

\[
\prod_{k=0}^{N-1}(N^2-k^2)
=N(2N-1)!.
\]

Therefore the sign of `s_N` is again the sign of a single endpoint Hermite remainder coefficient, now naturally expressed on the squared-node grid.

## 6. Exact match to the upstream squared-node dictionary

The 2026 finite CvS prime-event analysis identifies the squared nodes

\[
0,1^2,\dots,N^2
\]

with one simple node at zero and double confluent nodes at positive squares. Its universal jet annihilator is

\[
S\prod_{k=1}^N(S-k^2)^2,
\]

and its confluent-Vandermonde determinant contains

\[
\prod_{1\le i<j\le N}(j^2-i^2)^4.
\]

The congruence above shows why precisely the same squared geometry appears in the positivity problem: it is the intrinsic Loewner geometry of the even sector, not merely a feature of the prime-edge derivative calculation.

This gives a concrete place to combine the two theories rather than treating the event dictionary and positivity as separate constructions.

## 7. A tempting global shortcut does not appear to hold

If `G_C` were operator monotone on the whole positive half-line, Loewner's theorem would immediately imply positivity on every squared grid. However a high-precision exploratory scan at `C=100` finds `G_C'(x)<0` between the first two squared nodes (for example around `sqrt(x)=0.5`). Thus ordinary interval operator monotonicity is not supported.

The special object is therefore the **discrete confluent sequence**

\[
\bigl(G_C(k^2),G_C'(k^2)\bigr)_{k\ge0},
\]

not the behavior of `G_C` at every positive real point.

A rigorous interval check of that negative derivative can be added if interval operator monotonicity later becomes relevant; it is not needed for the exact squared-grid reduction itself.

## 8. Next target

The next useful theorem should exploit the special squared grid. Candidates are:

1. express the Schur/Jacobi continued-fraction coefficients of the discrete Loewner data and seek a sign recurrence;
2. combine the endpoint Hermite remainder with the upstream annihilator
   \[
   S\prod_{k=1}^N(S-k^2)^2;
   \]
3. derive a discrete moment representation for the squared-grid data, weaker than global operator monotonicity but strong enough to force all Schur pivots positive;
4. use the completed-log-derivative normal form of note 018 to identify how each prime-power frequency enters those discrete continued-fraction coefficients.

No such global sign theorem is established here.