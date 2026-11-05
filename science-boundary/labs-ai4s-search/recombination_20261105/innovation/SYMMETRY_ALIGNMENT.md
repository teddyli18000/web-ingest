# Source-elite parent symmetry is a search variable — preregistered 2026-11-05

## Basis

The exact 66-known-optimal-triple repair-order analysis found seven apparent unavoidable uphill paths under one frozen representation, but only **two** remained when re-optimizing the full eightfold LABS symmetry of the source and known third target. The stronger complete [all-symmetry certificate](results/symmetry_robust_paths_v1.json) is an **oracle diagnostic**, not a deployable policy.

In actual independent source-pair innovation successes the original generator hard-coded **minimum Hamming distance** alignment of source B to A. For the N60 E226 target, the exact lower bound of net repair edits from any raw allowed mask is **8** under this fixed nearest alignment, versus **4** when arbitrary A/B/target symmetries are optimized. For another N60 parent pair these values are 8 vs 5; for N59 E209, 10 vs 3. None of these target sequences will be used to choose prospective alignments.

A successful [2800-session genuine-vs-virtual-parent ablation](SOURCE_ABLATION.md) shows **some real B quality-preserving information** relative to Hamming-matched virtual B, especially N46/47, but no source-novel ≤5% energy discovery. Therefore, it is reasonable to test whether choosing symmetry *jointly* with donor/consensus variation makes more of the genuine parent information usable.

## Frozen experiment, no hidden target labels

For each pair of certified source-distinct high-quality parents A,B, compare orientations among all eight LABS-equivalent B words. The physical source A is held fixed for all arms. Let d0=the minimum orbit-Hamming distance of B to A, k=floor(d0/2), and r=4 for N46/47, 8 for N50, 6 for N≥59. **Every** proposed child from any non-source arm is required to differ from source A by **exactly k+r physical positions**. Its initial inheritance of B is always k positions from the selected oriented B-difference set, and r off-parent flips from that orientation's source-consensus sites. This fixes actual radius across all alignment treatments even when selected B orientation changes its native Hamming distance.

All source-B arms use the *same* exact-energy coupled 4-bit donor/consensus mask generator, 24 candidate swaps, and the same steepest descent + 64 accepted Tabu-7 moves + final steepest. The **120ms end-to-end wall time** includes any symmetry selection scouts, candidate generation, and repair, and a source-copy/null and fake-B/null arm are carried forward. One source family has genuinely source-distinct historical seeds; N92/99 each have only one cross-source elite pair.

Predeclared arms:
0. Baseline: B orientation with minimum Hamming distance.
1. Minimum squared signed-correlation-profile distance sum_k (Ck(A)−Ck(B_g))²; Hamming distance only breaks ties.
2. Maximum signed-correlation-profile distance (negative alignment control).
3. Random one of 8 symmetry orientations freshly chosen each generation.
4. Maximum Hamming distance orientation (antipodal representation control).
5. Costed two-probe raw exact-energy preselection over eight B orientations, using the same candidate geometry.
6. Matched virtual B donor with no true parental genotype.
7. Source A copy, same repair.
8. Costed one-probe steepest-quench preselection over eight B orientations.

The signed-correlation selection accesses only A/B exact LABS profiles; it **does not** access any withheld optimal C or replay success. Signed autocorrelation remains exact under reverse, flip and alternate symmetries (odd-lag sign flips). All true-B orientation treatments are label-blind for true new descendants. The raw-energy and steepest-quench alignment choices are strong **classical** baselines.

Primary: count unique source-novel fully repaired ≤5/10%-of-known-best orbits, per time and source pair. Secondary: symmetry-aware min source Hamming, mean final E and full throughput. Pair-aware comparisons not child-as-independent. Predeclared selected/holdout source pairs N46/47/50/59/60/92/99, unseen random seeds. A success must outperform min-Hamming, virtual B, and source-copy by *new high-quality repaired structure rate*, not raw mask E.

This is NOT a full official GOMEA, nor a modern GPU-MTS search; see [official cold-start GOMEA baseline](../official_gomea/README.md) and [matched real/virtual information ablation](SOURCE_ABLATION.md). No neural model is warranted until source- and length-heldout improvement is reproducible.
