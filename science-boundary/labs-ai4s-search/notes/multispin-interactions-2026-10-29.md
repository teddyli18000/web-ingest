# Multispin epistasis and *post-relaxation improvement*: controlled follow-up (2026-10-29)

## Verdict first

**Positive but sharply qualified.** For random-start local minima of LABS(100), the *combined* energy of a coordinated four-bit move contains predictive information beyond the **sum of its four individual flip penalties**. This is confirmed by an independently implemented integer-exact C++ dataset and paired group-level bootstraps. Pairwise interaction terms explain much of that effect. But **the effect collapses in deeper minima, does not consistently survive switching the descent algorithm, and does not produce a measurable cross-length learned-model advantage over exact instantaneous-energy ranking.** We found no N100 energy below 578 and no record submission.

This distinguishes **(i) interaction exists mathematically**, **(ii) it predicts immediate energy**, **(iii) it predicts *post-descent* gain in shallow minima**, and **(iv) it predicts rare improvements across difficult basins**. We substantiate i–iii, not iv.

## 1. Exact analytic structure (not a priority/novelty claim)

For spins s_i∈{±1}, C_k=Σ_i s_i s_{i+k}, and E=Σ_k C_k², expansion gives the exact *balanced-quartet* Hamiltonian:

\[
E(s)=\frac{N(N-1)}2+2\sum_{\substack{2\le d<N\\d\ \mathrm{even}}} C_d(s)
+4\sum_{\substack{0\le a<b<c<d<N\\a+d=b+c}}s_as_bs_cs_d.
\]

Proof: diagonal terms of every C_k² give N(N−1)/2; crossed lag-pairs with one shared site give twice even-lag correlations; two disjoint pairs of equal lag form a four-spin term, and a sorted four-tuple admits these pairs iff a+d=b+c, giving coefficient 4. This is an explicit quartic representation of the established Bernasconi/LABS Hamiltonian; no claim that such a representation is historically new.

For four flipped positions S, define Δ_i=E(s^i)-E(s) and I_ij=E(s^{ij})-E(s^i)-E(s^j)+E(s). Exact Möbius decomposition:

\[
E(s^S)-E(s)=\sum_{i∈S}\Delta_i+\sum_{\{i,j\}⊂S}I_{ij}+R_{≥3}(S).
\]

Writing Q for balanced quartets, its **full high-order residual** is:

\[
R_{≥3}(S)=-32\sum_{\substack{Q:\,|Q∩S|=3}}\prod_{q∈Q}s_q
          -64\sum_{\substack{Q:\,|Q∩S|=4}}\prod_{q∈Q}s_q.
\]

Each chosen triple (p<q<r) has at most three completing quartets, with fourth position in {p+q−r, p+r−q, q+r−p} after checking bounds and distinctness. Thus for a **fixed four-flip move**, R_{≥3} can be computed by enumerating at most 4×3 candidate completions, *independent of N*. A coarse absolute bound is 448; its measured standard deviation in our generated data is around 83–88 energy units for N40/64/100, while the **pair sum** SD rises ~133→171→216 in stage-40 minima. The value of R itself is not a universal predictor of eventual basin gain.

**Independent checks:** [motif_identity.py](../motif_identity.py) verifies the full Hamiltonian for 30 random sequences at N8,12,20,40,64,100 and the four-flip residual for 720 independent random actions. The official N100 baseline was also verified via both expressions to be exactly E=578. [fresh_interactions.cpp](../fresh_interactions.cpp) separately self-tests all incremental one-bit Δ values against O(N²) direct energy, post-flip energies and local-descents on N12,24,64,100, and checks the E578 official baseline.

## 2. Independent controlled dataset (not a trained-policy result)

All data generated with the independently implemented [fresh_interactions.cpp](../fresh_interactions.cpp), compiled g++ -O3 -std=c++17. One dataset group = one independent initial random sign sequence, locally minimized with exact deterministic steepest descent; after stage h∈{0,40,120}, h independent uniform random **4-flip** basin proposals each followed by steepest descent, accepting only lower-energy endpoints. From each resulting base, sample **six independent uniform 4-flip candidates**. From every *identical* candidate, compute its pre-relaxation scores and then relax with (a) steepest improvement or (b) first improvement in ascending spin index. One winner selected per six-candidate pool; the rest of the six endpoints are computed for *offline comparison only*. The oracle evaluates all six and is not a fair runtime rival.

| length | stage | independent groups | exact candidate endpoints | median incumbent energy | PRNG seed |
|--:|--:|--:|--:|--:|--:|
| 40 | 40 | 6,000 | 36,000 | 164 | 631499 |
| 64 | 40 | 6,000 | 36,000 | 448 | 726100 |
| 100 | 0 | 5,000 | 30,000 | 1374 | 489773 |
| 100 | 40 | 3,500 | 21,000 | 1150 | 962167 |
| 100 | 120 | 1,200 | 7,200 | 1106 | 602361 |

