# FunSearch t=9 one-hit frontier

Status as of 2026-10-27 (America/Los_Angeles). These are exact computational statements about the stated construction/search family, not a proof that `alpha(C7^10)=134753`.

## Seed and signed orbit

The DeepMind FunSearch public `C7^5` independent set of size 367 is reconstructed from pinned source commit `b02fdbfeb1e138ff3fd74592439e645a3a11de69`.

Its raw signed-coordinate action has 3840 transforms and 768 distinct 367-point images. Against all 160 valid BPZ t=9 obstruction masks, exact FFT correlation covers `768 * 160 = 122880` image/obstruction cases.

There is no zero-hit translated state. The minimum-hit histogram contains exactly 40 one-hit cases and 60 two-hit cases.

## Exact decomposition of the 40 one-hit cases

The 40 one-hit cases are concentrated in exactly two image basins:

- image 330, `perm=[0,2,4,1,3]`, `negmask=10`, translation `[6,3,6,3,6]`: 20 one-hit states;
- image 341, `perm=[0,2,4,1,3]`, `negmask=21`, translation `[5,4,5,4,5]`: 20 one-hit states.

Under 16-way image-index sharding these are precisely shard 10 and shard 5.

### Exact basin isomorphism

The two 20-state basins are not independent search targets. The explicit `C7^5` graph automorphism

`T(x) = -x + (4,0,4,0,4) mod 7`

maps the complete image-330 one-hit state collection bijectively onto the complete image-341 collection. An exact replay checked all 20 states: both the translated 367-set and its obstruction set are mapped to a unique state in the other basin, and the unique obstruction hit maps to the partner state's unique hit. The verification completed with `matched=20`, `unmatched=[]`, `bijection=true`.

Therefore all automorphism-invariant repair/existence questions need only be solved on one of the two basins. From radius 9 onward, search only one representative basin unless a deliberately symmetry-breaking constraint is introduced.

Reusable verifier: `code/bpz_t9_funsearch_basin_isomorphism.py`.

### Exact C5 case-orbit compression inside one basin

The representative image-330 367-set has a cyclic coordinate stabilizer of order 5. Exact replay of that stabilizer on all 20 one-hit obstruction states partitions them into four orbits, each of size 5:

- `[0,5,8,13,17]`;
- `[1,4,9,12,16]`;
- `[2,7,10,15,19]`;
- `[3,6,11,14,18]`.

Thus the exact representatives are cases `[0,1,2,3]`. Any automorphism-invariant radius search, unrestricted local modification search, or neutral-component calculation need only be run on these four cases. Together with the inter-basin isomorphism, this compresses the original 40 one-hit states to four exact representatives.

Reusable verifier: `code/bpz_t9_funsearch_case_orbits.py`.

## Exact fixed-radius repair boundary

For every one-hit state, pre-delete its unique obstruction hit. A `k`-for-`k` repair searches for `k` pairwise-compatible additions whose blocker union against the retained 366-set has size at most `k-1`; padding the removal set restores 367 auxiliary points. The solver is the pinned `molind/c7-five/search/exchange_dfs.cpp` at commit `ae81e0d24b356aef3d388238f6fb4d02c4aa32a5` with budget-bitset pruning.

### 6-for-6

Both one-hit basins are completely exhausted with cutoff 300 and zero cutoff states:

- shard 5 / image 341: 20 searched, 20 exhausted, no witness;
- shard 10 / image 330: 20 searched, 20 exhausted, no witness.

Candidate pools are about 7801-7802 vertices. Individual searches complete after roughly 332k-356k DFS nodes. Thus all 40 signed-orbit one-hit states are exactly negative through 6-for-6.

### 7-for-7

The full 16-shard radius-7 campaign completed under an explicit `complete` guard. Every shard finished without a repair witness; the Few Shots verification step was skipped in every job. In particular both one-hit-bearing shards 5 and 10 were completely exhausted with zero cutoff states. Therefore all 40 one-hit states are exactly negative through 7-for-7.

### 8-for-8

The two one-hit-bearing basin jobs both completed under the same explicit completion guard with no witness and no Few Shots verification step. Therefore all 40 one-hit states are exactly negative through 8-for-8. This is an exact statement for the fixed-radius blocker-budget repair family.

### Radius 9 and beyond

