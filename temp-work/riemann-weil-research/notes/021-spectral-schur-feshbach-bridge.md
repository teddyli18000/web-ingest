# Spectral Schur functions, Feshbach inverse moments, and ground-state endpoint weights

Status: exact finite-dimensional linear algebra plus quantitative inequalities; no RH claim.

This note connects the static Schur quantities used throughout this workspace to the inverse spectral moments that occur in continuum Feshbach/proxy-bridge formulations.

The point is that the same scalar Schur complement has two distinct evaluations:

- at spectral parameter `z=0`, it is the static positivity pivot `s_N`;
- at the lowest eigenvalue `z=mu_N`, it vanishes, and its derivative is the inverse ground-state weight / Feshbach inverse moment.

The static Schur normal therefore gives a directly computable approximation to a genuinely spectral quantity whenever the new ground root lies far below the previous block's spectrum.

## 1. Setup

Let

\[
E=
\begin{pmatrix}
B&b\\
b^T&d
\end{pmatrix}>0,
\]

where `B` is an `N x N` positive-definite principal block. Put

\[
\delta:=\lambda_{\min}(B)>0,
\qquad
\mu:=\lambda_{\min}(E)>0.
\]

By Cauchy interlacing, `mu <= delta`; in the nondegenerate coupled case relevant below we have

\[
0<\mu<\delta.
\]

Define the spectral Schur/Feshbach function for real `z<delta` by

\[
\boxed{
f(z):=d-z-b^T(B-zI)^{-1}b.
}
\]

The static Schur pivot and normal are

\[
s:=f(0)=d-b^TB^{-1}b,
\]

\[
\boxed{
w_0:=\binom{-B^{-1}b}{1}.}
\]

## 2. Determinant-ratio identity

Block determinant factorization gives

\[
\boxed{
f(z)=\frac{\det(E-zI)}{\det(B-zI)}.}
\]

Consequently, every eigenvalue of `E` below `delta` is a zero of `f`. In particular,

\[
\boxed{f(\mu)=0.}
\]

At the ground root,

\[
\det(E-\mu I)=0,
\]

and the unnormalized eigenvector with final coordinate one is

\[
\boxed{
w_\mu:=
\binom{-(B-\mu I)^{-1}b}{1}.}
\]

Thus the static Schur normal `w_0` is simply the zero-spectral-parameter version of the exact ground-state Feshbach vector `w_mu`.

## 3. Derivative = Feshbach inverse moment = inverse endpoint weight

Differentiate:

\[
\boxed{
f'(z)
=-1-b^T(B-zI)^{-2}b.}
\]

Define

\[
\Sigma'(z):=b^T(B-zI)^{-2}b\ge0.
\]

Then

\[
-f'(z)=1+\Sigma'(z)=\|w_z\|_2^2,
\]

where

\[
w_z=\binom{-(B-zI)^{-1}b}{1}.
\]

Let `q_mu=w_mu/||w_mu||` be the normalized ground eigenvector, with sign chosen so that its last coordinate is positive. Then

