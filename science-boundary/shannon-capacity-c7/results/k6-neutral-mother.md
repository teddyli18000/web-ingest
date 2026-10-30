# Verifier-valid k6 neutral mother at score 134,753

Status: **new equal-score mother state, not a breakthrough; unrestricted net-+1 is now exactly negative through radius 5 around this mother**.

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

## Exact unrestricted local closure through radius 5

Follow-up packed GitHub Actions run `40993829841` rebuilt the same mother from pinned data, independently re-verified the hash above, applied only the known compile repair to the exact local-search source, and completed the unrestricted net-+1 search through radius 5.

Radius <=4 returned:

```json
{"kind":"none","method":"exact-unrestricted-net1-r4-complete","baseline_size":134753,"coverage0":0,"coverage1":4336,"coverage2":149883,"coverage3":998101,"coverage4":2127912,"support2_groups":141027,"support3_groups":968117,"support4_groups":2074572,"owner4_checked":10791241,"eligible_owner4":595647,"max_supported_pool":16}
```

The two exact radius-5 strata returned:

```json
{"kind":"none","method":"exact-unrestricted-net1-r5-direct-c5","baseline_size":134753,"coverage0":0,"coverage1":4336,"coverage2":149883,"coverage3":998101,"coverage4":2127912,"coverage5":2555905,"coverage2_groups":141027,"coverage3_groups":968117,"coverage4_groups":2074572,"coverage5_groups_checked":2489839,"eligible_groups":152720,"max_supported_pool":21}
```

```json
{"kind":"none","method":"exact-unrestricted-net1-r5-connected-lower-support","baseline_size":134753,"coverage0":0,"coverage1":4336,"coverage2":149883,"coverage3":998101,"coverage4":2127912,"coverage2_groups":141027,"coverage3_groups":968117,"coverage4_groups":2074572,"generated_calls":253041263,"unique_owner5_checked":108271260,"eligible_owner5":7849057,"max_supported_pool":21}
```

No improvement certificate was materialized, and the Few Shots breakthrough-verifier step was therefore correctly skipped.

## Scientific meaning

This state is useful because it is not a shallow neutral 1-for-1 perturbation of the public record. It changes 18 ten-dimensional points simultaneously while preserving the record score, creating a genuinely different basin. The exact local profile is also materially different from the original public baseline: singleton coverage drops while the number of eligible radius-5 owner sets grows. Nevertheless, this basin is still exactly rigid through remove-5/add-6.

This is evidence against merely increasing local radius around one equal-score mother. Prefer either a different neutral mother/plateau geometry or a changed support/product representation before spending substantial compute on radius 6 here.