Total: **130,200 candidates** in five complete, independently seeded datasets, each evaluated by two exact descent operators = **260,400 evaluated final energies**. This total **excludes** warm-start/hopping steps. Two earlier oversized parallel runs timed out: those partial files are *excluded*, not counted as complete. A separate complete 1,500-group N100 stage-40 exploratory replication (seed 882019) showed a different apparent positive pair effect; it is disclosed below rather than silently pooled/cherry-picked.

Reproduction:
\`\`\`bash
cd science-boundary/labs-ai4s-search
g++ -O3 -std=c++17 fresh_interactions.cpp -o /tmp/labs_fresh
/tmp/labs_fresh fresh_n40_stage40.csv 40 6000 631499 40
/tmp/labs_fresh fresh_n64_stage40.csv 64 6000 726100 40
/tmp/labs_fresh fresh_n100_stage0.csv 100 5000 489773 0
/tmp/labs_fresh fresh_n100_stage40_final.csv 100 3500 962167 40
/tmp/labs_fresh fresh_n100_stage120_final.csv 100 1200 602361 120
python analyze_interactions.py fresh_n40_stage40.csv fresh_n64_stage40.csv fresh_n100_stage0.csv fresh_n100_stage40_final.csv fresh_n100_stage120_final.csv --output interaction_statistics.json
python interaction_generalization.py
python motif_identity.py
\`\`\`

Input/rank rules:
- **Singles:** choose candidate with smallest ΣΔ_i.
- **Pair-approximate:** choose smallest ΣΔ_i+ΣI_ij (6 pair interactions).
- **Immediate:** choose smallest *exact* E(s^S)-E(s) (includes 3-/4-order motifs).
- **Oracle:** choose largest actual positive gain max(0,E_base−E_after); included only as ceiling.

Stats are *positive gain*, so going to a worse different basin scores zero. 95% uncertainty intervals use resampling of **independent base groups**, not candidate rows (3,000 paired cluster bootstrap draws). Each comparison uses the *same* base groups and candidate perturbations. Intervals are unadjusted and the multiple exploratory contrasts must not be interpreted as controlled discovery p-values.

## 3. Genuine evidence for multi-bit information, and its limitations

Primary target: positive gain from *steepest* local descent, mean units of E per one executed selected candidate.

| N, stage | Singles | Pair-approximate | Exact immediate | Pair−Singles gain delta (95% CI) | Exact−Singles delta (95% CI) |
|---|---:|---:|---:|---|---|
| 100, 0 | 58.277 | 65.622 | 66.302 | **+7.346 [+5.124,+9.513]** | **+8.025 [+5.722,+10.085]** |
| 100, 40 | 1.909 | 2.129 | 2.265 | +0.221 [−0.225,+0.689] | +0.357 [−0.147,+0.834] |
| 100, 120 | 0.517 | 0.800 | 0.593 | +0.283 [−0.045,+0.685] | +0.077 [−0.127,+0.318] |
| 64, 40 | 0.623 | 0.692 | 0.767 | +0.069 [−0.070,+0.202] | +0.145 [+0.002,+0.282] |
| 40, 40 | 0.289 | 0.257 | 0.309 | −0.031 [−0.107,+0.041] | +0.020 [−0.054,+0.097] |

**Primary result:** at ordinary N100 minima, pairwise interactions significantly improve which one of six random 4-flip candidates will lead to a lower endpoint. At deeper minima, evidence for this advantage is inconclusive, even with thousands of base pools. It would be misleading to generalize the easy-stage finding to near-record exploration.

A preliminary independent N100 stage-40 set, 1500 groups, gave +0.752 [+0.207,+1.340] for pair-approximate minus singles on steepest. The subsequent 3,500-group confirmatory set gave only +0.221 [−0.225,+0.689]. Thus a possible weak deep-basin effect is not robust enough to claim. These results should be reported separately, not selectively.

**Operator failure:** exact instantaneous ranking *versus singles* on N64 stage-40: steepest +0.145 [+0.002,+0.282], **first-improvement −0.219 [−0.365,−0.069]**. At N100 stage120, for first-improvement, exact instantaneous *versus singles* **−0.657 [−1.183,−0.193]**. For N100 stage40 the **mean of the two operators' positive gains** is 2.779 for exact immediate and 2.752 for singles, gain difference only +0.027 [−0.400,+0.443]. Strong operator dependence remains a serious obstacle.

**Compute:** at N100 stage0 on steepest descent, selected-candidate gain per steepest-descent neighbor-sweep proxy is 9.792 for singles versus 10.660 for exact immediate; at N100 stage40 it is 0.371 versus 0.429. This charges relaxation length but **does not fully charge feature extraction, candidate scoring, hardware wall-time, or model-training cost**. Note exact 4-flip immediate energy can be calculated with 4 sequential O(N) flip updates; explicitly summing 6 pair interactions typically costs **more** work than directly evaluating the exact move. Pair decomposition is explanatory; pair approximation alone is not yet a computationally attractive implementation.

## 4. The strongest conditional test: *equal exact immediate energy*

If pair motifs predict **future basin fate independently** rather than merely helping estimate immediate energy, candidates with identical 4-flip E_delta but different pair coupling should have detectably different later outcomes. Within each base group, select one such exact-energy-tied candidate pair with maximal pair-sum separation based on PRE-relaxation features alone. All comparisons use candidates from the same basin and same k, and the exact immediate energy is identical.

| dataset | groups with tied candidates | average positive gain, more negative pairs vs more positive pairs, steepest | paired 95% CI |
|---|---:|---:|---|
| N100 stage 0 | 569 | +0.773 | [−8.303,+9.582] |
| N100 stage 40 | 370 | −0.043 | [−1.838,+1.697] |
| N64 stage 40 | 966 | −0.099 | [−0.406,+0.182] |

None gives convincing added basin-forecast information. This **does not prove zero information** (few independent tied pools and broad uncertainty), but blocks the stronger claim that the pair-motif signature is an independently predictive geometry rather than simply a better immediate-energy surrogate.

## 5. Held-out length and operator-ensemble learning: negative

Additional exploratory fit [interaction_generalization.py](../interaction_generalization.py): **train only on N40/64 stage-40** (72,000 labeled candidate actions); hold N100 entirely out and test N100 stage40 +120 (28,200 candidate actions). Target: positive mean gain over *both* steepest and first-improvement descents. Histogram gradient boosting with pre-fixed parameters (125 iterations, 7 leaves, min leaf 120, lr .045, L2 20), two families:
1. cheap: normalized incumbent energy, sum of single-flip barriers, exact immediate 4-flip energy;
2. multispin: all cheap inputs **plus pair-interaction sum and exact 3+/4-order residual**.

Out-of-scale AUC for *any positive gain*:
- cheap classification **0.7335**, multispin classification **0.7331**;
- cheap gain regression **0.7327**, multispin gain regression **0.7319** (measured against binary hit label).

N100 stage-40 candidate-selection mean two-descent gain:
- best simple cheap rule (exact immediate): **2.779**;
- cheap probability classifier: **2.514**;
- multispin probability classifier: **2.666**, difference from exact immediate −0.114 (95% CI [−0.530,+0.280]).
At N100 stage120, multispin probability classifier 0.843 versus immediate 0.668; difference +0.175 [−0.095,+0.457], still inconclusive and not superior to a cheap model's 0.858.

No transfer gain established. Learning inference/training costs ignored, favoring learned models in this comparison. We therefore reject any claim that a neural model or boosted trees currently learned a useful cross-basin multi-spin representation.

## 6. Research implications and next falsifiable direction

1. **Separate action physics from trajectory value.** Balanced quartets yield an exact sparse hypergraph, with cheaply computable bounded high-order residual for four flips. But most immediate-energy benefits are mediated through ΔE; a deep-basin improvement predictor needs additional trajectory/committor signals.
2. **Test targeted motifs rather than extra generic statistics:** perturb spin quartets satisfying a+d=b+c versus matched random quartets with identical initial ΔE and similar local barriers, then check *post-relaxation improvement*, especially at elite starts. The null is no advantage after instant-energy matching.
3. **Change action representation if flat:** use coordinated sets of strongly negative epistatic pairs, iteratively refine inside small selected subgraph, then apply multiple descent operators and compare against a complete instantaneous-energy ranking baseline. A graph/hypergraph model should only be used if these pre-net mechanisms show consistent advantage.
4. Do not confuse “can leave incumbent basin” with “can beat current incumbent,” and do not run near-record N100 searches on the basis of ordinary local minima data. Re-run official verifier on any claimed E<578 certificate and coordinate with independent p006 owner.

## Source provenance

- Gallardo, Cotta, Fernández (2009), *Finding low autocorrelation binary sequences with memetic algorithms*, Applied Soft Computing: https://www.sciencedirect.com/science/article/pii/S1568494609000404
- Tomassini (2021), *Complex networks analysis of the energy landscape of the low autocorrelation binary sequences problem*, Physica A: https://www.sciencedirect.com/science/article/abs/pii/S0378437121003629
- Zhang et al. (2025), *New Improvements in Solving Large LABS Instances Using Massively Parallelizable Memetic Tabu Search*: https://arxiv.org/abs/2504.00987
- Pšeničnik et al. (2026), *Prioritizing Search Space Regions in the Low Autocorrelation Binary Sequences Problem*: https://arxiv.org/abs/2607.09688
- Few Shots official E578 source and verifier: https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100
- Prior exploratory baseline and transfer analysis within this topic: [basin-geometry-2026-10-29.md](basin-geometry-2026-10-29.md).

**Engineering boundary:** All new code and results are inside science-boundary/labs-ai4s-search/. Do not edit science-boundary/labs-100/. Source CSVs (~12 MB across five complete datasets) are reproducibly regenerated on demand rather than committed to avoid unchecked large artifacts.
