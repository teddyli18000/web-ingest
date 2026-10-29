# LABS causal intervention-response study — 2026-10-29

## Current decision

**Yes, finite-horizon interventions make different long-lived differences from identical frozen LABS local minima; no, we have not shown these differences offer a new search policy beyond Tabu/Bandit/ALNS.** The largest and reproducible intervention effect is a minimal one-spin **Tabu tenure 7**, not quartic-structure LNS. Energy alone explains part of the cross-state treatment heterogeneity; currently tested pair-coupling statistics and limited search-history probes do not supply additional out-of-sample value. At *true record-quality* N64, N80, N100 anchors, all short-budget treatments return no improvement, so no intervention winner is identifiable there.

No new N100 result below 578, no novel adaptive controller demonstrated, and no alteration of the independent record-oriented labs-100 topic.

## Primary-source originality boundaries

- Lau/Gangat, Competitive scaling of small-subsystem-optimization heuristics for LABS (revised 2026-10-14): https://arxiv.org/abs/2610.14361 — subsystem LABS search is known; their isolated subproblem drops exterior couplings.
- Pšeničnik et al., 2026 Thompson allocation for LABS self-avoiding search: https://arxiv.org/abs/2607.09688 — online allocation is already studied in LABS.
- Zhang et al., 2025 massively parallel memetic tabu: https://arxiv.org/abs/2504.00987 — strong published baseline **not reproduced here**.
- BALANS, IJCAI 2025: https://ijcai.org/proceedings/2025/286 — bandit selection with separate state and neighborhood exploration is established.
- Dudel, runtime-sensitive learned ALNS operator selection, 2026: https://doi.org/10.5282/jums/v11i1pp1-26.
- Frozen reference sequences: N64 exact optimum 208 from https://github.com/ZIB-AOPT/QOBLIB/blob/main/02-labs/solutions/labs064.opt.sol ; N80 best-known 352 from https://github.com/ZIB-AOPT/QOBLIB/blob/main/02-labs/solutions/labs080.bst.sol ; N100 best-known 578 from https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100 .

Learning operator choice, adapting tenure, or optimizing LABS blocks is **not inherently novel**.

## Experimental design and causal interpretation

Code: causal.cpp, causal_repeats.cpp, tabu_ablation.cpp; shared exact Gray-code LNS/evaluator from ../lns_mask.cpp. Analysis: analyze.py, analyze_repeats.py.

For each N=64,80,100, generate **140 independently seeded frozen bases** from random binary spins via exact steepest one-spin descent then **1000 strict-improvement four-bit perturb+descent proposals**. Every method gets the *same fixed base* and the same elapsed time, using separate reproducible random streams. Common preprocessing and 12 off-policy diagnostic probes are outside the intervention clock. The latter are **retrospective features only**; no gain from deploying them is claimed.

Six arms, each for **15 ms**, followed by the **same random-four strict-improvement search for 20 ms** from its own best intermediate solution, with a common continuation seed:
0. Random four-spin perturb+steepest descent.
1. Single-spin **Tabu-7**, with tenure-based no-reversal, aspiration to best, and nonimproving intermediate moves.
2. Uniform 10-variable full-environment exact LNS, 1024 states/mask, diverse exit, two descents.
3. Negative pair-epistasis conditional 10-variable LNS, same exact subproblem solve.
4. Simplified cost-weighted Thompson sampler choosing arms 0/2/3.
5. Fixed portfolio with periodic random LNS and a stagnation-triggered eight-spin kick and some Metropolis acceptance. **Not a full score-adaptive ALNS baseline.**

All arms are evaluated for all frozen bases. This is a paired counterfactual *algorithmic* test: the actual random draws differ between arms, but base states are held fixed. Common continuation resets the optimizer's Tabu/Bandit controller history and retains the *best solution reached*. Thus persistence measures the **resulting solution's long-horizon search value**, not persistence of policy memory. There is no identifiability claim over all infinitely long trajectories.

### 140 independently fixed bases per N: mean integer energy decrease

