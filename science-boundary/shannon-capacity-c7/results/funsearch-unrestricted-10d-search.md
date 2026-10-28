# FunSearch one-hit deletion seed: unrestricted 10D exact search

Status: 2026-10-27 (America/Los_Angeles).

These results concern the four exact C5 orbit representatives `[0,1,2,3]` of the 40 FunSearch t=9 one-hit states. The two 20-state basins are also exactly isomorphic, so automorphism-invariant conclusions below apply to all 40 states.

## Baseline

Deleting the unique obstruction-hit auxiliary point from a t=9 one-hit state leaves a valid 366-point auxiliary set and a verifier-accepted `C7^10` independent set of size

`(367-9)^2 + 2*9*366 = 134752`.

The dedicated materializer is `code/bpz_t9_funsearch_deleted_seed.py`. The earlier attempt to reuse the 134770-only BPZ builder was an implementation error and produced no mathematical result; the dedicated replay fixes this and each search workflow independently checks score 134752 with the Few Shots p004 verifier before searching.

## Exact unrestricted radius 0: add 2

Full-space `7^10 = 282,475,249` coverage transforms show `coverage0 = 0` on the representative deletion seeds. Thus each seed is maximal: there is not even one directly addable ten-dimensional vertex.

Reusable solver: `code/search_add2.cpp`.

## Exact unrestricted radius 1: remove 1 / add 3

All four C5 representatives are negative. Representative statistics include:

- case 0: `coverage1=6308`, 36 owners with at least two coverage-one candidates, maximum raw group size 2, 36 candidate pairs checked;
- case 1: `coverage1=6290`, 18 such owners, maximum group size 2, 18 pairs checked;
- case 3: `coverage1=6269`, 18 such owners, maximum group size 2, 18 pairs checked.

No single-owner coverage-one group contains the compatible additions required for a net +2 exchange. The radius-2 and radius-3 solvers independently recheck the lower-radius conditions rather than assuming these artifacts.

Reusable solver: `code/search_net2_r1.cpp`.

## Exact unrestricted radius 2: remove 2 / add 4

All four C5 representatives are negative. The search recovers exact coverage-two owner pairs with separable min/max transforms and checks every relevant real two-owner candidate pool.

Representative statistics:

- case 0: `coverage1=6308`, `coverage2=143680`, 360359 owner pairs checked, 227439 eligible pools, maximum supported pool 6;
- case 1: `coverage1=6290`, `coverage2=143706`, 248001 owner pairs checked, 115038 eligible pools, maximum supported pool 6;
- case 2: `coverage1=6287`, `coverage2=143950`, 359588 owner pairs checked, 226693 eligible pools, maximum supported pool 6.

No unrestricted remove-2/add-4 net-+2 witness exists in any of the four representatives.

Reusable solver: `code/search_net2_r2.cpp`.

## Exact unrestricted radius 3: remove 3 / add 5

All four C5 representatives are negative. This solver was written specifically to avoid the historical completeness issue of considering only owner triples that appear as the support of a coverage-three vertex.

It first re-proves the radius-1 and radius-2 negatives internally, then exhausts all three-owner support patterns:

1. a selected coverage-three vertex directly supplies its three-owner union;
2. two distinct selected coverage-two supports sharing an owner supply their three-owner union;
3. with exactly one coverage-two support, radius-2 negativity forces the third owner to contribute a compatible coverage-one pair;
4. with coverage-one vertices only, radius-1 negativity forces at least two owners to contribute compatible pairs.

For case 0:

- `coverage1=6308`;
- `coverage2=143680`;
- `coverage3=999531`;
- `coverage2_groups=135344`;
- `coverage3_groups=961338`;
- `active_c1_owners=6272`;
- `heavy_c1_owners=0` (no owner has a compatible coverage-one pair);
- `triples_checked=1296968`;
- `eligible_triples=25505`;
- maximum supported three-owner pool 10.

For case 1 the analogous values are `coverage1=6290`, `coverage2=143706`, `coverage3=999380`, 135370 coverage-two groups, 961199 coverage-three groups, 1297139 owner triples checked, 25600 eligible triples, and maximum supported pool 10; again `heavy_c1_owners=0`.

All four workflows completed successfully with no candidate, so their Few Shots breakthrough verification steps were skipped.

Reusable solver: `code/search_net2_r3.cpp`.

## Exact neutral one-swap components

For each of the four C5 representatives, the entire neutral one-for-one swap component that keeps the unique bad point fixed has exactly two states: the starting state and one neutral neighbor. Each component has maximum depth 1, two transitions examined, and an empty frontier. No state admits a final obstruction-free replacement of the bad point.

Therefore arbitrary-length paths in this neutral 1-swap move graph are exactly ruled out for all 40 one-hit states, via the C5 orbits and inter-basin isomorphism.

Reusable solver: `code/bpz_t9_funsearch_neutral_component.py`.

## Current frontier

The unrestricted ten-dimensional local frontier is now exactly negative through remove-3/add-5 around every FunSearch one-hit deletion seed. This is strictly broader than the five-dimensional BPZ auxiliary repair search, because added vertices are arbitrary vertices of `C7^10`.

The next exact layer is remove-4/add-6. Before constructing it, `code/search_net2_r4_pair_census.cpp` measures the number of genuine two-owner pools with independence number 3; this controls the only disconnected support-graph case that cannot be generated cheaply from connected coverage-two/three/four support unions.

No result here proves global optimality of 134753, and no Few Shots-verified score above 134753 has been found yet.
