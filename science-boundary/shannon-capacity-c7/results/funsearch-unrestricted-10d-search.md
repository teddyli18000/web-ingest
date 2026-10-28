# FunSearch one-hit deletion seed: unrestricted 10D exact search

Status: 2026-10-27 (America/Los_Angeles).

These results concern the four exact C5 orbit representatives `[0,1,2,3]` of the 40 FunSearch t=9 one-hit states. The two 20-state basins are also exactly isomorphic, so automorphism-invariant conclusions below apply to all 40 states.

## Baseline

Deleting the unique obstruction-hit auxiliary point from a t=9 one-hit state leaves a valid 366-point auxiliary set and a verifier-accepted `C7^10` independent set of size

`(367-9)^2 + 2*9*366 = 134752`.

The dedicated materializer is `code/bpz_t9_funsearch_deleted_seed.py`. The earlier attempt to reuse the 134770-only BPZ builder was an implementation error and produced no mathematical result; the dedicated replay fixes this and every exact search workflow independently checks score 134752 with the Few Shots p004 verifier before searching.

## Exact unrestricted radius 0: add 2

Full-space `7^10 = 282,475,249` coverage transforms show `coverage0 = 0` on the representative deletion seeds. Thus each seed is maximal: there is not even one directly addable ten-dimensional vertex.

Reusable solver: `code/search_add2.cpp`.

## Exact unrestricted radius 1: remove 1 / add 3

All four C5 representatives are negative. Representative statistics include:

- case 0: `coverage1=6308`, 36 owners with at least two coverage-one candidates, maximum raw group size 2, 36 candidate pairs checked;
- case 1: `coverage1=6290`, 18 such owners, maximum group size 2, 18 pairs checked;
- case 3: `coverage1=6269`, 18 such owners, maximum group size 2, 18 pairs checked.

No single-owner coverage-one group contains the compatible additions required for a net +2 exchange. The deeper solvers independently replay the lower-radius conditions rather than assuming these artifacts.

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

For case 0: `coverage1=6308`, `coverage2=143680`, `coverage3=999531`, `coverage2_groups=135344`, `coverage3_groups=961338`, `active_c1_owners=6272`, `heavy_c1_owners=0`, `triples_checked=1296968`, `eligible_triples=25505`, and maximum supported pool 10.

For case 1 the analogous values are `coverage1=6290`, `coverage2=143706`, `coverage3=999380`, 135370 coverage-two groups, 961199 coverage-three groups, 1297139 owner triples checked, 25600 eligible triples, and maximum supported pool 10; again `heavy_c1_owners=0`.

Reusable solver: `code/search_net2_r3.cpp`.

## Exact unrestricted radius 4: remove 4 / add 6

All four representatives are exactly negative. The radius-4 solver replays the lower-radius conditions and generates the complete relevant owner-quadruple family using direct coverage-four supports and connected lower-support unions; it reconstructs the complete pool `P(U)` for each owner quadruple before testing six additions.

Case 0 statistics:

- `coverage1=6308`, `coverage2=143680`, `coverage3=999531`, `coverage4=2123481`;
- `coverage2_groups=135344`, `coverage3_groups=961338`, `coverage4_groups=2065189`;
- `quadruples_checked=10295587`;
- `eligible_quadruples=270426`;
- maximum supported pool 15.

The associated exact pair census/precondition establishes `alpha(P(U)) <= 2` for every genuine two-owner pool used by the completeness argument.

Reusable solver: `code/search_net2_r4.cpp`.

## Exact unrestricted radius 5: remove 5 / add 7

This layer is split into two complete stages.

1. **Direct coverage-five supports.** Every owner-five set appearing as the exact blocker support of a coverage-five candidate is replayed with its complete lower-support pool and tested for seven pairwise nonconfusable additions. All four representatives are negative.
2. **Connected lower-support owner-five sets.** Given the exact lower-radius bounds, every disconnected five-owner support pattern supports at most six additions. Therefore any remaining radius-5 witness must have a connected support hypergraph. `code/search_net2_r5_lower.cpp` generates every such owner-five union from coverage-two/three/four supports, internally rechecks `alpha <= 1` on one-owner pools and `alpha <= 2` on genuine two-owner pools, reconstructs the complete candidate pool, and solves it exactly.

