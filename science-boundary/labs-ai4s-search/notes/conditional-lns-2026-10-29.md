# Conditional large-neighborhood LABS search: exact joint masks, 2026-10-29

## Result and interpretation

**New positive mechanism-level evidence, but no competitive end-to-end solver and no N=100 record.** Exact joint reoptimization of ten selected variables *with all outside interactions retained* can benefit from a selector using **negative two-spin epistasis**, even after charging its selection overhead. It robustly outperformed random masks in fixed single-basin candidate generation on N64/100 and across two deterministic descent algorithms. However, **at identical 10 ms wall-time in iterative improve-only search, the policy did not beat random-mask LNS or a simple four-bit basin-hopping baseline**. A history-mixed variation also did not win. The distinction is critical: *first-stage candidate quality does not transfer into long-run search quality*. From the exact official N100 E578 starting sequence, **zero improvements** were found.

The attached conversation export argued for generating variable masks and jointly solving them rather than ranking random moves. We tested this **before** training a neural network. Current evidence says a learnable mask-selection task exists for *one-shot gain*, but its deployable long-run advantage has not been shown.

### Very recent prior art (not ours)

G. E. Lau and A. A. Gangat, **Competitive scaling of small-subsystem-optimization heuristics for LABS**, arXiv:2610.14361v2, October 14, 2026: https://arxiv.org/html/2610.14361v2 . Their ISO-subsystem method *drops* all terms involving spins outside the selected block during optimization, then accepts/rejects via the global objective. Their n=4 procedure uses complement checks, occasional uphill kicks, tracked masks, and multiple proposals and attains reported O(1.333^N) time-to-solution scaling on N27–60. This means **"optimizing LABS in small blocks" is known**, not a new principle. Our diagnostic deliberately optimizes the **full conditional objective with environment couplings fixed** and compares variable-set selection. We did **not** reproduce their end-to-end solver and make no claim of beating it.

Other strong work: 2025 GPU memetic tabu https://arxiv.org/abs/2504.00987 ; 2026 Thompson-sampling partition allocation https://arxiv.org/abs/2607.09688 ; 2021 neural LNS policy https://arxiv.org/abs/2111.03466 .

## Method (exact and reproducible)

Code: [lns_mask.cpp](../lns_mask.cpp), [online.cpp](../online.cpp), [analyze_lns.py](../analyze_lns.py), [compare_budget.py](../compare_budget.py). A mask M of m=10 unlocked spin indices is optimized by exhaustive Gray-code enumeration of **all 2^10 assignments**, while the other N−m spins are fixed. Energies are computed in exact integer arithmetic, including cross-mask couplings, with O(N) incremental flip updates. Two candidate exits from *each* mask are returned:

1. **Repair:** globally lowest instant-energy assignment within the mask (possibly the unchanged incumbent);
2. **Excursion:** lowest instant-energy assignment with Hamming distance at least max(3, floor(m/3)) from incumbent, potentially uphill.

Each exit is relaxed using both strictly energy-decreasing steepest and first-improvement descent. We measure true positive post-relax gain; other-basin-but-worse earns zero. Each arm performs the same exhaustive enumeration and all four relaxations per mask. The hindsight best among these four *already executed* relaxations is counted, as a fair algorithm could retain that best; all costs are charged.

Five selectors:
- **random**: uniform ten positions without replacement;
- **soft**: biased towards small nonnegative exact one-flip Δ_i;
- **negative-pair**: seed from top 80 favorable two-spin flips ranked by Δ_i+Δ_j+I_ij, then grow mask by minimizing Δ_i+sum_{j in mask} I_ij with stochastic noise;
- **absolute-pair**: grow a group with large absolute |I_ij|, regardless of sign;
- **window**: uniformly random contiguous ten positions.

I_ij=E(s^ij)−E(s^i)−E(s^j)+E(s); the selector computes the **entire** pair interaction matrix exactly. Cost is charged to the first negative-pair mask per start; the absolute-pair arm reuses this matrix but is not used in runtime superiority comparisons.

Each base state is generated with seeded random ±1 spins, steepest single-spin descent, then 40 or 120 attempted **random four-bit** perturbations plus steepest descent, accepting only strict energy improvement. Method comparisons reuse **identical base states**, but sample their own masks. Independent base groups are the bootstrap unit. Exact objective cross-checked with separate O(N²) direct computation for 8,680 one-flip deltas, 175 exhaustive masks (all 2^9 assignments independently recomputed), and N100 official E=578 baseline (selftest passed).

Main commands (run within the topic directory, Linux g++-14, Python 3 with numpy/pandas):

