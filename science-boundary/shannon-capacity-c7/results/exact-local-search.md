# Exact local replacement results

Date: 2026-10-27

These are exact negative results around the 134,753-point Few Shots p004 baseline in `C7^⊠10`. They constrain this specific baseline and these replacement neighborhoods only; they are not impossibility results for the graph itself.

## 0→1, 1→2, 2→3

`code/search_exact.cpp` performs exact full-space conflict coverage over all `7^10 = 282,475,249` vertices by ten separable cyclic `[1,1,1]` transforms.

Result:

- direct add-1: none;
- remove-1/add-2: none;
- remove-2/add-3: none;
- outside vertices of coverage 1: **5,178**;
- coverage-1 compatible pairs tested within their unique owner groups: **26**;
- coverage-2 vertices: **144,861**;
- coverage-2 owner pairs: **136,379**;
- largest exact remove-2 candidate union: **5**.

The initial exact run completed in a few seconds on a GitHub-hosted runner with roughly 4 GiB peak memory.

## 3→4

`code/search3.cpp` extends the owner reconstruction to coverage-3 vertices and exhaustively tests all relevant owner triples.

Exact result from GitHub Actions run `40516292494`:

```json
{"kind":"none","method":"exact-3-for-4-cov3","baseline_size":134753,"cov1":5178,"cov2":144861,"cov3":999144,"triple_groups":966479,"max_pool":10}
```

Key facts:

- coverage-3 vertices: **999,144**;
- distinct owner-triple groups: **966,479**;
- largest candidate pool for a remove-3/add-4 test: **10**;
- no independent 4-set was found in any admissible pool.

The search step completed in about 5 seconds wall-clock on a 4-vCPU GitHub runner, with about 4.98 GiB peak RSS.

## 4→5

`code/search4.cpp` reconstructs exact coverage-4 owner quadruples using min/max, first moment, and second moment transforms, then checks every admissible remove-4/add-5 candidate pool.

Exact result from GitHub Actions run `40520359723`:

```json
{"kind":"none","method":"exact-4-for-5","baseline_size":134753,"cov1":5178,"cov2":144861,"cov3":999144,"cov4":2131704,"quad_groups":2076092,"eligible_groups":97550,"max_pool":15}
```

Key facts:

- coverage-4 vertices: **2,131,704**;
- distinct owner-quadruple groups: **2,076,092**;
- groups with candidate-pool size at least 5: **97,550**;
- largest candidate pool: **15**;
- no independent 5-set was found in any admissible pool.

The scientific search step completed successfully with exit code 0 in about 9.3 seconds wall-clock and about 8.29 GiB peak RSS. The overall workflow was marked failed only because its final summary shell command used a false `[[ -f verify.json ]]` test under `set -e`; that CI status is not a search failure.

## Consequence

The current 134,753 construction is exactly locally rigid through remove-4/add-5 under the owner-support formulation used here. Further progress should not simply repeat shallower `k→k+1` neighborhoods. The current stronger route is the structural neutral2/MaxSAT family documented in the topic README and `neutral2-maxsat-summary.md`.
