# 023 — Boundary Pick Weyl disks and the same Schur denominators that extract zeta zeros

Status: classical boundary Nevanlinna–Pick / Weyl-circle theory specialized to the squared-node CvS data, plus exploratory high-precision diagnostics. **No RH claim.**

This note is deliberately framed as an application of existing interpolation theory, not as a new determinacy criterion. The finite boundary Julia-reduction machinery is classical (Sarason; Agler–Young), and the infinite limit-point / Weyl-disk criterion is classical in Nevanlinna–Pick and moment-problem theory (Delsarte–Genin–Kamp; Derevyagin; Dyukarev). The potentially useful point here is the exact identification of the relevant first-kind rational functions with the Schur Cauchy denominators already appearing in the CvS finite zero extraction.

## 1. Squared-grid boundary Pick data

From note 019, the even CvS block is congruent to the confluent Loewner/Pick matrix

\[
P_N=L_N(G_C)
\]

on the real nodes

\[
x_k=k^2,\qquad k=0,1,\ldots,N,
\]

with boundary data

\[
G_C(x_k)=w_k,\qquad G_C'(x_k)=v_k.
\]

Thus

\[
(P_N)_{jk}=\frac{w_j-w_k}{x_j-x_k}\quad(j\ne k),
\qquad
(P_N)_{jj}=v_j.
\]

When `P_N>0`, the finite boundary Nevanlinna–Pick problem is indeterminate and its solution set is a linear-fractional image of a free Pick-class parameter. At any fixed `z in C_+`, the set of possible values `f(z)` is a Weyl disk.

## 2. Classical Weyl-disk radius in Pick-matrix coordinates

Put

\[
q_N(z)=
\begin{pmatrix}
(x_0-\bar z)^{-1}\\
\vdots\\
(x_N-\bar z)^{-1}
\end{pmatrix}.
\]

The standard finite Weyl-circle formula, equivalently obtained by adding the interior interpolation condition `f(z)=y` and taking the Schur complement of the augmented Pick matrix, gives

\[
\boxed{
R_N(z)=
\frac{1}{2\,\Im z\;K_N(z)},
\qquad
K_N(z):=q_N(z)^*P_N^{-1}q_N(z).
}
\]

Thus the infinite boundary interpolation problem is determinate at the test point precisely when

\[
K_N(z)\longrightarrow+\infty,
\]

or equivalently

\[
R_N(z)\longrightarrow0.
\]

This is the boundary analogue of the classical Hamburger / Weyl-circle criterion expressed as divergence of a squared first-kind rational-function series.

The node sequence `x_k=k^2` alone does **not** force this divergence; the literature audit in note 022 found that sparse boundary nodes can remain indeterminate. Any proof must use the special CvS jet data.

## 3. Exact positive-increment decomposition from nested Schur complements

Partition

\[
P_N=
\begin{pmatrix}
P_{N-1}&b_N\\
b_N^T&c_N
\end{pmatrix}
\]

and let

\[
\sigma_N=c_N-b_N^TP_{N-1}^{-1}b_N>0
\]

be the last squared-grid Schur pivot. Define the endpoint-normalized Schur normal

\[
\boxed{
u_N=
\begin{pmatrix}
-P_{N-1}^{-1}b_N\\1
\end{pmatrix}.}
\]

Block inversion gives the exact identity

\[
\boxed{
K_N(z)-K_{N-1}(z)
=
\frac{|u_N^Tq_N(z)|^2}{\sigma_N}.
}
\]

Hence, with

\[
p_N(z):=\frac{u_N^Tq_N(z)}{\sqrt{\sigma_N}},
\]

we have

\[
\boxed{
K_N(z)=\sum_{n=0}^{N}|p_n(z)|^2
}
\]

(with the obvious one-node normalization at `n=0`) and therefore

\[
\boxed{
R_N(z)=
\frac{1}{2\Im z\displaystyle\sum_{n=0}^N|p_n(z)|^2}.
}
\]

This is exactly the shape of the classical first-kind rational-function determinacy series. No new criterion is being claimed; the useful specialization is the next identity.

## 4. The first-kind functions are the same Schur Cauchy denominators used in zero extraction

Define the Cauchy transform of the Schur normal

\[
\mathcal R_N(\zeta)
:=\sum_{k=0}^N\frac{(u_N)_k}{\zeta-x_k}.
\]

