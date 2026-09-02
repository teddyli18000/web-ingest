# Loewner--barycentric Hermite reformulation of the Schur pivot

Status: exact finite-dimensional algebraic lemma; no RH claim.

## 1. The CvS matrix is a divided-difference matrix

For a source function `psi` that is differentiable at the integer nodes

\[
I_N=\{-N,-N+1,\ldots,N\},
\]

define its confluent Loewner matrix

\[
(Q_\psi)_{mn}=
\begin{cases}
\dfrac{\psi(m)-\psi(n)}{m-n},&m\neq n,\\[1.2ex]
\psi'(m),&m=n.
\end{cases}
\]

The Connes--van Suijlekom finite matrix has exactly this divided-difference structure.  The prime, pole, and archimedean pieces are represented by source functions and the construction is linear in the source.  Hence the complete cutoff-free matrix can be treated as `Q_psi` for the corresponding combined source `psi`.

The point of this note is that the last Schur pivot of `Q_psi` has an exact rational-Hermite interpolation meaning.

## 2. Residue form of a Loewner quadratic form

Let `u=(u_m)_{m in I_N}` and put

\[
R_u(z)=\sum_{m=-N}^{N}\frac{u_m}{z-m}.
\]

If `psi` is holomorphic on a neighborhood of the integer nodes, then

\[
\boxed{
 u^TQ_\psi u
 =\sum_{m=-N}^{N}\operatorname*{Res}_{z=m}
 \bigl(\psi(z)R_u(z)^2\bigr).
}
\]

Indeed, near `z=m`,

\[
R_u(z)=\frac{u_m}{z-m}+\sum_{n\ne m}\frac{u_n}{m-n}+O(z-m),
\]

so the residue is

\[
u_m^2\psi'(m)
+2u_m\psi(m)\sum_{n\ne m}\frac{u_n}{m-n}.
\]

Summing over `m` and pairing the off-diagonal terms gives exactly the Loewner quadratic form.

Equivalently, for a contour `Gamma` surrounding the nodes and no other singularities of the integrand,

\[
 u^TQ_\psi u
 =\frac{1}{2\pi i}\oint_\Gamma
 \psi(z)R_u(z)^2\,dz.
\]

## 3. Numerator-polynomial parametrization

Let

\[
D_N(z)=\prod_{j=-N}^{N}(z-j)
=z\prod_{j=1}^{N}(z^2-j^2).
\]

Every coefficient vector has

\[
R_u(z)=\frac{P_u(z)}{D_N(z)},
\]

where `P_u` is a polynomial of degree at most `2N`, and

\[
P_u(m)=u_mD_N'(m).
\]

For a symmetric vector `u_{-m}=u_m`, `R_u` is odd, `D_N` is odd, and therefore `P_u` is even.

Under the standard even-sector embedding

\[
u_0=v_0,\qquad u_{\pm k}=\frac{v_k}{\sqrt2},\quad k\ge1,
\]

the normalization `v_N=1` gives

\[
P_u(N)=u_ND_N'(N)=\frac{(2N)!}{\sqrt2}.
\]

Thus the last Schur pivot is an extremal problem over **even numerator polynomials**:

\[
\boxed{
 s_N
 =\min_{\substack{P\ \mathrm{even},\ \deg P\le2N\\
 P(N)=(2N)!/\sqrt2}}
 \frac{1}{2\pi i}\oint_\Gamma
 \psi(z)\frac{P(z)^2}{D_N(z)^2}\,dz,
}
\]

whenever the preceding even block is positive definite.

The centered finite-difference stencil is exactly the **constant-numerator trial polynomial**.  Indeed, for

\[
d_m=(-1)^{N-m}\binom{2N}{N+m},
\]

one has

\[
\sum_{m=-N}^{N}\frac{d_m}{z-m}
=\frac{(2N)!}{D_N(z)}.
\]

After the even-sector normalization, the numerator is `(2N)!/sqrt(2)`.

This explains the previous exact-stencil experiment: it tested only the constant numerator, while the actual Schur normal is free to choose an entire even polynomial numerator of degree `2N`.

## 4. Exact constrained-minimizer Pythagorean identity

Write the even matrix as

\[
E_N=\begin{pmatrix}B&b\\b^T&c\end{pmatrix},
\qquad
w_N=\binom{-B^{-1}b}{1},
\qquad
s_N=c-b^TB^{-1}b.
\]

For any other trial vector `v=(z,1)`, set `r=v-w_N`; then `r_N=0` and

