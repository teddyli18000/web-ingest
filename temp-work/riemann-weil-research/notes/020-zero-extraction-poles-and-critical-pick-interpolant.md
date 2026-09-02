# Extracted finite zeros = Schur rational poles, and the critical Pick problem

Status: exact finite-dimensional algebra, plus a conditional boundary-Pick consequence; **no RH claim**.

This note connects three objects that had so far been treated separately:

1. the finite zero extractor in the public `connes-cvs` package;
2. the barycentric rational interpolant attached to the Schur normal from notes 015--016;
3. the squared-node boundary Nevanlinna--Pick problem from note 019.

The first connection is an exact identity. The second gives a clean finite-dimensional route to real finite zero approximants, conditional on a minimal-positivity/nonvanishing condition.

## 1. Exact simplification of the upstream zero extractor

Let

\[
L=\log C,
\qquad
z=\frac{L\tau}{2\pi}.
\]

For a real reversal-even coefficient vector

\[
u=(u_{-N},\ldots,u_N),\]

the upstream `extract_zeros` routine reconstructs

\[
F_{\rm even}(\tau)
=\frac1{\sqrt L}\Re\left[
 e^{i\tau L/2}
 \sum_{k=-N}^{N}u_k
 \frac{e^{-i\tau L}-1}{i(2\pi k/L-\tau)}
\right],
\]
with removable continuation when the denominator vanishes.

Since

\[
\tau L=2\pi z
\]

and

\[
e^{i\pi z}(e^{-2\pi i z}-1)=-2i\sin(\pi z),\]

we obtain, away from the removable integer points,

\[
\begin{aligned}
F_{\rm even}(\tau)
&=-\frac{\sqrt L}{\pi}\sin(\pi z)
  \sum_{k=-N}^{N}\frac{u_k}{k-z}\\
&=\frac{\sqrt L}{\pi}\sin(\pi z)
  \sum_{k=-N}^{N}\frac{u_k}{z-k}.
\end{aligned}
\]

Define, as in note 015,

\[
\boxed{
R_u(z):=\sum_{k=-N}^{N}\frac{u_k}{z-k}.
}
\]

Then the exact identity is

\[
\boxed{
F_{\rm even}(\tau)
=\frac{\sqrt L}{\pi}
\sin(\pi z)R_u(z),
\qquad
z=\frac{L\tau}{2\pi}.
}
\]

Both sides extend through the integer points by removable continuation, so this is an identity of the corresponding real-analytic finite test functions.

## 2. Therefore the extracted finite zeros are the barycentric poles

Write

\[
R_u(z)=\frac{P_u(z)}{D_N(z)},
\qquad
D_N(z)=\prod_{k=-N}^{N}(z-k).
\]

The factor `sin(pi z)` cancels the poles of `R_u` at the integer grid. Consequently every noninteger zero of `F_even` is exactly a zero of `P_u`.

The Schur barycentric rational interpolant is

\[
r_u(z)=\frac{S_u(z)}{R_u(z)},
\qquad
S_u(z)=\sum_{k=-N}^{N}\frac{u_k\Phi_C(k)}{z-k}.
\]

Thus, whenever there is no simultaneous cancellation of numerator and denominator,

\[
\boxed{
\text{noninteger roots of }F_{\rm even}
\iff
P_u(z)=0
\iff
\text{finite poles of }r_u.
}
\]

For the even Schur normal, `P_u` is even and `r_u` is odd. In the squared coordinate

\[
x=z^2,
\]

write

\[
P_u(z)=\widehat P_N(x),
\qquad
r_u(z)=z\,\frac{\widehat Q_{N-1}(x)}{\widehat P_N(x)}.
\]

The squared-grid rational interpolant of note 019 is therefore

\[
\boxed{
\rho_N(x):=\sqrt{x}\,r_u(\sqrt{x})
=x\frac{\widehat Q_{N-1}(x)}{\widehat P_N(x)}.
}
\]

Hence the positive finite zero approximants in the `z` coordinate are exactly the square roots of the positive poles of `rho_N`.

This explains why the independently computed Schur-rational pole diagnostics reproduce the same scaled Riemann zeros that the upstream ground-state Fourier extractor reports.

## 3. Numerical sanity check at C=100

With

\[
z_\gamma=\frac{\log 100}{2\pi}\gamma,
\]

the first zeta ordinate maps to

\[
z_{\gamma_1}=10.359843236753421949909204513998895\ldots.
\]

The `N=12` Schur-rational diagnostic gives its first positive pole

\[
10.359843236753421949909204513998866\ldots,
\]

agreeing through roughly 31 decimal places. This agreement is now understood algebraically: the two computations are evaluating roots of the same finite denominator/test function, not two unrelated approximations.

The pole-root computation itself is still a midpoint diagnostic; the identity in Sections 1--2 is exact.

## 4. Critical Schur downdate on the squared grid

Let

\[
x_k=k^2,
\qquad k=0,\ldots,N,
\]

and let `L_N(G_C)` be the ordinary confluent Loewner matrix of note 019. Write it in endpoint block form

\[
L_N=
\begin{pmatrix}
B&b\\
b^T&d
\end{pmatrix},
\qquad B=L_{N-1}>0.
\]

