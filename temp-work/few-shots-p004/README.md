# Few Shots p004 search

Temporary exploration of `few-shots/few-shots` problem p004 (independent set in `C7^⊠10`).

## Goal

Beat the current 134,753-point certificate without touching the upstream repository.

## Current approach

Treat the 10 coordinates as the torus `Z_7^10`. For the baseline independent set, compute the exact number of baseline points in every vertex's closed strong-product neighborhood by ten separable cyclic `[1,1,1]` convolutions over the full `7^10 = 282,475,249` vertex space.

This gives two exact local breakthrough tests:

1. coverage 0: a vertex can be added directly (`+1`);
2. coverage 1: vertices covered by exactly one baseline point are grouped by that unique owner; two non-adjacent vertices with the same owner give a valid `remove 1, add 2` move (`+1`).

A parallel XOR convolution propagates the unique baseline-owner index for every coverage-1 vertex, so the search does not need expensive neighborhood rescans.

The solver is deterministic and uses only integer arithmetic. Any candidate is rebuilt into the upstream certificate format and checked with the upstream p004 verifier before being kept.

## Files

- `search.cpp` — full-space exact coverage / 1-for-2 search.
- `materialize.py` — converts the upstream certificate to solver IDs and rebuilds any candidate certificate.
- `.github/workflows/temp-few-shots-p004.yml` — temporary one-shot/manual Action. It has no recurring schedule and does not write to upstream.

## Output policy

No ordinary failed search is committed. If an upstream-verifier-valid score above 134,753 is found, the workflow commits the verified certificate and search result under `temp-work/few-shots-p004/breakthrough/` in this repository only. Upstream submission remains a separate user decision.

Nothing from this experiment should become durable repository infrastructure unless explicitly requested.
