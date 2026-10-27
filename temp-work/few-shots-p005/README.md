# Few Shots p005 cap-set search

Temporary exploration of `few-shots/few-shots` problem p005: find a cap set in `F_3^8` larger than the 512-point baseline.

## Goal

Produce a verifier-valid certificate with at least 513 points. Do not modify or submit to the upstream repository.

## Approach

Run fixed-cardinality local search at size 513, seeded from the published 512-point cap. For a current selected set `S`, maintain for every ambient point `u` the number `conf[u]` of selected pairs whose third collinear point is `u`. Then:

- `conf[r]` for selected `r` is exactly the number of violating lines containing `r`;
- swapping selected `r` for outside `u` changes the number of violating lines by `-conf[r] + conf_after_remove[u]`;
- `conf_after_remove[u]` is available in O(1), while an accepted swap updates all conflict counts in O(|S|).

This supports tabu/min-conflicts and annealing at high move rates without materializing the roughly seven million affine lines.

Any zero-violation 513-set is converted to the upstream certificate format and checked with the upstream verifier before it is saved under this workspace.

## Files

- `extract.py` — converts the upstream baseline certificate to base-3 integer IDs and materializes a candidate.
- `search.cpp` — fixed-size 513 cap-set local search.
- `.github/workflows/temp-few-shots-p005.yml` — temporary one-shot/manual Action.

Nothing here should be promoted to persistent repository infrastructure without an explicit request.
