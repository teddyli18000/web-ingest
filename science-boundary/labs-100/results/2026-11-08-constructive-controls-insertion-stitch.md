# Constructive controls, movable insertion and paired-parent stitching — 2026-11-08 UTC

## Objective / verdict

Construct an unrestricted length-100 LABS sequence with original integer energy **E<=574** (current Few Shots best **578**), prioritizing new candidate basins over expanding exact exclusions.

**No new N100 record or E<606 target-class source was produced.** This round established a benchmark with proper control arms, tried a qualitatively different mobile-insertion latent representation and an independently sourced cross-parent construction, and rejected their *unchanged* formulations as unproductive.

For *exact E=574*, the global sign product must be +1 (energy 6 mod 8), as proved in [target congruence](2026-10-28-target-congruence.md). That statement must not be applied to the *whole* E<=574 range (E570 has the other product class).

## Verification and prior art

The public E578 baseline and the Few Shots p006 verifier specification were checked. The 2025 paper (revised v2, 2026) by Zhang et al., [arXiv:2504.00987](https://arxiv.org/html/2504.00987v2), supplies exact published **N99 E553** and **N98 E529** non-skew sources and reports no new N100 value. [QOBLIB](https://github.com/ZIB-AOPT/QOBLIB/tree/main/02-labs/solutions) supplies N59 E205 and N60 E218, plus N40 E108/N80 E352.

Separate [labs-ai4s-search](../../labs-ai4s-search/README.md) already ran true published-parent recombination, negative-pair epistasis LNS, and native memetic-tabu studies with strong negative controls. The present benchmark's pair-synergy heuristic is **not claimed novel**, and a lower immediate repair energy is not evidence of a competitive solver.

All best witness strings below were independently checked with a second literal O(N²) Python full-correlation scorer. Combinatorial loops use exact integer XOR/popcount energy. All count statistics below are *generated evaluations*, which may include repeated identical sequences or trivial parent copies.

## A. Fixed-work hidden-record positive controls

Local C++ pilot source available in the session artifact `hidden_block_benchmark.cpp`. The earlier Python pilot [hidden-improvement](2026-11-07-hidden-improvement-constructive-pilot.md) is too easy: half its starts were already at least as good as a hidden reference. This study therefore used a real *published* high-quality teacher at each length N40/60/80/100, but passed only a 10/15/20/23-bit mutated and one-flip-descended parent to the algorithms.

Algorithms:
- unrestricted single-spin tabu (non-greedy moves and aspiration), with diversify-on-stagnation;
- 8-spin exact Gray-code subcube optimization with random, contiguous, lag-tension graph or shuffled-lag graph site masks;
- hybrid tabu that inserts one exact 8-spin block every 20 tabu moves;
- a separate hybrid that samples 240 exact two-spin effects per mask, selecting disjoint negative-synergy pairs, **charging all sample evaluations**.

All accepted scores were original full LABS energies, not correlations surrogates. Each algorithm used the same starting bitstring and the same configured seed formula. Budgets are *neighbor energy-evaluation* counts, **not equal CPU time**: variable-site scoring, mask construction and cache effects differ.

For seed=20261108, 12 trials per length, 160,000 scored proposals per algorithm:

| N | hidden teacher E | pure tabu min | best of hybrid LNS arms min | teacher recovered |
|---|---:|---:|---:|---:|
| 40 | 108 | 116 | 116 | none |
| 60 | 218 | 318 | 282 | none |
| 80 | 352 | 520 | 544 | none |
| 100 | 578 | 934 | 950 | none |

For the same 12 starts at **1,600,000** scored proposals per algorithm:

| N | pure tabu mean/min | hybrid random mean/min | hybrid true-lag mean/min | hybrid shuffled-lag mean/min |
|---|---:|---:|---:|---:|
|40|120 / 108|121.7 / 116|120 / 108|118.7 / 108|
|60|295.7 / 250|303.3 / 270|301.3 / 274|295 / 262|
|80|559 / 520|566 / 540|550.3 / 504|573.7 / 540|
|100|924 / 878|929.7 / 874|936 / 890|931.3 / 866|

A fresh seed=20261109, 12-start **200,000** proposal test of direct pair-synergy selection gave N100 mean **984**, versus pure tabu **969.3** and genuine lag-graph hybrid **991.7**. The corresponding N60 means were **325**, **328.3**, **324.3**. This does not demonstrate transferable structural value. All best strings from these three batches were independently rescored.

**Decision:** no scaling of plain 8-bit exact-LNS, lag weights or negative-pair site scores as a candidate generator. Long-horizon result also rebuts the apparent advantage from the 160K N60 pilot.

## B. Moving insertion as a latent nonlocal move

A N99 source b and an index p/sign sigma define N100 s=insert(b,p,sigma). Moving p can rotate arbitrarily long intervals without the 100-bit Hamming-local representation. Given b, optimize **all** 100 insertion sites and **both** signs using exact original N100 energy.

Reproduction: [code/moving_insertion_exact.cpp](../code/moving_insertion_exact.cpp). Build `g++ -O3 -std=c++20 code/moving_insertion_exact.cpp -o /tmp/lift` from the LABS topic root, then run `/tmp/lift 99 3` and `/tmp/lift 59 4`.

Source N99 non-skew E553 (hex `0CF30C003783CBCC8DA92AAD4`; final padding bit removed):

| exact source Hamming radius | source variants | all optimal-lift trials scored | lowest N100 E |
|---:|---:|---:|---:|
| 0 | 1 | 200 | 606 |
| 1 | 99 | 19,800 | 606 |
| 2 | 4,851 | 970,200 | 606 |
| 3 | 156,849 | 31,369,800 | 606 |

Across all four shells: **32,360,000 candidate operations**, zero E<606. The best E606 string is

```
+++++--++----++--++++--++++++++++++--+----+++++----++-+----++--++-+++--+--+-+-++-++-+-+-+-+-+--+-+-+
```

This state belongs to the *E574-compatible exact mod-8 class*, unlike E578. The search is a finite radius-3 result in **N99 source coordinates**, not a general N100 exclusion; lifted sequences can be duplicates and have many different Hamming distances from E606.

Additional constructive probes:

- Optimizing the source itself by sampled source-bit tabu with full 200-choice insertion reoptimization per candidate, penalty lambda in {0,0.5,1,2}, four seeded 1,999,592-E100-evaluation runs, found best E606 in every run. Auxiliary N99 scores are not included in that E100 evaluation count; the exact N100 gradient probes are counted.
- All 99 cyclic rotations of the N99 source and both alternation phases, followed by optimal insertion (**39,600** full evaluations), also have min E606.
- The N59 published optimum E205 -> N60 is a stricter held-out positive-control failure: optimal insertion starts at **E246**, while independent published optimum is **E218**; exhaustive source radii 0 through 4 with 120 lifts per source, including **455,126 ×120=54,615,120** radius-4 evaluations, did not improve E246. Thus moving insertion alone does *not* recover known cross-length quality in this smaller regime.

## C. Two insertion sites and independent-parent inheritance

From the published non-skew N98 E529 source, exhaustively insert two signs at all pairs of N100 locations. The **19,800** choices give best E642. Allowing any single N98 source-bit mutation, and then reoptimizing both insertion sites/signs (**98×19,800=1,940,400** exact N100 scores) still gives E642.

A different interface combines a verified N100 E578 parent and the independent N99->100 E606 lifted non-skew parent. After all eight exact LABS sign/reverse/alternation symmetry orientations of the donor, exhaustively inherit the donor's sites in one or two disjoint contiguous intervals of the N100 recipient. Require the resulting child to be at symmetry-orbit Hamming distance >=8 from the E578 anchor for the structural novelty readout. Target-class readout requires E=6 (mod 8).

Reproduction: [code/two_parent_stitch_exact.cpp](../code/two_parent_stitch_exact.cpp), `/tmp/stitch 1` and `/tmp/stitch 2` after compiling as directed in that file.

| donor mask | exact generated N100 candidates | min E overall | min E away from E578 orbit | target-class min away |
|---|---:|---:|---:|---:|
| one interval | 40,400 | 578 | 606 | 606 |
| two disjoint intervals | 32,663,400 | 578 | 606 | 606 |

Both preserve the known E606 donor as a returned answer but do not construct even an E602 alternate; naive inheritance boundaries destroy the high-quality parent cancellation. This is an evaluated operator family, **not** proof that recombinant improvement is impossible.

## D. Periodic sign-gauge scout

Enumerated all 2^p multiplicative periodic sign masks at p in {4,6,8,10,12,14,16,18,20} around historical N100 E578. At p=20, **1,048,576** masks were scored, only 4 outcomes E<=900, all trivial symmetric copies of E578. Independent literal scorer verified the best nontrivial reported high-energy masks. Do not enlarge this family unchanged.

## Interpretation / next construction

The central failure is **not** local optimization precision. Both excellent published seeds are isolated from useful descendants under fixed local edits, insertion source reoptimizations, simple sign masks, and segment inheritance. Generating far Hamming variants is also not enough. Useful construction requires *jointly chosen* replacement terms that preserve much of the original signed lag-by-lag cancellation **during** a transition, or independent strong quality parents with genuinely complementary structures.

Next research should change the representation to **signed-correlation-cut joint proposals**, where a multi-bit mask is selected by its effect on the full vector `Delta C_k=-2 sum_{i: mask_i!=mask_{i+k}} s_i s_{i+k}` *before* committing; compare fixed-cardinality cut-space beam/repair to the strong historical/native MTS and costed negative-epistasis baselines already developed in [labs-ai4s-search](../../labs-ai4s-search/README.md). Require recovery of a hidden **truly better published orbit** at lengths N46/47/50/59/60 before any N100 campaign. Avoid claiming novelty until the sibling topic's prior cut/motif studies are inspected; do not spend more exact radius computation in the same N99-insertion or two-interval families.

**Status:** best verified global N100 578. No Few Shots certificate or shot submitted.

Sources: [Few Shots p006](https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100), [Zhang et al.](https://arxiv.org/html/2504.00987v2), [QOBLIB](https://github.com/ZIB-AOPT/QOBLIB/tree/main/02-labs/solutions), [our prior cross-length work](2026-10-27-cross-length.md).
