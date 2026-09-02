# 012 — Prime-phase Schur response after the N≤120 certification

Date: 2026-09-02

## What changed

The naive smooth-plateau guess for the even-sector Schur pivots is false.
The rigorous c=100 Arb sequence through N=120 is strictly positive at every
mode, but the large-N pivots oscillate strongly.  Examples:

- s_80  ≈ 3.271162989394057e-50
- s_82  ≈ 3.427752357942373e-44
- s_100 ≈ 6.984196884801587e-51
- s_107 ≈ 5.962726061878747e-47
- s_113 ≈ 6.456732141555173e-51
- s_120 ≈ 2.174956228634992e-50

Thus the three-point 48/80/120 picture was a sampling illusion.  Smooth
power/exponential/plateau fits do not distinguish themselves on the N≥80 tail.
The object to explain is an arithmetic-looking oscillatory scalar sequence,
not a monotone decay law.

## Fresh external result that changes strategy

Marcus Chuk, arXiv:2608.24827 (submitted 2026-08-25), studies the compact-window
profile lambda*(L).  The preprint gives an unconditional whole-window positivity
certificate at L=0.8 and unconditional tiny upper bounds through L=2.  Most
important for this project, it proves a barrier for a pointwise-envelope
certificate: one must resolve to a frequency scale

    T_1 = 2*pi*exp(A_L),   A_L ~ 4 exp(L),

so this strategy is doubly exponential in L.

For our c=100 convention, the prime-support boundary is log q < log c = 2L,
so L = (1/2) log c = log 10 ≈ 2.302585092994046.  Directly summing the
von-Mangoldt comb below 100 gives

    A_L = sum_{n<100} 2 Lambda(n)/sqrt(n) ≈ 33.79240268842737,
    T_1 ≈ 2.978748839762858e15.

That makes a brute pointwise-envelope positivity certificate at this window
hopeless.  A useful advance must exploit cancellation / nonalignment of the
prime phases rather than their pointwise absolute supremum.

Reference: https://arxiv.org/abs/2608.24827

## First phase diagnostic

For c=100 and N=32..120, detrend y_N=-log10(s_N) by a quadratic and test the
family of frequencies h log(q)/log(c), q=p^k<c, h=1,2,3.  A 4000-permutation
family-wise max statistic gives:

- strongest candidate: q=2, h=1
- frequency log(2)/log(100) ≈ 0.15051499783199057
- single-frequency R^2 ≈ 0.16606
- family-wise permutation p ≈ 0.02249

This is only exploratory.  It is not enough to claim an arithmetic spectral
law.  In particular c=100 has the exact alias

    log(2)/log(100) + log(5)/log(100) = 1/2,

so cross-cutoff controls are mandatory.

## Exact Schur-response lemma at a prime edge

This is the main analytic observation of this note.

Let an even prefix be partitioned as

    E_N(u) = [ B(u)   b(u) ]
             [ b(u)^T c(u) ]

with B positive definite, and define the nested Schur pivot

    s_N(u) = c(u) - b(u)^T B(u)^{-1} b(u).

Put x=B^{-1}b and w=(-x,1)^T.  For any differentiable matrix direction H,
ordinary differentiation gives

    D s_N[E_N](H) = w^T H w.                       (1)

Proof:

    d(c - b^T B^{-1}b)
      = dc - 2 (db)^T B^{-1}b
        + b^T B^{-1}(dB)B^{-1}b,

which is exactly w^T(dE)w.

The Groskin finite prime-edge identity, pinned in this project at upstream
commit 5a66d0cd177ef8b8ad1c2c93165b8d56ca40292c, is

    Q_N'(log q + 0) - Q_N'(log q - 0)
      = -a_q 1 1^T,

    a_q = 2 Lambda(q)/(sqrt(q) log q) > 0.

The orthogonal projection of the full coefficient vector 1 to the even basis
{1, sqrt(2)cos,...} is

    r_N = (1, sqrt(2), ..., sqrt(2))^T.

Writing r_N=(r_<, eta) in the B/new-mode split and applying (1), the derivative
jump of the nested Schur pivot is therefore

    s_N'(log q+0) - s_N'(log q-0)
      = -a_q (eta - r_<^T B^{-1}b)^2 <= 0.         (2)

This is exact and contains the von-Mangoldt weight as a scalar times a square.
It should be checked against the precise path/basis normalization at the prime
edge before publication, but within the pinned CvS matrix path the derivation
is elementary.

Interpretation: every prime-power event gives the slope of every Schur pivot a
non-positive impulse; the size of the impulse is not the crude prime weight
alone, but the square of a mode-dependent interpolation residual.

That residual is now a much sharper object than lambda_min.  A possible proof
program is to control the sequence of residuals over prime events, not to bound
the whole prime comb pointwise.

## Finite rank-one downdate identity

For a genuine rank-one matrix downdate

    E' = E - a v v^T,

partition v=(u,eta) according to E=[B b;b^T c].  If B and B-a u u^T are
invertible, Sherman-Morrison gives the exact Schur update

    s' = s - a (eta-u^T B^{-1}b)^2
                 / (1-a u^T B^{-1}u).              (3)

Equation (2) is the infinitesimal / derivative-jump version.  The denominator
in (3) is also a precise failure criterion.  This is closely aligned with the
Weyl/Sherman-Morrison identities already present in the 2026 matrix-valued
von-Mangoldt package, but here the object is the nested positivity pivot.

## Next falsification experiments

1. Prime-power ablation at c=100, initially q=2,3,5,7,79, with the exact
   cutoff-free Arb matrix.  Remove one source term and recompute the even Schur
   sequence.  This asks causally which prime sources create the valleys and
   rebounds.
2. Cross-cutoff phase check at prime cutoffs c=97,101,107.  If the q=2 feature
   is genuine, its frequency should move with log(2)/log(c); if it disappears,
   the c=100 signal was likely an alias / small-sample accident.
3. Compute the residual appearing in (2) directly across c and q.  The key
   theorem target becomes a quantitative nonalignment bound on these Schur
   residuals, rather than a pointwise bound on the original prime comb.

## Current claim discipline

What is rigorous now:

- at c=100, every even nested Schur pivot N=0..120 has a strict positive Arb
  interval lower bound;
- the prefix values agree across independent 3000/5000/7000-bit calculations;
- the rank-one prime-edge identity is part of the pinned upstream finite path;
- the Schur directional derivative formula is elementary linear algebra.

What is not rigorous / not established:

- that the pivot sequence has a positive asymptotic lower bound;
- that q=2 causes the observed oscillation;
- that the prime-edge square law alone prevents a pivot crossing zero;
- that positivity at one fixed c proves RH;
- any proof or disproof of RH.
