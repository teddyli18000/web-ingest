# Literature audit: Pick compactness is classical; the remaining issue is boundary determinacy

Status: literature-audited structural reduction plus elementary consequences of classical Pick/Herglotz theory. **No RH claim.**

This note corrects the research program after checking the human literature through September 2026. The purpose is to avoid claiming novelty for standard finite-dimensional interpolation machinery and to isolate the genuinely unresolved infinite-limit step.

## 1. What is already classical

Agler--Young, *Boundary Nevanlinna--Pick interpolation via reduction and augmentation* (2009/2011), proves for real boundary nodes with prescribed real values and positive derivatives that:

- the boundary problem is solvable iff the Pick matrix is positive definite or minimally positive;
- it is determinate iff the Pick matrix is minimally positive;
- Julia--Nevanlinna reduction corresponds to Schur complementation of the Pick matrix.

Thus the finite Schur-complement mechanism used in notes 015--020 is not itself a new interpolation theorem. Our application to the CvS/Weil Loewner data may be useful, but the underlying reduction belongs to classical boundary Pick theory.

Chen--Hu (2001) already relates multiple boundary Nevanlinna--Pick interpolation with derivative data to truncated Hamburger moment problems. Dyukarev (2022, 2025, 2026) develops infinite matrix Nevanlinna--Pick determinacy/indeterminacy in terms of rational functions of the first and second kind, Weyl disks/resolvent matrices, and Hamburger-type criteria. Therefore any infinite uniqueness claim for our squared-grid data should first be translated into that existing language rather than reinvented.

A separate literature audit of the Weil/CvS/CCM/Suzuki line found no source that explicitly packages the nested Weil Loewner matrices together with scalar Schur pivots, determinant ratios, Feshbach derivatives/inverse spectral moments, and the barycentric poles equal to the finite zero approximants. However, most of these finite identities are routine consequences of block Gaussian elimination, resolvent identities, and classical rational interpolation. Their value is as a coordinate system for the open convergence problem, not as standalone novelty.

## 2. Pick compactness does not require a new normalization argument

Assume the finite critical rational functions `rho_N` of note 020 are Pick functions. For every fixed `N>=1`, the squared-grid interpolation conditions include the same boundary jet at zero:

\[
\rho_N(0)=w_0,\qquad \rho_N'(0)=v_0>0.
\]

For any Pick function `f` analytic at a real point `x` with `f(x)=w in R` and `f'(x)=v>0`, positivity of the two-point Pick kernel (equivalently the Julia--Caratheodory inequality) gives

\[
\boxed{
|f(z)-w|^2
\le
v\,\frac{|z-x|^2}{\Im z}\,\Im f(z),
\qquad z\in\mathbb C_+.
}
\]

At `x=0`, `z=i`,

\[
|f(i)-w_0|^2\le v_0\Im f(i).
\]

Writing `f(i)=u+iy`, this is

\[
(u-w_0)^2+y^2\le v_0y,
\]

or

\[
\boxed{
(u-w_0)^2+(y-v_0/2)^2\le(v_0/2)^2.
}
\]

Hence every `rho_N(i)` lies in the same compact disk. Since the Pick class becomes a normal family after fixing one interior value in a compact set, the sequence `rho_N` is automatically locally precompact on the upper half-plane.

Therefore note 020, Section 8 step 2 ("choose a normalization that yields local-uniform compactness") is not a genuine obstacle once finite Pick membership is proved. The common boundary jet already supplies the needed normalization/compactness.

## 3. Equivalent Herglotz-measure bound

For a Pick/Herglotz function analytic at zero, write the Nevanlinna representation

\[
f(z)=a+bz+\int_{\mathbb R}
\left(\frac1{t-z}-\frac{t}{1+t^2}\right)d\mu(t),
\qquad b\ge0,\quad \mu\ge0.
\]

When zero is a regular boundary point,

