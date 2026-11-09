# Sealed third-optimum C: prospective, source-disjoint repair counterfactual (2026-11-08)

## Goal

For genuinely distinct published LABS optimum orbits at N=46,47,50, ask whether search history and exact joint autocorrelation constraints contain **incremental, transferable** information for recovering a high-quality basin **different from A**, after controlling the same initial damaged state and a costed local-search budget.

This is a research protocol, **not** a claimed neural generator or benchmark against modern GPU MTS. Public exhaustive enumeration establishes all optimal orbits for N≤66 [Packebusch & Mertens, 2016](https://doi.org/10.1088/1751-8113/49/16/165001). [Original high-quality corpus](../../data/combined/combined10.tsv) was independently direct-E and eight-symmetry verified. Exactly **3 optima N46 E131**, **6 N47 E135**, and **3 N50 E153** are eligible; `c50_3 E161` is **not** an optimum and must be excluded. At most 12 source-optimum identities exist here, **not 12 independent scientific replicates**.

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