| N | median base E [min,max] | record E | intervention | gain after 15ms | total gain after 20ms same-policy continuation | final contrast vs random four (95% cluster bootstrap) |
|---|---|---|---|---|---|---|
| 64 | 406 [328,452] | 208 | random four | 6.94 | 10.83 | reference |
| 64 | | | **minimal Tabu-7** | 24.60 | **26.74** | **+15.91 [11.54,20.23]** |
| 64 | | | pair-conditional LNS | 0.80 | 7.94 | −2.89 [−6.14,0.00] |
| 64 | | | Thompson-lite | 1.77 | 7.43 | −3.40 [−6.54,−0.31] |
| 80 | 644 [492,724] | 352 | random four | 4.71 | 7.97 | reference |
| 80 | | | **minimal Tabu-7** | 36.26 | **38.74** | **+30.77 [25.26,36.54]** |
| 80 | | | pair-conditional LNS | 1.54 | 6.49 | −1.49 [−4.37,1.14] |
| 80 | | | Thompson-lite | 2.31 | 5.51 | −2.46 [−5.43,0.26] |
| 100 | 1038 [878,1170] | 578 | random four | 5.17 | 9.29 | reference |
| 100 | | | **minimal Tabu-7** | 58.29 | **62.37** | **+53.09 [43.43,63.09]** |
| 100 | | | pair-conditional LNS | 5.63 | 11.94 | +2.66 [−2.11,8.09] |
| 100 | | | Thompson-lite | 2.09 | 7.09 | −2.20 [−6.03,1.09] |

Remaining arms: N64 random LNS final gain 7.51, stagnation portfolio 9.77; N80 6.60 and 8.14; N100 10.63 and 13.26. All intervals are paired 5000 bootstrap replicates resampling **entire starting states**, not correlated candidate rows; multiple exploratory contrasts unadjusted.

Longer N100 experiment: independent 55 bases, **15ms treatment + 100ms uniform random-four continuation**. Mean final gains: random-four 18.33, Tabu 63.71, random-LNS 21.38, pair-LNS 15.27, Thompson-lite 20.07, stagnation portfolio 22.84. Tabu−random four **+45.38 [33.45,57.89]** under base-paired bootstrap, showing persistence over this *finite* tested horizon.

### Replication, history versus structural prediction

Another 52 independent N64 frozen states and 52 N100 states, **three random seeds per arm for the *same* base**, 10ms treatment +20ms continuation. Relative Tabu-minus-random-four treatment effect has cross-repetition Pearson correlations **0.24–0.53 at N64** and **0.57–0.74 at N100**. Averaged over three replicas per state, the Tabu contrast is N64 **+13.03 [8.67,17.54]**, N100 **+43.95 [31.77,56.13]** (bootstrap states, not replicas).

At N100, the state-wise benefit correlates with start energy (Spearman **0.659**) and mean single-spin barrier (**−0.645**); the fraction/count of negative two-spin interactions (**−0.096**) and off-policy history-probe improvement rate (**−0.066**) are weak correlates. Crucially the probes almost always produce **zero successful improvements**: 139 of 140 N100 primary bases had zero successes in 12 random-four probes; likewise N64 139/140, N80 137/140. This severely limits the informational value of the tested historical summary; it is **not** a general disproof of history-conditioned policies.

Fivefold **out-of-base** Ridge(alpha=10), group-disjoint held-out prediction of the average *Tabu minus random-four* advantage over 52 N100 states:

| features | held-out R² | MAE |
|---|---:|---:|
| constant | −0.037 | 38.77 |
| **starting energy only** | **0.399** | **27.71** |
| E + barrier + pair count + Hamming | 0.357 | 28.13 |
| 12-probe historical summaries only | −0.013 | 38.26 |
| combined | 0.338 | 28.69 |

Added structural/history features showed no robust MAE advantage over energy-only, with small test sample and strong collinearity between energy and mean barrier.

**Transfer to unseen length:** train random forest on 140 N64 + 140 N80 bases, using structural, probe-history, or combined features to choose among six arms. On 140 completely held-out N100 states, **all three learned policies chose Tabu-7 for all 140 states**, exactly matching the fixed best-on-train choice, total gain 62.37. Unavailable perfect per-state hindsight chooser would yield 68.66 on this test, but this is an *upper bound*, not a fair policy. **No actionable extra value from learning was established.**

### Ablation: is familiar Tabu *history* enough to explain the effect?

A further independent 105 N64 +105 N100 frozen-base study, **15ms tenure-controlled single-spin search plus 20ms common random-four tail**, tested tenure [0,1,3,7,15,30]:

