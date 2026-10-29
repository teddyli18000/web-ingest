# Independent audit response and frozen Tabu intervention — protocol frozen 2026-10-29

## Scope / audit corrections

The uploaded external independent review assessed a repository version ending around commit 3fdc1efc3a. Subsequent work already imported the Zhang et al. (2025) GPU-MTS certificates, including N92 E490 and non-skew N99 E553; thus the report's most urgent *data omission* was corrected before this follow-up. We independently agree with two remaining code issues:

1. The old odd-lag "perfect iff |C_odd|=1" flag is invalid for odd N because C_k ≡ N−k (mod 2). Code `frontier_deformation/deform.cpp` now uses **D_odd = Σ_{k odd}(C_k² - ((N−k) mod 2))**. For even N this subtracts one from every odd C²; for odd N it subtracts zero. D_odd≥0, and D_odd=0 for a perfect odd-lag parity floor. This is a continuous feature, not a surrogate for near-skew classification. Selftest independently checks parity and direct energy.
2. The old mask-novelty measurement retained only the best-scoring relaxed endpoint from the **four** combinations (repair/excursion × two descents). We now separately count every raw endpoint, the number of distinct raw endpoint vectors and raw returns, retaining the earlier winner-only columns explicitly as winner-only. Do not infer all-endpoint basin compression from winner-only counts.

## Prespecified first controlled test

**Question:** after a stochastic Tabu trajectory has stagnated, does injecting a 10-variable full-conditional LNS neighborhood, chosen randomly or by negative epistasis, improve subsequent *actual* LABS energy more often than **continuing the exact same Tabu process** for equivalent wall-clock time? Does any benefit depend on preserving the tabu history?

This is an initial **mechanism diagnostic** with a native exact integer Tabu implementation plus the earlier exact Gray-code LNS kernels, NOT a state-of-the-art MTS/SAW comparison. Follow up with published strong solvers if a real intervention effect appears.

### Frozen input and strata

- [True frontier source set](../frontier_deformation/results/2026-10-29-frontier-elite-eval.tsv): 21 symmetry-distinct public certificates from GPU-MTS and QOBLIB across 19 lengths, including N99 skew E577, non-skew E553, N100 E578.
- [Independent historic solver set](../frontier_deformation/results/2026-10-29-strong-corpus.tsv): 25 symmetry-distinct 2009-era published `lMAts` outputs, 5 per N80/92/96/99/100, best N100 E762, **not** record or near-record.
- For each source solution and replicate, prepare a native Tabu-9 state retaining the full current vector, best-ever vector, last-flipped iteration per site and total iteration. Run at least 2000 warm-up moves, and freeze after ≥400 consecutive nonimproving Tabu moves or hard cap 12,000 warm-up moves. Record actual stall age and state quality. Source labels are **lineages**, stochastic warmups from one source are *not* independent scientific samples.
- For frontier and historical collections, use separate results/analyses to avoid laundering intermediate E≈750–800 as frontier elite.

### Seven intervention arms

Starting from the *exact same frozen* (current, best, tabu timestamps, iteration) for every arm and replicate:

A. Pure continuous Tabu-9, no intervention.
B. Uniform random 10-variable full conditional exact LNS; select best *different* post-relax endpoint across repair/excursion × first/steepest; inject nonmonotonically; **preserve** tenure history except touched indices.
C. Same as B, but **reset** tenure history at injection.
D. Negative-pair-epistasis mask, otherwise identical to B; preserve.
E. Same as D, reset.
F. Uniform random eight-flip + steepest relaxation, allowed uphill; preserve.
G. Same as F, reset.

Tabu resumes with identical move rule for every branch (one-flip min legal delta, aspiration to best). No generic "bandit" or "ALNS" shorthand: these arms are explicit, narrow ablations, and all proposal/scoring/relaxation work is **inside** the treatment clock. Direct energy is checked independently on every final best/current vector.

### Predetermined primary/secondary outcomes and confound controls

