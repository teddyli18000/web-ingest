# Constructive semantic circuit recombination — 2026-11-06

## Goal and score

Few Shots p008: construct a complete AES S-box circuit in **at most 100** two-input AND/XOR/XNOR gates. Public verified record at this checkpoint: 101 gates, 33 AND plus 68 linear, from merged PR #31. This line deliberately prioritizes **valid new circuits and global recombination**, not further local UNSAT calculations.

## Construction 1: multi-gate cone refactoring

Scripts:
- [neutral_cone_evolution.py](../neutral_cone_evolution.py)
- [care_cone_evolution.py](../care_cone_evolution.py)

Actions:
- [run 42251904892](https://github.com/teddyli18000/web-ingest/actions/runs/42251904892): exact-output 2/3-gate cone recomposition, six RNG/seed jobs, each 300 s.
- [run 42252448125](https://github.com/teddyli18000/web-ingest/actions/runs/42252448125): full-output-care-equivalent 2/3-gate recomposition, eight RNG/seed jobs, each 300 s.

A refactoring replaces a complete single-fanout intermediate cone with a different AND/XOR/XNOR implementation computing the same root on its exact full-circuit observability care set. Every accepted complete circuit is independently checked on all 256 AES inputs. Many tens of thousands of distinct valid states were generated per job, but neither run produced a <=100 candidate. The FS101 search stayed at 101 gates.

**Scientific correction**: The original progress counters counted SHA-256 hashes of the **ordered AND-output truth sequence**, not of the unordered set of nonlinear truth functions. A change in order is not evidence of changing the nonlinear basis. Direct inspection of all 40 archived FS101 101-gate circuits from six care-run shards found exactly **one distinct unordered set** of 33 AND truth functions, although 29 distinct AND sequences and 258 distinct full gate hyperedges appeared. The archived variants are real circuit-topology variants, but not proven distinct nonlinear architectures. A raw sequence counter must not be described as an AND-function-set diversity score.

The G103 103-gate archive of 12 variants contained **two** distinct unordered AND truth-function sets, so the same mechanism is capable of a genuine nonlinear change in that lineage.

## Construction 2: global parent recombination

Scripts:
- [semantic_parent_recombination.py](../semantic_parent_recombination.py)
- [semantic_32and_recombination.py](../semantic_32and_recombination.py)

These independently verify all parent circuits, align each intermediate wire by its exact 256-bit Boolean truth function, merge every alternative gate definition into a shared AND/OR hypergraph, and jointly select an **acyclic** lowest-cost DAG with OR-Tools CP-SAT. The complete selected witness is reconstructed and independently checked on all 256 AES inputs.

Results:
- [run 42254188167](https://github.com/teddyli18000/web-ingest/actions/runs/42254188167): FS101 parent union, up to 41 parents, 185 semantic nodes and 259 distinct gate hyperedges; constructed and verified 101, CP-SAT optimal for this represented union.
- [run 42254949268](https://github.com/teddyli18000/web-ingest/actions/runs/42254949268): NIST G103/G104/G105 family plus archived verified mutants, up to 28 parents, 225 nodes and 321 hyperedges; best constructed 103, CP-SAT optimal for this represented union.

These statements apply only to the finite, parent-supplied gate-function set. They are **not** global gate lower bounds.

## Construction 3: generate functions absent from every parent

[semantic_helper_closure.py](../semantic_helper_closure.py) expands the exact parent gate hypergraph with alternative direct edges between known functions and newly synthesized candidate XOR/XNOR/AND helper functions, ranked by the number of other semantic functions they can serve. CP-SAT then jointly chooses novel helpers, old functions, and entire parent reconnections.

[First run 42255894692](https://github.com/teddyli18000/web-ingest/actions/runs/42255894692) was a model-construction error: the direct semantic closure mistakenly tried to assign an active gate/rank to a free primary input. This is **not** negative search evidence. Fixed by excluding primary input truth functions from synthesized targets in commit 43365e3d69d523eb1a0a9b40a09c79eda6978e63. The fixed [run 42256077408](https://github.com/teddyli18000/web-ingest/actions/runs/42256077408) executes four helper-generation widths with and without newly introduced AND functions; consult its actual summary artifacts rather than inferring outcome from job status.

## Next constructive continuation

1. Inspect verified candidates from the helper-closure run, not merely its green/red status.
2. If no <=100, use successfully constructed **101-gate circuits that contain genuinely novel helper functions** as second-generation parents. Forcing novel-helper usage at cost <=101 is a concrete way to grow the semantic basis rather than retest the same 185 nodes.
3. For the 32-AND lineage, retain its true nonlinear-set-diverse 103 parents and develop coupled nonlinear factor shifts plus global affine reconstruction. Its 103->100 target requires three actual total gate savings.
4. Do not treat repeated 101 neutral variants or more finite-family exclusion certificates as improvement in record score.

Any candidate <=100 must pass the unchanged Few Shots verifier before being published as a shot.