\[
r^TE_Nw_N=0.
\]

Therefore

\[
\boxed{
 v^TE_Nv=s_N+r^TE_Nr
       =s_N+r_{<N}^TBr_{<N}.
}
\]

Equivalently, with trial residual

\[
y=Bz+b,
\]

we have

\[
\boxed{
 s_N=v^TE_Nv-y^TB^{-1}y.
}
\]

This is why an Euclidean overlap near one is not enough.  At `c=100`, the exact centered stencil has normalized overlaps around `0.99`, `0.98`, `0.97` with the actual Schur normals at `N=16,24,32`, but its quadratic energy exceeds the true pivot by roughly `10^41`, `10^57`, `10^72`, respectively.  The correction term is the essential variational content.

## 5. Barycentric rational interpolant

Define

\[
S_u(z)=\sum_{m=-N}^{N}\frac{u_m\psi(m)}{z-m},
\qquad
r_u(z)=\frac{S_u(z)}{R_u(z)}.
\]

Whenever `u_m != 0`, the common pole at `z=m` immediately gives

\[
r_u(m)=\psi(m).
\]

Now expand around `z=m`.  Write

\[
R_u(z)=\frac{u_m}{z-m}+r_0+O(z-m),
\]

\[
S_u(z)=\frac{u_m\psi(m)}{z-m}+s_0+O(z-m),
\]

where

\[
r_0=\sum_{n\ne m}\frac{u_n}{m-n},
\qquad
s_0=\sum_{n\ne m}\frac{u_n\psi(n)}{m-n}.
\]

The quotient expansion gives

\[
r_u'(m)=\frac{s_0-\psi(m)r_0}{u_m}.
\]

Using the Loewner matrix definition,

\[
(Q_\psi u)_m
=u_m\psi'(m)
+\sum_{n\ne m}u_n\frac{\psi(m)-\psi(n)}{m-n},
\]

hence

\[
\boxed{
 r_u'(m)=\psi'(m)-\frac{(Q_\psi u)_m}{u_m}.
}
\]

This identity is the central observation.

## 6. Schur normal = multipoint Hermite rational interpolant

Take `u` to be the full symmetric embedding of the even Schur normal `w_N`.  Symmetry of the source/matrix implies that the even Schur equations

\[
E_Nw_N=s_Ne_N
\]

are equivalent to

\[
(Q_\psi u)_m=0,\qquad |m|<N,
\]

and at the endpoint

\[
(Q_\psi u)_N=\frac{s_N}{\sqrt2},
\qquad
u_N=\frac1{\sqrt2}.
\]

Therefore the barycentric rational function `r_N=r_u` satisfies

\[
\boxed{
 r_N(m)=\psi(m),\qquad -N\le m\le N,
}
\]

and, at every interior node for which the corresponding barycentric weight is nonzero,

\[
\boxed{
 r_N'(m)=\psi'(m),\qquad |m|<N.
}
\]

At the right endpoint,

\[
\boxed{
 s_N=\psi'(N)-r_N'(N).
}
\]

The same endpoint defect occurs at `-N` by symmetry.

Hence the Schur pivot is exactly the **remaining endpoint derivative error of a multipoint Hermite barycentric rational interpolant** which already matches the source value at all `2N+1` nodes and matches its first derivative at all `2N-1` interior nodes.

## 7. Why this is a better theorem target

The positivity step

\[
s_N>0
\]

can now be read as

\[
\boxed{
 r_N'(N)<\psi'(N).
}
\]

This is the native language of boundary Nevanlinna--Pick / Julia reduction and rational Hermite interpolation.  It also explains why Schur complementation kept producing the right scalar variable: the Schur step is precisely the act of consuming all previous value/derivative interpolation conditions and exposing the next boundary derivative defect.

A useful next program is therefore:

1. identify the combined CvS source `psi` in the strongest analytic class available on the relevant strip/half-plane;
2. characterize `r_N` as a multipoint Pade/Hermite approximant to that source;
3. seek a remainder formula for `psi'(N)-r_N'(N)` that preserves the combined prime/pole/archimedean cancellation;
4. determine whether Pick/Herglotz comparison theorems give a sign for this endpoint derivative defect under a condition weaker than globally proving that `psi` is a Pick function;
5. connect the exact rank-one prime-threshold update to the corresponding rational-interpolant update.

This does not prove positivity, but it converts the current matrix problem into a sharply defined rational interpolation remainder problem.
