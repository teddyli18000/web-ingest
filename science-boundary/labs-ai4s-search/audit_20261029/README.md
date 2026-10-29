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
