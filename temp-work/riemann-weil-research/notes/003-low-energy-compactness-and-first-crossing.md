# Low-energy compactness and first-crossing reduction

Status: rigorous route sketch with clearly marked remaining gaps. The functional-analytic ingredients below are standard/log-Laplacian results; adapting them to the Weil form only uses bounded-form perturbations on each fixed ambient window.

## 1. Fixed-window Weil form as logarithmic energy plus bounded perturbation

For real test functions supported in a fixed ambient interval `[-Lbar, Lbar]`, write

\[
F(t)=\int_{\mathbb R} f(x)e^{itx}\,dx.
\]

The geometric Weil form has archimedean symbol

\[
a(t)=\operatorname{Re}\psi\!\left(\frac14+\frac{it}{2}\right)-\log\pi,
\]

plus finitely many prime-power cosine terms (only `log n < 2 Lbar`) and the finite-rank pole contribution.

The digamma asymptotic gives

\[
a(t)=\log |t|-\log(2\pi)+O(t^{-2})\qquad (|t|\to\infty),
\]

while `a(t)` is finite on compact frequency intervals. Hence the archimedean form has the same form domain as a standard logarithmic Fourier energy, for example

\[
\mathcal E_{\log}(f)=\frac1{2\pi}\int_{\mathbb R}\log(e+|t|)|F(t)|^2\,dt.
\]

On a fixed ambient window:

- every prime-power cosine multiplier is bounded on `L2`;
- equivalently in physical space it is a finite translation/shift term;
- the pole term is finite rank and bounded because `e^{\pm x/2}` is bounded on `[-Lbar,Lbar]`.

Therefore

\[
Q(f)=\mathcal E_{\log}(f)+B_{Lbar}(f,f)
\]

with `B_{Lbar}` bounded on `L2`. In particular there is a constant `C(Lbar)` such that

\[
\mathcal E_{\log}(f)-C(Lbar)\|f\|_2^2
\le Q(f)
\le \mathcal E_{\log}(f)+C(Lbar)\|f\|_2^2.
\]

This does **not** prove positivity. It identifies the correct closed form domain and transfers compactness from the logarithmic energy space.

Relevant literature:

- H. Chen and T. Weth, *The Dirichlet Problem for the Logarithmic Laplacian*, Comm. PDE 44 (2019), arXiv:1710.03416.
- A. Laptev and T. Weth, *Spectral properties of the logarithmic Laplacian*, Analysis and Mathematical Physics 11 (2021).

Both establish compact embedding of the Dirichlet logarithmic energy space into `L2` on bounded/finite-measure domains and discreteness of the associated spectrum.

## 2. Consequence: compact resolvent and attainment of the Weil window infimum

Let `H_L` be the logarithmic form domain of functions vanishing outside `[-L,L]`. The compact embedding

\[
H_L\hookrightarrow L^2([-L,L])
\]

survives adding the bounded form `B_L`.

Therefore the self-adjoint operator associated with `Q` on a fixed window has compact resolvent. In particular

\[
\lambda^*(L)=\inf_{\substack{f\in H_L\\ \|f\|_2=1}}Q(f)
\]

is attained by at least one normalized ground state, regardless of the sign of `lambda*(L)`.

This is a useful structural fact: a hypothetical first failure of Weil positivity is represented by an actual zero eigenfunction, not merely a minimizing sequence escaping to fine scales.

## 3. Boundary Hardy inequality gives a quantitative anti-concentration lemma

Chen--Weth prove for a bounded Lipschitz domain `Omega` (Proposition 6.1 in arXiv:1710.03416v6) that

\[
\int_\Omega |u(x)|^2\log\frac1{\rho(x)}\,dx
\le C_\Omega\bigl(\mathbf b(u,\Omega)+\|u\|_2^2\bigr),
\]

where `rho(x)=dist(x,partial Omega)` and `b` is the local logarithmic nonlocal energy. The same logarithmic boundary Hardy structure is developed more generally by Dyda--Jarohs--Sk for the logarithmic p-Laplacian (arXiv:2411.11181).

Since the Weil form controls the logarithmic energy up to a bounded `L2` perturbation, every normalized low-Weil-energy sublevel

\[
\mathcal K_E(L)=\{f\in H_L:\|f\|_2=1,\ Q(f)\le E\}
\]

has uniformly bounded logarithmic energy. Hence for the boundary strip

\[
S_\delta=\{x\in[-L,L]:\operatorname{dist}(x,\{\pm L\})<\delta\}
\]

one obtains, for sufficiently small `delta`,

\[
\sup_{f\in\mathcal K_E(L)}\int_{S_\delta}|f(x)|^2\,dx
\le
\frac{C(L)(E+C(L))}{\log(1/\delta)}.
\]

The exact constant is not important yet; the robust feature is the logarithmic decay.

This is also consistent with Beckner/Price logarithmic and local uncertainty principles: concentrating a fixed amount of L2 mass into a spatial interval of width `delta` forces logarithmic Fourier energy of order `log(1/delta)`.

## 4. Repairing the operator-norm obstruction

Let `a=2L-delta` and consider the almost-full-width shift overlap

