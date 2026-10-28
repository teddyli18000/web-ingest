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

## Exact fixed-radius repair boundary

For every one-hit state, pre-delete its unique obstruction hit. A `k`-for-`k` repair searches for `k` pairwise-compatible additions whose blocker union against the retained 366-set has size at most `k-1`; padding the removal set restores 367 auxiliary points. The solver is the pinned `molind/c7-five/search/exchange_dfs.cpp` at commit `ae81e0d24b356aef3d388238f6fb4d02c4aa32a5` with budget-bitset pruning.

### 6-for-6

Both one-hit basins are completely exhausted with cutoff 300 and zero cutoff states:

- shard 5 / image 341: 20 searched, 20 exhausted, no witness;
- shard 10 / image 330: 20 searched, 20 exhausted, no witness.

Candidate pools are about 7801-7802 vertices. Individual searches complete after roughly 332k-356k DFS nodes. Thus all 40 signed-orbit one-hit states are exactly negative through 6-for-6.

### 7-for-7

The full 16-shard radius-7 campaign completed under an explicit `complete` guard. Every shard finished without a repair witness; the Few Shots verification step was skipped in every job. In particular both one-hit-bearing shards 5 and 10 were completely exhausted with zero cutoff states. Therefore all 40 one-hit states are exactly negative through 7-for-7.

### Radius 8 and beyond

Exact 8-for-8 searches on the two one-hit-bearing shards are currently long-running. No mathematical conclusion should be recorded unless a job either produces a verifier-replayed witness or passes its completion guard with zero cutoff states.

A first whole-case 9-for-9 attempt on representative case 3 timed out after about 300 seconds and roughly 151 million DFS nodes, reaching only `next_root=27` of 15086 candidate roots. This is not a negative result. `code/bpz_t9_funsearch_representative_continue.py` provides lossless first-root interval continuation for exact radius-9+ sharding.

## Exact neutral-reconfiguration components

`code/bpz_t9_funsearch_neutral_component.py` explores the entire one-for-one neutral-swap component while keeping the unique obstruction hit fixed. Every reached state remains a 367-point independent set with exactly that one hit; each state is tested for a final private replacement of the bad point outside the obstruction. Frontier exhaustion therefore rules out neutral paths of arbitrary length, not merely a fixed Hamming radius.

Representative case 10 is completely exhausted:

- states seen / expanded: 2 / 2;
- maximum depth: 1;
- transitions examined: 2;
- neutral degree histogram: both states have degree 1;
- frontier remaining: 0;
- no zero-hit exit.

Thus case 10 has an exact two-state neutral component and no arbitrary-length neutral one-swap escape. Other obstruction cases are being evaluated separately; their queued or incomplete runs are not evidence.

## Unrestricted 10D escape route from the 134752 deletion seed

Deleting the unique bad auxiliary point from any one-hit t=9 state gives a verifier-checkable structured `C7^10` independent set of size

`(367-9)^2 + 2*9*366 = 134752`.

This opens a search family that is strictly broader than five-dimensional auxiliary repair: augment or locally modify the 134752 seed by arbitrary ten-dimensional vertices.

Reusable exact solvers now include:

- `code/search_add2.cpp`: full-space search for two mutually compatible coverage-zero vertices, which would give 134754 directly;
- `code/search_net2_r1.cpp`: exact unrestricted remove-1/add-3 net-+2 search using coverage-zero and unique coverage-one owners;
- `code/search_net2_r2.cpp`: exact unrestricted remove-2/add-4 net-+2 search using coverage-zero, coverage-one and coverage-two owner pairs.

`code/bpz_t9_bad_fiber_salvage.py` also checks the small natural candidate set `PH×bad`, `PV×bad`, `bad×PH`, `bad×PV` before the full-space transforms. Any candidate from these routes is materialized as an arbitrary 10D certificate and must pass the Few Shots p004 verifier.

## Reusable code

- `code/bpz_t9_funsearch_fft.py`
- `code/bpz_t9_funsearch_signed_orbit.py`
- `code/bpz_t9_funsearch_exchange_repair.py`
- `code/bpz_t9_funsearch_basin_isomorphism.py`
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
