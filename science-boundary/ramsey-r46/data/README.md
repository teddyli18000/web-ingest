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

## `r45_23_e101.g6`

Pinned unique 23-vertex Ramsey `(4,5)` graph with 101 edges. It is the entire minimum-edge stratum and therefore the unique possible antineighborhood in the lucky degree-12 reduction.

- Authoritative source archive: Brendan McKay, `https://users.cecs.anu.edu.au/~bdm/data/r45extreme.tar.gz`
- Source archive SHA-256: `9cfac9dbd1c209cfa342e5d5424df2a7a3fbb008ca00bf0a992e5bbe72f925b6`
- Source member: `r45extreme/r4523.101.g6`
- Source member contains exactly one graph6 record.
- Pinned file SHA-256: `bf403d6b148c60a26d2536ade61d74d552972f701f3fdbb143478d97652c20ec`
- Independently reproduced archive inventory: `../results/r45extreme-inventory.json` records exactly one `(n=23,e=101)` graph.
- Evidence artifact: GitHub Actions run `40628847295`, artifact `12790493429` (`ramsey-r46-r45extreme-inventory`), whose uploaded ZIP includes the authenticated source archive and inventory.

This tiny pinned record should be preferred for repeated exact gluing runs. Re-downloading and scanning the ~90 MB source archive is unnecessary once its provenance and uniqueness have been authenticated.
