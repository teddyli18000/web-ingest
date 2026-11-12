# p017 — Linear ordering N-be75eec_500

## Current state (2026-11-12)

Few Shots current merged record: **33,489,269** (baseline, no merged shots at initial synchronization on 2026-11-12).
A valid shot must score **>= 33,489,270**.

- **Exact instance:** 500×500 matrix, original SHA-256 `34e940a0ecd9c0a054dfa87c0ad4d2b9286ba141d98be1dcb7ce463fe3f22437`.
- **Objective:** `S(p)=Σ_{i<j} W[p[i]][p[j]]`. Use the full asymmetric matrix, not just pair differences for the numerical score.
- **Baseline canonical SHA-256:** `6c9cf526e303289cb0305c009fc8cef35e05f385ae98418c2b071ab8c9ebcd48`.
- **Public record:** `https://github.com/few-shots/few-shots/blob/main/data/board.json`.
- **Verifier:** `https://github.com/few-shots/few-shots/blob/main/problems/p017-lop-be75eec-500/verify/verify.py`.

## Constructive search mechanisms

1. **Multi-start ILS** (`search.cpp`) — full-insertion descent with variable ruin/recreate, reversals, swaps and random relocations. Search job `43241386921`: https://github.com/teddyli18000/web-ingest/actions/runs/43241386921.
2. **Exact sparse-hole reassignment** (`exact_holes.cpp`) — select `k ∈ [13,19]` rank positions and exactly optimize the reassignment of the existing vertices among those selected positions, with all other vertices fixed, by a Held–Karp-style subset DP. The DP solves an exact coupled `k!` permutation neighborhood with `O(k 2^k + nk)` work once pair subset sums have been computed; the hole selector alternates contiguous windows, disjoint windows, sparse segments, conflict-biased ranks, and global positions. Between exact moves, insertion-based basin shifts are applied. Job `43242538837`: https://github.com/teddyli18000/web-ingest/actions/runs/43242538837.
3. **Paired long-range insertions** (`paired_insert.cpp`) — enumerate lowest-loss first relocations `(i,j)`, perform each, then find the **globally best second relocation** in that modified ordering. Retain the pair if its sum is strictly positive and then run full insertion descent. This can realize coordinated long-range changes that are not in the small-hole exact neighborhood. Job `43243202275`: https://github.com/teddyli18000/web-ingest/actions/runs/43243202275.

4. **Large exact/anytime precedence windows** (`cpsat_windows.py`) — CP-SAT optimizes all pair orientations in contiguous blocks of sizes 36, 44, 54, 66, 78. Acyclicity is enforced by `0 ≤ x_ij+x_jk−x_ik ≤ 1` for each triple, with baseline orientation as an initial hint. Runs 4 independent worker processes. Job `43244298765`: https://github.com/teddyli18000/web-ingest/actions/runs/43244298765.

All methods use the matrix extracted by `prepare.py`, which checks the original instance hash and the baseline score. The job scripts run the independent Few Shots verifier against the final candidate; only final verified improvements are potential submissions. Persisted results go under `results/` after job completion.

### Sparse-hole DP derivation

Let `P[0..k-1]` be selected ranks, `V[v]=p[P[v]]` the selected vertices. For each rank `t` and selected vertex `v`, define `U[t,v]` as the objective contribution between `v` placed at rank `P[t]` and **all fixed vertices** (which are outside the selected set). The best selected ordering is exactly

`dp[mask ∪ {v}] = max(dp[mask ∪ {v}], dp[mask] + U[popcount(mask),v] + Σ_{u∈mask}W[V[u]][V[v]])`.

This jointly optimizes interactions both among selected vertices and with the frozen outer order. It is an exact neighborhood search, not a proof about the 500-element global optimum.

### Paired-insertion derivation

For a vertex `v=p[i]` and a relocation to position `j<i`, the score delta is `Σ_{j≤t<i}(W[v][p[t]]−W[p[t]][v])`. For `j>i`, reverse the sign of the corresponding pair sum. The second insertion is evaluated after applying the first, so its delta contains the coupling induced by the first move. The source checks the predicted double-move gain against a full 124,750-pair objective computation when it finds a strict improvement.

## Measured outcomes

- **2026-11-12 — paired insertion, completed:** scanned the 40,000 lowest-loss first moves from the published baseline (first-move losses up to 10,720), searching the globally strongest second insertion after each; **no improvement**. Official Few Shots verifier returned `{"valid":true,"score":"33489269"}`, canonical hash identical to baseline. This is only an unsuccessful *selected two-move neighborhood*, not evidence of global optimality. Output: `results/paired-search.log`, `results/paired-verification.json`, and `results/paired-best.json`. The search direction pivots toward larger coordinated subsets rather than expanding this enumeration blindly.

## Next steps

1. Inspect each job's official verifier result and source log (not merely its green/red status).
2. If a strict improvement is found, freeze the highest-scoring permutation and run Few Shots `tools/check.py` using a valid SHOT.md before opening the authorized submission PR.
3. If no improvement is found, compare the actual best scores and attempt counts, then reset the search representation: tune conflict-biased selection, use long-range precedence cycles / compound moves, and investigate exact larger coupled components.
4. Preserve structural diversity of distinct elites to facilitate true recombination; do not repeatedly sample the same single parent basin.

## Literature

- Lugo, Segura and Miranda (2025), *Future trends in the design of memetic algorithms: the case of the linear ordering problem*: https://doi.org/10.1007/s00521-025-11171-z ; preprint https://arxiv.org/abs/2405.08285 . This is the strong baseline construction; the paper emphasizes enhanced intensification at longer compute budgets.
- Lugo, Segura and Miranda (2021), *A Diversity-Aware Memetic Algorithm for the Linear Ordering Problem*: https://arxiv.org/abs/2106.02696 .
- Santucci and Ceberio, *Using pairwise precedences for solving the linear ordering problem*: https://www.sciencedirect.com/science/article/pii/S1568494619307793 . Motivates precedence-aware moves.
- Ando, Sugimoto and Sukegawa (2026), *Decomposition-Based Constructive Heuristics for the Linear Ordering Problem*: https://arxiv.org/abs/2606.24558 . Reports constructive recursive partition methods; local insertion search narrows differences.
- Benito-Marimon, Martí and Martínez-Gavara (2026), *Multiple linear ordering problem*: https://doi.org/10.1016/j.ejor.2025.10.040 . Discusses diverse high-quality permutations via VNS.
- Historical benchmark and permitted original matrix source: https://github.com/sgpceurj/EJOR2015 ; public BKS https://zenodo.org/records/14720629 .

## Work log

- **2026-11-12:** Synced p017 board and authoritative problem definition. Added exact instance decoder, an initial ILS engine, and a 4-thread 1000-second Action.
- **2026-11-12:** Designed exact sparse-hole dynamic programming and compiled successfully in a 4-thread Action (650 seconds). Added a separate long-range paired-insertion search; first selected two-move scan completed without improvement. Started a 4-worker CP-SAT larger-window search. Other campaigns run against the frozen published baseline or the best independently scored candidate available at job start. Awaiting independent verifier outputs.
