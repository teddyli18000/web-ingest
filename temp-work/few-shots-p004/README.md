# Few Shots p004 search

Temporary exploration of `few-shots/few-shots` problem p004 (independent set in `C7^⊠10`).

## Goal

Beat the current 134,753-point certificate without touching the upstream repository.

## Current approach

Treat the 10 coordinates as the torus `Z_7^10`. For the baseline independent set, compute the exact number of baseline points in every vertex's closed strong-product neighborhood by ten separable cyclic `[1,1,1]` convolutions over the full `7^10 = 282,475,249` vertex space.

The exact local search currently checks:

1. **add 1 directly**: any outside vertex with coverage 0;
2. **remove 1, add 2**: collect every outside vertex with coverage 1 by its unique conflicting baseline owner, then exhaustively test every pair in each owner group for non-adjacency;
3. **remove 2, add 3**: recover the exact two conflicting baseline owners for every coverage-2 vertex using separable min/max owner transforms, then for each owner pair search the full union of its coverage-2 candidates and the two coverage-1 groups for an independent triple.

These are exhaustive local statements, not random samples. The solver uses exact integer arithmetic for coverage and exact `C7^⊠10` adjacency tests.

Any candidate is rebuilt into the upstream certificate format and checked with the upstream p004 verifier before it is kept.

## Files

- `search.cpp` — earlier fast local-search prototype retained for comparison.
- `search_exact.cpp` — exhaustive direct / 1→2 / 2→3 local breakthrough search.
- `materialize.py` — converts the upstream certificate to solver IDs and rebuilds candidate certificates.
- `.github/workflows/temp-few-shots-p004.yml` — temporary Action. It has no recurring schedule and does not write to upstream.

## Output policy

Ordinary failed searches are not committed. If an upstream-verifier-valid score above 134,753 is found, the workflow commits the verified certificate and search result under `temp-work/few-shots-p004/breakthrough/` in this repository only. Upstream submission remains a separate user decision.

If the exact radius-2 replacement search is closed without a breakthrough, the next stage is a deeper branch-and-bound / stochastic search built from the low-coverage candidate structure rather than blind random mutation.

Nothing from this experiment should become durable repository infrastructure unless explicitly requested.
