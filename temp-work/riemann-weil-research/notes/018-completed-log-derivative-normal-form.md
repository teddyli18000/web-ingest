# Completed-log-derivative normal form of the global CvS source

Status: exact algebraic reformulation; **no RH claim**.

This sharpens `017-global-loewner-source-and-chuk-symbol.md`. The global source can be written almost entirely in terms of a finite-prime approximation to the completed zeta logarithmic derivative. In this form the Chuk symbol is exactly a **functional-equation defect**.

## 1. Critical-line coordinate

Fix

\[
C=e^L>1,
\qquad
s=s_L(z):=\frac12+\frac{2\pi i z}{L}.
\]

Then

\[
1-s=s_L(-z).
\]

Define

\[
P_0(s):=\frac1s+\frac1{s-1}.
\]

## 2. Truncated completed logarithmic derivative

Let

\[
\boxed{
\mathcal L_C(s)
:=P_0(s)
-\frac12\log\pi
+\frac12\psi(s/2)
-\sum_{q<C}\Lambda(q)q^{-s}.
}
\]

The sum is over prime powers. For `Re s>1`, replacing the finite sum by the full von Mangoldt series gives

\[
P_0(s)-\frac12\log\pi+\frac12\psi(s/2)+\frac{\zeta'}{\zeta}(s)
=\frac{\xi'}{\xi}(s),
\]

and the right-hand side supplies the meromorphic continuation.

Thus `L_C` is literally the completed logarithmic derivative with its Euler/von-Mangoldt term cut off at `q<C`.

## 3. Chuk symbol = exact functional-equation defect

From the definition,

\[
\mathcal L_C(s)+\mathcal L_C(1-s)
\]

has the following simplifications:

- `P_0(1-s)=-P_0(s)`, so the pole-factor terms cancel;
- the two `-1/2 log pi` terms sum to `-log pi`;
- the gamma terms give the symmetric digamma average;
- the two prime powers give
  \[
  -\Lambda(q)q^{-1/2}(e^{-it\log q}+e^{it\log q})
  =-2\Lambda(q)q^{-1/2}\cos(t\log q),
  \]
  where `t=2 pi z/L`.

Therefore the analytic function `B_C` of note 017 satisfies the exact identity

\[
\boxed{
B_C(z)=\mathcal L_C(s_L(z))+\mathcal L_C(1-s_L(z)).
}
\]

For real `z`, `1-s=conj(s)`, hence

\[
B_C(z)=2\Re\mathcal L_C(1/2+it).
\]

Under the scale change

\[
\ell=L/2,
\qquad t=2\pi z/L,
\]

this is exactly Chuk's compact-window symbol `Psi_ell(t)`.

The full completed logarithmic derivative obeys, by differentiating `xi(s)=xi(1-s)`,

\[
\boxed{
\frac{\xi'}{\xi}(s)+\frac{\xi'}{\xi}(1-s)=0.
}
\]

Hence `B_C` is precisely the failure of the **finite-prime completed logarithmic derivative** to satisfy the exact functional equation.

On the critical line away from zeros this can also be written as

\[
\boxed{
B_C(z)
=2\Re\left(
-\sum_{q<C}\Lambda(q)q^{-s}
-\frac{\zeta'}{\zeta}(s)
\right),
\qquad s=\frac12+it,
}
\]

where `zeta'/zeta` is understood by meromorphic continuation. This is an identity of the real parts, not a convergent critical-line Euler tail.

## 4. The remaining archimedean correction is a Lerch term

The off-diagonal source in note 017 contains

\[
-\frac{t}{\pi}
\sum_{k\ge0}\frac{e^{-(2k+1/2)L}}{(2k+1/2)^2+t^2}.
\]

Define

\[
\boxed{
\mathcal R_L(s)
:=\frac{e^{-L/2}}2
\sum_{k\ge0}
\frac{e^{-2kL}}{k+s/2}.
}
\]

Equivalently this is a Lerch-transcendent value

\[
\mathcal R_L(s)
=\frac{e^{-L/2}}2\,\Phi(e^{-2L},1,s/2).
\]

For `s=1/2+it`,

\[
\mathcal R_L(s)
=\sum_{k\ge0}
\frac{e^{-(2k+1/2)L}}{2k+1/2+it},
\]
so

\[
\frac{\mathcal R_L(s)-\mathcal R_L(1-s)}{2\pi i}
=-\frac{t}{\pi}
\sum_{k\ge0}
\frac{e^{-(2k+1/2)L}}{(2k+1/2)^2+t^2}.
\]

## 5. Antisymmetric normal form

Define

\[
\boxed{
\mathcal F_C(s)
:=\mathcal L_C(s)
-\cosh(L/2)P_0(s)
+\mathcal R_L(s).
}
\]

Then the non-gauge part of the source from note 017 is exactly

\[
\boxed{
\Phi_C^{\rm base}(z)
=\frac{\mathcal F_C(s)-\mathcal F_C(1-s)}{2\pi i}.
}
\]

The identity follows componentwise:

1. the truncated prime difference produces
   \[
   \frac1\pi\sum_{q<C}\frac{\Lambda(q)}{\sqrt q}
   \sin(t\log q);
   \]
2. the digamma difference produces the odd `S_L/pi` term;
3. the Lerch difference produces the geometric archimedean correction;
4. because
   \[
   1-\cosh(L/2)=-2\sinh^2(L/4),
   \]
   the `P_0` difference gives exactly the rational `W_02` source.

Consequently the **entire global source** has the compact normal form

\[
\boxed{
\Phi_C(z)
=
\frac{\mathcal F_C(s)-\mathcal F_C(1-s)}{2\pi i}
+
\frac{\sin(2\pi z)}{2\pi}
\left[\mathcal L_C(s)+\mathcal L_C(1-s)\right],
\qquad
s=\frac12+\frac{2\pi i z}{L}.
}
\]

The first term is the functional-equation **antisymmetric** part, modified only by the explicit window pole factor and Lerch correction. The second term is the cardinal-Hermite gauge multiplying the functional-equation **symmetric defect**.

At every integer `n`, the gauge value vanishes and its derivative is one. This is exactly why the defect does not affect off-diagonal divided differences but repairs the diagonal confluent data.

## 6. Why the enormous numerical cancellation is now less mysterious

The Schur-flow component experiments decomposed the CvS matrix into pole, gamma/archimedean, and prime pieces and found cancellations of roughly 50--85 decimal orders.

The normal form above shows that these are not three unrelated large terms. They are pieces of one object that is trying to satisfy

\[
\mathcal L(s)+\mathcal L(1-s)=0,
\]

the completed zeta functional equation. Splitting the pieces before forming the symmetric/antisymmetric combinations destroys this structure and therefore exposes enormous intermediate magnitudes.

This does not prove the sign of a Schur pivot, but it gives a structural reason that the **combined** scalar flow can be moderate while its artificial component decomposition is huge.

## 7. Relation to RH and why this is not yet a proof

Put

\[
X_L(z):=\xi\!\left(\frac12+\frac{2\pi i z}{L}\right).
\]

For real `z`, `X_L(z)` is real. A nontrivial zeta zero `rho=beta+i gamma` maps to

\[
z_\rho=\frac{L\gamma}{2\pi}
-\frac{iL(\beta-1/2)}{2\pi}.
\]

Thus RH is exactly the statement that all nontrivial-zero poles of the logarithmic derivative `X_L'/X_L` lie on the real `z` axis.

For a real entire function with only real zeros, the logarithmic derivative has the familiar Nevanlinna/Herglotz sign structure (after the conventional sign and affine normalization). This is closely related to the Pick/Loewner viewpoint, but invoking it here would simply repackage RH, not prove it.

The useful new target remains the finite rational-Hermite remainder:

\[
s_N=\sqrt2(2N-1)!H_N(N).
\]

The normal form says that any proof of `H_N(N)>0` should exploit the symmetric functional-equation defect *after* the truncation/window algebra has been assembled.

## 8. Next theorem target

A productive next step is to insert the boxed normal form into the residue identity

\[
u^TQ_{\Phi_C}u
=\sum_{m=-N}^N\operatorname{Res}_{z=m}\left(\Phi_C(z)R_u(z)^2\right)
\]

for the Schur normal and seek a representation of `H_N(N)` in which

\[
\mathcal L_C(s)+\mathcal L_C(1-s)
\]

appears as one combined quantity.

Two concrete possibilities are:

1. a finite-strip contour formula in which the symmetric defect is integrated against a kernel determined by the Schur rational denominator;
2. an `N -> N+1` Julia/Schur reduction in which the new endpoint derivative defect is expressed directly from the previous defect and one explicitly controlled evaluation of the completed-log-derivative normal form.

No global sign theorem is claimed.