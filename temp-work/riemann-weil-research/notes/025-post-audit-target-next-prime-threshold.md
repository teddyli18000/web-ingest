# 025 — Post-audit target: certify the next prime-power window threshold

Status: research target selected after literature audit. No new positivity theorem is claimed here.

Date: 2026-09-03

## 1. Why the target changed

The literature audit in notes 022–024 removed several apparent novelty claims:

- CvS already uses divided differences and interpolation;
- Agler–Young already identifies boundary Pick reduction with Schur complementation;
- infinite real-boundary Nevanlinna–Pick interpolation and its moment-problem/operator realizations are classical;
- generic Feshbach/proxy estimates have already been pushed hard in the 2026 semilocal-proxy work.

Therefore the workspace should stop manufacturing equivalent formulations and target a concrete unconditional improvement over an existing theorem.

The current published/preprint compact-window certificate in Xuefeng Zhu, arXiv:2608.24827v2, proves

\[
Q(f)\ge 8.9\times10^{-18}\|f\|_2^2
\]

for every test function supported in

\[
[-0.8,0.8].
\]

The paper's one-stroke lower-bound machinery is explicit and certified. The natural first target is to extend that exact method to the next prime-power threshold rather than invent a new method immediately.

## 2. The next threshold is exact and structurally special

The geometric Weil symbol contains only prime powers with

\[
\log n<2L.
\]

Starting from \(L=0.8\), the next new prime power is \(n=5\), at

\[
\boxed{L_5=\frac{\log 5}{2}=0.804718956\ldots.}
\]

For every

\[
0.8\le L\le L_5
\]

(with equality harmless in the strict \(\log n<2L\) convention), the active arithmetic comb is unchanged: \(n=2,3,4\).

Hence

\[
A_L
=\sum_{\log n<2L}\frac{2\Lambda(n)}{\sqrt n}
=\frac{2\log2}{\sqrt2}
+\frac{2\log3}{\sqrt3}
+\log2
\]

throughout this plateau, numerically

\[
\boxed{A_L=2.9419735252236205\ldots.}
\]

The pointwise-envelope alignment scale of Zhu's Theorem 1.1 is therefore also constant:

\[
\boxed{T_1=2\pi e^{A_L}=119.0865561877\ldots.}
\]

Solving the strict tail-floor condition

\[
\beta^*(T)=\log\frac{T}{2\pi}-\frac1T-A_L>0
\]

places the equality threshold at approximately

\[
T^\sharp_{\rm eq}=120.0824.
\]

Thus moving from \(L=0.8\) to \(L=L_5\) does **not** incur the arithmetic comb explosion that dominates the large-window cost.

## 3. Why crossing the threshold is qualitatively different

For every \(L>L_5\), the prime \(5\) contributes

\[
\frac{2\log5}{\sqrt5}=1.4395250311\ldots,
\]

so the comb mass jumps to

\[
A_L=4.3814985563\ldots
\]

until the next prime-power threshold.

Consequently

\[
T_1
=2\pi e^{A_L}
\approx502.3895,
\]

more than four times its pre-threshold value. The Legendre order required by the one-stroke reduction likewise increases from the low hundreds to roughly the high hundreds before any additional loss from the smaller spectral margin is considered.

This makes \(L_5\) the natural first stopping point for a replication-and-extension experiment.

## 4. Relation to the current Zhu v2 certificate

The latest v2 paper reports:

- certified lower bound at \(L=0.8\);
- certified simple-even ground-state separation at \(L=0.8\);
- converged but non-certified reference floors at \(L=0.9,1.0,\ldots\);
- a retracted earlier claim at \(L=1.19\), because the true comb supremum uses \(A_L\), not a smaller per-prime effective constant;
- a doubly-exponential asymptotic barrier for pointwise-envelope certificates.

The paper does not report a certified sweep over

\[
0.8<L<\frac{\log5}{2}.
\]

A text search of v2 likewise found no explicit values at 0.801 or 0.804. This is only evidence of an apparent gap in the reported results, not proof that the author has not computed it privately or in supplementary data.

## 5. Concrete experiment

Before claiming any extension:

1. reproduce the archived \(L=0.8\) lower-bound certificate independently;
2. keep the exact same theorem and interval-error accounting;
3. rerun at a monotone ladder, for example
   \[
   L=0.801,0.802,0.803,0.804,L_5;
   \]
4. certify both even and odd parity sectors if the target claim is for arbitrary complex test functions;
5. require a positive interval lower bound after all matrix-tail, quadrature, and Cholesky-residual budgets;
6. preserve exact version/hash information for all external source material.

If the certificate fails before \(L_5\), the failure itself is useful: locate whether it comes from the reduced-form ground margin, matrix truncation, or interval error budget.

## 6. What would count as progress

A rigorous result of the form

\[
Q(f)>0\quad\text{for all }\operatorname{supp}f\subset[-L,L]
\]

for any explicit

\[
L>0.8
\]

would improve the currently reported unconditional compact-window frontier.

The cleanest first theorem target is

\[
\boxed{L=\frac{\log5}{2}.}
\]

This is intentionally modest. It is a theorem-sized target with a clear existing baseline and an independent verification path, rather than another reformulation of RH.

## 7. If the plateau extension succeeds

Only after the pre-5 threshold is certified should the workspace consider crossing it. The next plateau has \(T_1\approx502\), so it is materially more expensive but still finite. At that stage there are two choices:

- brute-force the existing one-stroke certificate with compiled/multiprecision arithmetic; or
- introduce an arithmetic cancellation estimate that genuinely lowers the cost without violating Zhu's exact comb-supremum obstruction.

Any proposed cancellation theorem must be checked against zero-density / pair-correlation / simultaneous-Diophantine literature before being treated as new.