- **Primary:** best E improvement from the frozen best after nominal **80 ms total treatment wall-clock** (including injection), analyzed paired by *original source orbit* (not by warmup replicate or candidate), separately for true frontier and intermediate historic solver strata. First run **two independent seeded warmups** per source, to limit compute before the mechanism gate.
- Secondary: any-improvement hit count, first improvement time, iteration/flip count, injection elapsed time and overshoot, odd-lag parity-correct D_odd of final state, tenure preservation vs reset and heterogeneity by structural class and frozen stall age.
- 95% paired **source-orbit cluster bootstrap**, 4000 resamples. Effects are exploratory; no unadjusted CI alone constitutes a pre-registered confirmatory discovery because multiple arms/strata are compared. No claim of solver breakthrough unless repeatable effect exceeds the extra compute and tuned alternative algorithms.
- If an 80-ms LNS injection *itself* overruns the budget, the overrun is logged; the correct interpretation is failure of that policy under this deadline, not free extra work.
- **Hard negative controls:** pure Tabu and cheap multi-spin kick; no neural model training on all-zero positive labels.
- **Decision rule:** prioritize a second independent-seed, longer-horizon replication only if a clear stratum-conditional improvement is observed, and show strong published MTS/SAW before claiming novelty. If all true frontier lineages fail to improve, that means **insufficient positive signal to train a selector**, not proof that directed intervention or DL is impossible.

### Reproduction

From `science-boundary/labs-ai4s-search/`:

```sh
g++ -O3 -std=c++17 audit_20261029/stall_interventions.cpp -o /tmp/labs_stall
/tmp/labs_stall --test
/tmp/labs_stall frontier_deformation/results/2026-10-29-frontier-elite-eval.tsv audit_20261029/results/frozen_frontier_v1.tsv 80 2 9 10 400 12000
/tmp/labs_stall frontier_deformation/results/2026-10-29-strong-corpus.tsv audit_20261029/results/frozen_historical_v1.tsv 80 2 9 10 400 12000
python3 audit_20261029/analyze_stalls.py audit_20261029/results/frozen_frontier_v1.tsv audit_20261029/results/frozen_historical_v1.tsv --out audit_20261029/results/paired_summary_v1.json

g++ -O3 -std=c++17 mask_novelty.cpp -o /tmp/labs_novelty
/tmp/labs_novelty audit_20261029/results/endpoint_audit_n100.csv 100 40 100 771129 10 8
```

The experiment runs on a single Linux runner; actual elapsed values and observed source commit go in the verified result. Temporary GH Actions workflow is disposable and will be deleted after results are validated. Full data and result summaries remain topic-local.


## Verified outcome of frozen protocol v1 (complete)

