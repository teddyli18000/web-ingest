# Verifier-valid k6 neutral mother at score 134,753

Status: **new equal-score mother state, not a breakthrough**.

An exact lexicographic weighted-MaxSAT search over all ordered pairs of the four genuine outside-only k=6 support defects and all 18 public BPZ terminal configurations was run in GitHub Actions run `40993717057`.

The primary objective was the true score delta `selected_new - deleted_baseline`. The secondary objective, only within the primary optimum, maximized `selected_new`. Among 288 exact scenarios:

- positive-gain scenarios: 0;
- nonempty neutral scenarios: 126;
- largest neutral exchange found: **18 additions for 18 deletions**;
- resulting score: **134,753**.

Best scenario: terminal `q=H`, `r=H`, orientation 0, with `k6-0` on both factors.

The resulting certificate was checked by the upstream Few Shots p004 verifier:

- valid: true;
- score: 134,753;
- canonical hash: `636cbc9a3368fccd6bac3155aa0a73eaf9ddd5d9f053ba74ca00f748437b9d94`.

The exact exchange is frozen reproducibly in `code/bpz_k6_neutral_best_seed.py`.

## Scientific meaning

This state is useful because it is not a shallow neutral 1-for-1 perturbation of the public record. It changes 18 ten-dimensional points simultaneously while preserving the record score, creating a genuinely different basin for unrestricted local replacement search.

The first attempt to run unrestricted net-+1 radius <=4 on this new mother did **not** produce a mathematical result: the search source failed to compile because the known compile-only patch for `search_net1_r4_complete.cpp` was omitted (`auto k=..., n=...` mixed-type deduction). Therefore the red workflow conclusion from run `40993717057` must not be interpreted as a negative search result.

A follow-up packed workflow rebuilds the exact same mother from pinned source data, re-verifies its canonical hash, applies the audited compile-only patch, and continues exact net-+1 search through radius 5.
