# Five-dimensional whole-layer block reoptimization frontier

Date: **2026-11-04**. Status: **two-layer exact MILP pilot complete; three-layer decision probes launched; no verified 368 candidate**.

## Why change the representation

The pinned I0 367-word `C7^5` parent has no improving exchange deleting six or fewer words (see `c7p5-r6-and-basin-recombination.md`). Prior full-graph CHILS and 315-core large-neighborhood search also stopped at 367 (Actions `40998546104` and `40999375776`, respectively), and the earlier 315-core exact MaxSAT run `40998894894` was **cancelled**, not UNSAT.

Instead of fixing the incumbent set and increasing exchange radius, partition its 367 words by one coordinate into seven layers. The confusability graph on those layers is a cycle: only equal or neighboring symbols can conflict, and neighboring layers must have jointly independent projections in `C7^4`.

## Exact two-layer reduction

For adjacent cyclic layers `s,s+1`, freeze the other five layers. Let `P_s` be the 4D points not confusable with any fixed point in layer `s-1`; let `P_{s+1}` be the 4D points not confusable with any fixed point in layer `s+2`.

**Lemma:** The largest jointly feasible replacement of the two released layers has size exactly

`alpha(C7^4[P_s union P_{s+1}]).`

Proof: two words in the adjacent layers conflict exactly when their 4D projections are confusable, including equal. Thus a feasible joint selection projects to an independent set in the induced four-dimensional graph. Conversely, every independent set on the union can be assigned each word to a permitted layer, yielding a valid replacement. The other five layers are already respected by the definitions of the permitted pools. This is a lossless block formulation, not a local radius cutoff.

The reusable implementation `code/c7p5_two_layer_repair.py` builds the complete conflict graph on each four-dimensional pool, solves a binary independent-set MILP using SciPy/HiGHS, then independently verifies the full five-dimensional code. It prefers changed solutions among cardinality ties and can therefore walk between equal-size 367-word states.

### Verified pilot

GitHub Actions [run 41854052178](https://github.com/teddyli18000/web-ingest/actions/runs/41854052178), immutable BPZ/Tandon source commit `c753408492dde92a239708986d16c15dbf6c3235`:

| seed | exact 4D induced MIS solves | optimum solves | distinct global states visited | best five-dimensional size |
| --- | ---: | ---: | ---: | ---: |
| I0 | 70 | 70 | 39 | 367 |
| X | 70 | 70 | 41 | 367 |

Every MILP returned optimal status `0`, all selected full five-dimensional sets passed independent pairwise-confusability replay. The 4D pools ranged from **609 to 720** candidate points; individual updates changed up to **12** 5D points. Neither trajectory improved 367, so no p004 shot was materialized.

All 140 *visited* block neighborhoods were exactly optimized. This is not a global certificate that every 367-word state is two-layer optimal, or that no 368 word set exists.

Artifacts:
- [I0 run output](https://github.com/teddyli18000/web-ingest/actions/runs/41854052178/artifacts/13336920911)
- [X run output](https://github.com/teddyli18000/web-ingest/actions/runs/41854052178/artifacts/13337300228)

## Complete three-layer decision

The two-layer pilot's exact 367 plateau motivates releasing **three consecutive layers** simultaneously, not merely scaling the same two-layer walk.

For `s,s+1,s+2`, freeze the other four layers. The first and third have four-dimensional allowed pools after excluding conflicts with fixed layers `s-1` and `s+3`, respectively. The middle layer may use all `7^4` projected words. Create a binary selector for each permitted (layer,4D word) pair; forbid confusability both within every layer and between the two adjacent layer pairs. The outer layers do **not** conflict with each other (distance 2 in the 7-cycle).

This exactly represents every replacement of the three released layers. A CP-SAT query demanding at least `old_triple_size+1` selected words is therefore a lossless feasibility test for a +1 improvement in that specific full three-layer block. `INFEASIBLE` proves exclusion for that block; `UNKNOWN` proves nothing.

Code: `code/c7p5_three_layer_decision.py`.

Active GitHub Actions run [41854602289](https://github.com/teddyli18000/web-ingest/actions/runs/41854602289), probing four windows with initial triple occupancy 155: `I0(axis0,start4)`, `I0(axis4,start5)`, `X(axis1,start2)`, `X(axis4,start4)`. Each solve gets up to 75 seconds with four CP-SAT workers. Results must be read before claiming any exclusion or breakthrough.

## Decision criteria

- Any 368-word candidate must be replayed for all five-dimensional conflicts, squared to 135,424 ten-dimensional words, and checked with the upstream Few Shots p004 verifier.
- If the entire three-layer pilot remains `UNKNOWN`, do not call it an impossibility result; inspect problem size and choose a more selective exact decomposition.
- If all four are `INFEASIBLE`, the exclusion is only for those four frozen outside-layer patterns; other five-dimensional basins remain open.
- The next search should intentionally move outside the specific I0/X coordinate-block family if no candidate quality improves, rather than run many copies of the same plateau.
