# Native strong-search trajectory study — 2026-11-04

## Verified latest state (2026-11-04)

**Completed and fully checked:** [12 native lMAts source runs](results/native_mini_v1/manifest.json) across N48/64/80/92/99/100. Independent exact scoring covers **all 93,256 trace events**, with 5,057 complete native Tabu episodes and 127 GA global records. Full source-pinned trace and verification are committed in [results/native_mini_v1](results/native_mini_v1), and [mechanism/compensation analyses](results/native_mini_analysis) and [plateau transitions](results/native_plateau_v1) are source-backed. The legacy 2009-era solver primarily creates easy-to-relax offspring; its 97.7% local gain label is *not* a long-stall breakthrough label. Historical GA records from separate parents are not a physical path.

**Strong conditional representation but weak decision relevance:** [The native-compensation audit](results/native_plateau_v1/pretransition_compensation_transfer.json) shows the odd/even energy ratio alone predicts *which parity component increases* given a success after ≥16 accepted moves (heldout AUC≈0.874). Adding 12 spectral bins or cheap bit statistics did not help. This is after selecting on **future success** and does not predict when an improvement occurs.

**Actual prospective forecasting was tested and failed the incremental feature gate:** [hazard study](HAZARD_STUDY.md), with no future success/step in features, fixed next-horizon outcomes, and holdout N92/99/100. Stalled≥8, next16 (3,909 observations) gives energy+history AUC 0.847 vs spectrum 0.850, but log-loss 0.41120 vs 0.41193 (worse). Stalled≥16, next32 (1,450 observations) AUC 0.882 vs spectrum 0.879; log-loss 0.41423 vs 0.41957 (worse). Stalled≥32, next64 produces **only 3 training states and no positives**; stalled≥64,next64 produces **zero training states**. The data collection distribution is inadequate for long-stagnation learning. Do not train a large dual-branch architecture from these samples.

**Actual generator deployment also failed the solver-level superiority gate:** [costed original-MTS macro study](MACRO_STUDY.md) verified **144 entire 14-second lMAts runs**, six arms × N64/80/99/100 × six seeded runs. Spectral high-stress lag-pair macros and a fixed parity-corridor filter neither beat the original solver consistently nor beat random controls under fully counted search time. The true-energy-picked spectral pairs had slightly lower average E at all four lengths, but **all paired bootstrap intervals included zero** (N100 baseline mean E798 versus macro E795.33, paired +2.67 [−22.67,+33.33]); best observed macro N100 E726 remains far worse than public E578. A full preliminary run failed a bad final workflow assertion; a successful rerun verified all raw energies and committed outcomes. This rules out *this fixed 12-bit operator replacement* as a demonstrated advantage, not every coordinated generator.

**New action representation has reproducible candidate-level structure but no useful frontier outputs:** [exact fixed-weight signed-correlation-cut study](GEOMETRY_STUDY.md), six frozen published elite orbits ×20 seeds, all methods 50 ms. Optimizing the 12-spin mask directly by swapping selected/unselected positions beats both independent random masks and an equal-cost **uniform random mask walk** in every paired comparison. At N100 E578, its average best 12-bit candidate E1149.6 vs uniform mask walk E1734.0; after retrospective direct-objective descent E1096.2. **These still represent severe energy damage**, not a competitive macro for a true elite. A cheap classical mask-space optimizer already achieves the candidate-level gain: train a model only if it beats that strong baseline, and only if deployed search improves.

**Decision:** No deep/dual-branch architecture or generative diffusion training justified yet. Require native strong-solver *persistent stagnation checkpoints* with source-distinct elite lineages and true intervention winners, and develop correlation-preserving **joint cut / transition corridors**, not another slight lag-weight or fixed-m macro tuning. No new N100 record, no p006 submission.

---

## Question and source scope

Can one identify reproducible, cross-length LABS correlation-structure transitions that distinguish useful **large coordinated changes** from ordinary short-cycle Tabu moves, and would they justify a bit/spectrum dual-branch generative search method? This is **not** an N100 record-submission agent. No modifications to `science-boundary/labs-100/`.

