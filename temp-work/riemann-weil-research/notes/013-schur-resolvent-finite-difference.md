# 013 — Schur–resolvent telescope and the finite-difference normal mechanism

Date: 2026-09-02

## Bottom line

The single-prime Fourier story does not survive cross-cutoff controls, but a
stronger structural mechanism does:

1. every prime-power edge acts on a nested Schur pivot through one scalar
   residual R_{N,q};
2. the relative Schur sensitivity R^2/s telescopes exactly into a source
   resolvent r^T E^{-1} r;
3. at large prime edges the Schur normal is numerically very close to the
   unique centered finite-difference stencil that maximizes prime-edge
   vanishing moments;
4. for fixed N=24 this alignment improves systematically from q=97 to q=797,
   while M0, M2, and M4 simultaneously collapse by many orders of magnitude.

This suggests a concrete analytic subproblem: derive a two-parameter
(N, log c) asymptotic for the Schur normal and prove quantitative proximity to
the centered finite-difference stencil in an appropriate regime.

This is not an RH proof.  The decisive unresolved issue is the joint limit:
for each fixed support/cutoff one ultimately needs control as N -> infinity.

## 1. Cross-cutoff phase control kills the naive q=2 story

At c=100, a detrended Fourier diagnostic gave the strongest single candidate
at log(2)/log(100).  Nearby prime cutoffs do not preserve a unique q=2 law:

- c=97: top candidate q=17, harmonic 3; family-wise permutation p ≈ 0.00920.
- c=101: top candidate q=3; family-wise p ≈ 0.1655 (not significant).
- c=107: q=2 returns as top candidate; family-wise p ≈ 0.08197 (not significant).

The q=2 component remains nontrivial, but the identity of the strongest
single frequency is unstable.  Together with prime ablations, the evidence is
for nonlinear collective low-prime interference, not one-prime causation.

Result:
`results/cross-cutoff-schur-phase-c97-101-107-N80.json`.

## 2. Prime-power ablation: collective low-prime cancellation

At c=100, N=80, remove one prime-power contribution from the exact cutoff-free
Arb matrix and recompute Schur pivots (the ablated form is an artificial
control, not the zeta Weil form).  The midpoint response of s_80 is roughly:

- remove q=2: factor 10^49.53,
- remove q=3: factor 10^49.54,
- remove q=5: factor 10^49.29,
- remove q=7: factor 10^49.60,
- remove q=79: factor 10^16.28.

Low-prime removals also produce rigorously negative Schur pivots in the
artificial control.  Thus the true tiny positive pivots are the result of a
very delicate collective cancellation involving several low primes and the
analytic background.

Result:
`results/prime-power-schur-ablation-c100-N80.json`.

## 3. Exact prime-edge Schur square law

Let the orthonormal even-sector prefix at u=log c be

    E_N = [ B   b ]
          [ b^T d ]

and

    s_N = d - b^T B^{-1} b,
    w_N = (-B^{-1}b, 1)^T.

For any matrix direction H,

    D s_N[H] = w_N^T H w_N.                       (1)

At a prime-power edge q=p^k, the pinned CvS path has

    Delta E_N' = -a_q r_N r_N^T,

where r_N is the all-ones source projected to the orthonormal even basis and

    a_q = 2 Lambda(q)/(sqrt(q) log q)
        = 2/(k sqrt(q)).                           (2)

Therefore, with

    R_{N,q} := r_N^T w_N,

we have the exact edge response

    Delta s_N' = -a_q R_{N,q}^2 <= 0.             (3)

In the full symmetric Fourier coefficient basis, R_{N,q} is exactly the
zeroth moment / coefficient sum M_0(w_N).  Hence the Schur normal's
prime-edge blindness is a vanishing-moment statement.

The upstream finite vanishing-moment theorem says that a nonzero real even
level-N vector has visibility order at most 4N+1, with equality only for the
centered finite-difference stencil

    d_m = (-1)^(N-m) C(2N, N+m),  -N <= m <= N.

Thus the unique maximally-blind direction is already identified algebraically.

## 4. Exact Schur–resolvent telescope

Define the source susceptibility

    chi_N := r_N^T E_N^{-1} r_N.

The block inverse formula gives

    chi_N - chi_{N-1} = R_{N,q}^2 / s_N.          (4)

Consequently

    sum_{j=0}^N R_{j,q}^2/s_j = chi_N.           (5)

Since

    s_N = det(E_N)/det(E_{N-1}),

(3) also gives the logarithmic prime-edge response

    Delta (d/du log s_N)
      = -a_q R_{N,q}^2/s_N
      = -a_q (chi_N-chi_{N-1}).                   (6)

Summing (6) over N recovers the determinant/log-determinant prime-edge
response.  The point is that the total determinant barrier factors into
nonnegative mode-by-mode source-resolvent increments.

This suggests that chi_N may be a better global scalar control variable than
lambda_min or even individual s_N.

