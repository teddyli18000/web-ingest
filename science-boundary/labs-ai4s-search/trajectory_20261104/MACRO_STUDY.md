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