All four C5 representatives completed both stages with no candidate; every Few Shots breakthrough-verifier step was therefore skipped.

Representative connected-lower statistics:

- case 0: `generated_calls=227882179`, `unique_owner5_checked=101810016`, `eligible_owner5=3094151`, maximum supported pool 20;
- case 2: `coverage1=6287`, `coverage2=143950`, `coverage3=997826`, `coverage4=2127005`, `coverage2_groups=135339`, `coverage3_groups=960303`, `coverage4_groups=2067709`, `generated_calls=227229107`, `unique_owner5_checked=101826548`, `eligible_owner5=3064937`, maximum supported pool 22.

Thus arbitrary ten-dimensional net-+2 exchanges are exactly ruled out through remove-5/add-7 around all 40 FunSearch one-hit deletion seeds. This is strictly broader than any five-dimensional auxiliary repair family.

## Stronger low-owner census for radius 6

A dedicated exact census first replays the radius-4 precondition and then enumerates every three-owner support pattern capable of containing four independent additions. For case 0 it finds

- `triples_checked=1296968`;
- `eligible_triples_ge4raw=39056`;
- `productive_alpha4_triples=0`;
- `independent_quadruples_total=0`.

So case 0 actually satisfies `alpha(P(U)) <= 3` for every three-owner set `U`, stronger than the generic radius-3 bound of four. The same census is being replayed on representatives 1/2/3 before using this stronger fact globally.

With the one-owner, two-owner, three-owner, and radius-5 bounds, the radius-6 problem admits Hall-type support-incidence constraints; details are in `notes/support-hypergraph-exchange.md`.

## Exact support recovery through coverage 6

`code/census_support6_lists.cpp` uses an in-place exact support-list transform over all `7^10` ambient vertices. It stores up to six blocker-owner labels per vertex and an overflow marker above six. Support size is monotone across coordinate expansion, so every final coverage-`<=6` support is recovered exactly without high-order moment inversion.

For case 0, the transform reproduces the known exact coverage-two/three/four counts and reports:

- total coverage-one cells including the 134752 baseline vertices themselves: `141060` (`141060-134752=6308` outside candidates, matching the older solver);
- `coverage2=143680`;
- `coverage3=999531`;
- `coverage4=2123481`;
- `coverage5=2537726`;
- `coverage6=3173875`;
- distinct exact coverage-six owner sets: `2972218`.

The optimized transform uses about 6.8 GB RSS and completes the ten coordinate expansions in seconds on a hosted runner. The first workflow was marked failed only because its consistency check compared the inclusive coverage-one count to the older outside-only count; that check has been corrected and the transform itself agreed exactly on coverage 2--4.

## Bounded-hit private-swap components

A separate exact nonlocal search keeps 367 auxiliary points but permits legal private one-for-one swaps while allowing the BPZ obstruction hit count to temporarily rise. Zero hits would immediately yield a 134770 construction.

All four C5 representatives have been completely exhausted with hit caps 3, 4, 5, and 6, with no zero-hit state. These are true queue-exhaustion results, not random walks or state caps. For case 0:

- hit cap 3: 75 states;
- hit cap 5: 227 states;
- hit cap 6: 243 states, with hit-count histogram `{1:2,2:17,3:56,4:88,5:64,6:16}`, maximum frontier 97, and empty final frontier.

Reusable solver: `code/bpz_t9_funsearch_hitcount_component.py`.

## Current frontier

No Few Shots-verified score above 134753 has been found. Around the entire 40-state FunSearch one-hit family, the unrestricted ten-dimensional local frontier is now exactly negative through remove-5/add-7. The next exact layer is remove-6/add-8, decomposed into disconnected support cases (being eliminated by low-owner alpha censuses) and genuinely connected six-owner support sets with Hall-type incidence constraints.

In parallel, a genuinely different family is now being tested: the 20 public BPZ/Family-F t=9 one-hit states are being converted to verifier-valid 134752 deletion seeds and searched with the same unrestricted ten-dimensional machinery. This avoids overfitting the search to the FunSearch basin.

No result here proves global optimality of 134753.