Since

\[
q_{N,k}(z)=\frac1{x_k-\bar z}
=-\frac1{\bar z-x_k},
\]

we get

\[
\boxed{
u_N^Tq_N(z)=-\mathcal R_N(\bar z).}
\]

Therefore

\[
\boxed{
p_N(z)=-\frac{\mathcal R_N(\bar z)}{\sqrt{\sigma_N}}.}
\]

But `mathcal R_N` is precisely the barycentric denominator attached to the Schur normal. Notes 014–020 showed that its real zeros are the poles of the critical rational Pick interpolant, and after undoing the squared-coordinate / CvS scaling these are the finite real-zero approximants used by the CCM/Groskin spectral extraction.

Thus one and the same rational sequence controls two apparently different limits:

1. **finite spectral approximation:** zeros of `mathcal R_N` approximate scaled zeta ordinates;
2. **infinite interpolation determinacy:** off-real values `|mathcal R_N(\bar z)|^2/sigma_N` determine whether the Weyl disks collapse.

This is the main structural reason to retain the Pick route after the literature audit.

## 5. Exploratory Weyl-disk diagnostic at `z=i`

The one-shot workflow used the pinned cutoff-free Arb CvS builder for the input matrices and then high-precision midpoint Julia reductions / transfer matrices. Therefore the following radii are **diagnostics, not interval certificates**.

At `C=13`:

\[
R_0(i)\approx2.2666\times10^{-2},
\]

\[
R_8(i)\approx2.3857\times10^{-22},
\]

and

\[
\boxed{R_{32}(i)\approx8.2940\times10^{-49}.}
\]

The disk center at `N=32` is already stable to the displayed precision near

\[
-0.0003792396953426461028871066902010271894
+0.0453250046789267429427205469569897211287\,i.
\]

At `C=100`:

\[
R_0(i)\approx1.2559\times10^{-2},
\]

\[
R_8(i)\approx1.5748\times10^{-31},
\]

and

\[
\boxed{R_{32}(i)\approx8.5968\times10^{-87}.}
\]

The corresponding center is stable near

\[
-0.00009496961316968328799465047373750651593
+0.02511807251354290593748890490154704325896\,i.
\]

The observed shrinkage is dramatic at both cutoffs and is consistent with a limit-point / determinate infinite boundary problem. It is **not a proof** because:

- only finitely many `N` are sampled;
- the Julia reductions use high-precision midpoints rather than interval arithmetic;
- positivity of all future `P_N` is not established;
- even determinacy would still identify only a unique Pick representative of the jet data, not automatically the original meromorphic global source `G_C`.

## 6. The next proof problem is now precise

The generic node geometry cannot prove determinacy. We need a CvS-specific lower bound forcing

\[
\boxed{
\sum_{N\ge0}
\frac{|\mathcal R_N(\bar z)|^2}{\sigma_N}
=+\infty
}
\]

for one (hence, under the standard theory, every appropriate) `z in C_+`.

At `z=i`, the data suggest enormous growth. The right object to estimate is therefore **not** the tiny smallest eigenvalue by itself. It is the normalized off-real Schur denominator

\[
\boxed{
\frac{|\mathcal R_N(-i)|}{\sqrt{\sigma_N}}.
}
\]

Potential sources of a lower bound that are genuinely specific to this problem:

1. the squared-node product structure `prod(k^2+1)`;
2. the real-pole / negative-residue geometry of the finite critical Pick interpolants;
3. the completed-log-derivative normal form of note 018;
4. the exact finite Guinand–Weil zero-side dictionary;
5. a de Branges/canonical-system identification of the limiting first-kind rational functions.

## 7. Remaining identification problem after determinacy

Even if Weyl disks collapse, the squared-grid Hermite jets admit the analytic gauge freedom

\[
G\mapsto G+VH,
\qquad
V(x)=\frac{x\sin^2(\pi\sqrt{x})}{\pi^2},
\]

which preserves all prescribed values and derivatives at the squared nodes. Therefore determinacy in the Pick class says there is at most one **Pick** representative, not that the explicit meromorphic source `G_C` itself is that representative.

A second theorem would still be needed to identify the unique Pick limit with the zeta/Xi object. A plausible form is a growth-normalized uniqueness statement within the gauge class, but this must be checked against existing de Branges / meromorphic-inner / canonical-system inverse theory before being treated as a new route.
