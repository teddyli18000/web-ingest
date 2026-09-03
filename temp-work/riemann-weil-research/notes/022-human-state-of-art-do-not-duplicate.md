# 022 — Human state of the art: what not to reinvent

Status: literature map / research triage. No RH claim.

Date: 2026-09-03

This note is deliberately conservative. Its purpose is to stop the workspace from rediscovering known mathematics and then mistaking a reformulation for progress.

The focused sweep covered the Bombieri → Connes/Consani/Moscovici → Connes/van Suijlekom → Groskin → Suzuki line, adjacent prolate work, Hedenmalm's 2026 operator-pencil formulation, and recent Nevanlinna–Pick determinacy results.

## 1. The decisive human bottleneck is already known

Across the modern truncated-Weil / spectral-triple program, the central missing bridge is not the existence of finite self-adjoint models. Those exist.

The missing theorem is a rigorous infinite-limit identification: finite real-zero / self-adjoint approximants must converge to the actual Riemann Xi zero set (or suitably normalized regularized determinants must converge locally uniformly to Xi).

This is stated explicitly in:

- Connes–Consani–Moscovici, *Zeta Spectral Triples* (2025);
- Connes, *The Riemann Hypothesis: Past, Present and a Letter Through Time* (2026);
- Groskin, *High-Precision Approximation of Riemann Zeros via the Truncated Weil Form* (2026);
- Suzuki, *Weil's quadratic form via the screw function* (2026), in a different finite-interval operator language.

So "construct a finite self-adjoint operator whose spectrum is real and numerically matches zeta zeros" is already occupied territory.

## 2. Bombieri already did much of the compact-window variational setup

Bombieri's 2000/2003 work is the historical baseline for fixed-support Weil minimization.

Do not claim novelty for:

- minimizing the Weil quadratic functional on a fixed support interval;
- existence of fixed-window minimizers;
- studying finite truncations and their eigenvalues/inertia;
- the idea of a first support scale where positivity could fail;
- using variational equations for the extremizer;
- interpreting negative finite-dimensional inertia in terms of off-line zeros (under the corresponding hypotheses).

Any new compact-window argument must be stated relative to Bombieri, not as if the variational problem began in 2025–2026.

## 3. CvS already has divided-difference / interpolation structure

Connes–van Suijlekom, *Quadratic Forms, Real Zeros and Echoes of the Spectral Action* (2025), proves the finite-to-continuum real-zero theorem used by the later program.

Essential theorem:

If the convolution quadratic form defines a lower-bounded self-adjoint operator whose lowest spectral value is simple and isolated with an even eigenfunction, then the Fourier transform of that ground eigenfunction has only real zeros.

Important correction to this workspace:

The paper already develops the relevant finite matrix entries through divided differences and explicitly invokes Hermite's representation of divided differences. It also relates a rank-one determinant expression to ordinary Lagrange interpolation.

Therefore:

- "the matrix has divided-difference structure" is not new;
- "interpolation is hiding in the finite matrix" is not new;
- Hermite/Lagrange vocabulary by itself is not new.

Literal searches of the paper did **not** find:

- Schur complement / Schur pivot;
- Nevanlinna–Pick;
- Loewner (as terminology, although the matrix is of Loewner type);
- barycentric rational interpolation;
- a last-pivot endpoint-derivative remainder formula.

Thus our exact Schur-pivot/barycentric-Hermite endpoint-defect identity remains potentially distinct, but it must be presented as a refinement of an already-known divided-difference/interpolation structure.

## 4. CCM already has the rank-one determinant / resolvent skeleton

*Zeta Spectral Triples* constructs the finite self-adjoint operators

\[
D_{\log}^{(\lambda,N)}
\]

as rank-one perturbations of the scaling operator.

They rigorously prove a determinant identity of the form

\[
\det_{\rm reg}(D_{\log}^{(\lambda,N)}-z)
\propto
\widehat\xi_{\lambda,N}(z),
\]

and the finite spectrum equals the zeros of the corresponding finite Fourier/Mellin transform, hence is real under the required finite hypotheses.

Their explicit rank-one formula contains

\[
\sum_{j=-N}^{N}\frac{\xi_j}{2\pi j/L-z},
\]

which is exactly the same rational denominator structure that appears in this workspace's barycentric formulation.

Therefore:

- "finite zero approximants are poles/zeros of a rational Cauchy transform" is already structurally present;
- "rank-one determinant realizes those zeros spectrally" is already done.

The paper does **not** use Schur/Feshbach/Weyl/Pick/Loewner language explicitly.