\`\`\`sh
g++ -O3 -std=c++17 lns_mask.cpp -o /tmp/labs_lns
/tmp/labs_lns --selftest
/tmp/labs_lns n64_stage40_confirm.csv 64 40 1200 726100 10 4
/tmp/labs_lns n100_stage40_confirm.csv 100 40 1200 962167 10 4
/tmp/labs_lns n100_stage120_confirm.csv 100 120 800 602361 10 4
/tmp/labs_lns n100_stage40_budget.csv 100 40 800 20261031 10 8
/tmp/labs_lns n100_record_m12.csv 100 0 200 229919 12 8 record
python analyze_lns.py n64_stage40_confirm.csv n100_stage40_confirm.csv n100_stage120_confirm.csv n100_record_m12.csv
python compare_budget.py n100_stage40_budget.csv
g++ -O3 -std=c++17 online.cpp -o /tmp/labs_lns_online
/tmp/labs_lns_online online_n64_10ms.csv 64 180 161311 10 10
/tmp/labs_lns_online online_n100_10ms.csv 100 180 161311 10 10
/tmp/labs_lns_online online_n100_hybrid.csv 100 180 271311 10 10
\`\`\`

**Data footprint:** full candidate CSVs are re-generated by commands, not committed to avoid megabytes of transient tabular observations. SHA256 of the original locally validated \`lns_mask.cpp\` before adding the near-record perturb option: \`367c3171d922a53a4825d6069c59d86a2f09548a871bfb88498c999fbabeb520\`. The final source adds \`near<K>\` optional initial mode (does not change default mode). \`online.cpp\` tested source SHA256 \`67e47791cd8da2868865030afafce4a97ef390360ef482aa747e38927b4928f8\`. RNGs are std::mt19937_64; full-dataset reproducibility assumes comparable compiler/stdlib random distributions. Exact energies and selftest are compiler independent.

### Fixed candidate generation: strong positive signal

Metric: mean positive energy decrease of the **best candidate among four masks, using both repair/excursion exits and both descent operators**. One group is one independent base state. CIs are paired bootstrap over base states, 3000 resamples (unadjusted, many exploratory comparisons).

| N, stage | groups | median base E | random mask | soft mask | negative-pair mask | Δ pair−random (95% CI) |
|---|---:|---:|---:|---:|---:|---|
| 64, 40 | 1,200 | 452 | 4.063 | 4.747 | **6.170** | **+2.107 [1.143, 3.070]** |
| 100, 40 | 1,200 | 1146 | 16.797 | 17.240 | **28.510** | **+11.713 [9.196, 14.257]** |
| 100, 120 | 800 | 1098 | 7.435 | 7.860 | **12.770** | **+5.335 [3.305, 7.350]** |

N100 stage40 strict improvement-hit count across 1,200 starts: random 369; soft 419; negative-pair **592**. Same conclusion under either steepest or first-descent separately. These starts are *not* elite; their E values are roughly twice N100 record E578.

### Budget-matched single-basin counterfactual

New independent N100 stage40 sample: 800 starts, 8 candidates per arm, seed 20261031. Compute wall time includes exact mask selection, enumeration, two exits × two descents and the pair-matrix overhead.

| strategy / mask count | mean positive gain | hits / 800 | mean computational ms / base |
|---|---:|---:|---:|
| random, 6 masks | 25.500 | 336 | 2.306 |
| **negative-pair, 4 masks** | **29.535** | **409** | **2.351** |
| random, 8 masks | 30.360 | 391 | 3.077 |
| negative-pair, 6 masks | 35.025 | 472 | 3.133 |

Pair-mask four versus random-mask six: Δ gain **+4.035**, paired 95% CI **[+0.685,+7.385]**; mean wall costs 2.351 vs 2.306 ms (about +2% cost). A deliberately stronger random-eight baseline obtains similar gain but spends ~31% more wall time. The evidence supports *improved one-shot candidate generation with overhead charged*, not a global solver advantage. C++ tiny-ms wall time is noisy and machine-specific; favor same-machine paired measurements, objective operations and time curves rather than generalizing speedups.

The ablation also reveals different mechanisms. In 800-stage40 new groups, among four random-mask proposals, **only 2** found a strict immediate repair gain, whereas 165 found improvement after relaxing an excursion. With negative-pair masks, 276 groups found an improved *repair* and 399 an improved *excursion*. Thus coupling-aware masks expose a productive **conditional reoptimization** neighborhood, while random masks mostly rely on leaving then descending.

### Record-quality control: complete failure

For 200 independently sampled mask pools **all starting at the same official E578 certificate** (not 200 independent elite sequences), test **five selectors × 8 masks × 2 exits × 2 descents**, m=12, full enumeration of 4096 states each mask. All 8,000 masks and 32,000 relaxed exits yielded **no E<578**. This is strong evidence only against the specified distribution of masks/optima, **not** a formal exclusion of all 12-variable neighborhoods, nor a proof of optimality.

Also tested E578 disturbed by random 6/8/14 spins then steepest-relaxed. Perturb six returned to exactly E578 in 582/600 runs, perturb eight in 476/600 runs; perturb fourteen yielded median base E1342. Thus small perturbations almost always fall back to the record, while larger ones jump to very high E: these are **not** a source of independent elite (E<800) training states. Do not misrepresent them as distinct near-optimal solutions.

### End-to-end wall-time result: negative

Run **180 independent random-start stage40 base states** at each N64/100, equal *10 ms per method per base*, with method order randomized per base. Methods accept only strict improvement, continuously recompute new mask scores after changes, and measure time including scoring, exhaustive enumeration, all descents. Also compare cheap random **four-bit perturbation + steepest-descent** search, and a simple hybrid: one negative-pair mask every 80 proposals, otherwise random four-bit perturbations. The stage40 seed generation is shared preprocessing **not included** in 10ms (appropriate for matched downstream continuation).

| N | random-mask LNS | soft-mask LNS | negative-pair LNS | random four-flip hopping |
|---|---:|---:|---:|---:|
| 64 | 27.64 | 12.84 | 22.24 | **38.60** |
| 100 | **64.98** | 38.36 | 57.51 | 59.16 |

Values are mean improvement E over 180 paired seeds. Negative-pair minus random-mask LNS at N64: **−5.40 [−9.71, −1.04]**. At N100: **−7.47 [−15.56, +0.82]**. Negative-pair minus random four-flip: N64 **−16.36 [−20.69, −12.11]**; N100 **−1.64 [−10.51,+7.58]**. Only N100 random vs negative pair is inconclusive; **there is no defensible overall solver victory**. CIs based on 6,000 resampled paired seeds.

Independent N100 hybrid follow-up, 180 seeds (seed 271311), same 10ms budget: mean energy improvements random-mask 70.78, negative-pair 57.69, random-four 63.44, hybrid 61.27. Hybrid versus random-mask **−9.51 [−17.51,−1.16]**. The history-free periodic mix did not fix the mechanism. This hybrid was an exploratory candidate, not a predeclared optimum.

### Why one-shot and online disagree

1. **One-shot masked solver sees useful immediate multi-spin flips.** Its exact conditioned subproblem often finds improvements on the initial basin; random masks rarely do.
2. **After local gains are exhausted, the negative-pair mask selector stays biased toward similar soft, mutually attractive spins.** Static selection tends to recycle a subset of states. This repetition is a *hypothesis* supported by flat long-run performance; we have not yet measured the actual mask Jaccard overlap/number of distinct reachable basins.
3. **Search quality is long-horizon and path-dependent**, while our selector solves a myopic energy-lowering mask. The random-four baseline gets many inexpensive escape attempts per millisecond.
4. No learned model trained; the result is an *algorithmic precursor*, not an ML triumph.

## Decision and next falsifiable experiment

**Reformulate rather than repeatedly increase mask size.** The strongest new signal is a favorable selected *subspace*, not a reliable policy. To convert it into search improvements, test **novelty-sensitive, history-conditioned mask distributions**:

- Measure Jaccard overlap between consecutive negative-pair masks, distinct relaxed endpoints, return-to-same-basin rates, and improvement hazard as the solver stagnates. Compare random-mask and negative-pair at equal wall time.
- Explicitly penalize recently chosen spin subsets and employ an adaptive portfolio over negative-pair, random masks, and cheap four-bit moves **conditioned on measured stagnation**. Equal compute, independent holdout seeds; no arbitrary unreported tuning.
- Directly test the latest Lau–Gangat isolated-subsystem/KD baseline and stronger memetic-tabu/self-avoiding algorithms before making a general performance claim. We have not implemented those strong baselines here.
- For near-record N100, avoid repeatedly falling into E578 with perturb-and-relax; access independent elite non-near-skew candidate structures if publicly available, while respecting other agent's ownership.
- Only build neural graph-guided masks after an interpretable history-aware selector demonstrates an economically recoverable advantage at held-out lengths; otherwise the search representation likely needs a bigger change.

All edits kept in science-boundary/labs-ai4s-search/. No change to science-boundary/labs-100/, no official p006 submission, no E<578.
