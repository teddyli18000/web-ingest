# Verifier-valid global-k6 neutral mother at score 134,753

Status: **new equal-score mother state, not a breakthrough**.

The exact lexicographic optimizer over the complete union of all 32 k=6 clique-cover-gap support pools was run in GitHub Actions run `40994306953`. For each of the 18 pinned BPZ terminal baselines it maximized the true score delta `selected_new - deleted_baseline`; among equal primary optima it maximized the number of selected new points.

## Exact plateau result

- exact primary optimum: gain `0`;
- best terminal: `q=H`, `r=H`, orientation `0`;
- largest neutral exchange: **47 additions for 47 deletions**;
- resulting score: **134,753**;
- upstream Few Shots verifier: valid;
- canonical hash: `58e42b76eb31b1d0b719d5152b2a91d04c830fc275f540b4228062c10cb56b16`.

The complete exchange is frozen in `code/bpz_global_k6_neutral_best_seed.py`, so future work does not need to rerun the 18-scenario lexicographic MaxSAT.

## Exact unrestricted local search from the new mother

The same packed Action continued directly from the verifier-valid tie.

### Radius <= 4

```json
{"kind":"none","method":"exact-unrestricted-net1-r4-complete","baseline_size":134753,"coverage0":0,"coverage1":4224,"coverage2":149836,"coverage3":997561,"coverage4":2126985,"support2_groups":141036,"support3_groups":968076,"support4_groups":2074438,"owner4_checked":10794449,"eligible_owner4":596788,"max_supported_pool":16}
```

### Radius 5 direct-support stratum

```json
{"kind":"none","method":"exact-unrestricted-net1-r5-direct-c5","baseline_size":134753,"coverage0":0,"coverage1":4224,"coverage2":149836,"coverage3":997561,"coverage4":2126985,"coverage5":2556789,"coverage2_groups":141036,"coverage3_groups":968076,"coverage4_groups":2074438,"coverage5_groups_checked":2491533,"eligible_groups":152752,"max_supported_pool":21}
```

### Radius 5 connected lower-support stratum

```json
{"kind":"none","method":"exact-unrestricted-net1-r5-connected-lower-support","baseline_size":134753,"coverage0":0,"coverage1":4224,"coverage2":149836,"coverage3":997561,"coverage4":2126985,"coverage2_groups":141036,"coverage3_groups":968076,"coverage4_groups":2074438,"generated_calls":253003076,"unique_owner5_checked":108314136,"eligible_owner5":7912850,"max_supported_pool":21}
```

No radius <=5 improvement exists in these complete unrestricted strata.

## Why this mother remains interesting

Compared with the earlier 18-for-18 neutral mother, the 47-for-47 state has fewer coverage-1 outsiders but slightly more eligible five-owner lower-support pools (`7,912,850` versus `7,849,057`). The neutral move therefore did not merely create many private one-point repairs; it reorganized low-support candidates into a denser combinatorial boundary. This makes radius-6 exact search on this mother scientifically better motivated than blindly increasing radius on the original public baseline.

A packed single-runner radius-6 workflow reuses the previously audited support-6/5/4/3/2 decomposition, avoiding the historical 48-job matrix and repeated full-space preprocessing.
