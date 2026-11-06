# Constructive parity-half QUBO and joint energy search (2026-11-06)

## Goal and current record

p006 (length 100 LABS), verified public record E=578, improvement target E<=574. The exact near-skew minimum is already E=578. This study tests a *different*, candidate-generating search family, not another exhaustive exclusion.

Write A_j=s_(2j), B_j=s_(2j+1), j=0,...,49. Define odd and even contributions O and V, with E=O+V.

## Exact conditional QUBO identity

For 0<=r<50, the odd aperiodic correlation satisfies

    C_(2r+1) = sum_(j=r)^49 A_(j-r) B_j
             + sum_(j=0)^(48-r) A_(j+r+1) B_j.

Consequently, at fixed A, define T_A[r,j] as the sum of the available A_(j-r) and A_(j+r+1). All odd correlations equal T_A B and

    O(A,B) = B^T (T_A^T T_A) B.

At fixed B, the equivalent linear coefficients for A_j are B_(j+r) if j+r<50, plus B_(j-r-1) if j>=r+1. The corresponding Q matrices have integer entries. For two opposite spins i,j (to keep the half sum fixed), the exact update is

    delta O = -4 b_i (Qb)_i + 4 Q_ii
            -4 b_j (Qb)_j + 4 Q_jj + 8 b_i b_j Q_ij.

This is an exact objective reformulation, not a relaxation. Local search on a half is still heuristic. The fixed-half sums (2,2) correspond to the necessary class for the first non-odd-perfect O=58 layer, established in earlier records.

## Experiment 1 — alternating conditional odd QUBO

Source: [conditional_odd_qubo.cpp](../code/conditional_odd_qubo.cpp).

Build and reproduce:

    g++ -O3 -std=c++20 code/conditional_odd_qubo.cpp -o /tmp/labs-cond-odd
    /tmp/labs-cond-odd 100 300 18 15

The program alternates tabu optimization of B at fixed A and A at fixed B, making sum-preserving opposite-spin swaps, with bounded pair perturbations between rounds. Fresh starts include random (2,2) halves and transformed incumbent halves.

Local frozen transcript:

    SUMMARY runs=100 steps=300 rounds=18 bestOdd=58 bestESeen=2158 O50=0 O58=59 minAt58=5718 ms=5139

Here O58=59 is the **number of sampled round-end states**, not a count of distinct sequences. minAt58 is the smallest complete E among those 59 states; bestESeen tracks all sampled states and is not restricted to O58.

One independently re-scored O58 witness (not a breakthrough):

    ---+---++--++-+++--++-++---+---+---+++-++-+++-+++-++--+++--+---++--++-+++-+++-+++--++-++---++--+---+

For this 100-character sequence: E=38606, O=58, sum A=sum B=2.

**Inference:** Exact O=58 candidates are constructible without exhaustive support-orbit filtering, but minimizing O alone produces very poor even correlations.

## Experiment 2 — joint even/odd swap optimization

Source: [paired_half_joint_search.cpp](../code/paired_half_joint_search.cpp).

Build:

    g++ -O3 -std=c++20 code/paired_half_joint_search.cpp -o /tmp/labs-joint

Runs:

    /tmp/labs-joint 24 250 12 601 0
    /tmp/labs-joint 24 250 12 601 1

Both modes use exact full-correlation two-spin increments and periodically compare the incremental search state with the independently recomputed full objective for their best witness. Different schedules minimize V + lambda O at each stage. Fixed half sums remain (2,2).

Frozen summaries:

    mode=0 best E=1030, O=506, median E=1102, 4657 ms
    mode=1 best E=1030, O=522, median E=1110, 3872 ms

Independent literal double-sum recomputation of final witnesses confirmed both E values, O values, length 100, and half sums (2,2). Mode-0 best:

    ++--++--++--+--++-+++---+++-++++-+++++-+-+-+-++++-+-+--+-+--+--+-++-++--------+++----++++--++++-----

**Inference:** The QUBO-only approach finds O58 but with E>=5718 in this sample. Joint optimization lowers complete E dramatically (to 1030) but then O grows to roughly 500. Simple weighted local search does not find the necessary *joint* cancellations. Scaling the same swaps is unjustified without a more effective representation.

## Additional conditional O50 graph test

Fix A to the incumbent's parity half (sum A=10), keep B sum zero, and optimize exact conditional O via B opposite-spin swaps. Among 1,000 planted perturbed starts (150 QUBO steps each), 999 ended at O=50; 963 differed from the original B. The best differing full sequence had E=834. Direct enumeration at the incumbent showed exactly **25** O50-preserving B-swap neighbors and best neighbor E=834. These moves correspond to the known near-skew freedom, not an escape from the exact near-skew barrier. They should not be scaled.

## Conclusions and next construction

- The parity-half QUBO identity is useful as a *repair oracle*, not a standalone merit-factor objective.
- An effective construction must select half updates by their predicted effect on both odd cross correlations **and** even autocorrelations. An alternating O-only projection followed by scalarized descent loses essential joint information.
- Explore a jointly constructed set of target even correlations or spectral-power constraints during half optimization, rather than minimizing O first. Compare with unrestricted baselines by number of full sequence evaluations and best complete E, not QUBO score.
- Prioritize candidate-quality improvements over further O58 exclusions. Re-check live Few Shots board before any new-record claim.

## Literature / original provenance

- Few Shots p006 problem, verifier, and board: https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100
- Pšeničnik et al., 2026, adaptive search partition prioritization: https://arxiv.org/abs/2607.09688
- Lau & Gangat, 2026, isolated-subsystem LABS search: https://arxiv.org/abs/2610.14361
- Earlier LABS topic records: ../README.md

No new record or Few Shots shot resulted from these experiments.
