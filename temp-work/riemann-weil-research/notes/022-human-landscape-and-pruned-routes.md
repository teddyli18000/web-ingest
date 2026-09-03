# 022 — Current human landscape and pruned routes

Date: 2026-09-03

Status: literature map and research triage; no RH claim.

## Bottom line

Several directions explored earlier in this workspace are already special cases of substantially more developed human work. They should not be pursued as novel proof routes. The remaining workspace effort should focus only on cross-framework statements not located in the public literature.

## 1. Box/triangle tests and prime-threshold dynamics are known

Suzuki's 2023 screw-function paper proves the pointwise criterion

\[
\mathrm{RH}\iff \Psi(t)\ge 0\quad\text{for every }t\in\mathbb R,
\]

and identifies

\[
\Psi(t)=W(\Delta_t)=W(R_t*\widetilde R_t),
\]

where `R_t` is the rectangular box and `Delta_t` its triangular autocorrelation.

Reference: Masatoshi Suzuki, *Aspects of the screw function corresponding to the Riemann zeta-function*, J. London Math. Soc. 108 (2023), arXiv:2206.03682.

Therefore our early box-function threshold calculations are a local rederivation of a known one-parameter RH-equivalent test family. Keep them only as sanity checks and normalization diagnostics.

## 2. Prime-power checkpoint/no-crossing analysis is already highly developed

Rainer Andreas Mittermeier's August 2026 checkpoint series takes Suzuki's pointwise criterion much further:

- one constrained minimum per interval between consecutive prime powers;
- directed-rounding certification of every prime-power interval through `q = 10^10`;
- an exact active-event reserve `V_q = C_q - J_q`;
- service-clock/recovery-witness reduction;
- unconditional exclusion of a terminal active episode.

The surviving infinite-tail problem is an RH-independent proof

\[
\boxed{J_q\le C_q}
\]

at every recovery witness.

References: Zenodo records 21859280, 22076060, 22076071/21979513, 22076079, 22076088.

Consequence for this workspace: do **not** present prime-threshold scalar dynamics, checkpoint convexity, no-crossing, or recovery reductions as new ideas. Any future prime-threshold calculation must explicitly explain what it adds beyond this series.

## 3. Generic moment determinacy is not a shortcut

Suzuki 2023 also gives an RH-equivalent Stieltjes/Hankel moment formulation using

\[
\mu_n=\frac14\int_0^\infty e^{-t/2}\Psi(t)t^n\,dt,
\]

with positivity of two Hankel determinant families.

Dyukarev's 2026 Hamburger criterion for matrix Nevanlinna–Pick interpolation (arXiv:2608.23004) is relevant general interpolation theory, but it cannot simply be pasted onto our real-boundary confluent squared-grid data without verifying the boundary-node and derivative-data hypotheses. More importantly, a generic moment-determinacy reformulation would duplicate an existing RH-equivalent moment route unless it identifies a new finite-CvS object.

## 4. The prolate proxy / generic Feshbach bridge has already been audited deeply

The public repository `LeonardSEO/semilocal-weil-proxy-bridge` carries a detailed 2026 investigation of the prolate-proxy bridge. It proves energy-to-angle estimates, near-radical fixed-index upper bounds, parity decompositions, exact Feshbach reductions, and high-energy inverse-moment control.

Its remaining quantities are the bottom/middle spectral masses, schematically

\[
\frac{\|E_0w_\lambda\|^2}{(d_{\lambda,+}-\mu_\lambda)^2}+X_{\mathrm{mid},\lambda},
\]

plus eventual simple-even spectral separation. The project classifies the current generic proxy mechanism as strategically exhausted, not disproved.

Consequence: do not re-prove generic residual/gap or generic rank-one Feshbach estimates. Our finite Schur–Feshbach identities are useful only if they exploit the special CvS/Loewner structure beyond those generic facts.

## 5. Current CvS/CCM finite spectral work

Connes–van Suijlekom and Connes–Consani–Moscovici prove that the relevant finite spectral approximants have real zeros under the finite simple-ground-state hypotheses. The unresolved bridge is convergence to the actual zeta-zero spectrum as the cutoff grows.

Akiva Groskin's 2026 `connes-cvs` work gives high-precision Galerkin experiments and an exact finite Guinand–Weil dictionary with cutoff/tail certification. It studies zero locations and extremely small finite eigenvalues. A search of the public repository and current web literature did not locate a study of the **residues / spectral weights of the Schur barycentric rational approximants across the cutoff**.

References: arXiv:2511.23257, arXiv:2511.22755, arXiv:2605.20224, arXiv:2607.02828.

## 6. Suzuki's Zeta-string gives a natural spectral-measure target

Under RH, Suzuki writes the Zeta-string Titchmarsh–Weyl function as

\[
q_\xi(y)=\frac{i}{\sqrt y}\frac{\xi'}{\xi}\left(\frac12-i\sqrt y\right)
=\sum_{\gamma>0}\frac{2}{\gamma^2-y}.
\]

Thus the limiting Stieltjes spectral measure has an atom of mass `2` at every `gamma^2` (multiplicity included in the zero sum).

Our finite odd Schur rational has the exploratory Pick form

\[
r_{c,N}(z)=a_0z+\sum_j\frac{2c_{j,c,N}z}{t_{j,c,N}^2-z^2},
\qquad c_{j,c,N}>0,
\]

and

\[
\rho_{c,N}(x)=\frac{r_{c,N}(\sqrt x)}{\sqrt x}
\]

has mass `2 c_{j,c,N}` at `t_{j,c,N}^2`.

Put

\[
a_c=\frac{\log c}{2\pi}.
\]

The finite poles satisfy numerically `t_{j,c,N} ~ a_c gamma_j`. The physically rescaled candidate

\[
\widetilde r_{c,N}(w)=a_c r_{c,N}(a_c w)
\]

moves those poles back to `gamma_j` while preserving the pole residue `-c_{j,c,N}`. Equivalently,

\[
a_c^2\rho_{c,N}(a_c^2 y)
\]

has mass `2c_{j,c,N}` at the rescaled pole.

Therefore the natural spectral-measure convergence question is

\[
\boxed{c_{j,c,N(c)}\longrightarrow 1?}
\]

for fixed `j` after resolving the finite-band limit. The amplitude-free first diagnostic is

\[
\boxed{c_{j,c,N}/c_{1,c,N}\longrightarrow1?}
\]

This is strictly stronger information than pole-location convergence and is the first currently unpruned experimental target in this workspace.

## 7. Research policy after this survey

Before opening a new line:

1. search Suzuki / Connes / CCM / CvS / Groskin and current 2026 literature;
2. check whether the proposed scalar is only a renamed screw checkpoint, moment determinant, or Feshbach inverse moment;
3. if it is known, record the identification and stop;
4. only run computation when it distinguishes a genuinely additional invariant.

Current active target: finite-CvS Schur/Weyl **spectral weight** convergence, with cutoff and band convergence separated carefully.
