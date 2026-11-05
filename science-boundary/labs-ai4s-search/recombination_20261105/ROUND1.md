# Independently verified published-elite parent recombination — round 1, 2026-11-05

## Source data and parent independence

[Curated 20 true source orbits](data/parents.tsv), [source hashes, exact E and symmetry checks](data/parent_manifest.json); [successful curation run](https://github.com/teddyli18000/web-ingest/actions/runs/42029177151). Source archive from [Knauer 2004, mirrored by Borko Bošković](https://github.com/borkob/git_labs/blob/1aa123407636e48630174e0bf122037e369c1d68/results-2016/2004-Knauer-original.txt), matching the published exhaustive N≤66 optimum literature, plus genuine different-source [GPU-MTS/QOBLIB certificates N92/99](../frontier_deformation/results/2026-10-29-frontier-elite-eval.tsv). No perturbation is used as a second parent.

| N | distinct elite orbits | Energies | Minimum Hamming across *all 8* LABS symmetries | Provenance |
| --- | ---: | --- | ---: | --- |
|46|3|131,131,131|13|historical archived optimum structures|
|47|6|135 ×6|12|historical archived optimum structures|
|50|3|153 ×3|18|historical archived optimum structures|
|59|2|205,205|26|historical archived optimum structures|
|60|2|218,218|26|historical archived optimum structures|
|92|2|490,498|38|2025 GPU-MTS; QOBLIB|
|99|2|553,577|41|2025 GPU-MTS non-skew; QOBLIB skew|

**Important:** Distinct archived *symmetry orbits* are not proof of independent optimization lineages. The separate experiment `harvest_independent.py` obtains native solver starts with independent random seeds; it must pass an actual ≤1.20× known E gate before being called truly high-quality independent parent data. For N92/99 there remain only two independently published high-quality source orbits, insufficient to estimate population linkage reliably. The 2016 exhaustive enumeration makes strictly beating the known optimum impossible for N≤60; only novel equivalent or near-optimal orbits make scientific sense.

## Complete 1000-unit timed source-pair experiment

[Successful verified run 42029908854](https://github.com/teddyli18000/web-ingest/actions/runs/42029908854), C++ [recombine.cpp](recombine.cpp), independent full-row Python [evaluate.py](evaluate.py), [all 1000 session results](results/source_pairs_v1.tsv), [all 22 source-novel ≤10% certificate records](results/new_source_orbits_v1.tsv), [paired statistics](results/paired_summary_v1.json) and [provenance](results/metadata_v1.json).

For each of 25 parent-orbit **pairs**, 5 independent operator seeds and 8 method arms (25×5×8=1000), allocate **120 milliseconds** total per arm, including model/tree building, offspring generation, and common original-LABS steepest descent + **64 accepted Tabu-7 moves** + steepest descent for *every child*. All best terminal certificate sequences and all 'novel ≤10%' child records are rescored independently with O(N²) integer LABS energy and all eight valid symmetries. This is **not** a full modern MTS or GOMEA solver comparison. The 120ms CPU wall timing is on the same runner and cannot be equated with GPU papers' effort.

Eight methods:
0. Copy certified A/B source parent and local repair.
1. Direct uniform positionwise two-parent crossover.
2. One-point crossover.
3. Full-symmetry-aligned uniform crossover.
4. Simple *univariate* EDA built from all distinct archived parent orbits (Laplace-smoothed marginals); **not** a full population graphical model.
5. Single FOS-pass GOMEA-style optimal mixing on a uniform child, using random hierarchical linkage.
6. Same fixed GOM acceptance and donor rule, but FOS built by empirical population pairwise mutual information.
7. Same fixed GOM acceptance and donor rule, but FOS learned from **exact** LABS two-bit epistasis averaged over every parent state: |E(s^{i,j})−E(s^i)−E(s^j)+E(s)|. Every tree-build cost was counted.

The source parent pair defines the direct crossover, while MI/epistasis linkage is estimated from the **whole available same-length parent pool**, which can be only two source orbits for N92/99. FOS donor is the second parent after minimum-Hamming symmetry alignment; this is a **GOMEA-style approximation**, not the established full GOMEA implementation. No claim of outperforming a fully tuned classical GOMEA codebase. Different methods share the same source pair and replicate ID, but randomized operations consume different RNG streams, so source- and length-clustered comparison is required.

### Main results

- **0 source-novel children within 5%** of best known energy on *any* of the 7 lengths, across 1000 timed units.
- **22 source-novel certificate records within 10%** (not necessarily 22 different orbits across sessions), all from N46/N47. Zero N50/59/60/92/99.
- In N99 the original published elite pair E553 vs E577 is orbit-Hamming-distance **41**. Neither ordinary crossover, marginal EDA, any LT/FOS variant, nor exact epistasis tree returned a new source-novel orbit within 10% of E553 after costed repair.
- N92 pair E490 vs E498, orbit distance 38: also **zero new source-novel ≤10%** offspring.
- Single-point and GOMEA-style mixing more often preserve/return an existing excellent parent; uniform crossover and EDA return many **structurally novel, much higher-energy children**. The exact interaction tree did not close this diversity-quality gap.

**Best-session endpoint source-orbit identity:** on N99, among five seeded timed sessions, single-point 5/5 best candidates belong to either known source parent; random-FOS GOM 5/5; MI-FOS GOM 5/5; exact-epistasis-FOS GOM 5/5; uniform crossover 3/5; marginal EDA 0/5. The mean **all repaired offspring** energies are 806.7/725.6/949.5/738.3/1068.3/1074.3 respectively (we distinguish all-offspring mean from the session best). No GOM variant produced the desired distinct near-frontier new structure.

**No incremental exact interaction advantage established:** every N92/99 source-pair/bootstrap comparison of new ≤10%-elite production between exact vs MI/random FOS is a zero-event outcome. Best-session EP vs MI at N92 is actually −8 E (lower-best advantage reported as −8); at N99 is zero. N47 EP produced 4 loose-elite records vs MI 1, but these source records share pair parents and represent much weaker relative-to-optimum quality, so no statistically source-independent generalization or modern solver advantage is established. This says nothing about larger population GOMEA with learned linkage where >2 independent elite parent orbits exist.

**A mechanistic failure split:** *conservative donor copying collapses back into existing parent orbits*, whereas *unconstrained multi-locus mixing destroys long-range correlation cancellation*. Merely knowing high-epistasis links is not enough to preserve cancellation across the donor/recipient boundary. This suggests a new **constrained two-parent inheritance mask** representation requiring nontrivial contributions from both donors, with optimization of exact cross-boundary autocorrelation terms; at the end still compare the true repair results to source-copy, classic crossover, MI-FOS and exact-FOS.

### Interpretation boundaries / negative controls

- These 20 parent **orbits** are structurally independent, but archival N46–60 source lineages are uncertain; the only cross-source N92/99 pairs number one each.
- Repeated offspring evaluations in the same parent pair do not generate independent source experiments. Bootstrap CIs indexed by pair × random replicate are naive and tagged so in raw JSON. No source-clustered superiority claim on seven length strata.
- Cannot claim "GOMEA fails"; implementation intentionally covers just one-pass FOS candidate-level mixing, without all advanced model/selection/population controls.
- **No source-orbit novel 5%-near-elite** was found, but this is evidence only about this 120ms local repair/candidate space, not proof no recombinant structure exists.
- Do not pivot to a neural model based on 22 loose-elite records without positive heldout advantage over the classical baselines.
- All published parent bits, raw data, scripts and verifier are retained. Previous fixed-12-macro solver negatives remain in [trajectory study](../trajectory_20261104/MACRO_STUDY.md).

## Next hypothesis

Factor the exact LABS correlation of a recombinant child `s_i=a_i` or `b_i` into **within-recipient, within-donor and cross-boundary** terms. The independent coordinates of two high-quality parents only specify their own autocorrelation cancellations. Recombining their sites can break many cross-boundary cancellations. Require a minimum donor contribution after symmetry alignment, optimize the inheritance mask in fixed donor-cardinality space, and permit zero-energy-preserving compensatory changes. Crucially, *retain novel, quality-qualified repaired children*, not only an objective score that ultimately selects a copy of either parent. Start N46/47/50 where multiple optimum orbits exist, then test the much harder heldout N92/99 source pairs.

## Sources / reproduction

Compile in `science-boundary/labs-ai4s-search/`:
```sh
g++ -O3 -std=c++17 -Wall -Wextra recombination_20261105/recombine.cpp -o /tmp/labs_rec
/tmp/labs_rec --selftest
/tmp/labs_rec recombination_20261105/data/parents.tsv recombination_20261105/results/source_pairs_v1.tsv recombination_20261105/results/new_source_orbits_v1.tsv 5 120
python3 recombination_20261105/evaluate.py --parents recombination_20261105/data/parents.tsv --summary recombination_20261105/results/source_pairs_v1.tsv --novel recombination_20261105/results/new_source_orbits_v1.tsv --out recombination_20261105/results/paired_summary_v1.json
```

References: [2009 classical LABS memetic crossover](https://www.sciencedirect.com/science/article/pii/S1568494609000404), [2024 GOMEA/CGOMEA advances](https://arxiv.org/abs/2109.05259), [2016 exhaustive LABS N≤66](https://doi.org/10.1088/1751-8113/49/16/165001), [public Knauer historical RLE archive](https://github.com/borkob/git_labs/blob/1aa123407636e48630174e0bf122037e369c1d68/results-2016/2004-Knauer-original.txt).