\[
\boxed{
|(q_\mu)_N|^2
=\frac{1}{1+\Sigma'(\mu)}
=\frac1{-f'(\mu)}.
}
\]

This is the finite-dimensional version of the standard rank-one Feshbach identity: the derivative of the scalar Weyl/Feshbach function at a simple eigenvalue is the inverse squared weight of the retained vector in that eigenstate.

Using the determinant ratio,

\[
\boxed{
-f'(\mu)
=-\frac{\left.\frac{d}{dz}\det(E-zI)\right|_{z=\mu}}
{\det(B-\mu I)}.
}
\]

If the eigenvalues of `E` are

\[
\mu=\lambda_1<\lambda_2\le\cdots\le\lambda_{N+1}
\]

and those of `B` are

\[
\beta_1\le\cdots\le\beta_N,
\]

then

\[
\boxed{
-f'(\mu)
=
\frac{\prod_{j=2}^{N+1}(\lambda_j-\mu)}
{\prod_{j=1}^{N}(\beta_j-\mu)}.
}
\]

Thus the endpoint ground-state weight is also an exact ratio of interlacing spectral products.

## 4. Static Schur-normal norm is the zero-energy inverse moment

At `z=0`,

\[
\boxed{
-f'(0)=1+b^TB^{-2}b=\|w_0\|_2^2.
}
\]

Hence the large Euclidean norm of the Schur normal observed numerically is not an incidental conditioning artifact: it is exactly the static Feshbach inverse moment.

This already explains why the Schur pivot can be vastly larger than the smallest eigenvalue.

## 5. Exact integral identity linking pivot and ground root

Since `f(mu)=0`,

\[
\begin{aligned}
s
&=f(0)-f(\mu)\\
&=\int_0^\mu -f'(t)\,dt\\
&=\int_0^\mu \left(1+\Sigma'(t)\right)dt.
\end{aligned}
\]

Therefore

\[
\boxed{
\frac{s}{\mu}
=\frac1\mu\int_0^\mu\|w_t\|_2^2\,dt.
}
\]

So `s/mu` is literally the average Feshbach-vector norm squared between the static point and the true ground root.

## 6. Quantitative two-sided bounds

Diagonalize `B`. For `0<=t<=mu<delta`, every spectral component obeys

\[
\frac1{\beta_j^2}
\le
\frac1{(\beta_j-t)^2}
\le
\left(\frac{\delta}{\delta-\mu}\right)^2
\frac1{\beta_j^2}.
\]

Put

\[
\kappa:=\frac{\delta}{\delta-\mu}.
\]

Then

\[
\Sigma'(0)
\le\Sigma'(t)
\le\kappa^2\Sigma'(0).
\]

Using `1+Sigma'(0)=||w_0||^2`, the averaged identity yields

\[
\boxed{
\|w_0\|_2^2
\le
\frac{s}{\mu}
\le
1+\kappa^2\bigl(\|w_0\|_2^2-1\bigr).
}
\]

Equivalently,

\[
\boxed{
\frac{s}{1+\kappa^2(\|w_0\|_2^2-1)}
\le \mu
\le
\frac{s}{\|w_0\|_2^2}.
}
\]

The same pointwise estimate at `t=mu` gives

\[
\boxed{
\|w_0\|_2^2
\le
\frac1{|(q_\mu)_N|^2}
\le
1+\kappa^2\bigl(\|w_0\|_2^2-1\bigr).
}
\]

Thus when

\[
\frac\mu\delta\to0,
\]

we have the controlled asymptotics

\[
\boxed{
\frac{s}{\mu}
=\|w_0\|_2^2\left(1+O(\mu/\delta)\right)
}
\]

and

\[
\boxed{
|(q_\mu)_N|^2
=\|w_0\|_2^{-2}\left(1+O(\mu/\delta)\right),
}
\]

provided the norm is nontrivial; the displayed two-sided inequalities are the precise statements and do not require an asymptotic assumption.

A simple consequence, requiring no estimate of `delta`, is

\[
\boxed{
|(q_\mu)_N|^2\le\frac{\mu}{s}.
}
\]

Indeed `-f'(mu)` is at least the average value `s/mu` because `Sigma'(t)` is increasing.

## 7. Resolvent / Stieltjes formulation

The endpoint resolvent entry of the full matrix is

\[
m_E(z):=e_N^T(E-zI)^{-1}e_N.
\]

Block inversion gives

\[
\boxed{m_E(z)=\frac1{f(z)}.}
\]

At zero,

\[
\boxed{m_E(0)=\frac1s.}
\]

Differentiating,

\[
m_E'(0)=e_N^TE^{-2}e_N
=\frac{\|w_0\|_2^2}{s^2}.
\]

Hence

\[
\boxed{
\frac{m_E'(0)}{m_E(0)}
=\frac{\|w_0\|_2^2}{s}.
}
\]

The reciprocal

\[
\boxed{
\widehat\mu:=\frac{s}{\|w_0\|_2^2}
}
\]

is therefore the ratio of the first two inverse spectral moments of the endpoint spectral measure and is a rigorous upper bound for the true ground eigenvalue `mu`.

When the ground state dominates those inverse moments, `mu_hat` is extremely accurate. This provides a conceptual explanation for the observed numerical relation between tiny `lambda_min`, much larger Schur pivots, and huge Schur-normal norms.

## 8. Relation to the prolate-proxy Feshbach bridge

For a general rank-one decomposition

\[
A=
\begin{pmatrix}
a&\langle w,\cdot\rangle\\
w&D
\end{pmatrix},
\]

the scalar Feshbach function is

\[
f(z)=a-z-\langle w,(D-z)^{-1}w\rangle.
\]

If `mu` is a simple eigenvalue below the complementary spectrum, then exactly the same calculation gives

\[
\boxed{
|\langle \kappa,e_\mu\rangle|^2
=\frac1{1+\langle w,(D-\mu)^{-2}w\rangle}
=\frac1{-f'(\mu)}.
}
\]

Therefore the inverse moment that appears in quantitative prolate-proxy bridge work is precisely the derivative of a scalar determinant/Weyl ratio at the ground root.

The present finite CvS/Loewner calculations add a useful static viewpoint:

- `f(0)` is a Schur pivot;
- `-f'(0)` is the squared Schur-normal norm;
- `f(mu)=0` is the new ground eigenvalue equation;
- `-f'(mu)` is the inverse retained-vector ground weight.

This suggests a cross-scale strategy: rather than estimate the spectral projector mass directly, seek a scalar normal-family or Pick/Stieltjes control of `f(z)` from a reference point to its first zero.

## 9. Why this does not solve the continuum bridge

The inequalities are useful only if the reference point is spectrally separated from the complementary block. In the finite nested matrix problem this is measured by

\[
\mu/\delta.
\]

In the continuum prolate-proxy decomposition, the corresponding complementary bottom and gap themselves collapse on delicate scales. Existing work does not supply a uniform estimate strong enough to replace the unresolved bottom/middle spectral mass by its static value.

So this note does not bypass the known bridge obstruction. It identifies an exact scalar quantity and a sufficient regime in which the static Schur geometry controls the spectral inverse moment.

## 10. Next concrete test

For the cutoff-free CvS matrices, compute for a range of `C,N`:

\[
\mu_N,
\quad
\delta_N=\lambda_{\min}(E_{N-1}),
\quad
s_N,
\quad
\|w_N\|^2,
\quad
\widehat\mu_N=s_N/\|w_N\|^2,
\]

and the exact ground endpoint weight. Compare

\[
\widehat\mu_N/\mu_N-1
\]

against

\[
\mu_N/\delta_N.
\]

If the empirical error tracks the rigorous resolvent factor, that gives a stable finite laboratory for testing any proposed continuum estimate before attempting infinite-dimensional proofs.