| tenure | mean final gain N64 | mean final gain N100 |
|---:|---:|---:|
| 0, no memory | 5.26 | 5.64 |
| 1 | 5.49 | 8.69 |
| 3 | 17.37 | 38.02 |
| **7** | **24.69** | **59.50** |
| 15 | 17.07 | 50.74 |
| 30 | 10.10 | 35.77 |

N100 Tabu-7 minus tenure0 **+53.87 [43.66,64.57]**, versus tenure3 **+21.49 [11.54,31.39]**, versus tenure15 **+8.76 [−0.42,18.21]**. Forbidding recent reversals while allowing uphill intermediate moves is clearly impactful. The tested tenure 7 is an *exploratory best among a few values*, not a universal optimum.

### Actual record-quality controls

One public record/optimum sequence **per length** reused under 28 independent random streams × six interventions, 15ms +20ms per fork: N64 E208, N80 E352, N100 E578: **zero improvements in 168 forks at each length**. This is **one elite state repeated** for each N, not a cohort of 28 independent elite local minima. N64 no-improvement is mathematically expected from optimality; N80/N100 no-improvement is a narrow negative computational result, not proof of optimality. This blocks any claim of demonstrated predictive intervention effects in multiple distinct record-quality LABS basins.

## Replication commands and limitations

Build from science-boundary/labs-ai4s-search directory with g++ -O3 -std=c++17 (measured environment: GCC 14.2.0, AMD EPYC 9V74 x86_64). Core selftest independently checks 8680 incremental one-flip deltas and 175 exact masks versus direct LABS energy, and checks official N100 E578.

    g++ -O3 -std=c++17 causal_20261029/causal.cpp -o /tmp/labs_causal
    /tmp/labs_causal --test
    /tmp/labs_causal main_n64.csv 64 140 20261029411 15 20 -1000 10
    /tmp/labs_causal main_n80.csv 80 140 20261029411 15 20 -1000 10
    /tmp/labs_causal main_n100.csv 100 140 20261029411 15 20 -1000 10
    /tmp/labs_causal extended_n100.csv 100 55 20261029115 15 100 -1000 10
    /tmp/labs_causal record_n100.csv 100 28 20261029077 15 20 0 10
    g++ -O3 -std=c++17 causal_20261029/causal_repeats.cpp -o /tmp/labs_repeats
    /tmp/labs_repeats repeat_n64.csv 64 52 20261029743 10 20 -1000 10 3
    /tmp/labs_repeats repeat_n100.csv 100 52 20261029743 10 20 -1000 10 3
    g++ -O3 -std=c++17 causal_20261029/tabu_ablation.cpp -o /tmp/labs_tabu
    /tmp/labs_tabu tabu_n64.csv 64 105 202610296613 15 20 1000
    /tmp/labs_tabu tabu_n100.csv 100 105 202610296613 15 20 1000
    python causal_20261029/analyze.py main_n64.csv main_n80.csv main_n100.csv
    python causal_20261029/analyze_repeats.py repeat_n64.csv repeat_n100.csv

Also run record controls N64 and N80 with the identical record_n100 command substituting N and output file. CSV outputs log actual clock time, operation calls, starting-state probes, and final energies. Runtime caps may overshoot on the final LNS move; timing depends on compiler, CPU scheduling and fixed policy order. Candidate generation costs shared by all arms and 12 common diagnostics were excluded from treatment clock; costs of **using these diagnostic features in a deployed learner have not been demonstrated**. Our Tabu, Thompson and stagnation routines are intentionally **small diagnostic implementations**, not exact reproductions of published high-performance memetic Tabu, full ALNS, or large-scale Thompson-sampling LABS. Original full CSVs are in the companion user-facing research archive; scripts/seeds/critical evidence and handoff are retained here.

## Decision and next hypothesis

**No reason to scale a neural selector now.** First require multiple *different* near-best or non-near-skew N100 basins and a family of interventions with **different genuinely competitive winners**. Quantify state-conditional treatment response beyond starting E with *costed* history features, train on one set of lengths and validate on separate sizes and operators; compare with tuned Tabu, modern self-avoiding walks, and genuine ALNS/Bandit baselines. Study persistent histories and nonmonotone acceptance without conflating short-term move quality with long-term final value. If all states still favor basic Tabu under equal wall time, a more complex controller has no value. Record nulls rather than inventing a learned boundary breakthrough.
