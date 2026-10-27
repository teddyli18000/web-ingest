# Few Shots p005 cap-set search

Temporary exploration workspace for `few-shots/few-shots` problem **p005: cap set in F_3^8**.

## Goal

Beat the current 512-point certificate by finding a valid cap set with at least 513 points. This workspace is read-only with respect to the upstream repository: it may fetch public problem data and the official verifier, but it must not open PRs, push branches, create issues, or otherwise mutate `few-shots/few-shots`.

The upstream snapshot used to seed the campaign is commit `b3424ef44107cd31cc76db4dfaa7537462d78fc7` (2026-10-27). The seed certificate is `problems/p005-cap-set-8d/baseline/certificate.json`, score 512.

## Search

`search.cpp` keeps a valid cap set at every accepted state. For every outside point it maintains the number of selected pairs that would complete a 3-term affine line through that point. A move chooses a low-conflict outside point, ejects one endpoint from each blocking pair, inserts the point, then greedily repairs the set with zero-conflict insertions. Simulated-annealing acceptance and occasional shakes allow temporary size loss to move between maximal cap sets.

`capset_tools.py` converts the upstream JSON certificate to the compact integer representation used by the searcher, validates candidates independently, converts candidates back to the Few Shots certificate format, and selects the best shard result.

The disposable workflow `.github/workflows/few-shots-cap-set.yml` launches eight independent shards per wave. It is intentionally **not scheduled**. The initial workflow-file commit starts wave 0; a bounded `repository_dispatch` chain may run at most four waves total. If a shard reaches 513, the aggregate job re-validates it, runs the pinned official upstream verifier, and commits the verified certificate only under this workspace as `breakthrough/`.

## Outputs

- No routine search state is committed.
- Action logs/artifacts contain per-shard candidates for the current run.
- A verified improvement, if found, is committed under `breakthrough/` with the certificate and verifier result.
- Nothing is submitted upstream automatically. Upstream submission is explicitly out of scope until the owner reviews the result.

## Lifecycle

This is disposable temporary work. If the campaign does not produce a breakthrough, the workflow and workspace can be removed. If it does, only the verified certificate and concise search notes are worth preserving long enough for owner review; any upstream action requires a separate explicit decision.
