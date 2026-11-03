# O=58: independent K16 singleton census and K34 dual-layer reassessment

Date: 2026-11-04

## Scope and verified result

The target remains LABS length 100 with energy at most 574, and the first non-odd-perfect odd-energy layer O=58. We normalize the two parity-half sums to (2,2). At order-25 compression norm K=16 the even-energy budget is Q+R<=24, where Q=sum U_r^2 and R=sum V_r^2.

An independent exhaustive C++ enumeration analyzes the compressed split (kp,kc)=(1,15). Because sum p=1, its single nonzero coefficient is +1, and cyclic translation sets p=delta_0. The periodic cross equation is then simply

    2 c_0 = 2  (center defect) or 0 (noncenter);
    c_r+c_(25-r) = 1  at the chosen nonzero defect r=s,
                   0  at every other 1<=r<=12.

The sum c=1 and norm ||c||^2=15 follow from exactly seven antisymmetric nonzero mirror pairs plus one positive singleton. The construction exhausts all such c, without dividing by affine symmetries:

- center s=0: c_0=1, choose 7 of 12 mirror pairs, orient each => C(12,7)*2^7 = 101376.
- noncenter s=1 or s=5: c_0=0, choose which of {s,25-s} is +1, choose 7 of the remaining 11 mirror pairs and orient each => 2*C(11,7)*2^7 = 84480 each.

For each sequence the code verifies the exact periodic cross coefficients, sum c, norm c, computes G_r=PAF_c(r), SG=sum_{r=1}^{12} G_r^2 and qmin(G)=sum ceil(G_r^2/2).

| defect location | exhaustive c | min SG | min qmin | SG<=48 | qmin<=24 |
|---|---:|---:|---:|---:|---:|
| center, s=0 | 101376 | 35 | 21 | 680 | 180 |
| unit, s=1 | 84480 | 19 | 13 | 314 | 152 |
| five, s=5 | 84480 | 19 | 13 | 350 | 200 |

These nonzero surviving periodic counts **do not give complete length-100 candidates**. Negacyclic cross, complement fibre, R budget, and original LABS objective are still required. The (15,1) split is symmetric to (1,15) at the compressed periodic level because the cross equation and SG are symmetric under swapping p and c; this does not by itself imply full aperiodic energy symmetry.

Reproduction:

    g++ -O3 -std=c++20 science-boundary/labs-100/code/o58_k16_singleton_census.cpp -o /tmp/o58-singleton
    /tmp/o58-singleton

This is independent of the GF(2) support-orbit and mod-3 solvers in the ongoing exact Actions campaign. It supplies a concrete cross-check on its extreme-split compressed output.

## Structural alternative: K=34 dual fibre sparsity

The K=16 layer is sparse in periodic compression, but the other edge of the exact feasible range, K=34, is sparse in **negacyclic fibres**. Both have 16 nonzero ternary coordinates in the corresponding pair of channels:

    K = ||p||^2+||c||^2,
    ||alpha||^2+||gamma||^2=50-K.

At K=34, m=K-25=9 and the odd-defect half sums imply

    sum_{r=1}^{24} U_r=-16,
    Q+R<=24.

For every integer U, U(U+1)/2 is nonnegative and vanishes precisely at U=-1 or U=0. Set

    d = sum_{r=1}^{24} U_r(U_r+1)/2 >=0.

Then the identity Q=16+2d gives the exact sparsity budget

    2d+R <= 8.

Consequently there are at most four indices where U is outside {-1,0}, and at most eight nonzero V coordinates (counting V_r^2). At d=0 the U multiset is exactly (-1)^16, 0^8.

There are only **21 possible sorted 24-entry U-value multisets** under these constraints, before imposing the periodic cross equation. Indeed d<=4 forces each U into {-3,-2,-1,0,1,2}. Enumerating nonnegative counts n_v with sum n_v=24, sum v*n_v=-16 and sum [v(v+1)/2]*n_v=d gives:

| d | possible U multisets | residual R budget |
|---:|---:|---:|
| 0 | 1 | 8 |
| 1 | 2 | 6 |
| 2 | 3 | 4 |
| 3 | 6 | 2 |
| 4 | 9 | 0 |

For d=0 the unordered pairs (U_r,U_(25-r)) have G_r in {-2,-1,0}; if n2 is the count G=-2, then n2=4,5,6,7,8 and SG=2n2+16. By the exact fibre identity SH=2Q-SG, with Q=16, this restricts **SH to {8,6,4,2,0}**, much tighter than the global SG+SH<=48 condition. This remains a necessary condition only.

This K34 formulation is *not* an exclusion. It suggests a non-mechanical next search: enumerate low-norm (16) negacyclic fibre pairs first under their coupled sparse commutator, then solve the high-norm periodic compression, instead of simply scaling the K16 compressed enumerator or continuing old odd-perfect K=25,27,... slices.

A local necessary-condition probe found a 16-sparse negacyclic vector with SH=10, so a naive universal SH>24 bound would be false. Such a vector alone is not an O=58 or full LABS candidate.

## Current exact-work boundary

The one-runner four-extreme-split Actions campaign was launched on main at run 41719753889. A successful run must show the declared compressed qhits equal the actual number of emitted HIT records in **every** task; the producer presently caps retained hits at 10000/task, so any truncation makes downstream fibre exclusion invalid. The next required evidence is complete qgroup outputs and, for nonzero QHITs, all matching full length-100 lifts/rescoring.