A first whole-case 9-for-9 attempt on representative case 3 timed out after about 300 seconds and roughly 151 million DFS nodes, reaching only `next_root=27` of 15086 candidate roots. This is not a negative result. `code/bpz_t9_funsearch_representative_continue.py` provides lossless first-root interval continuation for exact radius-9+ sharding.

The C5 orbit result means only cases `[0,1,2,3]` need exact radius-9+ treatment; all other one-hit cases are automorphic copies.

## Exact neutral-reconfiguration components

`code/bpz_t9_funsearch_neutral_component.py` explores the entire one-for-one neutral-swap component while keeping the unique obstruction hit fixed. Every reached state remains a 367-point independent set with exactly that one hit; each state is tested for a final private replacement of the bad point outside the obstruction. Frontier exhaustion therefore rules out neutral paths of arbitrary length, not merely a fixed Hamming radius.

Representative case 10 is completely exhausted:

- states seen / expanded: 2 / 2;
- maximum depth: 1;
- transitions examined: 2;
- neutral degree histogram: both states have degree 1;
- frontier remaining: 0;
- no zero-hit exit.

By the C5 case-orbit compression, future exact neutral-component runs should target cases `[0,1,2,3]`; case 10 is automorphic to case 2. Other queued or incomplete runs are not evidence.

## Seeded global CHILS search

A genuinely nonlocal seeded MIS search was run with CHILS commit `515952724cd3dcc6c4365a340ecf0f1da782119a`. For each sampled obstruction case, the graph was the full obstruction-free `C7^5` induced graph and the known 366-point core was supplied as the initial solution. Four 300-second jobs completed without finding 367; for example case 0 remained at best WIS 366 for the full run. This is useful heuristic evidence only, not a proof.

## Unrestricted 10D escape route from the 134752 deletion seed

Deleting the unique bad auxiliary point from any one-hit t=9 state gives a verifier-checkable structured `C7^10` independent set of size

`(367-9)^2 + 2*9*366 = 134752`.

This opens a search family that is strictly broader than five-dimensional auxiliary repair: augment or locally modify the 134752 seed by arbitrary ten-dimensional vertices.

Reusable exact solvers now include:

- `code/search_add2.cpp`: full-space search for two mutually compatible coverage-zero vertices, which would give 134754 directly;
- `code/search_net2_r1.cpp`: exact unrestricted remove-1/add-3 net-+2 search using coverage-zero and unique coverage-one owners;
- `code/search_net2_r2.cpp`: exact unrestricted remove-2/add-4 net-+2 search using coverage-zero, coverage-one and coverage-two owner pairs.

`code/bpz_t9_bad_fiber_salvage.py` also checks the small natural candidate set `PH×bad`, `PV×bad`, `bad×PH`, `bad×PV` before the full-space transforms. Any candidate from these routes is materialized as an arbitrary 10D certificate and must pass the Few Shots p004 verifier.

The first unrestricted Action attempts exposed a materializer bug: the shared BPZ builder asserted the 134770 target and therefore rejected a correct 134752 deletion seed before any full-space search ran. This was an implementation failure, not negative mathematical evidence. `code/bpz_t9_funsearch_deleted_seed.py` now has a dedicated deletion-seed replay that accepts and independently verifies the intended 134752 score. Subsequent unrestricted runs must use the exact four C5 representatives `[0,1,2,3]`.

## Reusable code

- `code/bpz_t9_funsearch_fft.py`
- `code/bpz_t9_funsearch_signed_orbit.py`
- `code/bpz_t9_funsearch_exchange_repair.py`
- `code/bpz_t9_funsearch_basin_isomorphism.py`
- `code/bpz_t9_funsearch_case_orbits.py`
- `code/bpz_t9_funsearch_representative_case.py`
- `code/bpz_t9_funsearch_representative_continue.py`
- `code/bpz_t9_funsearch_neutral_component.py`
- `code/bpz_t9_funsearch_neutral_walk.py`
- `code/c7_fiber_neutral_walk.cpp`
- `code/bpz_t9_funsearch_deleted_seed.py`
- `code/bpz_t9_bad_fiber_salvage.py`
- `code/search_add2.cpp`
- `code/search_net2_r1.cpp`
- `code/search_net2_r2.cpp`
- `code/bpz_t9_exchange_repair.py`
