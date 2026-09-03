# 023 — Squared-grid boundary-Pick extremal and a falsified direct Weyl identification

Date: 2026-09-03

Status: one conditional exact finite theorem plus exploratory numerical falsification of a natural cross-framework conjecture. **No RH claim.**

## 1. Why this note exists

After the literature survey in note 022, the only useful role for the Schur rational interpolant is to expose structure not already supplied by Suzuki's screw checkpoint theory, the existing CvS zero-location numerics, or generic Feshbach/prolate arguments.

Two questions arose:

1. Can the observed real-pole/real-zero behavior of the Schur rational be explained structurally by boundary Nevanlinna--Pick theory?
2. Is the same rational function already a finite approximation to Suzuki's Zeta-string logarithmic derivative `i xi'/xi`, so that its reciprocal would approximate the 2026 characteristic target `z^2 xi/xi'`?

The answer to (1) is conditionally yes in an exact finite-dimensional sense. The simplest version of (2) is numerically false on band-stable data through `c=100`.

## 2. Work on the squared grid, not directly on the +/- integer compression

Let the combined odd CvS source be `Phi_C` and define

\[
G_C(x)=\sqrt{x}\,\Phi_C(\sqrt{x}).
\]

Note 019 proves the exact congruence

\[
E_N=D_NL_N(G_C)D_N,
\qquad
D_N=\operatorname{diag}(1,\sqrt2,\ldots,\sqrt2),
\]

where `L_N(G_C)` is the ordinary confluent Loewner matrix on

\[
x_k=k^2,\qquad k=0,\ldots,N.
\]

If `sigma_N` is its last Schur pivot and `s_N` is the even CvS pivot,

\[
s_N=2\sigma_N.
\]

This squared-grid reduction is essential. A Schur downdate in the even +/- integer compression is not a diagonal derivative downdate in the full boundary Pick matrix, whereas the last squared-grid Schur step is exactly such a downdate.

## 3. The critical derivative downdate

Write

\[
L_N=
\begin{pmatrix}
B&b\\
b^T&d
\end{pmatrix},
\qquad B=L_{N-1}>0,
\]

and

\[
\sigma_N=d-b^TB^{-1}b>0.
\]

Define

\[
\widetilde L_N=L_N-\sigma_Ne_Ne_N^T
=
\begin{pmatrix}
B&b\\
b^T&b^TB^{-1}b
\end{pmatrix}.
\]

Then

\[
\widetilde L_N\succeq0,
\qquad
\ker \widetilde L_N
=\mathbb C w_N,
\qquad
w_N=\binom{-B^{-1}b}{1}.
\]

The matrix `tilde L_N` is exactly the Pick matrix for the squared-grid boundary data

\[
f(k^2)=G_C(k^2),\qquad 0\le k\le N,
\]

with all interior derivatives unchanged and the last derivative lowered to

\[
f'(N^2)=G_C'(N^2)-\sigma_N.
\]

## 4. Full-support kernel implies minimal positivity

Assume

\[
\boxed{(w_N)_k\ne0\quad\text{for every }k=0,\ldots,N.}
\]

Then `tilde L_N` is minimally positive in the sense of boundary Nevanlinna--Pick interpolation.

Indeed, suppose

\[
\widetilde L_N-D\succeq0
\]

for a nonnegative diagonal matrix `D`. Testing on the kernel vector gives

\[
0\le w_N^*(\widetilde L_N-D)w_N
=-\sum_{k=0}^ND_{kk}|(w_N)_k|^2.
\]

Every summand is nonpositive and every kernel coordinate is nonzero, so `D=0`.

Agler--Young's boundary Nevanlinna--Pick theorem then implies that the boundary interpolation problem is determinate and has a unique real rational Pick solution of degree at most

\[
\operatorname{rank}\widetilde L_N=N.
\]

Reference: Jim Agler and N. J. Young, *Boundary Nevanlinna-Pick interpolation via reduction and augmentation*, Math. Z. 268 (2011), arXiv:0905.4759. Their reduction operation corresponds exactly to Schur complementation of the Pick matrix.

