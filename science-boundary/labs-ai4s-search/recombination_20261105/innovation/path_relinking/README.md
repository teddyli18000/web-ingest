# Source-elite protected path relinking — 2026-11-05

## Falsifiable question
Can gradually introducing a second, genuinely distinct elite LABS parent B while protecting already adopted B alleles and repairing unlocked variables outperform *classical path relinking* and single-elite iterated local search, measured by **new postrepair near-elite orbits per total wall time**?

The prior exact triple-orbit analysis finds that 64/66 listed optimum triple relationships have a non-uphill compulsory-consensus-edit ordering after jointly choosing symmetry orientation. However this is an oracle diagnostic, not a prospective policy. Prior true-vs-fake B source tests show some mean repaired-E preservation but near-zero novel elite yield. Static mask mixing damages LABS even with an exact spectral envelope.

This is an experimental **variant of the established path-relinking framework**, not a claim of general algorithm novelty: [Laguna et al. 2025](https://doi.org/10.1016/j.ejor.2025.02.022). Comparison includes previously published [LABS memetic search](https://doi.org/10.1016/j.asoc.2009.03.005), [2025 GPU MTS](https://arxiv.org/abs/2504.00987), [2026 GPU SAW](https://arxiv.org/abs/2607.09688).

## Frozen design

Use only the 29 independently certified source orbits in `../../data/combined/combined10.tsv`, with nine fixed pairs:
N46 c46_0-c46_1; N47 c47_0-c47_2; N50 c50_0-c50_1; N59 c59_0-c59_2; N60 c60_1-c60_4, c60_0-c60_3, c60_2-c60_5; N92 c92_0-c92_1; N99 c99_0-c99_1. No N100 perturbed clone and no known third target in the generator.

All arms use identical **400ms inclusive wall budget** and shared source/seed pairs. Four stages each introduce a further quarter of the A/B disagreement positions, evaluating repaired outcomes after each stage using identical exact-objective steepest → 64-move Tabu-7 → steepest. Arm variants:
0. Single-elite strong short-radius 2/4/8/12 ILS baseline (no B).
1. Copy A/B + identical repair.
2. Classical greedy exact-E path relinking (no protected intermediate repair).
3. Classical random path relinking (no protected repair).
4. Greedy path with 12-step protected Tabu+steepest among unlocked sites at each stage; carry *protected* state to next stage.
5. As 4, but random donor ordering.
6. As 4 with one best exact-E compensating consensus flip per newly locked donor site.
7. As 6 with exact A/B lag-correlation envelope penalty during compensating flip selection.
8. Lag-label-shuffled envelope placebo (same protected geometry/cost).

Parent B is aligned over all eight LABS symmetries using minimum Hamming; tie-breaking deterministic. Every kept B allele stays locked during intermediate protected repair. Ordinary unrestricted final repair is used to score offspring but never recycled into the next stage (to avoid erasing protected progress).

Primary: new source-novel fully repaired <=5/10% E_opt symmetry-orbits per time and successful independent-seed sessions; secondary: collapse to original parent orbit, best repaired E, throughput and source diversity. Verify all retained sequences independently with integer O(N²) and eightfold symmetry. Source-pair bootstrap, never offspring-level pseudo-replication. This is a mechanism trial, not an established GPU solver comparison or a neural model. Stop if novelty fails on heldout N59/60/92/99; do not tune four-stage parameters repeatedly.

## Execution
C++ `protected_relink.cpp`, independent `validate_relink.py`, one-shot GitHub Actions, durable raw outputs under `results/`. No change to `science-boundary/labs-100/`.
