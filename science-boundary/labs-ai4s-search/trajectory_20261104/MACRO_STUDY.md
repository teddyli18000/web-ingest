# Costed large-scale coordinated macro proposals inside native lMAts — 2026-11-04

## Objective

Test whether a **predefined spectral/parity-guided 12-bit macro proposal** injected on GA global-record stagnation improves entire original unrestricted memetic-Tabu *solver* results, compared with no intervention and matched random controls. All generator scoring, candidate selection, native Tabu repair, crossover, and native population overhead are inside the original GA runtime timer.

Historical code and literature: original 2009 Gallardo/Cotta/Fernández lMAts C solver from [borkob/git_labs](https://github.com/borkob/git_labs) pinned `1aa123407636e48630174e0bf122037e369c1d68`. This is **not** the 2025 GPU MTS [Zhang et al.](https://arxiv.org/abs/2504.00987) or 2026 GPU self-avoiding/bandit [Pšeničnik et al.](https://arxiv.org/abs/2607.09688). We explicitly do not claim outperforming either.

## Hypothesis and six fixed arms

The previous native-Tabu trace study established an observational fact: successful long-gap local best updates frequently exchange odd and even correlation energy, but heldout-length directional prediction was captured by the very cheap **odd/even energy share**. More complex binned spectrum and simple bit statistics did not beat it. More importantly this label was selected *after success* and does not imply a better proposal.

This experiment instead modifies the GA generation stage: when time since last **GA-wide** record reaches 2N generations, inject a macro proposal once every 25 generations before the native Tabu call. Otherwise leave all original reproduction, GA replacement and native Tabu untouched.

Arms (`LABS_MACRO_ARM` env):

- 0: unchanged original solver (the macro function is never called).
- 1: **one** uniform 12-spin mask from the current GA best; all 12 flipped, then native Tabu.
- 2: **eight** uniform 12-spin masks, choose the candidate with minimum *true* immediate E.
- 3: **eight** lag-paired 12-spin masks; lag sampled proportional to 1 + C_k²/(N−k), choose a parity-corridor candidate using 0.25 multiplier on the part currently lower at source, with an E overshoot penalty.
- 4: **eight** lag-paired masks sampled uniformly over lags, same parity-corridor candidate score (structural-value placebo).
- 5: eight stress-lag-weighted paired 12-spin masks, choose best *true* immediate E (selection-score ablation).

Every mask flips exactly 12 distinct positions; each lag pair comprises two spins at a particular separation. All arms use the *same* subsequent native Tabu repair rule and native GA selection. No neural network is trained.

**Design caveat:** the macro replaces the original GA crossover/mutant offspring for the intervention event rather than injecting alongside it. Thus the method tests **operator replacement** under stagnation, not additive improvement while keeping full original GA candidate evaluation. Arm 0 and arm>0 RNG streams diverge after first intervention; matched seeds control initial randomness only. Instrumented baseline also calls an inexpensive environment-arm check, charged to all arms. The GA stops by wall-clock seconds internally, but independent simultaneous processes contend for CPU; record per-job external wall time and avoid strong hardware-neutral speed claims. We do **not** feed published N99 E553 target bits to the generator.

**Predeclared primary:** difference in final best exactly evaluated LABS E vs original lMAts per independent seed, at N64,80,99,100. Cluster bootstrap by seed within length. Secondary: best observed E, near-skew status, count of macro injections, mean proposed E, final parity odd/even energy, number of superior outcomes. Six arms mean 5 exploratory contrasts ×4 lengths; any 95% intervals are **exploratory**, not familywise-adjusted confirmatory evidence. No claim of novel method success without independent seeded replication, strong published solver comparison, and time-to-target curves.

## Initial completed 6-second smoke

[Native smoke raw dataset](results/macro_smoke_v1/results.tsv), [meta](results/macro_smoke_v1/summary.json): source-pinned original C solver successfully compiles after patching. Two lengths N64,99 × one matched seed × six arms = **12 completed outputs**; all reported exact integer energies were independently recomputed; every active arm triggered (macro proposals >0), baseline triggered zero. N64 baseline E280, best arm5 E272; N99 baseline E769, arm5 E737. **Not a statistical win:** these are single-seed debugging samples at much worse quality than published records (N64 E208, N99 non-skew E553). More important, average macro-generated immediate E is hundreds or thousands above contemporaneous incumbent E; candidate geometry likely destroys too much structure. This is evidence against claiming that proposal scoring alone constitutes a high-quality generative model.

## Execution

Compile upstream as transient source, no GPL vendoring:
```sh
PIN=1aa123407636e48630174e0bf122037e369c1d68
git clone https://github.com/borkob/git_labs.git /tmp/git_labs
git -C /tmp/git_labs checkout "$PIN"
python3 patch_macro_mts.py /tmp/git_labs/solvers/lMAts-lRRts/src
make -C /tmp/git_labs/solvers/lMAts-lRRts/src
python3 run_macro_mts.py --exe /tmp/git_labs/solvers/lMAts-lRRts/src/lMAts \
 --out results/macro_full_v1 --lengths 64,80,99,100 --reps 6 --seconds 14 --workers 4
python3 analyze_macro_mts.py results/macro_full_v1/results.tsv --out results/macro_full_v1/paired_analysis.json
```

The temporary GitHub Actions workflow performs exact output checks and commits the full results. Afterward remove one-shot workflow; retain durable scripts, source SHA and output within this topic. Do not touch `science-boundary/labs-100/`.

## Go/no-go

If arm 3/5 shows no reproducible gain over both original solver and random mask/corridor controls, **stop tuning these macro parameters**. Revisit the formulation: large replacement moves destroy strong correlations, and next candidate family should operate on balanced correlation-changing **cycles** or conditional pair-coupling-preserving reversible transformations rather than flipping arbitrary 12 positions. N99 skew E577 versus non-skew E553 is an oracle-only structural calibration; it cannot be used as a parent or hidden target for prospective unbiased search.


## Full prospective source-native MTS benchmark — validated complete

[Successful GitHub Actions run 41988872875](https://github.com/teddyli18000/web-ingest/actions/runs/41988872875); [all 144 exact-scored terminal sequences](results/macro_full_v1/results.tsv), [run metadata](results/macro_full_v1/summary.json), [paired statistical analysis](results/macro_full_v1/paired_analysis.json), and [SHA256 provenance](results/macro_full_v1/provenance.json).

N=64,80,99,100, six arms, six pre-fixed seeded runs per arm, 14 seconds per **full solver run**, all evaluation, LNS generation, population replacement and local Tabu included. Every active method was triggered hundreds to thousands of times, and original untouched arm triggered zero. The 144 independent final solutions all pass integer LABS E recomputation and exact odd+even accounting. Paired differences are original best E minus alternate final best E, so **positive means the macro helps**.

| N | original mean E | spectral-pair parity-corridor mean E | difference (95% seed bootstrap) | spectral-pair true-E selection mean E | difference (95% seed bootstrap) |
|---|---:|---:|---|---:|---|
|64|276.0|274.0|+2.0 [−1.33,+5.33]|272.0|+4.0 [−2,+10]|
|80|481.33|486.0|−4.67 [−24,+13.33]|472.67|+8.67 [−18,+32.67]|
|99|795.0|796.33|−1.33 [−14,+16]|784.33|+10.67 [−8,+28.67]|
|100|798.0|800.67|−2.67 [−21.33,+17.33]|795.33|+2.67 [−22.67,+33.33]|

The spectral-pair true-E arm has a slightly lower mean E than original in each of these four length strata, but **every interval crosses zero**, and at N100 it wins only 2/6 paired seeds and loses 4/6. No reproducible solver advantage is supported. The strongest observed single N100 macro solution E726 is still far above the published E578.

Other arms and their results are fully available in the paired JSON; notably uniform-pair parity-corridor at N64 is **worse** than baseline by 12.67 energy units [−19.33,−6.0]. Selecting a convenient best arm after observing 5 arms×4 sizes is exploratory multiple comparison; no corrected familywise superiority claim is possible here.

**Important control:** the prior attempted 144-run job [41988188919](https://github.com/teddyli18000/web-ingest/actions/runs/41988188919) completed all science runs and printed paired analysis, but a *malformed final workflow assertion* incorrectly asserted a zero truth value for the original baseline arm. The job failed before committing raw TSV. The corrected complete independent run above successfully committed the raw data and independent verification; the preliminary job should not be counted as separate independent seed replication because it uses the same fixed seed assignments. Its descriptive run means were almost identical, which is a debugging check only.

**Verdict:** the tested *operator-replacement* family, fixed 12-spin stress-lag pair generation and inexpensive parity-corridor selection, is **not** a demonstrated improvement over original historical MTS. Do not tune `lambda`/mask count or invoke complex NN architectures on this evidence. The more fundamental [fixed-weight mask-space study](GEOMETRY_STUDY.md) shows structured mask optimization can win dramatically at candidate level, but still fails to produce anything near frontier-quality states. Future work should target correlation-preserving large transitions, native stalled checkpoints, and stronger published solver baselines, rather than this particular macro operator.
