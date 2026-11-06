# Independent circular 367 basin — completed 2026-11-05 experiments

Status: **construction of a distinct 367-point `C7^5` parent basin**, with rigorous restricted-family diagnostics and no new p004 score. The follow-up port-gadget study is in [circular-port12-t9-t10-campaign-2026-11-06.md](circular-port12-t9-t10-campaign-2026-11-06.md).

## Source and verification

The novel circular-quantization descendant is frozen as `data/circular-phase-367-2026-11-04.json`: 367 distinct five-dimensional words, verified for all **67,161** pairwise nonconfusability checks, with a coordinate-marginal multiset distinct from the 38 pinned BPZ I0/X and Family-F source codes. The distinct signature excludes equivalence under coordinate permutations and independent coordinate rotations/reflections; it does not exclude all other graph equivalences.

## Completed independent experiments

| Experiment | Scope and authoritative run | Result |
| --- | --- | --- |
| Full two-basin Hall recombination | [Run 42021368242](https://github.com/teddyli18000/web-ingest/actions/runs/42021368242); circle paired with circle, I0, X, F0, each at every 16,807 relative translation; implementation `code/c7p5_circular_hall_translation.cpp` | **67,228** exact maximum bipartite matchings, each Hall-saturated; no 368-word code in these unions |
| Three-basin recombination | [Run 42022133205](https://github.com/teddyli18000/web-ingest/actions/runs/42022133205); `code/c7p5_circular_triple_union_milp.py` | Four triples × 20 relative phase trials. **78** MILPs exact optimum **367**, **2** time-limited at a feasible 367 (not a proof), none found >=368. A previous runner failed due a Python list/set bug; the successful run is the corrected replay |
| Connected bounded-radius repair | [Run 42023370916](https://github.com/teddyli18000/web-ingest/actions/runs/42023370916); `code/c7p5_circular_connected_exchange.cpp` | Every connected support-owner exchange with at most **5** removed points checked; radius-3 **2,093** states, radius-4 **13,511**, radius-5 **93,174**, no score gain |
| Unconstrained exact adjacent-slice reoptimization | [Run 42023847944](https://github.com/teddyli18000/web-ingest/actions/runs/42023847944); `code/c7p5_circular_two_layer_walk.py` | Four seed trajectories × **140** optimal 4D induced independent-set MILPs; all best **367**, but each trajectory visited 93–100 different 367-word states, with up to **50** symmetrically different points relative to the starting source |
| Private-owner-aware neutral search | [Run 42024771296](https://github.com/teddyli18000/web-ingest/actions/runs/42024771296); `code/c7p5_port_aware_block_walk.py` | Four trajectories × **175** optimal full-slice MILPs; increased distinct private-neighbor owners from **6** to **11–12**, preserving independence and all 367 words. Two 12-owner descendants are now separately frozen and independently replayed |

Hall matching identity: for the union of two independent 367-word sets A and translated B, removing common points produces a bipartite conflict graph. The union's exact maximum independent size is `367 + (#B-only - matching_size)`. The exhaustive matcher confirms zero deficiency for the four frozen partner choices across all shifts. This does not bound a three-code union or different parent families.

These experiments establish **a qualitatively different circular-code basin and its private-owner flexibility**; they do not prove `α(C7^5)=367`.

The 12-owner descendants were frozen on 2026-11-06 as `data/circular-port12-port12a-2026-11-05.json` and `data/circular-port12-port12b-2026-11-05.json`. The subsequent t=9/t=10 exhaustive auxiliary search and 366-word constructive threshold are documented in the linked 2026-11-06 result note.