Its last Schur pivot is

\[
\sigma_N=d-b^TB^{-1}b.
\]

Replace only the prescribed endpoint derivative by the critical value

\[
\boxed{
d_*:=d-\sigma_N=b^TB^{-1}b.
}
\]

The resulting boundary Pick matrix is

\[
M_*=
\begin{pmatrix}
B&b\\
b^T&b^TB^{-1}b
\end{pmatrix}.
\]

It is positive semidefinite of rank `N` and has null vector

\[
\boxed{
w_*=
\binom{-B^{-1}b}{1}.
}
\]

This is exactly the squared-coordinate Schur normal.

## 5. Minimal positivity if the Schur normal has no zero component

Assume every component of `w_*` is nonzero. Then `M_*` is minimally positive in Sarason's sense.

Indeed, if `D>=0` is any nonzero diagonal matrix, then

\[
w_*^T(M_*-D)w_*
=-w_*^TDw_*<0,
\]

so `M_*` cannot majorize a nonzero positive semidefinite diagonal matrix.

Agler--Young's boundary Nevanlinna--Pick theorem states that a boundary Pick problem is solvable exactly when its Pick matrix is positive definite or minimally positive, and is determinate exactly in the minimally-positive case. Therefore, under the nonvanishing hypothesis, the critical data have a unique Pick-class solution, rational of degree at most `rank M_*=N`.

## 6. Identification with the Schur barycentric interpolant

The squared Schur barycentric function `rho_N` already satisfies

\[
\rho_N(x_k)=G_C(x_k),
\qquad 0\le k\le N,
\]

and

\[
\rho_N'(x_k)=G_C'(x_k),
\qquad 0\le k<N,
\]

while its endpoint derivative is precisely

\[
\rho_N'(N^2)=G_C'(N^2)-\sigma_N=d_*.
\]

Moreover

\[
\rho_N(x)=x\frac{\widehat Q_{N-1}(x)}{\widehat P_N(x)}
\]

has rational degree at most `N`.

The unique Pick solution supplied by the minimally-positive problem also has degree at most `N`. Two rational functions of degree at most `N` satisfying the same `N+1` value conditions and `N+1` derivative conditions have a difference whose numerator has degree at most `2N` but at least `2N+2` zeros counted with multiplicity. Hence they coincide.

Thus, subject to the nonvanishing hypothesis,

\[
\boxed{
\rho_N\in\mathcal P.
}
\]

For a nonconstant rational Pick function, every real-axis pole is simple with negative residue. Therefore all finite poles of `rho_N` are real; equivalently, all noninteger roots of the finite `F_even` test function are real.

This upgrades the previously observed `real poles + negative residues` pattern from a numerical signature to a finite-dimensional theorem **whenever the critical Pick matrix is minimally positive**.

## 7. What remains unresolved

This does **not** prove RH. Two gaps remain qualitatively different.

### Finite structural gap

For a theorem valid at every level, one must rule out zero components of the critical Schur normal (or otherwise prove minimal positivity / Pick membership by a different argument).

A useful equivalent formulation is

\[
(M_*\text{ minimally positive})
\Longleftarrow
(M^{-1}e_N)_j\ne0\quad\text{for every }j,
\]

where `M=L_N(G_C)>0` is the pre-downdate matrix.

### Infinite convergence gap

Even if every finite approximant is rational Pick and hence has only real poles, RH follows only after proving that these poles converge, with the correct multiplicities and without spectral pollution, to the poles associated with the completed zeta logarithmic derivative / zeros of `xi`.

The public `connes-cvs` computations show spectacular numerical convergence, but this bridge is not presently a theorem.

## 8. New main target: compactness in the Pick class

The finite formulation suggests replacing raw eigenvector compactness by rational-Pick compactness.

For suitably normalized Pick functions, Nevanlinna representations give a normal-family framework. A possible program is:

1. prove the critical `rho_N` are Pick functions for all `N`;
2. choose a normalization that yields local-uniform compactness in the upper half-plane;
3. identify every subsequential limit with the completed-log-derivative target (or a uniquely normalized representative of the squared-node gauge class);
4. prove convergence of the discrete pole measures with no mass escaping to finite nonreal locations;
5. conclude that the target pole set is real.

Step 3 is the hard part. Interpolation only on the sparse squared grid does not by itself identify an analytic limit.

## 9. Gauge-class warning

The squared-grid jet data do not uniquely determine an analytic source. The entire function

\[
\boxed{
V(x)=\frac{x\sin^2(\pi\sqrt{x})}{\pi^2}
}
\]

has a double zero at every `x=k^2`, including zero. Hence

\[
G_C(x)\mapsto G_C(x)+V(x)H(x)
\]

for arbitrary analytic `H` leaves every value and first derivative on the squared grid unchanged, and therefore leaves every finite confluent Loewner matrix unchanged.

Thus the correct global question is not whether the particular representative `G_C` is Pick on the whole positive axis; note 019 already found evidence that it is not. The stronger and more natural question is whether the **jet-equivalence class** contains a suitably normalized Pick representative, and whether the finite `rho_N` converge to a canonical representative of that class.

This gauge freedom must be fixed by additional analytic/growth/asymptotic information before a limit-identification argument can work.
