# Innovation round 1: exact donor-plus-consensus coupled search (2026-11-05)

## Source-backed completed experiment

[Successful 1,680-unit run](https://github.com/teddyli18000/web-ingest/actions/runs/42034371482), [source](innovation.cpp), [independent Python exact scorer and eightfold symmetry verifier](validate.py), [all session records](results/combined10_sessions.tsv), [all 217 retained unique-within-session source-novel ≤20% offspring certificates](results/combined10_new_children.tsv), [analysis](results/combined10_analysis.json), [machine/source SHA256](results/provenance.json).

The prior exact finite triple result [66 source-parent/third-optimum combinations](../results/allele_compatibility_all_orientations.json) established that another *known* N46/47/50 optimum always requires **changes at 3–9 positions shared by both source parents**. This motivated a real search-space reformulation rather than larger neural networks or tweaking lag weights.

For each of the same **29** certified source-distinct ≤10%-near-optimal parent orbits across N46/47/50/59/60/92/99, choose aligned parents A and B and split positions into donor disagreement set D and parent-consensus set Q. A proposal selects exactly floor(|D|/2) donor positions and flips **r positions in Q** not provided by either parent, where r was fixed *before observing outcomes*: 4 at N46/47, 8 at N50, 6 for N59/60/92/99. The result uses A's value on other coordinates. Offspring receive identical original energy steepest descent, **64** Tabu-7 accepted flips, and final steepest descent, with **all proposal generation, scoring and repairs charged** to 120 ms total per source pair/replicate/arm. A source-copy arm and donor-only exact-E swap arm are included as crucial controls.

10 arms, 56 source parent pairs × 3 separately seeded runs × 10 = **1,680 complete exact-verifiable budgeted sessions**:

0. Donor-only true-E 24-swap optimization;
1. Uniform donor+consensus masks (24 fresh proposals per generated child);
2. Donor-only swaps with consensus flips frozen;
3. Consensus-only swaps with donor flips frozen;
4. Alternating independent donor/consensus swaps under true energy;
5. One **coupled 4-bit** donor+consensus swap under true energy;
6. The same coupled geometry under E plus exact lag-wise parent autocorrelation-envelope exceedance penalty;
7. Lag-envelope-shuffled placebo with identical geometric move;
8. Four costed steepest-descent pre-quench evaluations from random donor+consensus masks, select lowest prequench E and apply common full repair;
9. Simple source-copy baseline plus common repair.

**All methods 0–8 use only the two exposed parent sequences as context** and never train on a hidden third optimum. No trained neural model, full GOMEA solver, or modern GPU-MTS involved.

## Repaired offspring results

| Source N | Independent source pairs | New source-novel ≤5% events | ≤10% events | ≤15% events | ≤20% events |
|---|---:|---:|---:|---:|---:|
|46|3|0|8|27|61|
|47|15|0|11|60|130|
|50|6|0|4|13|21|
|59|15|0|0|0|3|
|60|15|**1**|**1**|1|2|
|92|1|0|0|0|0|
|99|1|0|0|0|0|
|**TOTAL**|**56**|**1**|**24**|**101**|**217**|

These counts represent retained *source-orbit novelty certificate events within a session*, not unique independent new discoveries across all sessions. New means not present in the entire **29-orbit input parent library**; there may be historical other records and no first-ever discovery is claimed.

### The one successful near-elite transition

At N60 source pair `c60_1-c60_4`, source parent energies E218 (archived optimum, also independently recovered from native 2009 solver) and E234 (another independent native source run), replicate 1, **arm 8** (costed pre-quench-aware random donor+consensus mask generation) produced **exact E226**, 3.67% above exhaustive N60 E218. Certificate:

`111110000111111101110100100100010100101011001110010110001100`

Canonical eightfold orbit:

`000001111000000010001011011011101011010100110001101001110011`

The solution is **not near-skew**, and has minimum Hamming distance **24** to either complete source parent symmetry orbit. All 9 other methods at exactly this pair/replicate failed to generate a new ≤5%-near-optimal source orbit, including donor-only exact E and full lag-envelope approaches. Nevertheless **this is a single selected event**, not reproducible superiority; the baseline source-copy arm always obtains E218 from the parent, so E226 is *structurally new but energetically worse than the original best*.

### Representation quality and current limits

- At N46/47/50 the source-novel ≤10% certificate counts increase compared with more conservative source-only methods, but few events and many non-independent source pairs prevent a method superiority claim. At N59 and N60, most unselected innovations damage quality.
- At the more frontier-relevant N92/99 **zero source-novel ≤10% offspring** occur, and all novel candidate finals remain hundreds of energy units worse than source E490/E553; this mechanism is not a strong new LABS solver.
- The signed spectral envelope adds *some* N47 mean repaired-E value against a lag-permuted placebo (pair-cluster bootstrap interval excludes zero), but the improvement reverses at N50/60 and does not lead to new near5 records. It is a descriptive selected-stratum effect, not heldout cross-length transfer, nor justification for a dual-branch neural architecture.
- The rare N60 E226 event comes from **costed steepest-descent proxy selection**, which is a cheap classical predictor of the ensuing native-like repair. A learned model must beat this strong non-neural history-free proxy under identical end-to-end budget; any policy based on correlation spectrum alone has not earned computational complexity.

## Prospective independent replay / clear gate

The next [independent replication protocol](https://github.com/teddyli18000/web-ingest/actions/workflows/temp-labs-ai4s-innovation-independent-replication.yml) predeclares **100 new seed replicates** on the successful source pair and **50 each** on three *untouched* source-distinct N59/60 pairs, 10 arms each, 120 ms per complete run. Primary: new source-novel ≤5/10% orbit production frequency, not posthoc minimum pre-quench E. All complete certified bitstrings are archived. A single source-pair effect must **replicate across seeds and other genuine source parent pairs** before progressing to neural architecture or modern solver deployment.

No N100 record effort, no official LABS shot, no modification to `science-boundary/labs-100/`.
