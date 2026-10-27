# Research inputs

## `few-shots-baseline.json`

Pinned copy of the authoritative Few Shots p003 baseline certificate used as the 35-vertex seed for local/exact-neighborhood searches.

- Upstream repository: `few-shots/few-shots`
- Upstream path: `problems/p003-ramsey-r46/baseline/certificate.json`
- Upstream branch when pinned: `main`
- Upstream Git blob SHA: `858e9b6c71938a24964ce38e228524d20c4a1870`
- Local Git blob SHA after correction: `858e9b6c71938a24964ce38e228524d20c4a1870`
- Meaning: Exoo (2012) 35-vertex `(4,6)` graph used by Few Shots as the current p003 baseline.

The identical Git blob SHA is the byte-for-byte provenance check. Search scripts should use this pinned local copy rather than silently fetching a mutable remote `main` file.

## `r36_17.g6`

Pinned complete catalogue of all seven non-isomorphic Ramsey `(3,6,17)` graphs, used to exhaust the degree-17 branch of a hypothetical `(4,6,36)` graph.

- Authoritative catalogue page: Brendan McKay, Ramsey Graphs, `https://users.cecs.anu.edu.au/~bdm/data/ramsey.html`
- Upstream data URL: `https://users.cecs.anu.edu.au/~bdm/data/r36_17.g6`
- Checked 2026-10-27: catalogue page states exactly 7 graphs on 17 vertices.
- SHA-256 of the 175-byte pinned file: `3286c5366ddc70f349c3f7e798d7acbc79dc026c7abe0c8f406cad41ca990361`

`degree17_catalog_sat.py` independently decodes and validates every record as triangle-free with no independent 6-set before using it.
