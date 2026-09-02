# Why generic logarithmic compactness does not scale to an RH proof

Status: abstract quantitative lemma explaining why the low-energy compactness idea is useful diagnostically but cannot by itself propagate Weil positivity to large windows.

## 1. Abstract fixed-window model

Let `H` be a Hilbert space with an orthonormal basis `(e_k)` and let

\[
E(f)=\sum_k w_k|\langle f,e_k\rangle|^2,
\qquad w_k\uparrow\infty,
\]

be a positive closed form. For the logarithmic-order source model,

\[
w_k\asymp\log(e+|k|).
\]

Write the fixed-window Weil form schematically as

\[
q(f)=E(f)+b(f,f),
\]

where `b` is represented by a bounded self-adjoint operator with

\[
|b(f,g)|\le M\|f\|\|g\|.
\]

This is the structure behind Notes 003 and 006 after a harmless normalization of the positive logarithmic part.

Let `P_N` project onto modes `|k|<=N`, and suppose the exact finite compression has certified lower bound

\[
q(P_Nf)\ge\mu_N\|P_Nf\|^2,
\qquad \mu_N>0.
\]

The question is whether this finite positive margin plus generic compactness can certify positivity of the full form.

## 2. Any negative direction has bounded logarithmic energy

If `||f||=1` and `q(f)<0`, then

\[
0>q(f)=E(f)+b(f,f)\ge E(f)-M,
\]

so necessarily

\[
\boxed{E(f)<M.}
\]

Thus negative directions, if they exist, lie in a fixed bounded logarithmic-energy set. This is the compactness fact that originally looked promising.

For `R_N=I-P_N`, it gives

\[
\|R_Nf\|^2
\le\frac{E(f)}{w_{N+1}}
<\frac{M}{w_{N+1}}.
\]

Set

\[
r_N=\sqrt{M/w_{N+1}}.
\]

Then every hypothetical normalized negative direction obeys `||R_N f||<r_N`.

## 3. Finite-compression positivity criterion

Because `E` is diagonal in this decomposition,

\[
E(f)=E(P_Nf)+E(R_Nf)
\]

with no cross term. Therefore

\[
\begin{aligned}
q(f)
&=q(P_Nf)+E(R_Nf)
 +2\operatorname{Re}b(P_Nf,R_Nf)+b(R_Nf,R_Nf)\\
&\ge
\mu_N\|P_Nf\|^2
-2M\|P_Nf\|\|R_Nf\|-M\|R_Nf\|^2\\
&\ge
\mu_N(1-r_N^2)-2Mr_N-Mr_N^2.
\end{aligned}
\]

Hence a sufficient finite-dimensional certificate for global positivity is

\[
\boxed{
\mu_N(1-r_N^2)>2Mr_N+Mr_N^2,
\qquad
r_N=\sqrt{M/w_{N+1}}.
}
\]

For example, assuming `0<mu_N<=M`, the simple stronger conditions

\[
r_N\le\frac12,
\qquad
r_N\le\frac{\mu_N}{8M}
\]

are enough. The second condition requires, up to an inessential numerical constant,

\[
\boxed{
w_{N+1}\gtrsim\frac{M^3}{\mu_N^2}.}
\]

## 4. Logarithmic order makes this catastrophically expensive

For the natural logarithmic source energy,

\[
w_N\asymp\log N.
\]

The generic compactness certificate therefore asks for

\[
\boxed{
\log N\gtrsim\frac{M^3}{\mu_N^2},
\qquad
N\gtrsim\exp\!\left(C\frac{M^3}{\mu_N^2}\right).
}
\]

This is already hopeless when the finite positive margin is tiny.

Marcus Chuk's 2026 compact-window work shows that the true profile `lambda*(L)` plunges extremely rapidly; at `L=0.8` it is already of order `10^-17`, and under RH the paper proves an upper bound of the form

\[
\lambda^*(L)\le\exp(-Le^L)
\]

for large `L`.

Even before optimizing constants, inserting a margin on that scale into the generic estimate forces enormous, effectively double-exponential resolution. This is the same qualitative obstruction seen from a different angle in Chuk's pointwise-envelope barrier.

## 5. Interpretation

This kills a tempting route:

> `bounded perturbation + compact logarithmic embedding + increasingly large Fourier matrices` is not, by itself, a plausible all-window proof of RH.

The compactness argument remains useful for:

- proving attainment and excluding weak escape for bounded-energy sequences;
- distinguishing true compact candidates from truncation artifacts;
- establishing continuity with respect to window/domain parameters;
- reducing hypothetical failure to a critical zero mode.

But a scalable positivity proof needs a substantially stronger property of **actual low eigenfunctions**, not arbitrary members of the form domain.

## 6. What improvement would matter

Suppose the critical eigen-equation bootstraps a low mode to a stronger regularity class giving

\[
\|R_N f\|\lesssim N^{-\alpha}
\]

instead of the generic `1/sqrt(log N)` tail. Then the same bounded-perturbation argument would require only a polynomial power of `1/mu`, rather than `exp(C/mu^2)`.

If an adapted basis captured the boundary singularity and gave exponential coefficient decay for eigenfunctions, the finite-dimensional barrier could improve further.

Therefore the next analytically meaningful questions are:

1. what regularity does the **full Weil zero-mode equation** force beyond the bare logarithmic form domain?
2. can one identify and factor out the universal logarithmic boundary profile?
3. in a boundary-adapted basis, do critical eigenfunctions have substantially faster coefficient decay?

Those are structural questions; merely increasing `N` is not.
