# p017 — Linear ordering N-be75eec_500

## Current state (2026-11-12)
Few Shots `data/board.json` (generated 2026-11-12T12:05:18Z) reports **33,489,269**, no merged shots. The authoritative instance is a 500×500 integer matrix embedded in Few Shots' p017 verifier, original SHA256 `34e940a0ecd9c0a054dfa87c0ad4d2b9286ba141d98be1dcb7ce463fe3f22437`. Objective: maximize `sum(M[order[i]][order[j]] for i<j)`. Baseline canonical SHA256 `6c9cf526e303289cb0305c009fc8cef35e05f385ae98418c2b071ab8c9ebcd48`. Strict improvement requires >=33,489,270.

## Research plan
1. Independently verify baseline against embedded matrix.
2. Compile a C++ insertion-based iterated local search baseline and compare candidate quality and diversity.
3. Experiment with long-range ruin/recreate and recombination of elite permutations, then verify each new record using Few Shots verifier and `tools/check.py`.
4. Submit only after a valid strict improvement.

## Sources
- [Few Shots p017 definition](https://github.com/few-shots/few-shots/blob/main/problems/p017-lop-be75eec-500/PROBLEM.md)
- [Few Shots live board](https://github.com/few-shots/few-shots/blob/main/data/board.json)
- [2025 memetic algorithm, Lugo et al.](https://doi.org/10.1007/s00521-025-11171-z), baseline archive [Zenodo 14720629](https://zenodo.org/records/14720629)
- [2026 decomposition-based constructive LOP heuristics](https://arxiv.org/abs/2606.24558)
- [2026 diverse LOP solutions](https://arxiv.org/abs/2605.31051)

## Experiments
Pending first reproducible run. Solver source will be preserved in this topic; workflows are ephemeral orchestration.

## Handoff
Use only verified scores. The baseline is extremely strong and a local insertion optimum may not improve it. Search diversity and coupled perturbations matter more than repeating identical descent basins.
