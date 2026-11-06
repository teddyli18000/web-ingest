# Candidate-generating exact segment transformations and O66 repair

Date: 2026-11-06

## Status / question

Can large, correlated sign changes escape the N=100 LABS best-known E=578 basin when ordinary Hamming shells and near-skew modifications are saturated? The new operator preserves **internal** autocorrelation of an entire segment, while changing its correlation with the exterior, allowing Hamming-far moves that would be prohibitively unlikely under bitwise perturbations.

**No E<=574 candidate emerged.** This is a measured comparison of *specific constructive mechanisms*, not a proof of optimality or a general exclusion of two-stage search.

Few Shots p006 live board and baseline were rechecked on this date: record E=578, next achievable target E=574.

## Exact nonlocal operators

For a binary sign string s of length 100:

1. Reverse a contiguous interval [i,j), optionally negate the reversed signs. The contributions to each autocorrelation from pairs wholly within that interval remain unchanged.
2. Exchange adjacent intervals [i,j) and [j,k), optionally negating either relocated interval. Internal correlations of both exchanged blocks remain unchanged.

These operations do not leave *full* aperiodic autocorrelations invariant; the changed cross-boundary terms are scored from scratch.

Implementation: [segment_move_exact.cpp](../code/segment_move_exact.cpp), using two 64-bit popcounts of a 128-bit exact sign mask for each of 99 lags. Entire one-step operator sets (with the ranges in the code) are enumerated; duplicate strings may arise from different operations.

Build and run from the topic root:

    g++ -O3 -std=c++20 -fopenmp code/segment_move_exact.cpp -o /tmp/labs-segment
    /tmp/labs-segment 0
    /tmp/labs-segment 1

Frozen local summaries from the same scanner:

    mode=0 tested=9,900, min E=578, O=50, le578=337, le650=337
    mode=1 tested=666,600, min E=578, O=50, le578=665, le650=665

Across both complete one-move scans, all **1,002** operation hits at E<=578 reduce to **6 distinct sequences**, every one obtained by applying reversal, sign negation and/or alternating sign to the public incumbent. The best strictly nontrivial complete energy is **686** (gap 108). This set of moves never supplies a new independent E578 parent.

The distinct low-energy, nontrivial one-step candidates with E<=950 number exactly **100** (at this threshold and for these operators).

## Coordinated two-move construction

To try escaping via an intermediate higher-energy state, [segment_move_beam2.cpp](../code/segment_move_beam2.cpp) first generates those 100 distinct nontrivial E<=950 states, sorts by E, greedily selects parents with pairwise Hamming distance >=16, capped at beam 32, then enumerates **every** one-step segment operation from each selected parent. The greedy diversity criterion yields 17 selected parents.

Build and run:

    g++ -O3 -std=c++20 -fopenmp code/segment_move_beam2.cpp -o /tmp/labs-segment-beam
    /tmp/labs-segment-beam 32 950

Frozen summary:

    STAGE1 uniqueLE950=100 best=686 beam=17
    SUMMARY candidates1=100 beam=17 best2Nontrivial=686 witnessNontrivialLE578=0

Exactly 17*(9900+666600)=**11,500,500** second-step candidate *operations* were evaluated (duplicates allowed). No operation produced a nontrivial E<=578 sequence, and the best nontrivial state after a second move was still E=686. The previously recorded unfiltered minimum at stage two was E=578, but it was a trivial return to the incumbent orbit.

This is a **beam-limited** search, not an exhaustive two-move composition: the other 83 distinct parents below E950 were not expanded, nor were the larger-energy parents.

## Other independent constructive probes this session

### Exact 14-bit block repair

A C++ packed-popcount block search selected 14 positions, enumerated all 2^14 sign assignments by Gray code, chose the best complete E, and periodically kicked 14 random bits. Four selection methods were compared at equal budgets: random sites, lag-correlation-weighted bond endpoints, near-skew mirror pairs, contiguous sites.

For **8 starts per method, 90 blocks per start**, there were 4*8*90*(2^14-1)=**47,183,040** scored proposed states. None beat E578. The two qualifying runs per method both began at the historical incumbent; the random and mutated starts did not reach a new elite. This experiment is a heuristic pilot, not exhaustive coverage of the unconstrained Hamming-14 neighborhood.

