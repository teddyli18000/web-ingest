# Exact Hermite-error factorization for the Schur rational interpolant

Status: exact finite-dimensional algebraic lemma; no RH claim.

This continues `015-loewner-barycentric-hermite-reformulation.md`.

## Setup

Let

\[
I_N=\{-N,-N+1,\ldots,N\}
\]

and let `psi` be holomorphic on a neighborhood of these nodes.  Its confluent Loewner matrix is

\[
(Q_\psi)_{mn}=
\begin{cases}
\dfrac{\psi(m)-\psi(n)}{m-n},&m\ne n,\\[1.2ex]
\psi'(m),&m=n.
\end{cases}
\]

For a coefficient vector `u=(u_m)`, define

\[
R_u(z)=\sum_{m=-N}^{N}\frac{u_m}{z-m},
\qquad
S_u(z)=\sum_{m=-N}^{N}\frac{u_m\psi(m)}{z-m},
\]

and

\[
r_u(z)=\frac{S_u(z)}{R_u(z)}.
\]

Also let

\[
D_N(z)=\prod_{j=-N}^{N}(z-j),
\qquad
R_u(z)=\frac{P_u(z)}{D_N(z)}.
\]

For the symmetric even-sector Schur normal, `P_u` is even and the endpoint normalization `v_N=1` gives

\[
P_u(N)=\frac{(2N)!}{\sqrt2}.
\]

## 1. The interpolation residual is a Loewner row residual

Define the analytic function

\[
A_u(z)=\psi(z)R_u(z)-S_u(z)
      =\sum_{m=-N}^{N}u_m\frac{\psi(z)-\psi(m)}{z-m}.
\]

At every node `j`, removable continuation gives

\[
\boxed{A_u(j)=(Q_\psi u)_j.}
\]

Indeed,

\[
A_u(j)=u_j\psi'(j)
+\sum_{m\ne j}u_m\frac{\psi(j)-\psi(m)}{j-m}.
\]

Now take `u=u^{(N)}` to be the full symmetric embedding of the last even Schur normal.  Then

\[
(Q_\psi u)_j=0\qquad(|j|<N),
\]

while, with `u_{\pm N}=1/\sqrt2`,

\[
(Q_\psi u)_{\pm N}=\frac{s_N}{\sqrt2}.
\]

Therefore

\[
A_N(j)=0\qquad(|j|<N),
\]

and

\[
A_N(\pm N)=\frac{s_N}{\sqrt2}.
\]

## 2. Exact factorization

Let

\[
D_{N-1}(z)=\prod_{j=-N+1}^{N-1}(z-j).
\]

Since `A_N` vanishes at all `2N-1` interior nodes, there is a holomorphic function `H_N` such that

\[
\boxed{A_N(z)=D_{N-1}(z)H_N(z).}
\]

Because

\[
\psi(z)-r_N(z)=\frac{A_N(z)}{R_N(z)}
               =\frac{A_N(z)D_N(z)}{P_N(z)},
\]

and

\[
D_N(z)=(z^2-N^2)D_{N-1}(z),
\]

we obtain the exact multipoint Hermite-error factorization

\[
\boxed{
\psi(z)-r_N(z)
=
\frac{(z^2-N^2)D_{N-1}(z)^2H_N(z)}{P_N(z)}.
}
\]

Consequences:

- `psi-r_N` has a double zero at every interior integer node, encoding simultaneous value and derivative interpolation;
- it has a simple zero at each endpoint `+-N`, where only the value has already been matched;
- all remaining analytic difficulty is concentrated in the quotient `H_N/P_N`.

## 3. The Schur pivot is exactly the endpoint error coefficient

Differentiate the factorization at `z=N`.  Since all other terms are regular there,

\[
\psi'(N)-r_N'(N)
=
\frac{2N\,D_{N-1}(N)^2H_N(N)}{P_N(N)}.
\]

But

\[
D_{N-1}(N)=(2N-1)!,
\qquad
P_N(N)=\frac{(2N)!}{\sqrt2}
       =\frac{2N(2N-1)!}{\sqrt2}.
\]

Hence

\[
\boxed{
 s_N=\psi'(N)-r_N'(N)
    =\sqrt2\,(2N-1)!\,H_N(N).
}
\]

Equivalently,

\[
\boxed{
 H_N(N)=\frac{s_N}{\sqrt2\,(2N-1)!}.
}
\]

Thus positivity of the Schur step is exactly

\[
\boxed{H_N(N)>0.}
\]

This is sharper than the statement `s_N>0`: it identifies the precise analytic remainder coefficient whose sign must be controlled.

## 4. Endpoint value of `H_N` directly from the residual

Since `A_N(N)=s_N/\sqrt2` and `D_{N-1}(N)=(2N-1)!`, the same identity follows without differentiation:

\[
H_N(N)=\frac{A_N(N)}{D_{N-1}(N)}
      =\frac{s_N}{\sqrt2\,(2N-1)!}.
\]

So the endpoint derivative defect and the Loewner residual are literally the same scalar written in two normalizations.

## 5. A contour/divided-difference target

By Cauchy's formula, for any contour `Gamma` enclosing the interior nodes but no singularities of `A_N`,

\[
H_N(N)
=
\frac{1}{2\pi i}
\oint_\Gamma
\frac{A_N(z)}{D_{N-1}(z)(z-N)}\,dz
\]

whenever the contour representation is chosen in a domain where the quotient is analytic.  Substituting

\[
A_N(z)=\sum_{m=-N}^{N}u_m\frac{\psi(z)-\psi(m)}{z-m}
\]

shows that the Schur pivot is a high-order divided-difference remainder of the **combined** CvS source, not of its prime/pole/archimedean pieces separately.

This is important because the numerical Schur-flow experiments show 50--85 decimal orders of cancellation between those pieces.  Any proof that estimates them separately before forming `H_N` is structurally misaligned.

## 6. Current theorem target

The finite positivity problem has now become:

> For the explicit combined CvS source `psi`, prove that the endpoint Hermite remainder coefficient `H_N(N)` is positive for every `N` and every relevant cutoff `c`, with the exact negative rank-one prime-threshold updates incorporated rather than bounded independently.

Possible routes:

1. obtain an integral representation of `H_N(N)` in which the cancellation has already occurred and the remaining measure/kernel has a sign;
2. identify `r_N` as the extremal solution of the corresponding boundary Nevanlinna--Pick problem and prove an endpoint derivative comparison for this particular source;
3. characterize the poles and residues of `r_N` and derive a monotone/interlacing remainder formula;
4. transport the same remainder coefficient into Suzuki's screw-function formulation and check whether it becomes a known positive/conditionally positive kernel quantity.

No one of these steps is presently established globally; the value of the factorization is that it isolates one exact scalar analytic remainder instead of an astronomically ill-conditioned matrix eigenvalue.