This round measures actual time-ordered state changes from **published unrestricted memetic Tabu** (Borko Bošković's archive of Gallardo–Cotta–Fernández 2009 algorithm): `https://github.com/borkob/git_labs`, `solvers/lMAts-lRRts/src`, pinned commit `1aa123407636e48630174e0bf122037e369c1d68`. It consists of population crossover and mutation, a native short-term tabu search over accepted flips, population replacement and global-record updates. It is **not** the 2025 Zhang et al. GPU MTS nor the 2026 GPU parallel SAW. Do not use the resulting distribution as though it were the true frontier N99/100 distribution.

## Instrumentation and provenance

[Native patcher](instrument_mts.py) adds minimal tracing to the actual upstream `GA.c` and `TabuSearch.c`. The upstream GPL source is only cloned on the compute runner, patched transiently, compiled, and never copied into this topic. Trace fields:

`event,gen,episode,step,n,energy,best_energy,wall_s,seq,best_seq,tabu_remaining`.

Event taxonomy: `PARENT_1/PARENT_2` (crossover parents), `TS_START` (offspring post-mutation before Tabu), `TS_STEP` (accepted current state), `TS_BEST` (new local best), `TS_END` (current and best), `GA_CHILD_POST` (offspring after local search), `GA_RECORD` (new overall best). The full *native* per-spin tabu remaining-time vector is saved at TS events. Note that Tabu restarts at each offspring, so this is a **native per-episode tabu history**, not a fictitious persistent all-run tabu table. GA global records can be from **different lineages**; connecting two GA records as a physical spin-flip path would be invalid.

To control output, only generations `gen % LABS_TRACE_GENSTRIDE == 0` are exhaustively logged; **every GA_RECORD is retained** regardless of stride. Accepted intermediate states are sampled every `LABS_TRACE_STRIDE` native flips, not every step. Therefore `TS_STEP` time series are *snapshots*, not full unit-flip pathways. The sampling mechanism must be included as an input feature/gating condition, and GA records outside sampled generations cannot be assigned fabricated TS_START/END history.

## Frozen pilot protocol

Single-thread native lMAts per operating-system process; parallelize independent runs across runner cores. Use `N=48,64,80,92,99,100`, separate seeds and finite time budgets, instrumented with strides 4 generations/32 accepted flips (pilot may adjust sample rate based on output size and sample integrity). Disable target termination with target=0. Report source revision, target, thread count, machine, trace SHA256, number of events/episodes/GA records, output length, exact-scored energy and parity structure.

**First inferential layer — observation:** For every sourced local episode compare pre-Tabu `s`, native best and current path after Tabu. Compute exact per-lag correlations, parity-correct odd defect `D_odd=Σ_{odd k}[C_k²-((N−k) mod 2)]`, even energy, near-skew class, total energy, correlation spectrum bins, and Hamming distance. Label local improvement and GA global-record improvement separately. Capture crossover parent separation versus produced offspring. Do not mix distinct GA lineages as literal dynamical trajectories.

**Second layer — cross-length prediction:** Group train/test by entire independent run and hold out all larger lengths `N∈{92,99,100}`; train on `{48,64,80}`. Compare inexpensive starting energy and stagnation/time/history against spectrum-only, bit-coordination, and combined features for predicting the **next episode's true improvement**. Report label prevalences, calibration, log loss, AUPRC/ROC when defined, group-bootstrap uncertainty and feature acquisition cost. This is observational representation testing, **not** demonstration of an effective generator. Compare length-wise normalizations, leak checks and class imbalance.

**Third layer — generative solver gate:** Only if a clear cross-length representation signal emerges, formulate a donor-free or independently sourced, history-conditioned multi-bit *proposal* using the learned structure, insert into the authentic solver and test against its original crossover, random coordinated recombination and costed alternatives with identical end-to-end CPU wall time. Sample unit is independent seeded *run*, not correlation time points. Preserve terminal best and time-to-target curves. At N99 use published skew E577 versus non-skew E553 as a **known-answer structural positive control**, not as demonstration the model can discover E553 blindly; at N100 near-skew E578 do not claim record-breaking without exact independent verification.

## Negative controls retained

Previous [weighted-lag and direct-skew target-deformation failures](../frontier_deformation/README.md), [644 zero-event frozen full-Tabu treatments and one exploratory E786→782 event at 2 seconds](../audit_20261029/README.md), and [misleading winner-only LNS endpoint compression](../audit_20261029/README.md) remain informative. We will not perform more weight microtuning nor infer a neural-network success from retrospective oracle labels.

## Research state

The compact native mini cohort is now fully validated and committed; see the **Verified latest state** above. Earlier high-density runs failed because full exact checking exceeded runtime or an incorrectly parsed bitstring column; the compact validated 12-run source is authoritative. Keep pilot failures visible. Retain full raw or lossless compressed trace rows when feasible, not only aggregated narrative. Record every validation failure and correct it before claims.

## Sources

- [2009 memetic algorithm and upstream code](https://github.com/borkob/git_labs)
- [2025 GPU memetic Tabu paper](https://arxiv.org/abs/2504.00987)
- [2026 GPU Thompson-sampling/self-avoiding LABS](https://arxiv.org/abs/2607.09688)
- [2026 isolated-subsystem LABS](https://arxiv.org/abs/2610.14361)
- [2026 MixBinNet low-cross-correlation binary generation](https://doi.org/10.1049/ell2.70699): its loss and multisequence cross-correlation targets are **not** equivalent to LABS record-level energy minimization, so not an unqualified LABS solver benchmark.
