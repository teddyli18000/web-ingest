# Bombieri's boundary-escape phenomenon revisited with logarithmic energy

Status: prior-art correction + a rigorous modern diagnostic. This note does **not** prove RH and does not claim that fixed-window minimization or critical-window behavior is new.

## 1. Prior art changes the novelty target

Enrico Bombieri's 2000 memoir, *Remarks on Weil's quadratic functional in the theory of prime numbers, I*, already proves that the Weil quadratic functional attains its minimum on the unit ball of `L2` functions supported in a fixed interval `[-t,t]`, derives a variational equation, studies finite truncations, and performs numerical experiments after inserting a fictitious off-critical-line zero.

In the fake-zero experiment (`rho0 = 0.52 + 3.14 i`), Bombieri reports numerical critical values `t_c^+` and `t_c^-` separating two regimes of the finite truncations. Below the apparent critical radius the negative finite-truncation eigenvalue tends to zero as the truncation grows, and the normalized associated eigenfunctions converge weakly to zero while their `L2` mass concentrates increasingly near the boundary. Above the apparent critical radius the negative eigenvalue tends to a strictly negative value and the eigenfunctions behave differently.

Therefore the following ideas are **not** new by themselves:

- minimizing the Weil form on a compact support window;
- attainment/variational equations;
- even/odd decomposition;
- a critical support scale associated with an off-line zero;
- boundary concentration as a numerical phenomenon in finite truncations.

The potentially useful modern contribution is to reinterpret the boundary-concentration transition using the logarithmic-Laplacian form domain and quantitative logarithmic Hardy/uncertainty estimates that were developed much later.

Primary prior-art reference:

- E. Bombieri, *Remarks on Weil's quadratic functional in the theory of prime numbers, I*, Rend. Lincei Mat. Appl. 11 (2000), 183--233.

## 2. Edge concentration has an exact logarithmic energy price

Let `phi in C_c^infty(0,1)` satisfy `||phi||_2=1`. For a right-edge bump on `[-L,L]`, define

\[
f_\delta(x)=\delta^{-1/2}\,\phi\!\left(\frac{L-x}{\delta}\right),
\qquad 0<\delta\ll1.
\]

Then `||f_delta||_2=1` and its Fourier transform has the scaling form

\[
F_\delta(t)=\delta^{1/2}e^{itL}\Phi(\delta t)
\]

(up to the harmless sign convention in `Phi`). For the positive logarithmic Fourier energy

\[
\mathcal E_{\log}(f)=\frac1{2\pi}\int_{\mathbb R}
\log(e+|t|)|F(t)|^2\,dt,
\]

change variables `u=delta t` to get

\[
\mathcal E_{\log}(f_\delta)
=
\frac1{2\pi}\int_{\mathbb R}
\log\!\left(e+\frac{|u|}{\delta}\right)|\Phi(u)|^2\,du.
\]

Since `phi` is smooth and compactly supported, `Phi` is rapidly decreasing and the logarithmic singularity at `u=0` is integrable. Thus

\[
\boxed{
\mathcal E_{\log}(f_\delta)=\log(1/\delta)+C_\phi+o(1)
}
\qquad(\delta\downarrow0).
\]

So boundary localization on scale `delta` costs exactly logarithmic energy to first order.

A local FFT quadrature performed during this sprint confirms the scaling numerically: for a smooth compact bump, `E_log - log(1/delta)` remains `O(1)` as `delta` decreases. This numerical check is only sanity evidence; the scaling identity above is the proof.

## 3. The `1/log` boundary Hardy bound is order-sharp

Note 003 used the logarithmic boundary Hardy inequality to obtain, on bounded-energy sets,

\[
\int_{S_\delta}|f|^2
\lesssim \frac{E+1}{\log(1/\delta)}.
\]

The edge-bump scaling shows that the logarithmic denominator cannot be generically improved to a power of `delta` using only logarithmic energy.

Indeed, take a fixed normalized interior state `g` and an edge state `f_delta` with disjoint support, and set

\[
h_\delta=\sqrt{1-m_\delta}\,g+\sqrt{m_\delta}\,f_\delta,
\qquad
m_\delta\asymp\frac{E}{\log(1/\delta)}.
\]

