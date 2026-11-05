# Consensus-innovation donor recombination — predeclared mechanism (2026-11-05)

## Why a new variable family

The prior costed source-pair experiments show opposite failure modes: conservative Linkage Tree/GOM-style copying returns to a source parent, while ordinary uniform mixing creates distinct but high-E children. An exact independent structural check over *all eight LABS symmetries for every triple of archived optima* finds that the third known optimum is never allele-only expressible from the first two: in N46 three optima require at least 3 deviations on consensus positions; in N47 60 source-pair/third-optimum triples need 3–9 such deviations (median 6); in N50 three triples need 8. See [exact triple certificate](../results/allele_compatibility_all_orientations.json). Another exhaustive source-sorted study [12.05M aligned inheritance masks](../results/exhaustive_parent_closure_d21.tsv) also found zero source-novel ≤10%-near-optimal raw mixed alleles among 17 pairs with D≤21, without claiming anything about parent pairs outside that exact domain.

Hence a representation restricted to parental-difference sites cannot *directly* form another known optimum without further off-allele mutation. This is a structural reason to introduce **consensus innovation** rather than tuning more linkage weights. It does not prove that the same mechanism helps high-N published GPU fronts.

## Frozen intervention family

For independently certified source-distinct parent A,B align all eight LABS symmetry copies of B for maximum agreement with A. Split coordinates into **D={i:A_i≠B_i}** and **Q={i:A_i=B_i}**. A proposal chooses donor mask x over D with inheritance count between ceil(|D|/4) and floor(3|D|/4), plus innovation mask z of exactly r coordinates in Q; generated word flips A on x∪z.

Predetermined r from exact lower-N compatibility (not optimized on outcomes): r=4 for N46/47, r=8 for N50, r=6 for N≥59. These settings allow actual off-parent alleles and give upper-cost comparisons for the more difficult N50 case. They are **hypotheses**, not known optimal cardinalities. If no source-novel elite exits result, do not tune r endlessly.

All same-source conditions use a fixed **120 ms total CPU wall** per independent seeded parent pair and arm, including complete generation, any learned linkage or exact lag feature, incremental scoring, and **same steepest-descent → 64-move Tabu-7 → steepest descent** child repair as previous work. Population parents are frozen and never sourced from one record's perturbations. Compare the following fixed methods:

- donor-only fixed-count exact-E mask-swap (without consensus innovations);
- random exact-cardinality donor+consensus subspace proposals;
- true-E improving donor-only and consensus-only coordinate swaps;
- coupled 4-bit donor+consensus pair swaps under true E;
- same coupled swap geometry with **exact parent per-lag envelope** penalty;
- same coupled swap geometry with an **independently shuffled lag-envelope placebo**;
- optional cheap best-of-repair-score method, fully costed, only if validated and no leakage.

Always hold out the known third optimum from *operator input*. For methods requiring a parent population model, learn only from the two exposed source parents; don't fit hidden targets into per-bit marginals. Parent-orbit dependence and historical archive lineages remain noted.

## Primary end-to-end endpoints

Cost per **unique new source-novel ≤10%-of-known-optimum child orbit**, after full repair, per paired source family. Additionally report *any third archived optimal orbit not equal to either active pair parent*, separately from new-to-full-parent registry; **never confuse the former with new discovery when a method trained on the full registry**. Distinct repaired orbital Hamming distance to both parents; retained best E and quality-diversity frontier; absolute throughput; exact integer independent score on retained certificates; N92/99 truly unseen structure (not the known alternative as secret target).

Tests are at least N46/47/50 (structural positive calibration) and heldout N59/60/92/99. Never claim standard GOMEA or modern GPU-MTS superiority from a GOMEA-style approximation. Prior failures and current results remain immutable. This scope is independent of `science-boundary/labs-100/` record-submission work.

## Status

Pre-registered new representation. Executable implementation and independent verification are to be added in this round. No prospective performance claim is supported yet.
