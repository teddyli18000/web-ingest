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


## First 9-pair, 216-session exact pilot — completed 2026-11-08

[Verified source-pair/seed results](results/pilot_v1/analysis.json) | [All 216 rows](results/pilot_v1/sessions.tsv) | [84 recorded novel ≤20%-orbits](results/pilot_v1/novel.tsv) | [successful native selftest and independent exact verifier](https://github.com/teddyli18000/web-ingest/actions/runs/42575167393).

Nine true source-distinct parent pairs × four pre-fixed seeds × six methods × **150 ms inclusive** = 216 complete sessions. Original and virtual donor models use identical cardinality, and every proposed candidate in methods 0–4 undergoes the exact common steepest → 64 accepted native Tabu moves → steepest before acceptance is decided.

**Principal outcome:** zero **new source-orbit ≤5%** offspring in all 216 sessions. Source-novel ≤10% successes occur **only N46/47** (N46 true-B random=3, postrepair-guided=2, virtual-B postrepair-guided=2, novelty-guided=2; N47 true-B random=1, novelty-guided=1). At N50/59/60/92/99 there are **zero source-novel ≤10%** offspring under *any* method. These are not 216 independent source lineages; there are nine overlapping parent-pair families.

There is a candidate-quality benefit but not new high-grade structure: at N59 source pair c59_0-c59_2, raw/true random/postrepair-guided full-repair best mean E=278/282/**259**; at N92=752/751/**730**, at N99=916/904/**876**. Fake-B postrepair-guided at N92 E756, N99 E878. But **single-source small-radius ILS** preserves known elite E205/E490/E553 respectively and all outcomes are far from the near-elite goal. Individual source-pair improvements are exploratory with four seeds only.

**Important mechanistic distinction:** optimizing postrepair E indeed can outperform optimizing pre-repair E in some source contexts, but this does not imply that the actual second parent's structure supplies incremental near-elite recombination benefit. N99 true B guided E876 vs virtual B guided E878 is indistinguishable at this scale. Therefore do **not** train a network on this positive raw-quality proxy.

The compile-only first run [42575062349](https://github.com/teddyli18000/web-ingest/actions/runs/42575062349) failed due to missing C++ `<memory>` and reused loop variable before any experiment. The corrected run completed, passed integer energy and eightfold orbit identity checks, and committed input SHA256 and all raw offspring certificates.

## Frozen out-of-sample replication

Use the **unchanged same six candidate/repair rules**, same nine fixed source pairs, but **16 independent unseen seed indices 4–19** (seed offset 4) and **250 ms full time** per session; 9×16×6=864 paired sessions. Because budget differs from the pilot, this is a longer-cost *independent-seed test*, not identical-protocol replication. Primary true-B guided vs virtual-B guided **novel ≤5/10%** success and source-pair-clustered repaired-E difference. Also compare same-source raw-E-guided, true-random and short-radius ILS. All nonparent canonical sequences must pass independent integer energy and source registry checks. Treat first nine pair contexts as nine not 864 independent parental scientific samples. The negative pilot does not support increasing this exact local-mask family indefinitely; this one replay is the defined final evaluation gate.


## Held-out seed replay — completed and independently verified

[Successful run 42575682860](https://github.com/teddyli18000/web-ingest/actions/runs/42575682860). [Full 864 source-run sessions](results/replay_v1/sessions.tsv), [all 343 independently re-scored novel ≤20% endpoint certificates](results/replay_v1/novel.tsv), [independent exact score/orbit verification](results/replay_v1/verified.json), [source-pair bootstrap](results/replay_v1/paired_analysis.json), and [source revision / SHA256 provenance](results/replay_v1/provenance.json). Every parent, final candidate and recorded novel child was evaluated by independent integer O(N²) LABS scorer, eightfold canonical orbit and explicit parent registry. Same nine pairs ×16 previously untested seeds 4–19 ×6 arms = **864** sessions at **250ms all-cost inclusive** each. These share source pairs with the 216-pilot but not search seeds or budget, so don't pool outcomes as if identical interventions or 1,080 independent parents.

### Primary near-frontier novel structure outcome

| Arm | Source-novel ≤5% session events | Source-novel ≤10% session events | Distinct source-new ≤10% orbits over all lengths |
| --- | ---: | ---: | ---: |
| 0 true B random inheritance | 0 | 7 | 5 |
| 1 true B true-immediate-E swaps | 0 | 2 | 1 |
| 2 **true B postrepair-E mask search** | **0** | **5** | **2** |
| 3 fake B same geometry and postrepair search | **1** | **6** | **6** |
| 4 true B postrepair-novelty search | 0 | 5 | 3 |
| 5 elite-A short-radius ILS | 0 | 4 | 3 |

**The sole ≤5% success in the replay occurred in the *fake-B* condition**, at N60 pair `c60_2-c60_5`, seed 5, repaired E226, full canonical `000001111000000010001011011011101011010100110001101001110011`. The exact same **N60 E226 orbit** was previously found in a genuine two-parent experiment using different parents, and is not a novel discovery relative to the complete historical research result registry. It was only novel relative to the frozen **source-parent** registry. That is strong negative evidence against treating any previous isolated E226 hit as proof the real second parent contributed the causal necessary feature. It is NOT evidence real parental information is generally worthless; the matching fake geometry still shares its Hamming statistics and original A elite.

For N≥59 (six pair contexts), **the true-B postrepair-guided and true-B novelty-guided arms generated zero ≤10% novel events**. The fake B arm generated two ≤10% events (one E226, N60 and one N59), versus true-B random one and raw-E true B zero. N92/99 zero novel ≤10% across all arms. The total of 7+2+5+6+5+4 successful discovery events should not be treated as distinct independent discoveries; the distinct-orbit column above handles duplicates.

### Source-pair clustered costed secondary quality comparison

Comparison = mean per-pair final **best repaired E** of comparison method minus true-B postrepair-guided E; positive favors true B. Nine-pair bootstrap with the nine source pairs as clusters, 10,000 draws, unadjusted exploratory 95% intervals:

- True-B random minus guided: **+2.19**, CI [−1.56,+7.33].
- True-B immediate-E swaps minus guided: **+4.06**, CI [−1.00,+9.92].
- Fake B postrepair-guided minus true B postrepair-guided: **+3.17**, CI [−1.03,+8.11].
- Single-elite ILS minus true B postrepair-guided: **−97.25**, CI [−176.98,−35.58]; this is largely preservation or return to an existing excellent source, **not** creation of new structures.

Among six N≥59 pairs, fake B minus true B is +4.46 [−0.17,+10.58], still spanning zero, and N92/99 separately show negligible +0.75 and +1.00 differences per pair in final best E. Numerical gains are tiny compared with inherited-parent damage (e.g. N99 true B guided mean best E873, while A original E553). Source pairs within the same length share parents; **nine clusters are not nine fully independent source populations**. Inference is therefore descriptive and unadjusted across multiple methods.

### Verifier and parent geometry

[Independent 29-orbit audit](results/cohort_geometry.json), successful [workflow 42576015594](https://github.com/teddyli18000/web-ingest/actions/runs/42576015594), confirms seven length groups have 3/6/4/6/6/2/2 distinct exact-energy eightfold orbits, respectively. N46 and N47 parents are all *known best*; N92 exact cross-source pair Hamming distance **38**, N99 pair distance **41** after best symmetry. **An archive optimum orbit may not be a separately documented solver-run lineage**: these are legitimate independent *genetic structures*, but independence of historical optimization processes is narrower. N100 is not included because there is no second independently sourced elite orbit.

### Research decision

**Stop this static donor-half + consensus-r (+postrepair hillclimb) operator family.** It now fails the genuine-new-frontier structure gate in both pilot and unseen seed replay despite a real B-vs-fake B quality-preservation signal in early work. Crucially, making mask acceptance depend on actual basin fate did **not** solve the dominant failure. The stronger family should evolve the *interface*: permit donor-group cardinality to change and inherited constraints to be released, use **joint A/B signed relative interactions** rather than separate one-parent spectra, and coordinate original-objective repair with a moving spatial inheritance support. A genuinely useful learned policy needs new diverse elite data and an increment over *actual full standard GOMEA*, source-conditioned classical recombination, strong native tabu and modern 2025+ GPU MTS; the current cold-start official GOMEA experiment has a different scope and cannot decide the former.

Do not claim a new N100 record, a new N60 E226 orbit, deep-model superiority, or any source-independent cross-length elite-generation advance.
