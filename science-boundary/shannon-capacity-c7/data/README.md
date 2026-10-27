# Public input provenance

The durable research code intentionally does not copy large or authoritative upstream inputs into this directory.

## Few Shots p004 baseline and verifier

Repository: `few-shots/few-shots`

Paths:

- `problems/p004-shannon-capacity-c7/baseline/certificate.json`
- `problems/p004-shannon-capacity-c7/verify/verify.py`
- `problems/p004-shannon-capacity-c7/PROBLEM.md`

At migration time on 2026-10-27, the public Few Shots board still listed the p004 baseline as **134,753** with no merged p004 record above it.

For the exact local searchers, convert each 10-digit base-7 point string in the baseline certificate to an integer ID using `int(point, 7)`, one ID per line.

## C7^⊠5 parent set

Repository: `nathanielitty/lower-bounds-for-shannon-capacity`

File: `c7/R367.txt`

The initial exploration used the public revision around commit `fe8966079013abaac21d1c08441500100f8e3b86`, which contains the 367-point parent and the construction script used to interpret the baseline structure.

## Verification policy

Any candidate with score at least 134,754 must be independently replayed through the Few Shots p004 verifier before it is treated as a breakthrough. The research scripts here are search machinery, not the final authority on certificate validity.
