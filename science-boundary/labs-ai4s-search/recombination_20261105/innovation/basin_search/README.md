# Repair-aware parent-mask search: pre-registered experiment (2026-11-08)

**Question.** Does *joint genuine two-parent disagreement geometry* help optimize the **basin reached after complete LABS Tabu repair**, beyond (a) raw exact-E donor/consensus swaps, (b) random inheritance, (c) same-cardinality virtual donor, and (d) single-elite restarts?

The [verified parent corpus](../data/combined/combined10.tsv) contains 29 unique ≤10%-best-known source orbits, 20 originally archived public optimal/frontier orbits plus independently seeded historic lMAts. Do not turn variants of the one N100 E578 orbit into extra sources. The [prior true/virtual parent study](SOURCE_ABLATION.md) demonstrates post-repair energy preservation at small N but no reliable near-elite innovation. The [2070 orientation experiment](SYMMETRY_ALIGNMENT.md) and [972-session protected path relinking](path_relinking/results/source_pair_analysis_v1.json) found no transferable source-novel ≤5% advantage. This experiment **changes the selection feedback variable** from raw candidate E or fixed locks to *actual postrepair fate*; it is not another lag-envelope parameter sweep.

## Frozen inputs and methods

Exactly nine true distinct source pairs: N46 c46_0-c46_1; N47 c47_0-c47_2; N50 c50_0-c50_1; N59 c59_0-c59_2; three N60 pairs c60_1-c60_4 / c60_0-c60_3 / c60_2-c60_5; N92 c92_0-c92_1; N99 c99_0-c99_1. B is symmetry-aligned to A by minimum Hamming, a fixed non-optimized choice. Define disagreement D and consensus Q, h=floor(|D|/2), r=(N≤47?4:N=50?8:6). Each two-parent mask flips exactly h positions in D and r positions in Q, so all two-parent and fake-B methods start at identical **physical Hamming radius h+r** from A. Candidate repair is the *identical original* LABS steepest → 64 accepted Tabu-7 moves → steepest (the existing `repair`), with all costs inside **400ms per source-pair/seed/arm**.

Arms:
0. **True-B random fixed-cardinality inheritance+consensus**; repair, no mask optimization.
1. **True-B cheap exact raw-E mask swaps** (24 four-spin donor/consensus exchanges) before complete repair; legacy strong classical baseline.
2. **True-B postrepair E-guided mask search:** propose donor/consensus swaps, execute complete repair for **each** proposed mask, then keep the mask when the *postrepair E* improves; restart periodically. This adapts the action-search space to actual basin fate rather than pre-repair energy.
3. **Fake B** (uniformly random donor disagreement set with same cardinality) **and identical postrepair-E mask search**; tests source-information rather than a new basin-search algorithm alone.
4. **True B, postrepair novelty-sensitive mask search:** prioritize a repaired child that is outside the **full registered source orbit library**, then its true E; all repaired children still counted in same <=5/10/20% novelty metric and total time. Avoid score comparisons that grant arbitrary novelty over energy: use this as an exploratory utility ablation and judge actual threshold success.
5. **Single-source short radius 2/4/8/12 ILS** with same complete repair (no B information) and same time.

All arms use a single shared exact integer LABS implementation and independently scored source sequences. The postrepair objective uses only source-library canonical identities and original E, **never hidden third-optimum target identities**. Do not use any known replay N60 E226 / N59 E209 word as training input. The mask’s repair stream is hashed from the mask’s spin vector and source-run seed, not from arm, for reproducible basin scores across comparable candidate masks. This is a deterministic seeded evaluation *of one stochastic Tabu repair realization*, not an exhaustive basin predictor. Strictly local repair is costed even when evaluating a mask that is subsequently rejected.

## Primary outcomes and controls

Original-parent-pair/seed outcome is count of **unique nonregistered fully repaired symmetry-orbits** within ≤5% and ≤10% of the known length optimum. Report actual new sequences and exact eightfold canonical identity, source distance, energy, and per-pair novel-yield counts, not just best E or proportion of masks with low raw energy. Secondary: best repaired E excluding source-library returns, all-basin diversity, parent-return fraction, true B vs fake B and classic exact E control, candidate repair calls and total wall time.

**Sufficient success** requires repeated *new* high-quality orbits, preferably on heldout N59/60 or N92/99, with true-B postrepair guided method beating both fake-B and classic E search on source-pair-clustered outcomes; no claim of standard GOMEA or 2025 GPU MTS superiority. Small N46/47/50 can serve positive calibration but cannot establish cross-length transfer. If no reliable effect after a bounded pilot and heldout replication, treat as negative for this precise representation and reformulate rather than adding more mask temperature/lag parameters.

## Reproduction and public literature

Use `basin_mask_search.cpp`, `validate_basin.py`, and a one-shot self-cleaning Actions workflow; preserve source commit, exact test outputs and hashes. Scope limited to `science-boundary/labs-ai4s-search/recombination_20261105/innovation/basin_search/`, without changing `science-boundary/labs-100/`.

Prior art includes [Gallardo, Cotta, Fernández 2009 LABS memetic recombination](https://www.sciencedirect.com/science/article/pii/S1568494609000404) and [Parameterless GOMEA, 2024](https://research-portal.uu.nl/files/248508813/evco_a_00338.pdf). This method is a straightforward combination of guided LNS/postrepair lookahead with mask search, **not a novelty claim**.