Local exact source and raw transcript were retained in session scratch as `exact_block_lns.cpp` and `block14.log`; future reuse requires migrating this code to the topic.

### Direct O66 construction and constrained polishing

Odd-autocorrelation tabu from random strings can reach O=66 without going through the incumbent's Hamming-near basin. A pilot of 12 independent random starts, at most 12,000 odd-projection steps and 250 O66-preserving pair-tabu steps, found **8 O66 seeds**. Lowest complete E after polishing: **1318**. This is much worse than the public E578 candidate and weaker than previous fixed-(2,2) complete-energy pilots (E1030). It shows O66 can be constructed nonlocally, but not yet coordinated with low even energy.

Local source and transcript: `odd66_constructive.cpp` / `odd66pilot.log`; migrate if scaling or developing the route.

### Affine decimation and parity-block exchange

All 4000 parity-preserving affine reindexings `s'_i=s_(u*i+b mod100)` of the incumbent, `gcd(u,100)=1`, were scored using a separate NumPy integer-32 autocorrelation. Their best E was 578; none had O=58 or O=66. These transforms preserve zero cyclic odd autocorrelations but not the aperiodic score.

For the interleaved 50-bit parity halves, all 10,200 choices of a nonempty aligned interval, optional reversal, and independent signs when exchanging the two half-intervals were also rescored in integer-32 NumPy. No improvement below E578; the best other energy was E686.

These are small, reproducible transformation censuses, not a global upper bound.

## Follow-up geometry audit: distance to the incumbent symmetry orbit

An independent check measured the minimum Hamming distance of every one-step candidate to **any** of the eight reversal/negation/alternation images of the incumbent (not merely distance from its printed orientation).

- At orbit distance 0, there are 1,002 operation hits, all E578.
- At orbit distance 1, the minimum energy is E686; the two-step beam's final nontrivial E686 witness lies exactly one bit from the incumbent (O=178). Thus this score is **not** evidence for a novel distant basin.
- At orbit distance 2, the minimum energy is E874.
- Across all candidates with orbit distance >=8, the minimum energy is E722 (O=146); this witness is the incumbent after alternating-sign symmetry followed by rotation by two positions. Thus even that relatively low-energy, Hamming-far state is a familiar rotated incumbent, not a new independent elite construction.

The orbit-distance audit independently rescored all candidate strings via the packed original LABS formula, and a literal double-sum scorer confirmed the E686 and E722 witnesses.

This is a cautionary outcome: allowing a large *nominal* Hamming displacement does not imply a genuinely new structural basin. The proposed segment operator is not worth scaling unchanged.

## Interpretation and pivot

These checks constrain specific large-move interfaces, but do not warrant repeating them at greater depth. Unrestricted and odd-lag-constrained heuristic basins remain disconnected in terms of **joint** odd/even quality. The single best published candidate E578 is unusually isolated even under coherent segment transformations.

The constructive next step should **change the variables being jointly optimized**: instead of moving physical indices or choosing a fixed odd-defect level first, design a simultaneous target profile of odd cross-correlation and even parity-half autocorrelation and solve for binary A,B as coupled objects. One potential interface is an alternating exact/approximate repair of two complete 50-bit halves under spectral constraints, with acceptance based on *full* E and no forced (2,2) sums. Validate such an algorithm on hidden higher-quality solutions at neighboring lengths before spending large N100 compute.

## Verification notes

- Published numerical energy scores in this note are sums of 99 exact integer aperiodic correlation squares; the low-energy witness scores were also recomputed independently using literal dot products.
- Operation counts refer to generated, possibly duplicate states. The counts 100 and 6 explicitly refer to *distinct* binary strings.
- The source of the public record and eligibility criterion is the official Few Shots p006 verifier and 2026-11-06 board. No record claim or shot submitted.

## Literature inspected

- Packebusch & Mertens, exact LABS and skew enumeration (2016): https://arxiv.org/abs/1512.02475
- Pšeničnik et al., bandit search-space allocation (2026): https://arxiv.org/abs/2607.09688
- Lau & Gangat, small-subsystem optimization (October 2026): https://arxiv.org/abs/2610.14361
- Pšeničnik et al., dual-step unrestricted priority refinement (2025): https://doi.org/10.1016/j.dsp.2025.105316
