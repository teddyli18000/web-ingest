# 024 — Infinite Pick problems already reduce to moment problems

Status: literature correction / route narrowing. No RH claim.

Date: 2026-09-03

This note further narrows the Pick/Loewner direction after checking older interpolation literature.

## 1. The broad infinite-Pick-to-Hamburger bridge is not new

Chen and Hu developed this theory around 2000–2001.

For a denumerable Nevanlinna–Pick interpolation problem, their 2000 paper constructs an intrinsic correspondence with a full Hamburger matrix moment problem. The formulation uses a block Hankel vector, generalized Schur complements and Weyl matrix disks.

Their 2001 paper treats multiple Nevanlinna–Pick interpolation with both interior and boundary data, including angular derivative data, and reduces the finite boundary problems to truncated standard/nonstandard Hamburger moment problems, with possible constraints excluding mass at the real interpolation nodes.

Therefore the broad strategy

\[
\text{infinite Pick interpolation}
\longleftrightarrow
\text{Hamburger moment determinacy}
\]

is classical and must not be presented as a new bridge.

## 2. Agler–Young covers the finite boundary Schur recursion

Agler–Young 2011 gives the finite real-boundary theory in a particularly clean scalar form:

- the boundary Pick matrix is the confluent Loewner matrix of value/derivative data;
- Julia reduction corresponds to Schur complementation (up to a diagonal congruence);
- solvability requires positive definiteness or minimal positivity;
- determinacy is equivalent to minimal positivity;
- the determinate solution is real rational Pick.

Thus the finite Schur recursion and the infinite moment correspondence are both established general theory.

## 3. Derevyagin gives the operator/Padé side for infinite interior data

Derevyagin's Jacobi-matrix approach to an infinite scalar Nevanlinna–Pick problem represents the problem by a linear pencil and an associated symmetric operator.

In the determinate/self-adjoint case, the multipoint diagonal Padé approximants converge locally uniformly off the real axis to the unique Nevanlinna solution. The theory naturally contains Weyl circles, m-functions, continued fractions and orthogonal rational functions.

Its nodes are in the upper half-plane rather than general confluent real-boundary jets, so it is not a direct plug-in for the CvS squared-grid data. It is nevertheless another warning: convergence of rational extremals under determinacy is also an established phenomenon in the appropriate NP setting.

## 4. Dyukarev 2026 strengthens the determinacy machinery

Dyukarev's 2026 Hamburger-type criterion for matrix Nevanlinna–Pick interpolation characterizes determinate versus indeterminate behavior through convergence of matrix series built from rational functions of the first and second kind.

Again, the general determinacy machinery is not missing.

The technical issue for this workspace is whether the exact CvS problem — real boundary nodes, confluent first-derivative jets, and the squared grid — can be transported into the hypotheses of a criterion of this type without losing the arithmetic structure.

## 5. Revised zeta-specific target

What remains potentially useful is much narrower:

1. Start from the exact even-sector CvS jets at
   \[
   x_n=n^2.
   \]
2. Construct **the actual Hankel/moment data** associated with these jets under an established Chen–Hu-type boundary interpolation correspondence.
3. Determine whether a standard moment criterion (Carleman/Hamburger, Weyl-disk collapse, or the appropriate rational-function criterion) proves determinacy for these *specific* data.
4. If determinate, use an existing convergence theorem for finite rational extremals rather than re-proving compactness from scratch.
5. Identify the unique limiting Nevanlinna object with the CCM/Suzuki/Xi spectral object without inserting RH in the identification.

Only steps 2–5 are research here. The surrounding interpolation theory is existing machinery.

## 6. Circularity warning

Finite Pick-matrix positivity for every truncation is itself a strong condition. For the zeta Weil data, one must not assume the very positivity that is equivalent or close to the desired RH statement and then use moment theory to 'prove' it back.

A non-circular use of the moment correspondence would need one of the following:

- work in a parameter/window regime whose positivity is already independently certified and extract a convergence theorem there;
- derive the moment data and its determinacy from arithmetic/functional-equation information that does not assume global Weil positivity;
- or use the moment representation to isolate a strictly weaker quantitative condition whose proof would advance an existing author-stated convergence bridge.

## 7. Current decision

Do **not** launch a generic 'infinite Pick convergence' proof project.

First derive or recover the Chen–Hu Hankel vector for the CvS squared-grid jets and test whether the resulting moment problem has an obvious determinacy mechanism. If that mapping itself merely rewrites Weil positivity with no new estimate, stop this route.
