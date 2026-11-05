# Distinguish parental structural information from elite-centered restart (2026-11-05)

## Primary falsifiable claim

An aligned second LABS parent B may provide useful **spatial information in its disagreement set** D(A,B), beyond what a single elite parent A, the count |D|, and an equally costed local repair can provide. Does that information improve the **rate of genuinely new, high-quality post-repair symmetry orbits**?

### Exact identity, no machine learning required

Let A,B∈{−1,+1}^N and D={i:A_i≠B_i}. A pure crossover choosing B at subset M produces
`child_i=A_i * (−1)^{1(i∈M∩D)}`.
Therefore any binary LABS allele-only crossover is **literally structured mutation of A, confined to D**. It cannot create a new allele type on a site where A and B agree. More generally, selecting donor sites X⊆D and source-consensus innovation sites Z⊆Dᶜ produces `child=flip(A,X∪Z)`. This exact reduction is why two-parent effects must be distinguished from the *location of their disagreement mask*, the *number of changed sites*, local repair, and bias toward an existing parent. The second parent contributes a mask geometry D, not new binary alleles. Different eightfold symmetry alignments change D and must be declared as part of the representation.

### Frozen experimental design

Source: same certified, symmetry-distinct 29 ≤10%-near-optimal parent orbits from `../data/combined/combined10.tsv`, N46/47/50/59/60/92/99, including different public-source N92 and N99 certificates and the independently seeded native 2009 solver sources at smaller N. No synthetic perturbed record is used as a second parent. Parent-source A/B may be permuted per independent generator start for directional fairness; partner B always aligned by minimum orbit-Hamming before computing D. Denote d=|D|, h=floor(d/2), Q=Dᶜ, r=(N≤47?4:N=50?8:6), H=h+r. All matched-radius proposal arms flip exactly H bits relative to A **before** the common repair.

Fixed 11 arms (source identity is never leaked to an independent training corpus):
0. Original parent-copy + common repair.
1. **Single-parent H-bit uniform random mutation**, no second-parent information, H matched.
2. **Actual two-parent disagreement mask D**: h uniform flips inside D plus r innovation flips in Q. Identical to balanced two-parent inherited alleles + consensus-site mutations.
3. **Randomized disagreement support D′**: choose random d of N as fictitious donor mask, same h/r selections (position-null). No actual partner sequence is used beyond the count d.
4. Optimize true immediate LABS energy by 24 *joint* 4-bit selected↔unselected swaps in real D and Q masks (group cardinalities exact).
5. Same true-energy optimization but with *randomized D′* (the placebo with identical group size and evaluation/move geometry).
6. Unrestricted single-parent fixed-H mask, optimize true energy by 24 2-bit selected↔unselected swaps, same Hamming radius.
7. **Small-radius strong elite restart**: uniform mutation at 2/4/8/12 bits, entirely independent of the second parent. Distinct from matched-radius contrast, included to test whether any actual two-parent action is useful rather than just a giant damaging jump.
8. Small-radius single-parent mask true-energy optimization with 24 swaps, same low-radius family as arm 7.
9. Real D balanced inheritance+consensus with four costed steepest-descent pre-quench candidate selections, from the original rare E226 generating method.
10. Unrestricted single-parent H-radius with four costed steepest-descent pre-quench selections (tests incremental value of D at same quench cost).

**Budget:** 120ms actual full wall-clock per (source pair, seed, arm), all proposal/model generation, exact E evaluations, and standard original-LABS steepest-descend →64 Tabu moves →steepest-descend common repair. 56 certified source pairs ×5 seeds ×11 arms = **3,080 full sessions**. All output source orbits, best terminal word, source-relative distances and new ≤5/10/15/20% certificates independently scored using a separate O(N²) implementation. Only unique-within-session new source-orbit certificates counted. Exact source-pair clustering for uncertainty, full competing count denominator and all-length coverage. Same B-disagreement *cardinality* and Hamming-from-A in arms 1–6/9/10; arm 7–8 are stronger unrestricted small-radius solvers whose distance differs by design.

### Pre-declared conclusion criteria

A genuine two-parent structural advantage requires consistent **repaired** new-source near5/10 orbit yield beyond (i) single-parent same-H radius, (ii) random D′ of same size, (iii) true-energy-optimized D′, (iv) elite-centered small-radius ILS and (v) post-quench-aware single-parent H; ideally also under independent new-source-family held-out lengths N59/60/92/99. Difference in immediate raw E or copying back a source parent is not enough. If both true D and random D′ do equally badly, the second parent's putative spatial contribution is not established. If better, test more genuinely independent parents, stronger full solver-level and modern GPU MTS before proposing NN/dual-branch encoder.

### Historical findings preserved

- [Round1](../ROUND1.md): 1000 classic crossovers, source-only GOMEA-style controls and post-repair failures at high N.
- [Round2](../ROUND2.md): 3510 balanced donor and exact-lag envelope/lag-permuted sessions; no stable incremental spectrum benefit.
- [Round3 and independent replication](ROUND3_REPLICATION_ORACLE.md): 2500 unseen-seed 4-parent-pair sessions, N60 E226/ N59 E209 near5 and 64/66 exact third-optimum triples with a monotone *known-target* consensus-repair order under some symmetry.
- [Relative alignment trial](results/symmetry_planning_v1/analysis.json): 1176 target-blind sessions, novel <=10% in only N46/47/50 (8 certificate events, 5 distinct orbits); zero <=5% all lengths. Parent alignment oracle does not translate into a prospective advantage.

No N100 record claim; do not change `science-boundary/labs-100/`.
