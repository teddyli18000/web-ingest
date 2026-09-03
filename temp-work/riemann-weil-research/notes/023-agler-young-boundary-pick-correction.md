# 023 — Agler–Young correction: Schur pivots are standard boundary Pick geometry

Status: literature correction / novelty downgrade. No RH claim.

Date: 2026-09-03

This note corrects the novelty assessment in `022-human-state-of-art-do-not-duplicate.md`.

## 1. General boundary Pick theory already contains the Schur step

Agler and Young, *Boundary Nevanlinna–Pick interpolation via reduction and augmentation* (Math. Z. 2011; arXiv:0905.4759), study interpolation data

\[
 x_j\in\mathbb R,
 \qquad f(x_j)=w_j\in\mathbb R,
 \qquad f'(x_j)=v_j\ge0
\]

for Pick-class functions.

The associated boundary Pick matrix is

\[
 M_{ij}=\begin{cases}
 \dfrac{w_i-w_j}{x_i-x_j},&i\ne j,\\[1ex]
 v_i,&i=j.
 \end{cases}
\]

This is exactly the confluent Loewner/divided-difference matrix form that occurs for the CvS source when

\[
w_j=\psi(x_j),\qquad v_j=\psi'(x_j).
\]

Agler–Young prove that Julia/Nevanlinna reduction acts on the Pick matrix by a Schur-complement operation. They also characterize solvability in terms of positive definite or minimally positive Pick matrices, and the determinate case is represented by a unique real rational Pick function of controlled degree.

Therefore the broad conceptual statement

> "the last Schur pivot is the remaining endpoint derivative slack in a boundary Pick problem"

is **not new**. It is a direct instance of standard boundary Nevanlinna–Pick geometry.

## 2. Consequence for our endpoint formula

Our finite CvS calculation gave

\[
s_N=\psi'(x_N)-r_N'(x_N),
\]

where the rational interpolant already matches the previous value/derivative conditions.

That explicit barycentric formula can still be useful computationally and may be a convenient CvS-specific realization, but its conceptual content must be stated as an application/refinement of Agler–Young reduction, not as a new interpolation principle.

Likewise, replacing the final derivative by the critical value

\[
v_N^{\rm crit}=b^TB^{-1}b
\]

makes the last Schur pivot zero. If the resulting singular matrix is **minimally positive**, Agler–Young already supplies a unique rational Pick extremal. Minimal positivity is an extra condition; singular PSD alone is not enough.

## 3. What this does *not* solve for the zeta data

Boundary Pick theory does not prove the needed positivity for the CvS/zeta matrices. Using it as

\[
\text{Pick solvable}\iff M_N\succeq0
\]

and then claiming positivity would be circular.

The zeta-specific questions that remain are instead:

1. prove, from arithmetic/functional-equation structure rather than the Pick criterion itself, that the relevant finite matrices/pivots have the required sign;
2. understand whether the critical singular matrices are minimally positive for the CvS data;
3. study the infinite boundary interpolation problem on the squared grid and decide determinacy/indeterminacy;
4. if determinate, identify the unique Pick/Herglotz representative and prove convergence of finite rational extremals to it;
5. connect that limit to the Xi/zeta spectral object without assuming RH.

These are application-specific statements not supplied by the general Agler–Young theorem.

## 4. Revised novelty filter

The following are now marked **known/general** and should not be promoted as contributions:

- confluent Loewner matrix interpretation of boundary value/derivative data;
- Schur complementation as one step of boundary Pick reduction;
- endpoint derivative slack as a Schur pivot;
- existence of rational extremal Pick solutions in the determinate finite problem.

The following remain **candidate research targets**, pending wider literature checks:

- CvS/zeta-specific control of the Pick/Schur recursion;
- minimal-positivity structure of the critical CvS matrices;
- infinite squared-grid boundary Pick determinacy for these exact jets;
- rigorous convergence/identification of the finite extremal rational functions;
- use of the arithmetic Loewner structure to control continuum inverse spectral moments that generic Feshbach estimates leave open.

## 5. Research rule

A change of vocabulary is not progress. From this point on, any Schur/Loewner/Pick statement must first be checked against classical boundary interpolation theory before it is treated as new.
