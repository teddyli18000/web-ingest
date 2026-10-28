# BPZ / t=9 obstruction frontier

Status as of 2026-10-28. These are computational statements about the stated search families, not a proof that `alpha(C7^10) = 134753`.

## BPZ/Tan J+ seed

A public eight-exchange 10-dimensional seed `J+` was materialized from the pinned public implementation in `tandonravi/C7-Shannon-Capacity-Heterogeneous-Recursion` at commit `c753408492dde92a239708986d16c15dbf6c3235`.

The Few Shots p004 verifier accepts this seed with score `134753` and canonical hash

`ac593f1040cef29621bfe705305359360ca58cb47fa1482ae810a51ca9b16b95`.

It is therefore a genuinely different verifier-valid boundary state, not merely a re-encoding of the original certificate.

Exact local search around this seed found no improvement through the searched owner-union neighborhoods:

- add-1 / 1-for-2 / 2-for-3: none;
- exhaustive 3-for-4: `1,299,798` candidate owner triples, none;
- exhaustive connected 4-for-5: `10,398,325` candidate owner quads, none.

The J+ seed remains useful as a structurally different boundary state, but shallow local exchange is exhausted through 4-for-5.

## BPZ t=9 obstruction formulation

The t=9 Gao/BPZ-style construction would have score

`367^2 + 9^2 = 134770`,

a gain of 17 over the Few Shots baseline, if a 367-point auxiliary independent set can avoid the obstruction `D = N(P^H) intersect N(P^V)` for a valid nine-private-pair witness.

The public seed family used in the translation scan contains 38 verifier-replayed `C7^5` independent sets: BPZ `I0`, BPZ `X`, and the 36-state Family F from `molind/c7-five` pinned at commit `ae81e0d24b356aef3d388238f6fb4d02c4aa32a5`.

Across 38 seeds and 160 obstruction masks (`6080` seed/mask cases), exact FFT correlation found 20 unique translated states with minimum obstruction intersection exactly one. This is the strongest translated public-seed boundary found so far.

### Exact repair radius around the 20 one-hit states

All searches below regenerate the translation and obstruction exactly and replay every candidate independent set before constructing a 10D certificate.

- 1-for-1: none. The one-hit states expose no legal direct replacement.
- 2-for-2: none. `7320` second removals were tested; only 50 candidate pools existed; maximum pool size was 2.
- 3-for-3: none. `1,335,900` removal triples were tested, `21,400` had candidate pools of size at least 3, `15,866` candidate triples were checked, and the maximum pool size was 5.
- 4-for-4 owner-union search: none. Across the 20 states there were `31,060` external candidates satisfying the four-owner budget, at most `1554` in one state, and `41,395` DFS nodes were explored. No compatible four-tuple reached the terminal condition (`terminal_candidate_quads = 0`).

The 4-for-4 implementation omits old-set vertices from the addition pool. This is exact given the already completed 1/2/3-for-3 negatives: if a 4-repair re-added an old removed vertex, cancelling that remove/add pair would yield a smaller repair already covered exactly.

### Two-hit translated states

There are 30 unique public translated states whose minimum obstruction intersection is exactly two. Exact removal of both obstruction hits followed by a 2-for-2 repair found no candidate at all: the maximum replacement pool was zero in every state.

## Larger unresolved exact models

Two larger exact formulations have not produced mathematical negative results; they timed out and must not be recorded as UNSAT.

1. `rank3_x294_ambient_maxsat.py` frees the special rank-3 `H(X_294)` fiber over all `7^5` endpoints and jointly optimizes live port variables. Setup size was 30,001 variables, 2,033,647 special-fiber independence edges, 178,362 special cross clauses, and 3,480 ordinary cross clauses. RC2 was cancelled at the 90-minute workflow limit.
2. `bpz_t9_obstruction_mis.py` asks directly whether `C7^5 \ D` contains an independent set of size 367 for a strong t=9 obstruction witness. The exact cube-cover + global-cardinality Minicard formulation was cancelled after roughly two hours. A ranked-small-obstruction campaign also timed out rather than proving UNSAT.

These remain open computational directions; the bottleneck is the general-purpose global cardinality/MIS solve, not construction or verifier replay.

## Current active route

`code/bpz_t9_exchange_repair.py` converts each one-hit translated state to the exact blocker-budget format used by `molind/c7-five/search/exchange_dfs.cpp`.

After pre-deleting the unique bad point `x`, a `k`-for-`k` repair is exactly a choice of `k` pairwise-compatible new vertices whose union of blockers against the remaining 366 old vertices has size at most `k-1`. Therefore the upstream exchange DFS with radius `r` searches `r+1` additions with at most `r` blockers.

The first campaign uses blocker budget 4, i.e. exact 5-for-5 repair, sharded across all 20 one-hit states. Any witness is replayed as a 367-point obstruction-avoiding auxiliary set and then passed through the Few Shots p004 verifier as a nominal 134770-point certificate.

## Reusable code

- `code/bpz_jplus_seed.py`
- `code/search3_full.cpp`
- `code/search4_full.cpp`
- `code/bpz_t9_aux_translation_fft.py`
- `code/bpz_t9_translation_one_repair.py`
- `code/bpz_t9_translation_two_repair.py`
- `code/bpz_t9_translation_three_repair.py`
- `code/bpz_t9_translation_four_repair.py`
- `code/bpz_t9_exchange_repair.py`
- `code/bpz_t9_obstruction_mis.py`

Transient workflow files and logs are intentionally not treated as durable scientific evidence; the numerical facts above were read from completed Action logs and correspond to the pinned code paths listed here.