The open step remains convergence as \(N,\lambda\to\infty\), plus the required simple-even ground-state statement in the continuum setting.

## 5. Connes 2026 already identifies the prolate proxy bottleneck

Connes' 2026 survey/"Letter to Riemann" introduces the prolate proxy

\[
k_\lambda=\mathcal E(h_\lambda),
\]

where \(h_\lambda\) is a special combination of the even prolate modes of index 0 and 4.

Already known / explicitly stated:

- the finite minimizer's Fourier zeros are real once the CvS hypotheses hold;
- \(\widehat k_\lambda\) has the desired Xi limit behavior;
- the smallest Weil eigenvalue tracks a prolate angular quantity at a dramatic scale;
- the decisive missing approximation is to prove that \(k_\lambda\) is sufficiently close to the true Weil ground state;
- one also needs eventual simple-evenness of the true ground state.

So "try a prolate proxy" is not new. The approximation theorem is the problem.

Our exploratory cutoff-free probe at \(c=13\) found ground-direction overlaps

\[
0.9668,\ 0.9924,\ 0.99763,\ 0.999126
\]

for \(N=4,8,12,16\), respectively. This supports the known proxy picture but is not itself new theory; the Rayleigh excess remains far above the true tiny gap at float64 trial accuracy.

## 6. A separate prolate/Feshbach bridge has already been pushed hard

The public 2026 project *Semilocal Weil proxy bridge* carried the prolate-ground-state comparison much further than this workspace initially realized.

It already proves, among other things:

- compact-resolvent/parity setup;
- energy-to-angle control
  \[
  \|k_\lambda-\langle e_\lambda,k_\lambda\rangle e_\lambda\|^2
  \le \mathcal E_\lambda/g_\lambda;
  \]
- fixed-index exponentially small trial upper bounds;
- an exact bottom-cluster Feshbach/arrowhead reduction;
- a high-energy inverse-moment bound;
- explicit isolation of the unresolved bottom-cluster coupling and middle-band contribution.

Its final classification is "strategically exhausted" for that particular proxy mechanism: the active bottom mass and middle-band inverse moment remain uncontrolled.

Therefore we should **not** spend time re-proving generic energy/gap angle estimates, generic Feshbach reduction, or generic high-energy splitting.

If we revisit this route, it must inject genuinely zeta/Loewner-specific information into those unresolved inverse moments.

## 7. Suzuki already supplies the continuous-function / de Branges operator language

Suzuki 2023/2025 and 2026 provide another complete baseline.

Already available:

- screw-function realization of the Weil form by continuous kernels;
- finite-interval lower-bounded/self-adjoint operators via Friedrichs extension;
- continuity of the lowest eigenvalue in the window parameter;
- small-window positive simple-even ground state;
- deficiency-index \((1,1)\) first-order operators whose self-adjoint extensions have characteristic entire functions with all real zeros;
- a de Branges-space model for the Weil Hilbert space under RH / equivalent formulations;
- a conjectural strong-resolvent / characteristic-function limit to a Hilbert–Pólya object.

Suzuki 2026 does not use Schur, Feshbach, Pick, Loewner, barycentric interpolation, or inverse-moment language explicitly.

Hence translating our finite Schur data into Suzuki's characteristic-function / de Branges language may be useful, but simply observing "there is a de Branges/Herglotz interpretation" is not new.

## 8. Hedenmalm 2026 is a different spectral route, not a solved Hilbert–Pólya model

Hedenmalm proves an exact boundary-value eigenvalue interpretation:

\[
L_{\phi_{00}}D^\times u+\alpha L_{\phi_{00}}u=0
\]

has a nontrivial solution with the prescribed boundary conditions iff \(\Xi(\alpha)=0\).

This is an exact spectral interpretation, but not an unconditional construction of a single self-adjoint Hilbert–Pólya operator.

The missing step is to construct a suitable Hilbert-space sesquilinear form making the operator pair self-adjoint; if such a form exists, reality of the Xi zeros follows.

So "write a differential eigenvalue equation whose eigenvalues are zeta zeros" is also occupied territory and by itself does not solve RH.

## 9. Śliwiński 2026 gives a real limitation on finite spectral matching

For the CCM \(D_{\log}^{(\lambda,N)}\) operators, Śliwiński proves a lower bound on an averaged spectral discrepancy of order

\[
\epsilon(\lambda,N)\ge \frac{1}{4\log\lambda}.
\]

Under a particular scaling this yields an inverse-logarithmic lower scale.

This does not disprove pointwise convergence, but it warns against expecting arbitrary uniform finite-\(\lambda\) spectral accuracy in every metric.

