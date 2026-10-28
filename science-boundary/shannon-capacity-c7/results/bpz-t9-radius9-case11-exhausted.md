# BPZ t=9 radius-9 case 11: exact exhaustion

Status date: 2026-10-28.

This records a mathematically complete negative result for one of the 20 translated one-hit BPZ t=9 obstruction cases.

## Statement

For one-hit case 11, there is **no 9-for-9 repair** of the 367-point auxiliary within blocker budget 8.  Equivalently, after deleting the mandatory obstruction hit and obtaining the canonical 366-point obstruction-free set, there is no independent 9-set of allowed additions whose conflict-owner union has size at most 8.

This is an exact finite search result, not a timeout inference.

## Exact decomposition

The pinned increasing-index DFS has 15,085 first-choice roots for this case.  The complete root range `[0,15085)` was covered by disjoint exact runs:

- initial search: completed `[0,17)` before timeout;
- first continuation: completed `[17,115)` before timeout;
- exact shards: `[115,120)`, `[120,128)`, `[128,136)`, `[136,148)`, `[148,160)`, `[160,256)`, `[256,512)`, `[512,1024)`, `[1024,2048)`, `[2048,4096)`, `[4096,15085)`.

Every shard above returned `status=exhausted`; no shard produced a witness, so the Few Shots verifier step was correctly skipped.

## Reproducibility

Public sources are pinned to:

- `tandonravi/C7-Shannon-Capacity-Heterogeneous-Recursion@c753408492dde92a239708986d16c15dbf6c3235`;
- `molind/c7-five@ae81e0d24b356aef3d388238f6fb4d02c4aa32a5`.

Durable continuation driver:

- `code/bpz_t9_exchange_continue.py`

Relevant temporary Action runs:

- initial radius-9 matrix: `40609094769`;
- case11 continuation from root 17: `40611695811`;
- case11 large tail shards: `40620090449`;
- case11 final early shards: `40620440007`.

The important correctness condition is the solver's own `status=exhausted` for every interval.  GitHub Action success by itself is not treated as a proof because earlier workflows intentionally returned normally on solver timeout.

## Consequence

Case 11 cannot yield the nominal t=9 score `367^2 + 9^2 = 134,770` by any repair of radius at most 9 around its translated one-hit auxiliary.  The other 19 one-hit cases are being completed independently; this file makes no claim about them.
