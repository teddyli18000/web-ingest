# Direct ten-dimensional constructive search with adaptive fibers (2026-11-06)

## Objective and baseline

Few Shots p004 asks for a verified independent set of at least **134,754** points in `C7^⊠10`. Upstream `data/board.json` still lists **134,753** as baseline on 2026-11-06. Nothing in this note constitutes a new record unless explicitly replayed through the upstream `verify.py`.

This line was selected to prioritize **better ten-dimensional candidates**, rather than ever-larger exclusion radii around existing 134,753-point seeds.

## Inputs

- Two independent new five-dimensional **367**-word codes, `neutral14a` and `neutral14b`, with **14 distinct private-neighbor owners** each, frozen in `data/circular-neutral-high-port-p004.json` as SHA256-checked little-endian uint16 arrays. They arose from 367-preserving neutral replacements of a separate circular-code seed.
- Auxiliary 367-word `port12a`, `port12b`, from successful Actions run [42024771296](https://github.com/teddyli18000/web-ingest/actions/runs/42024771296), and the 36 Family-F and original `I0/X` parent codes from pinned public sources.
- Existing t9/t10 scans of these 367-word fixed auxiliary codes over all `7^5` translations failed to find a zero-obstruction certificate. For parent `port12a`, a t9 orientation reached **five** conflicting auxiliary points, not zero; a full signed-permutation search of 41 sources on four specific orientations also failed to close that gap. These motivate changing the actual fibers, not repeating the same obstruction scan.

## Construction: independently optimized 10D fibers

Choose a five-dimensional parent `I` of size 367, a set `R⊂I` of `t` deleted points, and `B=I\R`. Let `X` be any 367-word independent auxiliary code. An endpoint `e` is permitted if all its confusable parent vertices are within the chosen deletions `R`.

For each auxiliary vertex `x∈X`, **independently** select two five-dimensional independent endpoint fibers `H_x` and `V_x`. The resulting ten-dimensional candidate is

`(B×B) ∪ ⋃_{x∈X} (H_x×{x}) ∪ ⋃_{x∈X} ({x}×V_x).`

Because `X` is independent, all row-row and column-column cross-`x` pairs are automatically nonconfusable. The only coupled constraints are **row-column**, requiring no simultaneously selected pair `e∈H_x`, `f∈V_y` with `e~y` and `x~f`. Each fiber also must be independent and nonconfusable with the retained parent core.

The CP-SAT model encodes **all** these restrictions, jointly decides deleted owners and selected per-`x` endpoints, and maximizes the **actual ten-dimensional score**, not an intermediate obstruction measure. A separate nested-pair checker replays the chosen geometry and materializes the 10D point list for every feasible incumbent. The upstream Few Shots verifier is called automatically for any score above the baseline.

If `a` auxiliary vertices have at least one possible endpoint conflict, the other `367-a` vertices can each use the full deleted owners `R` in both orientations. With these inert fibers fixed, the score is exactly

`(367-t)^2 + 2t(367-a) + ∑_{x active} (|H_x| + |V_x|).`

Code: `code/c7p004_joint_fibers_construct.py`.

## First constructive runs: actual replayed scores

| Candidate model | Exact or time-limited | Best score | Actions |
| --- | --- | ---: | --- |
| Six symmetric `t=9,10,11` parent/auxiliary choices | Six valid CP-SAT incumbents; all solver statuses **FEASIBLE** at 220 s | **134,656** | [42264771625](https://github.com/teddyli18000/web-ingest/actions/runs/42264771625) |
| Six symmetric `t=12,13,14` choices | Five **FEASIBLE** at 220 s; one **OPTIMAL** (t14, parent neutral14a, aux port12a, score 134487) | **134,554** | [42265317094](https://github.com/teddyli18000/web-ingest/actions/runs/42265317094) |
| Six asymmetric deleted subsets `R_L != R_R` with distinct deletion *sets* but same left/right parent code | Six **FEASIBLE** at 220 s | **134,656** | [42265806595](https://github.com/teddyli18000/web-ingest/actions/runs/42265806595) |

All these scores are from explicitly generated certificates and internal independent-set replay. None beats 134,753, so the upstream record verifier was deliberately not invoked. These are incumbent quality observations; statuses **FEASIBLE** do not claim any restricted-family impossibility. The single `OPTIMAL` instance is a narrow model-specific optimum.

The asymmetric version, `code/c7p004_joint_asymmetric_fibers_construct.py`, independently chooses deleted *left* and *right* owner sets of sizes `l` and `r`, still using the same parent I on both sides:

`(B_L×B_R) ∪ ⋃_x (H_x×{x}) ∪ ⋃_x ({x}×V_x).`

This removes the artificial equality `R_L=R_R`, but the tested incumbents did not yet improve beyond 134,656.

## Distinct constructive spaces launched

1. **Full auxiliary isometry optimization**, `code/c7p004_port_aux_full_isometry.py`, exhaustively applies all **120** permutations and **32** coordinate sign choices plus cyclic translations of each of 42 independent five-dimensional 367-word source codes. It chooses auxiliary X with few active endpoint conflicts, then the actual 10D asymmetric solver reevaluates the best X per source shard. [Run 42266672617](https://github.com/teddyli18000/web-ingest/actions/runs/42266672617) (nine shards, state to inspect).
2. **Different left and right parent codes**, `code/c7p004_two_parent_full_fibers.py`, lets the core be `B_L×B_R` with `I_L` and `I_R` independently selected from `neutral14a` and `neutral14b`. Its endpoint domains and deleted owner sets are separate. In contrast to all previous adaptive-fiber versions, it also **removes the per-fiber upper cap** `|H_x|≤l,|V_x|≤r`; this is a genuine new candidate space because a larger independent fiber would itself give a five-dimensional improvement. [Run 42267021902](https://github.com/teddyli18000/web-ingest/actions/runs/42267021902) (six instances, state to inspect).

Neither active run's scientific result should be inferred from runner status alone. If a 10D candidate scores >134753, first confirm the exact `verify.py` JSON result, then follow the Few Shots shot instructions and submit only with appropriate publication authorization.

## Remaining structural bottleneck

A 14-owner parent contains only about 33 low-support endpoint candidates, while each fixed 367-word auxiliary source still makes several dozen of its words interact with the endpoint envelope. Allowing individual fibers and asymmetric deleted owner sets has so far cost too many endpoints to beat the record. This is evidence that **auxiliary identity and endpoint geometry should be optimized jointly**, not evidence that all such constructions are impossible.

Further constructive directions if the two active campaigns do not improve the best score:

- Generate auxiliary words while selecting fiber endpoints, rather than picking X through a single parent isometry and fixing it before optimization.
- Exchange whole 4D slices of X jointly with the forbidden endpoint envelope, while preserving all five-dimensional independence and evaluating the resulting **actual 10D certificate**.
- Combine a near-record 134753 tenth-power seed with a distinct 10D port construction at the *10D* level, allowing coordinated gain via an exact large-neighborhood reoptimization.

Do **not** repeatedly extend exact exclusion radii or re-run the original 41-code fixed-translation t9/t10 screen.
