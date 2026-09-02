# Global CvS Loewner source and the exact Chuk-symbol bridge

Status: exact algebraic reduction, with a numerical guard planned separately; **no RH claim**.

This note closes a technical gap in `015-loewner-barycentric-hermite-reformulation.md` and `016-hermite-error-factorization.md`: the Loewner source used there can be chosen explicitly and independently of the Galerkin level `N`. It is not merely a finite interpolation polynomial fitted after the matrix is known.

## 1. Setup

Let

\[
C=e^L>1,
\qquad a=\frac{\pi}{L},
\qquad c_k=2k+\frac12.
\]

Prime-power sums below are over `q=p^j<C`. If `q=C` happens to be a prime power, its direct CvS matrix contribution is identically zero because its reduced position is one; omitting it from both source terms is therefore harmless.

The cutoff-free CvS matrix is

\[
Q_C=W_{02}-W_R-W_p.
\]

For integer nodes `m,n`, the pinned verifier uses

\[
(W_{02})_{mn}
=32L\sinh^2(L/4)
\frac{L^2-16\pi^2mn}
{(L^2+16\pi^2m^2)(L^2+16\pi^2n^2)},
\]

\[
(W_R)_{mn}
=\frac{S_L(m)-S_L(n)}{\pi(n-m)}\quad(m\ne n),
\]

and

\[
(W_p)_{mn}
=\sum_{q<C}\frac{\Lambda(q)}{\sqrt q}
\frac{\sin(2\pi m\log q/L)-\sin(2\pi n\log q/L)}{\pi(n-m)}
\quad(m\ne n).
\]

The diagonal formulas contain the additional archimedean and prime factors recorded below.

## 2. Explicit pieces

Define

\[
G_{02,L}(z)
=32L\sinh^2(L/4)\,
\frac{z}{L^2+16\pi^2z^2}.
\]

Then directly

\[
\frac{G_{02,L}(m)-G_{02,L}(n)}{m-n}=(W_{02})_{mn}
\]
for `m != n`, and the derivative gives the diagonal.

Define the odd archimedean off-diagonal source

\[
S_L(z)=
\frac{
\psi(\frac14+iaz)-\psi(\frac14-iaz)
}{4i}
-
\frac{2\pi z}{L}
\sum_{k\ge0}
\frac{e^{-c_kL}}
{c_k^2+(2\pi z/L)^2}.
\]

For real integer `n`, this is exactly the `S[n]` of the cutoff-free Arb verifier. Hence

\[
\frac{S_L(m)/\pi-S_L(n)/\pi}{m-n}=-(W_R)_{mn}
\qquad(m\ne n).
\]

Define the prime off-diagonal source

\[
P_C(z)
=\frac1\pi
\sum_{q<C}
\frac{\Lambda(q)}{\sqrt q}
\sin\!\left(\frac{2\pi z\log q}{L}\right).
\]

Then

\[
\frac{P_C(m)-P_C(n)}{m-n}=-(W_p)_{mn}
\qquad(m\ne n).
\]

So the only remaining issue is to make the diagonal derivatives agree *without changing any integer-node values*.

## 3. Exact diagonal correction

Introduce

\[
\boxed{
B_C(z)=
\frac12\left[
\psi\!\left(\frac14+\frac{i\pi z}{L}\right)
+
\psi\!\left(\frac14-\frac{i\pi z}{L}\right)
\right]
-\log\pi
-2\sum_{q<C}\frac{\Lambda(q)}{\sqrt q}
\cos\!\left(\frac{2\pi z\log q}{L}\right).
}
\]

Because `sin(2 pi n)=0` and

\[
\left.\frac{d}{dz}\frac{\sin(2\pi z)}{2\pi}\right|_{z=n}=1,
\]

the gauge term

\[
\frac{\sin(2\pi z)}{2\pi}B_C(z)
\]
changes no off-diagonal divided difference on the integer lattice, but adds exactly `B_C(n)` to every diagonal derivative.

The global source is therefore

\[
\boxed{
\Phi_C(z)=
G_{02,L}(z)
+\frac{S_L(z)}{\pi}
+P_C(z)
+\frac{\sin(2\pi z)}{2\pi}B_C(z).
}
\]

The claim is

\[
\boxed{
(Q_C)_{mn}=
\begin{cases}
\dfrac{\Phi_C(m)-\Phi_C(n)}{m-n},&m\ne n,\\[1.2ex]
\Phi_C'(n),&m=n.
\end{cases}
}
\]

for every pair of integer nodes, independently of `N`.

## 4. Why the archimedean constant collapses to `log pi`

Write, for `w=2 pi n/L`,

\[
G_{CC}(n)=
\sum_{k\ge0}
\frac{e^{-c_kL}w^2}{c_k(c_k^2+w^2)},
\qquad
G_{X1}(n)=
\sum_{k\ge0}
\frac{e^{-c_kL}c_k}{c_k^2+w^2}.
\]

Termwise,

\[
G_{CC}(n)+G_{X1}(n)
=\sum_{k\ge0}\frac{e^{-c_kL}}{c_k},
\]
which no longer depends on `n`.

The elementary sum is