## 5. Identification with the Schur barycentric rational

Let the odd integer-grid Schur rational from notes 015--016 be

\[
r_N(z)=\frac{S_N(z)}{R_N(z)}.
\]

Because the source is odd and the Schur weights are symmetric, `r_N` is odd. Hence

\[
\boxed{\widehat\rho_N(x):=\sqrt{x}\,r_N(\sqrt{x})}
\]

is single-valued rational in `x`.

At every squared node,

\[
\widehat\rho_N(k^2)=k\,r_N(k)=k\Phi_C(k)=G_C(k^2).
\]

For `k<N`,

\[
\begin{aligned}
\widehat\rho_N'(k^2)
&=\frac{r_N(k)+k r_N'(k)}{2k}\\
&=\frac{\Phi_C(k)+k\Phi_C'(k)}{2k}\\
&=G_C'(k^2),
\end{aligned}
\]

with the `k=0` identity obtained by the removable limit. At the endpoint,

\[
G_C'(N^2)-\widehat\rho_N'(N^2)
=\frac12\left(\Phi_C'(N)-r_N'(N)\right)
=\frac{s_N}{2}=\sigma_N.
\]

Thus `widehat rho_N` satisfies exactly the critically downdated boundary data.

It is a barycentric rational function of type at most `(N,N)`. The Agler--Young Pick solution also has degree at most `N`. Two rational functions of type at most `(N,N)`, analytic at the `N+1` nodes, that agree in both value and first derivative at every node must be identical: after cross multiplication their difference numerator has degree at most `2N` but at least `2N+2` zeros counted with multiplicity.

Therefore:

> **Conditional finite boundary-Pick theorem.** If `L_{N-1}(G_C)>0`, `sigma_N>0`, and the one-dimensional critical Schur kernel has full coordinate support, then
> \[
> \boxed{\widehat\rho_N(x)=\sqrt{x}\,r_N(\sqrt{x})}
> \]
> is the unique rational Pick function solving the critically downdated squared-grid Hermite interpolation problem.

This gives a rigorous explanation for the repeated Pick-like finite rational diagnostics, subject only to the explicit full-support hypothesis. It does **not** prove global positivity for all `N` or `C`, and it does not by itself force all squared poles/zeros to be positive rather than merely real.

## 6. Do not confuse two different squared rational functions

There are two natural squared transforms of `r_N`:

\[
\widehat\rho_N(x)=\sqrt{x}\,r_N(\sqrt{x}),
\]

which is the squared-grid boundary-Pick interpolant to `G_C`, and

\[
q_{c,N}(x)=\frac{r_N(\sqrt{x})}{\sqrt{x}},
\]

which was introduced only because Suzuki's Zeta-string Weyl function has the form

\[
q_\xi(x)=\frac{i}{\sqrt{x}}
\frac{\xi'}{\xi}\left(\frac12-i\sqrt{x}\right)
=\sum_{\gamma>0}\frac{2}{\gamma^2-x}
\]

under RH.

The boundary-Pick theorem applies naturally to `widehat rho_N`, not automatically to `q_{c,N}`. Identifying the latter with the Zeta-string Weyl function requires a separate limiting theorem.

## 7. Spectral-weight flow already argues against a naive direct identification

At fixed cutoff the low Schur poles stabilize very rapidly with the band and reproduce the rescaled zeta zeros, but the corresponding positive residue parameters `c_j` do not show a simple approach to `1`, the Zeta-string value.

Examples of band-stable low weights include:

- `c=13`: approximately `(0.113543, 0.243132, 0.097659, 0.243880, ...)`;
- `c=29`: approximately `(0.322533, 0.187890, 0.310992, 0.228731, ...)`;
- `c=67`: approximately `(0.418970, 0.0190924, 0.230117, 0.349054, ...)`;
- `c=100`: approximately `(0.381835, 0.428537, 0.347421, 0.304662, ...)`.

The values reorganize strongly when prime powers enter the cutoff. Thus there is no evidence through `c=100` for the naive coefficientwise limit `c_j -> 1`.

## 8. A stronger falsifier: the reciprocal-characteristic poles

If, after the physical rescaling

\[
a_c=\frac{\log c}{2\pi},
\qquad
\widetilde r_{c,N}(w)=a_c r_{c,N}(a_cw),
\]

the Schur rational really converged to

\[
Q_\xi(w)=i\frac{\xi'}{\xi}\left(\frac12-iw\right),
\]

then the poles of

\[
\frac{w^2}{\widetilde r_{c,N}(w)}
\]

should approach the real zeros of `Xi'(w)` between consecutive zeta zeros.

The experiment `schur_reciprocal_characteristic_probe.py` computes those poles from the numerator of the Schur rational and compares them with high-precision real critical points of `Xi`.

The first `Xi'` critical point is

\[
15.5857085898293423445957\ldots
\]

while the band-stable Schur reciprocal pole is

- `c=13`: `15.074324656150827424...`, error about `0.51138`;
- `c=29`: `16.263701798220652774...`, error about `0.67799`;
- `c=67`: `17.160755752000141546...`, error about `1.57505`;
- `c=100`: `15.978480379938597665...`, error about `0.39277`.

There is no monotone or rapid approach. The same failure appears in the next several critical points.

Crucially this is not merely `N=16` truncation error. For example at `c=100`, the first reciprocal pole is

\[
15.97848037993859766496070275348\ldots\quad(N=12),
\]

and

\[
15.97848037993859766496070275440\ldots\quad(N=16),
\]

while the target remains `15.585708589829...`. At `c=13`, the first three reciprocal poles are likewise already stable from `N=12` to `N=16` while missing the `Xi'` critical points by order-one amounts.

Therefore:

> **Falsified natural conjecture (in the tested regime).** The finite CvS Schur rational, with the obvious physical scaling and no additional nontrivial transform, is not behaving as a direct finite approximation to `i xi'/xi` through `c<=100`.

This does not rule out a different Möbius/gauge transformation, a substantially different simultaneous `(c,N)` limit, or Suzuki's own finite-interval characteristic functions. It does rule out treating the current Schur rational as the Zeta-string Weyl function merely because its poles reproduce zeta-zero locations.

## 9. Why cutoff dependence of the residues is unsurprising

The finite CvS source has the sine-transform form (schematically)

\[
\Phi_C(x)=\frac1\pi\int_0^L
\sin\left(2\pi x\left(1-\frac yL\right)\right)
\mathcal D_C(y)\,dy,
\qquad L=\log C,
\]

with prime, pole, and archimedean contributions.

Under the physical variable `x=Lw/(2pi)` and `s=L-y`,

\[
\boxed{
\Phi_C\left(\frac{Lw}{2\pi}\right)
=\frac1\pi\int_0^L\sin(ws)\,\mathcal D_C(L-s)\,ds.
}
\]

Thus the rescaled source samples a translated arithmetic distribution near the moving cutoff. There is no immediate pointwise source limit equal to a fixed logarithmic derivative. Prime-power threshold changes can strongly reorganize interpolation jets and residues while the extremal denominator zeros remain exceptionally stable.

This gives a structural explanation for the observed split between spectacular pole-location accuracy and unstable spectral weights.

## 10. Research decision

Keep:

1. the exact squared-grid boundary-Pick extremal theorem and its full-support condition;
2. the distinction between pole-location convergence and Weyl/spectral-measure convergence;
3. the Schur--Feshbach static inverse-moment identities of note 021.

Prune:

1. any claim that the current Schur rational is already Suzuki's Zeta-string Weyl function;
2. residue-to-one curve fitting on `c<=100`;
3. reciprocal-characteristic matching to `Xi'` without a new analytic transform.

The next useful task must first identify an analytically justified transform between the CvS Schur/Pick object and Suzuki's finite-interval characteristic/Weyl objects, or else return to a different open gap already isolated by the human literature. More finite zero-location numerics alone are not useful.
