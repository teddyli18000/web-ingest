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

The two 20-state basins are not independent search targets.  The explicit `C7^5` graph automorphism

`T(x) = -x + (4,0,4,0,4) mod 7`

maps the complete image-330 one-hit state collection bijectively onto the complete image-341 collection.  An exact replay checked all 20 states: both the translated 367-set and its obstruction set are mapped to a unique state in the other basin, and the unique obstruction hit maps to the partner state's unique hit.  The verification completed with `matched=20`, `unmatched=[]`, `bijection=true`.

Therefore all automorphism-invariant repair/existence questions need only be solved on one of the two basins.  From radius 9 onward, search only one representative basin unless a deliberately symmetry-breaking constraint is introduced.

Reusable verifier: `code/bpz_t9_funsearch_basin_isomorphism.py`.

## Exact 6-for-6 repair boundary

For every one-hit state, pre-delete its unique obstruction hit. The retained 366-set is then searched for six pairwise-compatible additions whose blocker union against the retained set has size at most five; padding the removal set yields an exact 6-for-6 repair. The solver is the pinned `molind/c7-five/search/exchange_dfs.cpp` at commit `ae81e0d24b356aef3d388238f6fb4d02c4aa32a5` with budget-bitset pruning.

Both one-hit basins are completely exhausted with cutoff 300 and zero cutoff states:

- shard 5 / image 341: 20 searched, 20 exhausted, no witness;
- shard 10 / image 330: 20 searched, 20 exhausted, no witness.

Candidate pools at radius 6 have about 7801-7802 vertices. Individual exact searches complete after roughly 332k-356k DFS nodes, with most branches killed by blocker-budget pruning. No Few Shots verification step was triggered because no repair witness was produced.

Thus all 40 FunSearch signed-orbit one-hit states are exactly negative through 6-for-6 repair.

## Active deeper searches

The same exact driver is being pushed to 7-for-7 and 8-for-8. These runs must only be promoted to negative evidence when their completion guards pass with zero cutoff states. A timeout, cancellation, or failed job is not a mathematical negative result.

A separate incremental neutral-reconfiguration walk keeps the unique bad point fixed while traversing long sequences of legal one-for-one swaps among the other 366 points.  This can escape fixed-radius Hamming balls before attempting the final bad-point replacement and is therefore a genuinely different search family.

Reusable code:

- `code/bpz_t9_funsearch_fft.py`
- `code/bpz_t9_funsearch_signed_orbit.py`
- `code/bpz_t9_funsearch_exchange_repair.py`
- `code/bpz_t9_funsearch_basin_isomorphism.py`
- `code/bpz_t9_funsearch_neutral_walk.py`
- `code/c7_fiber_neutral_walk.cpp`
- `code/bpz_t9_exchange_repair.py`