## 5. Rigorous prime-edge residual map

Using 3000-bit Arb at the actual threshold c=q, for q=2,3,5,7,17,97 and
N<=32:

- all tested even LDL pivots are strictly positive;
- the exact residual/impulse balls are computed for every N;
- selected minimum |R| values are:

    q=2:   min |R| ≈ 2.96e-2,
    q=3:   min |R| ≈ 3.14e-2,
    q=5:   min |R| ≈ 1.48e-2,
    q=7:   min |R| ≈ 2.62e-3,
    q=17:  min |R| ≈ 2.19e-6,
    q=97:  min |R| ≈ 1.72e-18 (at N=32).

At q=97, N=32:

    s_32 ≈ 3.8613094261e-38,
    R_32 ≈ 1.7208376600e-18,
    a_q R_32^2 ≈ 6.0134531569e-37,
    (a_q R^2)/s ≈ 15.57.

Thus increasing blindness does not by itself solve positivity: the Schur
margin may shrink even faster.  Equation (6) is the correct dimensionless
quantity.

Result:
`results/prime-edge-schur-residual-map-q2-3-5-7-17-97-N32.json`.

## 6. Schur normals are near high-order vanishing-moment stencils

Transform w_N to the full symmetric Fourier coefficient basis and compare its
normalized direction with the centered finite-difference stencil.

At q=97 the absolute overlaps are:

    N=8    0.9983394774
    N=16   0.9913711135
    N=24   0.9804620578
    N=32   0.9676435719

The overlap decreases with N at fixed q, so there is no evidence that the
N->infinity normal at fixed q converges to the finite-difference direction.
However, the direction remains highly structured, and many low even moments
are simultaneously tiny.

At q=97, N=32, dimensionless normalized moments are approximately:

    |M0|  1.94e-43
    |M2|  4.07e-40
    |M4|  1.27e-37
    |M6|  1.52e-35
    |M8|  9.56e-34
    |M10| 3.63e-32
    |M12| 9.09e-31
    |M14| 1.59e-29
    |M16| 2.00e-28

So tiny M0 is not an isolated cancellation: the Schur normal lies in a deep
approximate vanishing-moment cone.

Result:
`results/prime-edge-schur-normal-shape-q7-17-97-N32.json`.

## 7. Fixed-N large-edge test supports a genuine asymptotic

Hold N=24 fixed and move through larger prime edges:

| q | overlap with centered difference | normalized |M0| | normalized |M2| | normalized |M4| |
|---:|---:|---:|---:|---:|
| 97  | 0.9804621 | 2.72e-35 | 4.35e-32 | 1.01e-29 |
| 193 | 0.9876545 | 1.38e-38 | 3.13e-35 | 1.05e-32 |
| 397 | 0.9920043 | 2.46e-41 | 7.42e-38 | 3.29e-35 |
| 797 | 0.9945614 | 1.09e-43 | 4.24e-40 | 2.39e-37 |

All four diagnostics move monotonically in the finite-difference direction.
This strongly supports the conjectural fixed-N asymptotic

    normalized w_N(c) -> normalized centered-difference stencil

as c -> infinity, at least along the tested prime edges.

No convergence rate is claimed from four points.  In particular an apparent
power law in log c would be premature.

Result:
`results/fixed-N24-prime-edge-normal-q97-193-397-797.json`.

## 8. Main analytic target now

The next theorem candidate is deliberately narrower than RH:

> Fixed-N finite-difference asymptotic.
> For each fixed N, derive a large-u expansion of the even Schur normal w_N(u)
> and prove that its normalized direction approaches the centered
> finite-difference stencil, with an explicit error depending on N and u.

The useful version must then be upgraded to a two-parameter estimate uniform
in a growing range N <= N_max(u).  That is where the RH relevance begins.

A plausible proof route is:

1. expand the smooth/prime-combined finite matrix in the frequency index;
2. identify a leading moment matrix whose deepest normal is exactly the
   centered finite-difference stencil because it annihilates
   1,m^2,...,m^(2N-2);
3. bound the remainder in an N-dependent operator norm;
4. apply a quantitative subspace/eigenvector perturbation estimate to obtain
   the Schur-normal error;
5. feed the moment bounds into R_{N,q}, chi_N, and the distributional log-pivot
   dynamics.

The hard part is step 3 uniformly as N grows.  A fixed-N asymptotic alone
cannot prove RH.

## 9. Relation to the new compact-window barrier

Marcus Chuk, arXiv:2608.24827 (2026-08-25), proves a doubly-exponential barrier
for pointwise-envelope certificates of compact-window Weil positivity.  That
strengthens the case for the present route: a successful method should exploit
structured cancellation/nonalignment rather than absolute pointwise bounds on
the prime comb.

The Schur-residual formulation does exactly that compression, but no theorem
yet shows that its smooth background and prime-edge susceptibility terms keep
all pivots positive.