The useful lesson is that the two-parameter limit \((\lambda,N)\to\infty\) and the choice of metric matter. Numerical matching of low zeros can coexist with nontrivial global discrepancy.

## 10. Groskin already closes the naive finite-cutoff numerical loophole

Groskin 2026 provides:

- the exact finite Guinand–Weil dictionary;
- the exact relation of every finite Galerkin quadratic value to a zero sum;
- a totally positive Cauchy–Stieltjes archimedean tail;
- a rigorous two-sided tail budget;
- cutoff-free interval LDL certification.

Hence brute-force large \(T\) quadrature is obsolete for sign questions at tiny scales.

Our earlier \(T=480\) failure was exactly the sort of numerical pathology this literature warns about.

Future finite experiments should use cutoff-free / interval-certified paths whenever sign is load-bearing.

## 11. Compact-window state of the art moved sharply in August 2026

Two very recent results matter directly.

### Chuk 2026

For compact support \([-L,L]\), Chuk gives rigorous two-sided bounds for

\[
\lambda^*(L)=\inf Q(f)/\|f\|_2^2,
\]

including unconditional positivity at \(L=0.8\), and shows extremely rapid Landau–Widom-type decay of the ground scale. He also proves a doubly-exponential barrier for a broad class of pointwise-envelope certificates.

Consequences:

- generic absolute-value domination of the prime comb is not a realistic global proof route;
- structured cancellation / spectral geometry is necessary.

### Alpöge–Furman 2026

Finite compression + rank/trace + Sylvester inertia yields an unconditional result that at least two thirds of nontrivial zeros are simple and on the critical line (with slight numerical improvements in a refined window).

This is a major warning against treating finite compression as merely heuristic: finite inertia arguments already extract strong unconditional zero information. Any new finite-matrix invariant should be compared to this framework.

## 12. Nevanlinna–Pick determinacy is an available general tool, but not yet applied here

Dyukarev 2026 gives a Hamburger-type criterion for determinacy versus indeterminacy of matrix Nevanlinna–Pick interpolation problems.

The focused literature sweep did **not** find an application of infinite boundary Pick determinacy to the squared-node jet data arising from the CvS even-sector matrices.

However, this is only a negative literature-search result, not a novelty proof.

Potentially distinct research question:

> Does the infinite jet data at the squared nodes
> \[
> x_n=n^2
> \]
> determine a unique Pick/Herglotz representative in the relevant growth class, and can the finite Schur rational interpolants be proved to converge to it?

Before pursuing this, the exact hypotheses of infinite boundary NP interpolation and Dyukarev's determinacy criterion must be checked against our confluent real-boundary data.

## 13. What in this workspace still looks potentially non-duplicative

After the literature audit, the following are **not found explicitly in the central papers searched**:

1. **Last Schur pivot as a barycentric multipoint-Hermite endpoint derivative defect**
   \[
   s_N=\psi'(N)-r_N'(N)
   =\sqrt2(2N-1)!H_N(N).
   \]
   CvS already has divided differences and Lagrange/Hermite machinery; our claim, if retained, must be this sharper endpoint-Schur identity, not the general interpolation viewpoint.

2. **Static-to-spectral Schur/Feshbach two-scale bound**
   for
   \[
   f_N(z)=d-z-b^T(B-zI)^{-1}b,
   \]
   connecting
   \[
   f_N(0)=s_N,
   \qquad f_N(\mu_N)=0,
   \qquad -f_N'(0)=\|w_N\|^2,
   \]
   with a quantitative error controlled by \(\mu_N/\delta_N\).

3. **Use of the Schur/Loewner inverse-moment structure to attack the unresolved continuum bottom-cluster/middle-band coupling**, rather than applying generic Feshbach estimates.

4. **Infinite boundary Pick determinacy for the squared-grid CvS jet data**, provided the boundary/confluent hypotheses can be made rigorous.

These should be treated as *candidate* contributions, not claimed novelties until a wider citation/reference search is done.

## 14. Research discipline from now on

Before promoting any new lemma as progress:

1. search Bombieri / CvS / CCM / Connes / Suzuki / Groskin explicitly for the structure;
2. search references and citing papers, not only abstracts;
3. distinguish literal novelty from a change of vocabulary;
4. prefer attacking an author-stated missing theorem over inventing another RH-equivalent reformulation;
5. record negative/strategically exhausted routes just as carefully as positive ones.

The best current targets are therefore not "find another self-adjoint operator" or "find another equivalent positivity criterion." They are quantitative bridges that existing programs explicitly lack.
