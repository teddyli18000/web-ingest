# Elite-parent LABS recombination: source-distinct structures (2026-11-05)

## Question

Can two genuinely distinct, independently archived LABS elite sequence **orbits** recombine so that the new candidate remains elite-quality *after identical costed local improvement*, and does exact autocorrelation-aware linkage supply incremental value beyond classic one-/two-point, uniform crossover, a simple population product model, and a strong *linkage-tree gene-pool optimal mixing* control?

## Current state, safeguards

Before any experiment, the existing 21-orbit verified public frontier corpus has only two length-matched parents at N92 (published GPU E490 and QOBLIB E498) and two at N99 (GPU non-skew E553, historical QOBLIB skew E577). **N100 has only one validated record orbit**. Never make a N100 E578-perturbed sequence into another independently excellent parent. It is invalid to mistake 25 historical lMAts n80–100 E440–817 final solutions for near-record.

The [pinned borkob/git_labs original 2004 Knauer archive](https://github.com/borkob/git_labs/blob/1aa123407636e48630174e0bf122037e369c1d68/results-2016/2004-Knauer-original.txt) explicitly lists multiple symmetry-distinct optimal solutions under the LABS 8-fold symmetry, e.g. N46 (3), N47 (6), N50 (3), N59 (2), N60 (2). Exact integer scoring and group action deduplication will be performed **again**, and any inaccurate row excluded. These are distinct *solutions/orbits*, not necessarily independently executed optimizer lineages; label such provenance carefully. The 2016 exhaustive results of Packebusch–Mertens determined all N≤66 optimal sequences, so N≤60 fitness improvement below the known optimum is mathematically impossible. On those N, new unique **equally optimal** or reasonably near-optimal child orbits, inheritance from both parents, diversity and cost are meaningful; no record claim.

For every source group with ≥2 certified elite parent orbits, compare six or more fixed action families under **same end-to-end wall time** including all proposal construction, learning the linkage, all exact-energy evaluations, and the *same post-crossover original-objective local improvement*:
1. source-copy + local improvement (no crossover control);
2. 1-point and uniform two-parent crossover;
3. uniform independent per-bit population marginal model (simple EDA);
4. random hierarchical linkage-tree mixing (FOS placebo);
5. linkage-tree mixing based on empirical population pairwise mutual information, using gene-pool optimal mixing-style candidate acceptance (name this **GOMEA-style approximation**, not the original GOMEA implementation);
6. exact-LABS correlation interaction linkage and conditional donor-part mixing;
7. ablation: correlation linkage **without** structural scoring versus matched random linkage, and if needed symmetry alignment.

Use the same saved parents and replicate seeds across arms, not synthetic children as "new independent parents". Runtime equalized per parent pair, and report **number of exact scored and repaired children, best post-repair E, fraction new nonparent orbits within +0/5/10% of known optimum, fraction strict improvement for above-optimum N92/99, min symmetry-aware distance to all parents, parity/spectral effects, evaluation/repair costs**. Most importantly **cost per new superior orbit** and **novelty after repair**, rather than immediate candidate energy. Blind/heldout orbit test when enough independent orbits exist. Archive all raw outputs and exact verifier. Repeat seeds by *source orbit family*, and never interpret many offspring from a few parent orbits as independent biological evidence.

## Literature baseline status

- Gallardo–Cotta–Fernández (2009), *Finding low autocorrelation binary sequences with memetic algorithms*, explicitly studies classic LABS recombination; replicate the structure of those blind controls where feasible, but don't claim a single implementation equals its full study. [Paper](https://www.sciencedirect.com/science/article/pii/S1568494609000404).
- Dushatskiy, Virgolin, Bouter, Thierens & Bosman (2024), *Parameterless Gene-pool Optimal Mixing Evolutionary Algorithms*, and linkage-tree FOS/CGOMEA: linkage modeling and GOM are **established strong classical methods**, not AI4S novelty. [Paper](https://arxiv.org/abs/2109.05259).
- Packebusch–Mertens (2016) exhaustive LABS groundstates N≤66. [Paper](https://doi.org/10.1088/1751-8113/49/16/165001).
- Modern 2025 GPU-MTS/2026 self-avoiding search remain necessary for any future claim of solver superiority, not for proving a low-N recombination primitive.

## Observational baseline and limits

Prior [93,256 native solver events](../trajectory_20261104/README.md), [144 complete native-MTS 12-bit macro runs](../trajectory_20261104/MACRO_STUDY.md), and [fixed-Hamming-12 mask search](../trajectory_20261104/GEOMETRY_STUDY.md) show that good immediate proposals and high conditional odd/even direction AUC don't imply a better deployed search solver. Retain those negative controls; this study targets an entirely different *multiple-distinct-elite-parent* generative representation.

## Reproducibility / handoff

- `curate_parents.py`: fetch pinned public Knauer RLE archive and existing topic-local N92/N99 frontier source; score every entry with a separate exact O(N²) evaluator, dedup using all eight LABS invariances, check group counts, emit `data/parents.tsv`, `data/parent_manifest.json`.
- `recombine.cpp`: reproducible C++ source for the candidate operators, FOS and exact score/local repair; independent Python verification of persisted child solutions.
- `evaluate.py`: report source-orbit-paired outcomes, diversity, and significance under no train/test leakage.
- One-shot GitHub Actions computation can be used; after results pass, clean workflow, keep scripts/data here. Nothing in `science-boundary/labs-100/` may be edited or submitted without coordinating the owning agent.

**Do not infer a method win until actual terminal child repair and cost-matched comparisons run and pass external verification.**