[GitHub Actions run 40938136586](https://github.com/teddyli18000/web-ingest/actions/runs/40938136586) completed successfully. Source commit, compiler, CPU kernel and SHA256 hashes of all raw files are preserved in [metadata](results/run_metadata.json). The first attempt [40937951206](https://github.com/teddyli18000/web-ingest/actions/runs/40937951206) failed to compile due to a test-symbol collision with the included LNS source, **before any candidate execution**; the symbol was fixed and the full corrected run validated, including 90 independent exact states, 270 full injection/continuation selftest paths and the old 27,200 independent exact delta checks.

**Crucial null:** 21 frozen true-frontier source states × two independent warmup replicates × seven arms = **294** complete 80ms experiments. Separately, 25 historical memetic solution orbits × two replicates × seven arms = **350**. In **all 644 runs**, no treatment improved its source's warm-start best energy, even though 96%-98% of intervention proposals actually changed the current spin state. After warming, frozen historical-solver best energy averaged 681 (versus 618 across the mixed-size frontier source set); mean frozen stall age was effectively 2,000 Tabu steps. Thus the response labels were **all zero**, confidence intervals of zero versus pure Tabu are degenerate by construction and **not evidence of equivalence or futility**. The native protocol remained efficient: actual full-arm elapsed wall time averaged ~80.0ms, intervention overhead inside that cap, overshoot ~0.006–0.008ms. The experiment *answered a data sufficiency question negatively*, not whether trained LNS control is intrinsically incapable.

Reproduce: [raw frontier outcomes](results/frozen_frontier_v1.tsv), [raw historical outcomes](results/frozen_historical_v1.tsv), [paired analysis JSON](results/paired_summary_v1.json). These source-orbit labels must not be treated as 644 independent scientific instances.

**All-exit versus winner-only correction, now measured rather than hypothesized:** [raw endpoint dataset](results/endpoint_audit_n100.csv), 100 N100 bases per selector, eight distinct m10 masks/base, each mask's repair/excursion × steepest/first endpoints counted separately. Winner-only versus all-endpoint return-to-identical-base rates: random **89.25% vs 74.81%**, soft one-spin **74.63% vs 54.53%**, negative pair **74.75% vs 48.22%**. Mean distinct endpoint vectors among all 32 paths/source: random **7.56**, soft **4.49**, negative-pair **7.29**; chosen-winner unique counts 1.78/1.68/2.30. The earlier inference from only selected best endpoints overstated the compression of the **full** four-exit outcome map. Endpoint counts use exact vector equality, not eightfold symmetry-canonical basin identity; they also do not represent transition probabilities under all hypothetical perturbations.

**Next minimal experiment:** Because both quality strata lack any positive target at 80ms, a **longer 2-second** independent replication on *a narrower, prespecified cross-quality slice* (N80 and N100, including published frontier and historical lMAts sources) can test whether the all-zero issue is merely horizon censoring. This is exploratory after seeing v1 null and cannot be folded into v1's primary estimate. If no positive events, the next change must be a new acceptance/exit formulation and genuinely strong solver-state checkpoint harvest, not bigger classifiers.



## Completed follow-ups: 2-second stall intervention and known-answer structural bridge

**2-second exploratory extension:** [successful GitHub Actions job 40938740891](https://github.com/teddyli18000/web-ingest/actions/runs/40938740891), exact data files [historical](results/frozen_historical_long_v2.tsv), [frontier](results/frozen_frontier_long_v2.tsv), [analysis](results/paired_summary_long_v2.json) and [SHA256 manifest](results/long_v2_checksums.json). A preselected N80/N100 slice contains two public frontier orbits (QOBLIB N80 E352, N100 E578) and ten 2009-era independent published memetic final sequences (five N80 and five N100). Each was warmed to full local Tabu state and forked to the same seven arms for **2.0 seconds inclusive of injection**, one fresh seeded warmup per source orbit, totaling **84** complete treated trajectories. Frontier: **zero** true energy improvements across 14 arms. Historical: **one** out of 70 trajectories improved a frozen best: N100 published lMAts source **E786**, pair-conditional LNS with preserved Tabu history (arm 3) gave **E782**, first new best after **0.5506069 s** and **49,682 post-fork Tabu calls** (mask selection itself took 0.0008869 s). All six alternatives from that same frozen state failed to improve within their 2-second budgets. Across ten historical source orbits, pair-preserve minus pure Tabu: mean gain **+0.4**, cluster bootstrap 95% CI **[0,+1.2]**. This is an exploratory **single selected positive**, not a statistically replicated historical-memory interaction or neural model evidence, and this candidate remains far worse than public N100 E578. Zero-event frontier differences are noninformative about model value. The earlier 80ms frozen treatment remains separate, not pooled or reinterpreted.

**Known-answer N99 positive control:** [C++ source](bridge_positive_control.cpp), [runner-validated output](results/n99_bridge_positive_control.txt) and [GH Actions reproduction](https://github.com/teddyli18000/web-ingest/actions/runs/40939547252). Source N99 QOBLIB skew E577 versus published GPU-MTS non-skew E553, both integer exact verified. Full eightfold LABS symmetry reduces their Hamming distance to **41**. Restrict to a **monotone 41-step path** that flips each differing bit exactly once, using the *known target word* (an oracle; not a deployed solver). From 10,000 random orders (seed123456), peak intermediate LABS energy min **2725** and median **4593**; greedy minimum-immediate-E order peaks at **1949**; width-1500 deduplicated beam using minimize (peak, current E) found a path peaking at **1537**. All reach E553 exactly. This is an **upper bound on the unknown optimal minimum barrier within the tested path family**, not a lower bound on any LABS transition barrier; alternative detours, simultaneous multispin changes or different symmetry frames may have far lower barriers. It demonstrates why a strategy that only moves monotonically toward the final Hamming target is a poor *candidate representation*, and motivates optimizing low-energy joint paths without knowing the target in advance.

**Research gate after audit:** We now have a mathematically sound odd-lag defect, unbiased all-four-endpoint diagnostics, a frozen full-Tabu-memory comparison, **one** non-frontier improvement after extending budget, and one known-answer N99 positive control. We still **do not** have (a) multiple independently sampled near-record N100 non-near-skew states, (b) a strong published memetic-Tabu checkpoint with its native history, (c) repeated contrasting best-arm labels at the frontier, or (d) cost-matched superiority of any new controller over genuinely tuned strong classical baselines. Do not train a policy now or generalize the one selected positive. Instrument the published solver's *native checkpoint state/history* at stalled improvement thresholds, harvest independent lineages, and only then test a state-conditioned repeated-intervention policy. For structural target shaping, avoid pure lag-weight/odd-defect rewards; assess joint odd/even lag correlation **Pareto corridors** on the N99 known-answer positive control, then blind target identities for real search.

