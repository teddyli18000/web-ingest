# Coupled-root direct-100 searches — 2026-11-04

## Objective and public status

Search for a valid AES S-box circuit of at most 100 two-input AND/XOR/XNOR gates, starting from the merged Few Shots 101-gate certificate (33 AND + 68 linear). The official board was rechecked on 2026-11-04 and still records 101, verified 2026-10-29. Both scripts independently validate the original seed on all 256 inputs.

These are narrowly stated constructive searches, not lower bounds for AES S-box complexity.

## Method: joint observability, not separate ODC

Ordinary ODC requires each replacement to preserve the outputs by itself. Two individually invalid replacements may compensate.

For a shared replacement signal h, let F00 and F11 be full-circuit counterfactual AES outputs when both selected gate roots are forced to 0 or both to 1. If h is computed before the earlier root, F(h,h) is F00 where h=0 and F11 where h=1. Therefore at each input byte at least one forced output must match the original AES output. Those two forced evaluations give a necessary and sufficient 256-bit care mask for h.

For deletion + compensation, the first gate root is replaced with an earlier wire, even if the circuit becomes incorrect. Each later gate is forced to 0 and 1 under that broken circuit, giving an exact repair mask. Every single legal retarget AND/XOR/XNOR gate is tested against the repair mask.

## Experiment 1: shared signal, true joint ODC

Script: [joint_pair_cofactor_search.py](../joint_pair_cofactor_search.py)
Action: [run 41720513108](https://github.com/teddyli18000/web-ingest/actions/runs/41720513108)
Commits: ae50a212b0e929e80da73fbd1acf695698dd65d0, 89892d241f56e4445b38b690e03eb751de37ab87.

All 8 shards completed:

- 5,050 ordered root pairs (all i<j among 101 gates);
- only 48 pairs admit even an arbitrary Boolean common replacement h under joint AES output care;
- 325,119 concrete single-helper candidate checks; no helper matches, no aliases match;
- zero valid <=100 candidate.

The first admissible example on each shard had 255 fixed truth-table positions, so identifying two roots to the same signal leaves almost no freedom.

Scope: replace both root outputs by one earlier existing wire or one new AND/XOR/XNOR from two earlier wires. Surviving same-operand gates are rejected. Does not exclude three-site changes, nonlinear factorization changes, or nontrivial constant simplification.

## Experiment 2: delete one root, compensate at a later gate

Script: [delete_alias_compensate.py](../delete_alias_compensate.py)
Action: [run 41721273255](https://github.com/teddyli18000/web-ingest/actions/runs/41721273255)
Commits: e89c1589d988d359f4dbd80acd3f2920357c9873, f0cf384890be8ed09dfe493de35c31d7d0fbbd7a.

All 8 shards completed. Its positive two-gate control validated the mechanism.

- 5,858 distinct earlier-wire alias deletion cases;
- 207,050 (deletion, later-repair-position) cases;
- 3,329 positions admit some abstract Boolean repair function;
- 32,330,940 concrete legal AND/XOR/XNOR gate candidates tested;
- no matching gate and zero verified <=100 circuit.

Scope: alias-delete an earlier gate, retarget one *later* gate to an arbitrary two-input AND/XOR/XNOR over available signals, and keep the remaining network fixed except dead-gate pruning. Neither individual edit must be AES-correct. Not a global exclusion.

## Related G103 two-new search

The 32-AND/103-gate G103 late-tail search in [run 41195582759](https://github.com/teddyli18000/web-ingest/actions/runs/41195582759) completed all 16 shards. It checked all 4,368 choices to drop five of 16 internal late-tail guides, retained eight output functions, and inserted two new helpers, with approximately 3.47 million second-helper checks. No <=100 result. Every shard's best residual was (0 unreleased AND, 2 missing AES outputs, 2 blocked retained guides).

## Scientific interpretation / handoff

Candidate quality stayed flat while exact exclusions grew around fixed 101/G103 DAG interfaces. Do not extend these one- or two-site families. Change representation: allow coordinated three-or-more-site transformations including AND factorizations, and jointly search seed architectures and affine interfaces instead of only minimizing a frozen tail.

There was no certificate for the official Few Shots verifier, and no submission PR was appropriate.
