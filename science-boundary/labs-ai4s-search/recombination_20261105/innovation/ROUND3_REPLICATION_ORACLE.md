# Round 3 — independent elite recombination replication and structural oracle (2026-11-05)

## Scientific question

Do two genuinely distinct LABS near-optimal parents contain recombinable, transferable information, or are successful offspring mainly rare destinations of local search? Can exact per-lag autocorrelation or **parent-relative eightfold symmetry alignment** improve truly novel, repaired, near-elite offspring yield under cost-matched classic controls?

The proper outcome is **new source-orbit near-elite offspring AFTER fully charged local repair**, not low immediate crossover energy, a conditional predictor trained on successful future events, or a copy of an existing parent.

## Fully verified multi-pair replication (not selected-arm fitting)

[Action run 42035449921](https://github.com/teddyli18000/web-ingest/actions/runs/42035449921); [provenance SHA256](results/replication_v1/provenance.json); [complete independent analyses](results/replication_v1/selected_analysis.json), [holdout60a](results/replication_v1/holdout60a_analysis.json), [holdout60b](results/replication_v1/holdout60b_analysis.json), [holdout59](results/replication_v1/holdout59_analysis.json) and all individually scored result/certificate TSVs alongside those files.

Four distinct high-quality source parent pairs, selected before independent replay:
- selected N60 `c60_1-c60_4`, energies E218/E234: 100 unseen seeds;
- holdout N60 `c60_0-c60_3`, energies E218/E222: 50 unseen seeds;
- holdout N60 `c60_2-c60_5`, energies E222/E234: 50 unseen seeds;
- holdout N59 `c59_0-c59_2`, energies E205/E213: 50 unseen seeds.

**2,500 complete treatments** = 250 source-pair/seed settings ×10 methods ×120 ms full CPU wall per arm, common original-energy steepest descent +64-move Tabu-7 + steepest descent. All near-elite retained offspring independently validated using integer O(N²) energy and eightfold symmetry classes. This is a 2009-era native-inspired short repair benchmark, NOT a competitive full GPU MTS / GOMEA evaluation. All 40 source lMAts runs and all parent orbits are separately certified in this topic.

| Pair | Fresh settings | New source-orbit ≤5% *events* | ≤10% events | Method(s) for ≤5% |
|---|---:|---:|---:|---|
| selected N60 E218/E234 | 100 | 2 | 3 | joint four-bit exact true E; joint four-bit exact spectral envelope |
| holdout N60 E218/E222 | 50 | 0 | 0 | none |
| holdout N60 E222/E234 | 50 | 1 | 1 | alternating donor/consensus true-E swaps |
| holdout N59 E205/E213 | 50 | 1 | 1 | random donor+consensus mask |
| **TOTAL** | **250** | **4** | **5** | *among all 2,500 arm-level fixed-time sessions* |

**Crucial new correction:** all 3 independent N60 E226 near5 successes (2 on the originally selected pair, 1 on a genuinely different holdout source pair) are the **same eightfold symmetry orbit** as the original N60 E226 certificate! This is *repeatable access to one near-optimal basin*, not three independent structural inventions. The N59 E209 near5 success is **one other orbit**, not a new record. Thus there are **only two** distinct length-separated near5 orbit targets across this replication, compared with one N60 original discovery. Near5 offspring are not always exact replicas in bit orientation, but they collapse to the same canonical identity.

N60 E226 canonical:
`000001111000000010001011011011101011010100110001101001110011`
N60 certificate direct E=226 (public global E218, 3.67% above), nearest parent orbit distance 24 in original selected pair; selected pair label `c60_1-c60_4`.
N59 E209 canonical:
`00000010110100000010010011010101110100111000001100011001110`
E209 (public global E205, 1.95% above), nearest A/B orbit distance 25, holdout pair `c59_0-c59_2`.

The **originally successful arm 8, costed 4× steepest-descent oracle-free pre-quench selection**, obtained **zero additional near5 successes on 100 new seeds** of its selected pair, while raw-energy and exact-spectrum variants each scored the same E226 orbit once. The N59 target was obtained from the simplest random donor+consensus method, the other N60 holdout from true-E alternating swaps. So exact spectral features **do not** have demonstrable cross-parent, cross-length incremental unique-orbit yield.

Original run [42034371482](https://github.com/teddyli18000/web-ingest/actions/runs/42034371482) and a full repeated fixed-seed run [42035310028](https://github.com/teddyli18000/web-ingest/actions/runs/42035310028) have slightly differing loose ≤10/≤20 offspring counts due wall-clock evaluation count variation, despite identical seed assignments, while the sole original N60 E226 certificate was reproduced. **Do not treat those runs as fully independent seeds.** Main prospective replication uses *fresh* integer seed offsets 1000/2000/3000/4000.

## Mechanism: offspring required repair of source-consensus bits

Each source pair is aligned over eight exact LABS symmetries. At initial construction exactly **6** sites at which the two source parents AGREE may be flipped. Yet the final certified near5 offspring require the following minimum source-consensus edits over **all 8³ simultaneous representations**:

| Pair | Final target | Source-consensus flips required in any representation | Candidate construction quota |
|---|---|---:|---:|
| N60 E218/E234, `c60_1-c60_4` | E226 | **8** | 6 |
| N60 E222/E234, `c60_2-c60_5` | E226 | **10** | 6 |
| N59 E205/E213, `c59_0-c59_2` | E209 | **8** | 6 |

Therefore the common 64-step Tabu/steepest repair **necessarily** introduced at least 2–4 *additional net* changes on parent-consensus positions in the path to the certified target (not necessarily monotonic in energy). Source sequence bits and all complete offspring orbits are saved. This is rigorous, narrow evidence for two-stage mechanism: donor inheritance + off-allele reconstruction by local repair. **Not** evidence for a neural generator.

## Known-optimum structural oracle: exact energy path representation

[All 66 triple-optimum oracle paths](results/oracle_consensus_paths_v1.json) via [source](oracle_correction_paths.py), independently checked in Action [42038344400](https://github.com/teddyli18000/web-ingest/actions/runs/42038344400) using a second O(N²) scorer for **all 2^k** correction states per triple. This is a *hidden known answer* diagnostic with target C explicit, never input to a prospective solver.

Known N46/47/50 exact optimum triple A/B→third optimum C needs **3–9** edits where parents agree, under all 8-fold symmetry transformations, confirmed in [prior 66-triple inheritance incompatibility](../results/allele_compatibility_all_orientations.json). After choosing the *minimum-edit and minimum-precursor-energy representative*, target-guided exact mask enumeration and optimal order DP find:
- N46: 3/3 triples can complete consensus corrections by a non-increasing one-bit sequence.
- N47: 53/60 can, **7/60 require a positive-energy step** under that ONE chosen orientation.
- N50: 3/3 can. Even when monotone completion exists, greedy ordering may be much worse: N47 average greedy total uphill 8, globally minimal 1.73 and random-order mean uphill 75.85 under the chosen representation. These are descriptive oracle numbers, **not transferable to unseen target C**.

A more stringent [all 8×8 relative orientations for fixed A](results/symmetry_robust_paths_v1.json), [source](symmetry_robust_paths.py), independently validated [run 42038900236](https://github.com/teddyli18000/web-ingest/actions/runs/42038900236), reveals:
- Of the apparent 7 uphill-obstructed N47 triples under the first chosen orientation, **5 are eliminated by changing the relative parent/target symmetry alignment**.
- **Only 2/60 N47 triples**, and 2/66 overall, require positive cumulative uphill to complete the minimum-consensus-edit correction even under *every valid relative symmetry alignment*. Their minimum cumulative uphill costs are **20 and 4**.
- The other **64/66 triples admit some monotone completion** of the *target-known* consensus corrections after an appropriately chosen orientation.
- For these exact finite cases, symmetry alignment and edit ordering are substantially **coupled decision variables**, not mere bit-distance normalization. Do not assert that 2/66 is a universal low-N LABS property or that a target-unknown solver can find these paths by itself.

**Critical insight for algorithm design:** when the known target C is held out, identifying the helpful relative symmetry orientation by cheap features (rather than minimizing parent Hamming distance) might improve fully repaired new elite production. This is a stronger, more operationally testable representation than simply increasing fixed-size source-consensus mutations.

## New prospective source-only symmetry-planning test (running/validation gate)

[Source](symmetry_planning.cpp), [independent verifier](validate_symmetry_planning.py), one-shot [Action workflow](https://github.com/teddyli18000/web-ingest/actions/workflows/temp-labs-ai4s-relative-parent-symmetry-planning.yml).

**No target C labels, no hidden known optimum structure used for operator decisions.** Same 29 source-distinct ≤10% parent orbits, **56 pairs across 7 lengths**, 3 seeded runs, 7 arms = **1,176 total budgeted 120-ms sessions** including all orientation selection, mixed donor+consensus proposal, four candidate pre-quenches, and full 64-step local repair. Compared arms: minimum-Hamming alignment, fresh random alignment each child, maximum-Hamming alignment, minimum-mean raw energy over 16 proposals per orientation, minimum-best raw energy over 16, and minimum-best pre-quench energy over two probes per orientation, plus source-copy. Primary metrics: source-novel ≤5/10% terminal child orbits, symmetry-aware parent distance, total CPU/wall cost, source-parent-pair clustered outcomes; never select a model architecture on in-sample mean score only.

A first workflow [42039795779](https://github.com/teddyli18000/web-ingest/actions/runs/42039795779) failed at C++ compile due to main include and type/brace errors, no scientific calculation. The code was corrected and a fresh workflow was launched. If it cannot pass full independent exact verification, do NOT claim a result.

## Literature and external bar

- [Gallardo, Cotta & Fernández 2009 classic LABS memetic recombination](https://www.sciencedirect.com/science/article/pii/S1568494609000404): classic crossover and original memetic recombination must be compared; currently our GOMEA experiments are only approximations, **not complete optimized published GOMEA**.
- [Pšeničnik et al. 2026 GPU parallel SAW with Thompson sampling](https://arxiv.org/abs/2607.09688) and [2025 dual-step GPU search](https://www.sciencedirect.com/science/article/pii/S1051200425003380) are far stronger modern solver-level baselines. Their advances primarily concern restriction-class scheduling and GPU high-performance search; do not confuse native 2009 120ms local Tabu repair with these algorithms. No claims of solver boundary breakthrough until matched whole-solver budget, unseen lengths, and genuinely near-frontier elite states.
- Full result conservation, source-run hashes, failures, data, verifiers, and instructions are under `science-boundary/labs-ai4s-search/recombination_20261105/`. **Do not modify `labs-100/` or submit as the separate p006 owner.**

## Decision gate

Progress to neural generator only after a target-unknown, cross-source-family, cross-length **significant improvement of rate of new repaired elite orbits over exact-score classical operators, source-copy, relative-orientation selection controls, and optimized local repair**. The current rare N59/60 certificates and two-barrier oracle are mechanistic evidence, not that gate.
