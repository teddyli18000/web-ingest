# Sealed third-optimum C: prospective, source-disjoint repair counterfactual (2026-11-08)

## Goal

For genuinely distinct published LABS optimum orbits at N=46,47,50, ask whether search history and exact joint autocorrelation constraints contain **incremental, transferable** information for recovering a high-quality basin **different from A**, after controlling the same initial damaged state and a costed local-search budget.

This is a research protocol, **not** a claimed neural generator or benchmark against modern GPU MTS. Public exhaustive enumeration establishes all optimal orbits for N≤66 [Packebusch & Mertens, 2016](https://doi.org/10.1088/1751-8113/49/16/165001). [Original high-quality corpus](../../data/combined/combined10.tsv) was independently direct-E and eight-symmetry verified. Exactly **3 optima N46 E131**, **6 N47 E135**, and **3 N50 E153** are eligible; `c50_3 E161` is **not** an optimum and must be excluded. At most 12 source-optimum identities exist here, **not 12 independent scientific replicates**.

## Latest exact-verified outcomes: 3 lengths, full-C and source-new structure audit

[Complete frontier-orbit audit](NEAR_ORBIT_RESULTS_20261109.md) (source-registry novelty exact checks; [N46 data](results/near_orbit_N46/near_orbit_audit.json), [N47](results/near_orbit_N47/near_orbit_audit.json), [N50](results/near_orbit_N50/near_orbit_audit.json)) establishes **zero wholly archive-new ≤5% symmetry orbits** in every length, treatment and state tier. In the real A/B-blind tier, 10%-near-best corpus-new success is uncommon, with N46 short-radius ILS 9/72 single incumbent vs 11/72 alternating-X; N47 A-only alternation 4/72 and short-radius ILS 2/72; N50 fake-B all-X simple restart 4/72 (only 2 global-new orbit identities), while true-B and both learned models obtained only 1/72 each. These outcomes must not be called different energy basins until convergence is independently studied.

[Full-cost C-only first-hit orbit forensics N46](results/branch_fresh_N46/C_recovery_forensics.json), [N47](results/branch_fresh_N47/C_recovery_forensics.json), [N50](results/branch_deploy_v1/C_recovery_forensics.json): first hidden-C recovery in almost every alternating-X A/B-blind instance occurred **directly from original X**, while the rare N50 single-parent ILS hit came from an intermediate state. All 3 lengths also show substantial *C-shell* restoration gains over a single incumbent, but C-shell states were privileged formed using hidden C.

A stronger N50 control [repeatedly repairing original X only](results/all_x_20261109/all_X_vs_alternating_verdict.json) beats alternating-X on C-shell (real-B 28 vs 25/72, fake-B 27 vs 25, A-only 26 vs 23, learned full 27 vs 24) with the same full 150ms clock; this favors **classical multi-start from an informative anchor**, not an elaborate two-state policy. The one N50 source-blind real-B fixed-X C hit is [independently traced](results/all_x_20261109/C_first_return_forensics.json) from X at symmetry distance 22 from C. [N46/N47 analogous independent damaged-seed all-X replication protocol](CROSS_LENGTH_RETENTION.md) explicitly distinguishes unseen damaged state from genuinely unseen target optimum orbits.

**No network architecture gain is established.** C-shell restoration and isolated C returns from A/B do not amount to a new source-distinct front-line LABS solution or prove incremental true-parent B value over random fake B. Source parent target identities are few (3/6/3 exact optimum orbits); N50 orbit population was already exposed before the subsequent mechanism experiments. Modern strong MTS/GOMEA comparison also remains to be performed.

## Current verified state — 2026-11-09

[Detailed exact-output study](RESULTS_20261109.md) | [first sealed N50 verdict](results/test50/verdict.json) | [new-seed forced-action N50 verdict](results/test50_forced_v1/verdict.json) | [candidate reachability audits](results/bank_test50_forced_v1/bank_reachability.json) | [two-state representation audit](results/branch_test50_forced_v1/branch_causal_diagnostic.json).

**The strict test failed to show cross-basin learning**: original N50 AB_blind hidden C hits 0/72 per method; all 17/72 C_shell returns came from the same initial direct local repair. A no-op classical benchmark defect was found after first test, and all follow-ups on N50 are therefore **exploratory** rather than a second sealed holdout. Second frozen model based on N46/N47 nonzero actions: N47 cheap history selected mean postrepair E219.118, exact-joint+history E219.333; no incremental structural advantage. Fresh N50 seeds rep8–15: 864 full-time 150ms treatments, exact E for 697,569 events; all six AB_blind methods hit C zero times. The two true-B and one single-ILS non-A optimum hits all returned to the **provided B orbit**, not hidden C. C_shell 21 shared first-repair returns; ILS one extra, neither learned model any extra.

**Critical representation gate**: among 6,480 exactly evaluated j=1..5 donor candidate repairs, the post-first-repair N50 AB_blind and 51 C_shell failures contained **no reachable hidden C**, even to an oracle. Reinterpreting search state to keep the original damaged X in parallel, 12,960 more exact repairs found **one** N50 C_shell reachable candidate (X was 4 flips from C, greedy incumbent moved 20 flips away), but no AB_blind reachability and neither model chose it. C_shell is privileged target-conditioned evidence, not real C discovery. [Live costed two-state experiment source](run_retention.py) separately evaluates alternating exploration from X and repaired incumbent under identical full-budget controls.

**Current decision:** Model feature sophistication has not earned a deep architecture. First distinguish reachability failures, known-parent B reconstruction, and third-orbit target C innovation. Need genuinely new A/B-blind positive examples from independent orbit populations before claiming learnable cross-basin structure.

## Hard leakage barriers

1. Group at the **entire eightfold LABS orbit**, not string, and do not duplicate the same orbit under reversal, complement or alternating sign. A, B, C in each scenario are distinct.
2. Strict length split: **N46 training, N47 model selection/calibration, N50 final sealed test**. Thus neither test C nor its orbit appears in any train/validation data, and not even a test A or B orbit is shared with training. Test N50 optimum bitstrings must be excluded from training artifacts, features, model, and policy configuration.
3. At solver runtime, read **only** `scenario-input.tsv`, containing (N, A, true B, intermediate X, initial-state provenance, random seed); **never pass `C` or a C-containing `vault.tsv` to the search executable**. Separate independent post-run scorer reads the vault and target C after outputs exist. A public benchmark is procedural rather than cryptographically sealed, so the public parent catalogue may contain C; the executable must be audited for zero such file access.
4. No raw bitstring, absolute position-specific feature, stored C target signature, sequence lookup table, parent ID, or source-length fingerprint in the learned model. Use dimensionless summary values only (candidate E and pre-repair correlation features, Hamming to given A/B, second-order exact correlation interaction, compact known search history). Train on C outcomes **only within the N46 training portion**; choose model hyperparameters on N47 **without** fitting coefficients there; freeze model hash before any N50 policy run.
5. Each scenario's **initial X is identical across all arms**, with separate paired seed streams for arm decisions. Do not silently change initial quality/distance or use C-based route hints to generate what is labeled a blind test.

## Two explicitly separate starting-state regimes

- **AB-blind (primary):** generate X using *only A, B* and seeded donor/consensus perturbations; C is never accessed by the generator. This tests genuine source-blind cross-basin structure transfer. Record actual E(X), Hamming to A/B, symmetry and quality strata.
- **C-shell (diagnostic positive control):** an offline, privileged data constructor makes X by perturbing a hidden optimal C by a prespecified Hamming radius. Solver still cannot read C; however **X itself is conditioned on C**. Report separately. Its target-recovery ability measures local restoration and does **not** prove algorithms can discover C from A/B in a blind deployment. At a given scenario, all arms get exactly the same X.

Known targets C are scored by an offline process after actions. Primary labels are **any symmetry-distinct non-A optimum** and **target C orbit** (two metrics); report return to A, B, other known optimum and new near-optimum basin separately. No scoring or postrepair adaptive action can consult C target bits, even in the diagnostic C-shell tier.

## Treatment classes and cost accounting

- **A-only:** ordinary exact-energy single-source repair/short-radius ILS, with no true or fake B information.
- **True B:** identical local repair and proposal budget, with the actual B spatial support and usual exact-E candidate ranking.
- **Fake B:** B support replaced by a uniformly random same-Hamming-cardinality disagreement set, otherwise identical proposal/rank/repair costs.
- **Learned history+joint constraints:** frozen low-capacity model trained **only on N46 repair episodes**, selected through N47 calibration; rerank the *same* candidates as true-B by the model's past-result and exact LABS joint-epistasis summary. Does not get free extra fully repaired proposals; record feature+inference+training cost separately and include on-line feature extraction in search clock.
- Always include a **strong direct native `steepest → 64 accepted Tabu7 → steepest` repair(X)** baseline, not merely naive flip/descent.

Within a matched state and treatment, run all proposal generation, exact scoring and local repair under the same end-to-end wall-time cap; report both wall time and number of complete repair calls. Do not force equal repair counts while pretending the additional model complexity was free.

## Primary outcomes and uncertainty

*Primary*: probability of reaching any **other** exact optimum orbit (non-A) from X, with **C-orbit hit** as separately measured hidden-target positive control; report state-stratified outcomes by N, start mechanism, A/B/C orbit triple and seed. *Secondary*: first hit time, best **other-orbit** energy (exclude A return), distinct repaired orbit yield ≤1/5/10% of known optimum, source proximity, return-to-A, repair count and budget, stratified by initial E(X)/distance and C-shell corruption radius.

At N50 the only true final scientific replication units are **three optimum orbit identities** sharing the same source population. Seed replicates allow conditional within-orbit uncertainty, **not independent biological/structural populations**. Use paired context differences, orbit-cluster bootstrap and exact binomial intervals where applicable. Because N50 has only three optimum orbits, absence of a treatment effect must not be promoted to universal failure of learnability.

A *positive neural architecture gate* requires robust heldout N50 gain from learned history+joint features over true-B, fake-B, A-only and a cheap exact-energy history model **on postrepair alternative optimum recovery** under equal cost, and a positive training/validation signal not reliant on C-shell preparation. Otherwise keep the experiment as negative/diagnostic and do not train a transformer/diffusion model.

## Sources, prior falsifications and experiment state

- [Historical true/virtual-parent, actual postrepair outcome and 1080 verified sessions](../basin_search/README.md): source-novel near5 success did not establish true B causation; identical N60 E226 also recovered with fake B.
- [Exact 66 known optimum triple structure study](../results/symmetry_robust_paths_v1.json): may be consulted **only after final test**, never used in candidate features or test scenario construction.
- [Full native-LABS 64-step repair](../../../recombine.cpp); no need for new bespoke objective.
- [Original memetic LABS algorithms](https://www.sciencedirect.com/science/article/pii/S1568494609000404).
- [2026 adaptive GPU SAW](https://arxiv.org/abs/2607.09688). This is modern comparison context, not a baseline reproduced by this small controlled study.

**Status:** strict protocol frozen. Experiments, exact validation, heldout costed deployment and results below will be added only once actually verified. No changes to `science-boundary/labs-100/`.
