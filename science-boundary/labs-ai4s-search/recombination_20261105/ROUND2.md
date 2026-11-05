# Round 2: balanced source-donor inheritance — full costed evidence (2026-11-05)

## Purpose

Test the strongest prospective hypothesis after the first 1000-unit classical elite recombination study: **does exact LABS spectral structure improve source-balanced mixing and produce new repaired elite orbits**, beyond the classical crossover/GOMEA-style alternatives and a shuffled-lag placebo? This test does *not* assume a neural network.

The 40 independent source-run harvests are [certified](data/native_independent_2009_v1/independent_manifest.json). A deterministic [merge](merge_verified_parents.py) yields 29 distinct symmetry-orbit parent sources at ≤10% above known optimum and 33 at ≤20%; N92/99 retain two genuinely distinct public GPU-MTS/QOBLIB certificates, N100 is excluded. [Source hash/lineage](data/combined/combined_manifest.json).

## Fixed design, certified computation

[Complete successful re-run](https://github.com/teddyli18000/web-ingest/actions/runs/42033560104) and [source](conditional_inheritance.cpp) / [independent 8-symmetry O(N²) verifier](evaluate_conditional.py). Earlier runs 42032084625 failed C++ duplicate main/test compilation; 42032302671 **finished all calculations and independent validation** but could not push raw results due a concurrent change to `main`. The successful rerun uses bounded rebase/push retry; failed runs are not counted as separate scientific replication, especially because fixed seeds repeat.

For each same-length genuinely distinct elite pair, align B to the best of its eight LABS symmetry variants (minimum Hamming). Define D={i:A_i≠B_i}. An initial recombination child must select donor B on between 25% and 75% of D, with the rest from A; **no extra agreement-site innovations at proposal time**. Methods all share the same original-energy steepest descent, 64-step Tabu-7 and steepest descent repair per generated child, fully inside 120ms end-to-end wall per pair × arm × source-run seed.

Methods: source copying (null), balanced randomized inheritance, circular segment inheritance, random-walk exchange in fixed-cardinality inheritance masks, true-energy hillclimbing exchange, mutual-information FOS optimal mixing, exact two-spin LABS interaction FOS optimal mixing, exact parent-spectral envelope penalty, and **lag-shuffled envelope placebo**. MI/epistasis FOS model is formed from the available entire same-length source pool, **not** a blind heldout parental population; it is a single-pass GOMEA-style approximation, not full state-of-the-art GOMEA. Parent-only exact envelope does not access hidden target optima.

Primary: N46/47/50/59/60/92/99, 29 source orbits, 56 distinct pairs ×4 independent method seeds×9 methods = **2,016 verified 120ms sessions**. Secondary source-quality sensitivity: 33 distinct orbits, 83 parent pairs×2 seeds×9 methods = **1,494 verified sessions**. Both [raw session TSV](results/constrained_v1/primary_sessions.tsv), [raw novel certificate TSV](results/constrained_v1/primary_novel_children.tsv) / [sensitivity counterparts](results/constrained_v1/sensitivity_sessions.tsv), independent [primary paired analysis](results/constrained_v1/primary_analysis.json), [sensitivity paired analysis](results/constrained_v1/sensitivity_analysis.json), and [SHA256 provenance](results/constrained_v1/provenance.json) are committed on `main`.

### Main results: quality *after* common repair

| Parent cohort | Total sessions | Novel distinct-within-session source-orbit certificate *events* ≤5% | ≤10% | ≤15% | ≤20% |
|---|---:|---:|---:|---:|---:|
| ≤10% source quality | 2,016 | **0** | **15** | 73 | 175 |
| ≤20% source quality | 1,494 | **0** | **7** | 32 | 79 |
| Total | **3,510** | **0** | **22** | 105 | 254 |

These are **certification rows, not necessarily independent unique orbits across seeds/arms**. All 22 ≤10% records occur only at N46,47,50; **zero at N59,60,92,99 in either source-quality cohort**. No source-novel solution within 5% of optimum at any length. The new-to-source orbit criterion correctly excludes **all** current same-length parental orbits, so returning to a third *known* source optimum does not count as newly found.

At N92/99, every method finds no source-novel near-elite child, so no incremental value can be established for the exact spectral envelope. Typical best-session energies collapse back to an existing parent; in N99 the exact envelope arm actually produced average session-best E634 in the primary cohort versus true-energy-mask E553 and source-copy E553; its shuffled-envelope placebo had E637. Under the relaxed cohort the same exact method had mean E715 and the placebo E565, indicating unstable penalty selection, **not** a reliable correlation advantage. At N46/47 all variants typically find a known optimal source at least once; apparently excellent best-session E=Eopt is not evidence of new recombination.

**Verdict:** The tested *balanced inheritance mask only* action family cannot reliably transfer high-quality structures between long source-distinct N59/60 or N92/99 parents under this fixed budget. Exact parental spectral envelope does **not** show a robust advantage over randomized-lag placebo or cheaper true-energy mask search after full repair. Further mask cardinality/penalty microtuning would not be an appropriate response; change the **representation**.

## Better representation is now logically necessary for some known targets

[Exact all-symmetry triple optimum compatibility](results/allele_compatibility_all_orientations.json) shows that across *all* 66 archived known-optimum triples of N46/47/50, direct A/B inheritance cannot produce C, because C necessarily modifies ≥3 bit positions on which A and B agree (N50 requires 8, N47 up to 9). This is an exact finite *known-target* statement; local repair can and sometimes does introduce those required bits. [Independent 12M mask enumeration](results/exhaustive_parent_closure_d21.tsv) corroborates the aligned pure-inheritance damage for 17 finite parent pairs with D≤21.

**Next hypothesis:** jointly optimize a donor inheritance mask x over disagreement sites and a *non-parent consensus innovation* mask z over agreement sites, with matched true-energy and shuffled-spectral controls. See [frozen new representation](innovation/README.md). The new action must improve *repaired* novel near-elite throughput beyond random innovation, ordinary classics, donor-only controls and original strong solvers before neural modeling is justified.

## Limits

- Historical 2009 unrestricted native lMAts ≠ modern 2025 GPU MTS; additional older strong source seeds primarily enrich N46–60.
- One published source pair per N92 and N99 cannot support source-diversity generalization.
- Population-dependent FOS variants have oracle leakage for counterfactual *hidden known archive optimum* tests because they access the entire same-length source training pool. That is disclosed, and separate pair-only innovation controls do not use those hidden targets.
- All 3,510 sessions use the same common repair kernel and wall timer; this is not a full independent modern LABS solver versus tuned GOMEA benchmark.
- Multiple repeated child search trials are not independent source families and cannot be bootstrap-sampled as though they were.

**No N100 record, no neural generator result, and no changes to the independent `labs-100/` owner.**