Then a boundary strip can contain mass of order `1/log(1/delta)` while the logarithmic energy stays `O(E)` (cross terms can be controlled/removed by choosing separated smooth pieces and working at the level of the positive log-energy norm).

Therefore **boundary Hardy compactness alone cannot prove a no-crossing theorem**. A successful RH argument must use additional structure of the critical Weil eigen-equation, arithmetic shifts, parity, or a sharper relation valid specifically for zero/ground states.

## 4. A rigorous escape-to-high-energy dichotomy

On a fixed interval, the Dirichlet logarithmic energy space embeds compactly into `L2`. Consequently:

> If `f_j` are normalized in `L2`, supported in one fixed compact interval, and `f_j` converges weakly to `0` in `L2`, then their logarithmic energies cannot remain bounded.

Proof: if the log energies were bounded, compact embedding would give a subsequence converging strongly in `L2`. Its weak limit is `0`, forcing strong convergence to `0`, contradicting `||f_j||_2=1`.

A quantitative version follows from boundary Hardy: if essentially all mass is confined to boundary strips of widths `delta_j -> 0`, then

\[
\mathcal E_{\log}(f_j)\gtrsim \log(1/\delta_j).
\]

This gives a clean modern interpretation of Bombieri's reported weak-to-zero / boundary-concentrating finite-truncation eigenvectors: **they necessarily escape every bounded logarithmic-energy set.**

This statement is about the true compact-window logarithmic form domain. It does not by itself identify Bombieri's finite-zero truncations with a uniformly form-bounded approximation, so avoid the stronger unproved claim that every such mode is 'spectral pollution'. What is rigorous is the diagnostic: boundary escape implies divergence of the true logarithmic energy.

## 5. Why this may be computationally useful

A finite-dimensional negative eigenvalue is not enough evidence for an RH counterexample. Along a sequence of increasing truncations, monitor at least:

1. the candidate eigenvalue;
2. `L2` mass in shrinking endpoint strips;
3. an independent approximation of the true positive logarithmic energy `E_log`;
4. convergence of low-frequency observables / the candidate function in `L2`.

Two qualitatively different regimes should then be distinguishable:

- **edge-escape regime:** finite-truncation eigenvalue may look negative or approach zero, but endpoint mass moves to finer scales and `E_log -> infinity`;
- **compact negative-mode regime:** logarithmic energy remains controlled and a subsequence converges strongly in `L2`, leaving a genuine candidate in the true form domain that can be checked directly against the arithmetic Weil form.

This turns Bombieri's qualitative pictures into a falsifiable numerical protocol.

## 6. New research target: exploit the critical eigen-equation

Because generic boundary Hardy control is sharp, the next useful question is not whether arbitrary low-energy functions can concentrate; it is whether a **critical zero eigenfunction of the full Weil operator** can saturate that generic logarithmic concentration mechanism.

The candidate critical equation, schematically on `[-L_c,L_c]`, is

\[
P_{L_c}A(D)f
-\sum_{\log n<2L_c}\frac{\Lambda(n)}{\sqrt n}
\bigl(T_{\log n}+T_{-\log n}\bigr)f
+R_{\mathrm{pole}}f
=0,
\]

where

\[
A(t)=\operatorname{Re}\psi\!\left(\frac14+\frac{it}{2}\right)-\log\pi
\]

and `R_pole` is finite rank after separating parity. This should be compared carefully with Bombieri's exact variational equation before treating this schematic additive representation as canonical.

The hard subproblems are now:

- prove extra regularity for solutions despite the finite shifts being only bounded on `L2`;
- derive a boundary coefficient or trace law for an actual zero mode;
- test whether the arithmetic shift equation is compatible with the sharp `1/sqrt(log(1/rho))` boundary profile;
- derive a contradiction or a constructive negative mode from that compatibility problem.

This is substantially narrower than 'prove Weil positivity for every test function'.

## 7. Current conclusion

The first naive spectral-flow idea was too weak, and the first compactness repair is also not enough on its own. But together with Bombieri's old numerical transition they isolate a concrete, historically motivated analytic problem:

\[
\boxed{
\text{Classify boundary behavior of critical compact-window Weil zero modes.}
}
\]

That is the next line worth spending bot/search/compute budget on.
