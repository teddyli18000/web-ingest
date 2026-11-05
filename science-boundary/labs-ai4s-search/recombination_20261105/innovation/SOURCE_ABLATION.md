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


## Completed 2800-session independent source ablation — verified

[Successful complete Action run 42045227026](https://github.com/teddyli18000/web-ingest/actions/runs/42045227026) independently confirmed exact integer energies, eightfold LABS equivalence, fixed matched Hamming radius before repair, and parent-library novelty. The first [42045028397](https://github.com/teddyli18000/web-ingest/actions/runs/42045028397) only failed C++ duplicate-main compilation and produced **no** science data. No failed runs are counted as negative evidence.

Nine source pairs across seven lengths, with 60 previously selected N60 seeds, 40 each on three unseen N59/60 pairs, 20 each on N46/47/50/92/99, ten arms and **120ms fully charged generation+repair per arm**, total 2800 exact verified sessions. Raw 9-per-pair TSV data, exact independently verified source-novel child certificates, JSON metrics and provenance SHA256 are in [results/virtual_parent_v1](results/virtual_parent_v1/); the [pair-cluster summary](results/virtual_parent_v1/pooled_pair_cluster_summary.json) analyzes 9 source-pair contexts, **not 280 statistically independent elite families**.

### Main result: the real second parent conveys *some quality-preserving information*

Mean benefit = virtual-B mean best after-repair E minus true-B mean best after-repair E, divided by that length's known optimal E, averaged evenly across **9 source pairs**. Positive indicates true B helps:

| Method (equal proposal geometry except true versus virtual B) | Across nine source pairs: mean % of Eopt | Source-pair bootstrap CI (descriptive, NOT corrected) | Six N>=59 pair contexts: mean % of Eopt |
| --- | ---: | --- | ---: |
| Uniform inheritance+consensus innovation | **+3.48%** | [+0.97,+6.52] | +1.26% |
| Four-prequench proxy proposal search | +0.89% | [−1.36,+3.65] | −0.58% |
| Exact-E coupled four-bit mask moves | **+2.04%** | [+0.81,+3.86] | +1.10% |
| Signed-correlation envelope coupled moves | **+2.99%** | [+0.78,+5.97] | +0.75% |

The majority of this effect is from short **N46/47**. True B wins on N46 source uniform mean best E137.4 vs virtual E147.4; N47 E138.6 vs E156.2; N92 N=20 seeds uniform mean E765.6 vs E786.8. But at long N99 uniform E915.6 vs E921.2 and exact envelope E906.2 vs E905.8. These are still **far worse** than source parent E553, and at N92 all generated children were far above source E490. The benefit is reducing destruction in previously benign length regimes, not reaching different near-frontier basins.

**Zero source-novel ≤5% Eopt certificate events in all 2800 sessions** across all arms. Among six N>=59 source pair contexts: 10%-near-optimal novel-orbit events (not distinct across seeds) were **0/1** for true/virtual uniform, **0/0** for prequench, **1/0** for exact-E coupled, **1/0** for exact spectral coupled. Source-copy A always retains the old best and is the strongest final-E baseline. The exact signed spectral coupled method has no consistent incremental quality advantage over cheaper exact E coupled mixing, and no demonstrated new elite yield.

**Interpretation:** This is positive counterfactual evidence that **information from a genuine second elite parent can improve postrepair candidate quality** relative to a Hamming-matched fake second parent in some lengths. It is *not* evidence that the tested operator can reliably reach new elite structures. The 9 source-pair mean bootstrap is exploratory; source lineages overlap and four algorithm arms were inspected, so intervals are not independent confirmatory cross-length scientific proof.

### Important original-basin artifact

A separate [exact support geometry certificate](results/replication_hit_support_geometry.json) analyzes the independent N60 E226 and N59 E209 hits from the prior 2500-session replay. For the actual **minimum-Hamming B alignment used in our generator**, these repaired targets require at least **8, 8, and 10 net bit edits** from *any* allowed raw mixed mask, even though the mask itself modifies only 6 parent-agreement sites. Across all symmetry orientations of the three words, these exact minimum pre-repair distances shrink to **4, 5, and 3** respectively.

For aligned A/B and target T, let d=#disagreement sites, t_B=#those sites where T takes B's value, q_T=#consensus sites T flips, and k=floor(d/2), r=6. The exact lower bound is
  min_possible_Hamming(raw_mask,T)=|t_B-k|+|q_T-r|.
It follows from independent choice of the two fixed-cardinality subsets. This means the native local repair does substantial restructuring even for the rare *successes*. The true-B information gate should be applied **before** deciding to train a model on raw masks. A coordinated repair-path action and joint symmetry alignment are more principled next representations than tuning the old 0.75 envelope parameter.

## Decision

Do not train dual-branch/diffusion neural generator from these results. Do not claim exact-correlation plus B delivers better frontier search. Separate measurable quality preservation from still-absent elite innovation. A richer coordinated representation would need to beat the true-source and virtual-source controls *after identical full repair* on fresh high-quality parent pairs, and modern strong GPU-MTS baselines before a search-method superiority claim.
