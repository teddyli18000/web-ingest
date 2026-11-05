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


## Completed 2070-session source-symmetry experiment — verified

[Verified complete Action run 42048273380](https://github.com/teddyli18000/web-ingest/actions/runs/42048273380); [raw sessions and independently exact-scored LABS certificates](results/symmetry_alignment_v1/), [C++ generator](symmetry_alignment.cpp), [independent integer scorer and eightfold-symmetry verifier](validate_symmetry.py). Nine genuinely distinct source-parent pairs across N46/47/50/59/60/92/99, 230 previously unseen source-pair seeds, nine methods, 120ms charged for complete generation plus 64-step Tabu repair: **2070 fully validated treatments**.

**Exactly one new-to-parent-registry ≤5%-near-elite certificate event occurred:** N59, pair c59_0-c59_2, raw-energy-costed two-scouter arm, seed 24016, E209 (best known N59 E205). This is the **same canonical N59 E209 orbit** already found during the earlier independent 2500-session replay, not a new distinct structure. The selected N60 source pair produced no E226 in its 40 unseen seeds. Both N92 and N99 had zero source-novel ≤10% elite outcomes under any arm.

### Fully repaired mean best energy per 120ms session (smaller is better)

| Source pair | N | Minimum-Hamming alignment | Random symmetry alignment | Minimum signed-spectrum distance | Costed raw-E orientation scouts |
| --- | ---: | ---: | ---: | ---: | ---: |
| c60_1-c60_4 | 60 | 296.9 | 292.5 | 293.4 | 299.4 |
| c60_0-c60_3 | 60 | 295.2 | 296.67 | 299.07 | 294.27 |
| c60_2-c60_5 | 60 | 300.8 | 293.47 | 297.47 | 296.0 |
| c59_0-c59_2 | 59 | 284.47 | 286.2 | 282.87 | 284.73 |
| c46_0-c46_1 | 46 | 137.8 | 138.6 | 136.6 | 142.6 |
| c47_0-c47_2 | 47 | 144.0 | 156.8 | 143.6 | 156.2 |
| c50_0-c50_1 | 50 | 193.0 | 194.6 | 189.0 | 192.2 |
| c92_0-c92_1 | 92 | 775.2 | 784.0 | 774.8 | 779.0 |
| c99_0-c99_1 | 99 | 910.2 | 907.0 | 917.6 | 905.2 |

An apparent improvement from random alignment at N60 c60_2-c60_5 (E293.47 vs 300.8) reverses for N47 c47_0-c47_2 (E156.8 vs 144.0); there is **no transferable new-elite-rate advantage**. Importantly, per-arm pseudorandom seeds have different arm offsets. If two arms choose exactly the same physical B orientation, their differing mean E can be **sampling noise**, not evidence that signed-spectrum selection helps. No cross-source superiority is supported.

### Exact invariance and joint-parent structural alternative

All eight LABS symmetries preserve every individual correlation-energy Ck². Reversal and global complement preserve signed Ck, while alternating sign multiplies it by (-1)^k. Therefore even the complete **signed** single-parent autocorrelation profile distinguishes at most TWO symmetry classes, not eight; using separate power-spectrum encoders cannot identify the relative spatial orientation of A/B. Among the nine frozen source pairs, the B orientation minimizing complete signed-correlation Euclidean distance matched minimum-Hamming B on **eight**.

The full **relative A/B disagreement geometry**, however, can be described by [an independently verified exact fixed-cardinality fourth-moment formula](CORRELATION_MOMENTS.md). [All eight variants of all nine source pairs](results/expected_raw_alignment_v1.json) show that the expected *raw* offspring LABS energy at N99 differs by 35.66 across alignments, although their individual signed source profiles are identical. This is concrete mathematically exact cross-parent information **not recoverable from separate parent C²**. The raw offspring expected E remains around 4545–4580, versus parent E553; this is not a competitive new child.

**Decision:** stop tuning this fixed donor-half, fixed-consensus-cardinality operator. A different jointly constructed path representation, using cross-parent signed pair/lag interactions and costed stateful repair, is required before further neural architecture work. Results rule out this particular operator family only, not all re-combination.