\[
g_f(a)=\int f(x)\overline{f(x+a)}\,dx.
\]

Only a boundary strip of width `delta` contributes. Cauchy--Schwarz gives

\[
|g_f(2L-\delta)|
\le
\Bigl(\int_{-L}^{-L+\delta}|f|^2\Bigr)^{1/2}
\Bigl(\int_{L-\delta}^{L}|f|^2\Bigr)^{1/2}.
\]

Therefore on a fixed low-energy sublevel,

\[
\sup_{f\in\mathcal K_E(L)}|g_f(2L-\delta)|
\lesssim_{L,E}\frac1{\log(1/\delta)}\to0.
\]

This is the precise way around Note 002:

- on the full `L2` unit sphere the near-edge translation has operator norm one;
- on bounded logarithmic-energy / low-Weil-energy sets, its quadratic contribution vanishes uniformly.

So strong-but-not-norm continuity is not fatal once the correct compact energy sublevel is used.

## 5. `lambda*(L)` is monotone and should be continuous

Monotonicity is immediate from nested windows:

\[
L_1<L_2\implies H_{L_1}\subset H_{L_2}
\implies \lambda^*(L_2)\le\lambda^*(L_1).
\]

A standard compact-form argument gives continuity.

### Left continuity

If `L_j ↑ L`, smooth compactly supported functions strictly inside `(-L,L)` are dense in `H_L` in the logarithmic form norm. Approximate a ground state at `L` by such a function; its support eventually lies in `[-L_j,L_j]`. This yields

\[
\limsup_j\lambda^*(L_j)\le\lambda^*(L),
\]

while monotonicity gives the reverse inequality.

### Right continuity

If `L_j ↓ L`, choose normalized ground states `f_j` at `L_j`. On a common ambient interval the bounded-perturbation estimate gives a uniform logarithmic-energy bound. Compact embedding gives a strongly `L2`-convergent subsequence. The limit is supported in `[-L,L]`; closed-form lower semicontinuity gives

\[
\lambda^*(L)\le Q(f)\le\liminf_j\lambda^*(L_j).
\]

Monotonicity again supplies the reverse inequality.

A fully polished proof should explicitly fix one ambient window and write the common closed form there, but no new analytic ingredient appears necessary.

## 6. First-crossing reduction for a hypothetical RH counterexample

Marcus Chuk's 2026 compact-window certificate proves strict Weil positivity through `L=0.8` (support length `1.6`). If RH is false, Weil's criterion supplies some compactly supported admissible test function with negative quadratic form, hence `lambda*(L1)<0` for some finite `L1`.

Assuming the continuity argument above is written out, there is then a first critical radius

\[
L_c=\inf\{L:\lambda^*(L)\le0\}>0.8
\]

with

\[
\lambda^*(L_c)=0.
\]

Compact resolvent gives an actual normalized zero mode `f_c`:

\[
Q(f_c)=0,\qquad \operatorname{supp}f_c\subset[-L_c,L_c].
\]

Moreover `f_c` cannot be supported in any strictly smaller symmetric window, otherwise positivity would already fail before `L_c`.

Because the Weil form commutes with reflection, even/odd sectors decouple. At the first crossing the form is nonnegative on the whole critical window, so any nonzero parity component of a zero mode is itself a zero mode. Thus a hypothetical failure can be reduced to an even or odd critical zero eigenfunction touching the critical support radius.

This is a much sharper target than searching arbitrary negative test functions.

## 7. Important correction to Note 001

Note 001 observed that a rough test function with nonzero endpoint trace can produce a first-order kink when a new prime-power shift enters. That remains algebraically true for sufficiently regular functions with nonzero boundary trace.

However, it should **not** be assumed for a true minimizing eigenfunction. The Dirichlet logarithmic Laplacian has very weak but nontrivial boundary decay, and recent work proves the optimal scale `~ (log(1/rho))^{-1/2}` for bounded-source Dirichlet problems. Whether the full Weil ground-state equation satisfies the hypotheses needed to import that pointwise boundary law is not yet proved here.

Therefore:

- do not use the endpoint-kink heuristic as a property of `lambda*(L)`;
- the rigorous statement currently available is the uniform `1/log(1/delta)` overlap bound on low-energy sets;
- obtaining stronger boundary regularity for the **specific Weil operator** is now an explicit open subproblem.

## 8. What this does and does not buy us

Established/strongly supported:

1. fixed-window Weil form = logarithmic closed form + bounded perturbation;
2. compactness/attainment of the ground state;
3. quantitative boundary-layer anti-concentration on low-energy sublevels;
4. recovery of uniform near-threshold form continuity despite operator-norm failure;
5. a plausible standard proof of continuity of `lambda*(L)`;
6. reduction of any RH failure to a critical zero eigenmode.

Still missing:

- a sign or differential inequality preventing the critical zero mode;
- a relative estimate of the form `dangerous perturbation <= o(1) * Q` near zero energy;
- pointwise boundary regularity for eigenfunctions of the full Weil operator;
- a mechanism coupling prime arithmetic strongly enough to rule out zero crossings.

The next useful attack is the critical zero-mode equation itself, not another generic finite-dimensional eigenvalue scan.