\[
\boxed{
f'(0)=b+\int\frac{d\mu(t)}{t^2}.}
\]

Thus the common derivative `v_0` gives

\[
b_N+\int t^{-2}\,d\mu_N(t)=v_0.
\]

In particular,

\[
\int\frac{d\mu_N(t)}{1+t^2}\le v_0,
\]

so the normalized spectral measures have uniform weighted mass. This is the measure-theoretic version of the same normal-family compactness.

The finite real poles and negative residues of `rho_N` are therefore naturally interpreted as a discrete positive Herglotz spectral measure. The correct infinite object is a limiting real spectral measure, not an entire Pick function.

## 4. Important correction: an entire Pick representative cannot solve the gauge problem

Note 020 observed the jet gauge freedom

\[
G_C(x)\mapsto G_C(x)+V(x)H(x),
\qquad
V(x)=\frac{x\sin^2(\pi\sqrt{x})}{\pi^2},
\]

because `V` has a double zero at every squared node `k^2`.

If one insists that `H` be entire, then the modified representative remains entire. But an entire Pick/Herglotz function on the whole plane is necessarily affine:

\[
\boxed{f(z)=a+bz,\qquad a\in\mathbb R,\ b\ge0.}
\]

This follows immediately from the Herglotz representation: an entire extension has no real singular measure, so only the affine term remains.

Our squared-grid jet data are not affine. Consequently:

\[
\boxed{
\text{There is no non-affine entire Pick representative of the jet gauge class.}
}
\]

Any viable Pick representative must be meromorphic / possess a nontrivial real spectral measure. Thus the real poles observed in the finite rational approximants are not a nuisance to be removed; they are structurally necessary for a nontrivial Pick limit.

The gauge freedom should therefore be written more carefully as allowing a meromorphic/upper-half-plane analytic correction compatible with the double-zero interpolation constraints, not merely an arbitrary entire correction.

## 5. What local-uniform limits actually preserve

Let a subsequence `rho_{N_j}` converge locally uniformly in `C_+` to a Pick function `rho`.

For every fixed squared node `x_k=k^2`, all sufficiently large `N_j` satisfy the exact finite conditions

\[
\rho_{N_j}(x_k)=G_C(x_k),
\qquad
\rho_{N_j}'(x_k)=G_C'(x_k).
\]

However local-uniform convergence in the open half-plane does **not** automatically preserve equality of boundary derivatives. Classical Julia theory naturally yields a relaxed boundary problem: the limit can satisfy

\[
\rho(x_k)=G_C(x_k),
\qquad
0\le\rho'(x_k)\le G_C'(x_k),
\]

with strict derivative loss possible through boundary concentration invisible on compact subsets of `C_+`.

A model mechanism is a positive pole approaching the boundary node `x_k` with residue proportional to the square of its distance. Its contribution can vanish locally in `C_+` while leaving a finite amount in the derivative at the boundary point before the limit.

Thus the infinite problem is not merely:

> identify an analytic function from sparse jet data.

It is more precisely:

\[
\boxed{
\text{prove determinacy and rule out boundary-derivative defect in the infinite Pick problem.}
}
\]

This is exactly the type of question addressed by Weyl-disk / Hamburger-type determinacy theory.

## 6. Human state of the Weil/operator program

The 2025--2026 literature is consistent on the principal open bridge:

- Connes--Consani--Moscovici construct finite self-adjoint rank-one operators whose spectra give real finite approximants and explicitly state that rigorous convergence of the regularized determinants / spectra to `Xi` would prove RH.
- Connes--van Suijlekom prove real-zero consequences for a lower-bounded operator with simple isolated ground state.
- Groskin supplies the finite Guinand--Weil dictionary, rigorous tail certification, and very high precision finite computations, while keeping cutoff-to-continuum convergence open.
- Suzuki reformulates the Weil form through the screw function / de Branges framework and conjectures convergence of finite-interval self-adjoint operators to the zeta-zero spectrum.
- Sliwinski studies spectral error scales for the finite CCM operators but does not prove the required low-zero convergence theorem.

The literature search found no accepted theorem that closes the finite-to-infinite convergence gap, and no explicit application of infinite boundary Pick determinacy to the CvS squared-grid Loewner jets.

## 7. Updated research targets

The Pick branch should now be organized as follows.

### Target A: finite Pick membership

Prove the critical Schur normal has no zero components, or otherwise prove every finite `rho_N` is a rational Pick function. This is still a finite structural gap in note 020.

### Target B: apply existing infinite determinacy criteria

Translate the sequence of squared-grid boundary data and the Schur/Julia reductions into the rational first/second-kind functions and Weyl disks used in the Dyukarev theory. Determine whether the problem is determinate or indeterminate. Do not invent a new uniqueness theorem until this translation has been exhausted.

### Target C: boundary defect / pole-measure tightness

If the infinite problem is determinate, prove that subsequential Pick limits retain the full prescribed derivatives rather than merely the relaxed inequalities. Equivalently, exclude spectral measure collapsing onto fixed interpolation nodes in a way invisible to local-uniform convergence.

### Target D: identify the determinate limit with the zeta spectral object

Only after A--C should one attempt to identify the unique Pick limit with the Weyl/regularized-determinant object whose real pole set corresponds to the Riemann zeros.

This leaves the research aligned with the actual human frontier: the finite real-zero machinery is strong; the unresolved theorem is infinite convergence/determinacy.