\[
2\sum_{k\ge0}\frac{e^{-c_kL}}{c_k}
=
\log\frac{1+e^{-L/2}}{1-e^{-L/2}}
+2\arctan(e^{-L/2}).
\]

Together with the verifier definitions of `kappa(L)` and `J(L)`, and

\[
\psi(1/4)=-\gamma-\frac\pi2-3\log2,
\]
this gives the exact identity

\[
\boxed{
\kappa(L)+J(L)
+2\sum_{k\ge0}\frac{e^{-c_kL}}{c_k}
+\psi(1/4)=\log\pi.
}
\]

Differentiating `S_L` gives

\[
\frac{S_L'(n)}{\pi}
=\frac{2}{L}X_C(n)+2G_{X1}(n),
\]
where `X_C(n)` is the verifier's `XC[n]`. Therefore

\[
-W_R(n,n)-\frac{S_L'(n)}{\pi}
=
\frac12\left[
\psi\!\left(\frac14+\frac{i\pi n}{L}\right)
+
\psi\!\left(\frac14-\frac{i\pi n}{L}\right)
\right]-\log\pi.
\]

For a prime-power atom with `y=log q`, the derivative of `P_C` at an integer is

\[
2\frac{\Lambda(q)}{\sqrt q}\frac{y}{L}
\cos(2\pi ny/L),
\]
whereas the desired diagonal contribution of `-W_p` is

\[
-2\frac{\Lambda(q)}{\sqrt q}
\left(1-\frac yL\right)
\cos(2\pi ny/L).
\]

Their difference is exactly

\[
-2\frac{\Lambda(q)}{\sqrt q}\cos(2\pi ny/L),
\]
which is the prime part of `B_C(n)`.

Thus the diagonal correction above is exact.

## 5. Exact bridge to Chuk's compact-window symbol

For real `x`,

\[
B_C(x)=
\Re\psi\!\left(\frac14+\frac{i\pi x}{L}\right)-\log\pi
-2\sum_{q<C}\frac{\Lambda(q)}{\sqrt q}
\cos\!\left(\frac{2\pi x\log q}{L}\right).
\]

Set

\[
\ell=\frac L2,
\qquad
t=\frac{2\pi x}{L}.
\]

Then `log q<L=2 ell`, and

\[
\boxed{B_C(x)=\Psi_\ell(t)},
\]

where

\[
\Psi_\ell(t)
=\Re\psi(1/4+it/2)-\log\pi
-2\sum_{\log q<2\ell}\frac{\Lambda(q)}{\sqrt q}\cos(t\log q)
\]

is exactly the compact-window Weil symbol used in Chuk's 2026 formulation.

This identifies the two finite approaches at the level of the **same scalar symbol**, not merely by analogy:

- the CvS finite matrix is a confluent Loewner sampling of `Phi_C` on the integer lattice;
- the gauge term needed to repair its diagonal is precisely Chuk's compact-window symbol after the scale change `ell=L/2`, `t=2 pi x/L`.

## 6. The tempting Pick shortcut is blocked

`Phi_C` is meromorphic, not a Pick/Herglotz function on the upper half-plane. In particular, at

\[
z_0=\frac{iL}{4\pi}
\]

the combined source has a genuine upper-half-plane pole. Direct residue addition of the `G_02`, `S/pi`, and digamma-gauge pieces gives

\[
\boxed{
\operatorname{Res}_{z=z_0}\Phi_C(z)
=\frac{L}{2\pi^2}\sinh^2(L/4)\ne0.
}
\]

The finite prime trigonometric terms are entire and do not remove it.

Therefore a proof of the form

\[
\Phi_C\in\text{Pick class}
\Longrightarrow Q_{\Phi_C}\succeq0
\]

is impossible for this explicit global source.

This does **not** invalidate the finite boundary Nevanlinna--Pick interpretation: when a finite Loewner block is positive, the finite data may admit a Pick interpolant even though the original meromorphic source generating those data is not itself Pick.

## 7. Consequence for the Hermite remainder target

Notes 015--016 are now non-tautological. Their `psi` may be taken to be the explicit, `N`-independent function `Phi_C` above. Hence the last even Schur pivot satisfies

\[
s_N
=\Phi_C'(N)-r_N'(N)
=\sqrt2\,(2N-1)!\,H_N(N).
\]

So the finite positivity problem has become a concrete sign problem for the endpoint rational-Hermite remainder of one explicit meromorphic source:

\[
\boxed{H_N(N)>0.}
\]

The next useful theorem must preserve the **combined** cancellation already built into `Phi_C`. Splitting the pole, archimedean, and prime terms before taking the Hermite remainder is structurally wrong: the Schur-flow experiments show losses of roughly 50--85 decimal orders from such a split.

Promising next targets are:

1. derive a contour/residue formula for `H_N(N)` in terms of the poles of `Phi_C` and the poles/zeros of the rational interpolant denominator;
2. determine whether paired upper/lower imaginary poles yield a signed real contribution after symmetry;
3. express the Chuk symbol `B_C` inside that remainder **after** the cancellation, not as a separate pointwise lower bound;
4. derive the `N -> N+1` Hermite/Schur recursion directly and seek a one-dimensional sign invariant.

No global sign theorem is established here.