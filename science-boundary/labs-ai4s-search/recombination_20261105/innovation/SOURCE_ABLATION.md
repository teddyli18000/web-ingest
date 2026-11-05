# Prospective source-parent incremental value test — 2026-11-05

## Why this experiment

The independently verified replication_v1 run generated three more certificates of the **same** N60 E226 orbit (two on the selected pair, one on a different independent source pair), plus a distinct N59 E209 orbit, in 2,500 fully costed source-pair sessions across 10 arms. The original N60 near-elite discovery came from pre-quench selection; the replay successes came from true E and exact envelope joint swaps, while the holdout N59 result came from random donor+consensus proposals. **None** establishes that a second parent's sequence supplied incremental information: these hits may be generic one-parent random-restart search.

This frozen experiment tests whether a true B parent, rather than an equally large random virtual donor, improves the rate of novel high-quality **repaired** child structures.

## Matched source-controlled design

Use the same 29 certified <=10%-near-optimal orbits, and the same source pairs as the prior corpus. For each pair, align B to A using the eightfold LABS symmetry by minimum Hamming. Let d=Hamming(A,B), k=floor(d/2), and r=4 for N46/47, r=8 for N50, r=6 for N>=59.

The true-parent proposal samples exactly k positions from the d actual difference sites, and r from the (N-d) consensus sites. The **virtual-B null** independently selects d random positions to pretend B differs from A, and then samples k from those d and r from the complement; the resulting child has exactly the **same total Hamming distance k+r from A** and the same generation/repaired method. Virtual B contains no useful information from the true second parent. Virtual-parent construction cost is included in the 120ms solver timer. Each condition uses the exact same original LABS scoring and repair (steepest descent, 64 accepted Tabu-7 moves, final steepest descent).

Fixed arms:
- 0: source A copy + same repair (null).
- 1: true-B uniform donor+consensus inheritance (prior arm1).
- 2: virtual-B uniform donor+consensus.
- 3: true-B best-of-four candidates via fully costed steepest pre-quench (prior arm8).
- 4: virtual-B same pre-quench strategy.
- 5: true-B joint 4-spin improving mask swaps on exact E (prior arm5).
- 6: virtual-B identical joint swaps on exact E.
- 7: true-B joint 4-spin swaps guided by source spectral envelope (prior arm6).
- 8: virtual-B same envelope algorithm but using A and virtual B envelope, not hidden true-parent information.
- 9: one-source **unpartitioned** fixed-Hamming (k+r) improving mask swaps over all N, without the donor/consensus split.

The source A is frozen and the same in all arms; no third known optimal target enters candidate selection. The full 120ms per arm includes source abstraction, model/evaluation cost, generation, and repair.

Predeclared metrics: (i) unique new source-orbit certificates below 5%, 10% and 20% of the exhaustive known optimum, (ii) mean best postrepair energy, (iii) corrected per-parent-pair yield, (iv) time and throughput. Separate repeated hits to the same orbit from distinct new orbits. Source-pair tests and seeds are not independent source-lineage draws. Do not conflate N60 E226 repeats with new distinct findings.

Falsification criterion: if true B does not reliably outperform matched virtual B on unseen parent pairs, the previous rare successes are **not evidence of successful genetic recombination**, even if off-parent innovation is a useful search move.

Reference context: Gallardo–Cotta–Fernández (2009) LABS crossover, 2024 conditional GOMEA gray-box linkage, 2026 template/gray-box GOMEA linkage. This small historical Tabu repair is not a modern solver superiority test.

Full source/seed audit and exact downstream verifier will be stored in this topic. No new N100 record claim.
