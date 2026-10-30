# Exact 315-core prize reformulation for `alpha(C7^5)`

Status: **active computation; no 368-word witness and no global impossibility proof claimed here.** This note records a new exact formulation and its lossless symmetry decompositions while the corresponding Actions are running.

Public reference state: `molind/c7-five` at pinned commit `ae81e0d24b356aef3d388238f6fb4d02c4aa32a5` reports `367 <= alpha(C7^5) <= 401`, no public 368 construction, and no global proof that 368 is impossible. Its portable core-overlap result supplies a certified independent core `C` of size 315 such that every target 368-set omits at least four points of that core.

## Exact prize identity

Let `G=C7^5`, let `C` be any independent set, and let `Y` be an independent subset of `V(G) \ C`. Once `Y` is fixed, every core point not adjacent/confusable with `Y` can be added simultaneously because `C` itself is independent. Therefore the best completion of `Y` relative to `C` is exactly

`Y union (C \ N_C(Y))`

and has size

`|C| + |Y| - |N_C(Y)|`.

Taking the maximum over every independent outside set gives the identity

`alpha(C7^5) = 315 + max_Y ( |Y| - |N_C(Y)| ).`

Thus 368 exists **iff** some outside independent set has prize at least 53.

This is not a local approximation or a conditional bound. It is exactly the original maximum-independent-set problem projected through a certified large independent core. The value of the reformulation is algorithmic: core points need not be swapped individually; an outside move implicitly removes all touched core points and restores all newly unblocked core points.

Reusable implementations:

- `code/c7p5_core_prize_maxsat.py` — exact weighted MaxSAT optimization;
- `code/c7p5_core_prize_decision.py` — independent MiniCard feasibility encoding for score at least 368;
- `code/c7p5_core_prize_ls_export.py` and `code/c7p5_core_prize_ls.cpp` — projected large-neighborhood heuristic search over `Y` only.

The decision encoding also uses the independently certified target-specific cut

`|N_C(Y)| >= 4`

for any completed 368-set, directly translating the molind 315-core overlap theorem.

## Lossless zero symmetry break

`C7^5` is vertex-transitive. Any nonempty independent set can be translated so that vertex `00000` is selected. The prize representation remains exact after this graph automorphism even though the chosen 315-core is kept fixed: the transformed independent set is simply represented by a different outside set `Y` relative to that same fixed core.

All exact global decision formulations may therefore require completed vertex 0 without losing a target solution.

## Fifty second-vertex orbits

The stabilizer of zero includes all five coordinate permutations and an independent sign reversal in every coordinate. Consequently a nonzero vertex is classified, relative to zero, by the sorted multiset of its five cyclic distances, each distance in `{0,1,2,3}`.

There are

`C(5+4-1,4-1) = 56`

such multisets. Exactly six use only distances `{0,1}` and are confusable with zero. The remaining **50** are the nonconfusable second-vertex orbits.

For any target independent set containing zero, choose any second selected vertex. A zero-fixing automorphism maps it to the canonical representative of its orbit. Therefore the global 368 decision problem is losslessly covered by 50 branches of the form

`zero selected AND representative_i selected`.

`code/c7p5_core_orbit_decision.py` implements this exact 50-branch decomposition in MiniCard while reusing one solver instance per shard via assumptions.

## Pigeonhole strengthening

After zero is selected, the remaining 367 selected vertices are partitioned among those 50 nonconfusable orbit types. Hence at least one orbit contains

`ceil(367 / 50) = 8`

selected vertices.

Choose such a most-populated orbit and then map one of its selected vertices to the canonical representative. Thus every hypothetical 368-set has an automorphic image satisfying one of the stronger 50 branches

`zero selected AND representative_i selected AND orbit_i occupancy >= 8`.

`code/c7p5_core_orbit_pigeonhole_decision.py` implements this cover. Each orbit occupancy constraint is a native MiniCard `>=8` constraint gated by eight proxy literals equal to `NOT(selector)`, so inactive orbit constraints are automatically satisfied without a large CNF cardinality expansion. At-most-one selector clauses ensure that one branch assumption disables the other 49 constraints while preserving learned-clause reuse.

This is currently the strongest exact decomposition prepared for a future decision run. It has not yet been reported as SAT or UNSAT.

## Active / queued computation

As of 2026-10-30 UTC:

- Exact core-prize MaxSAT workflow: run `40998894894`. Two lossless parity-cover RC2 branches execute concurrently on one runner. A candidate >=368 would be squared to 135,424 and checked by the Few Shots p004 verifier. The run is active; no result is claimed yet.
- Full public-367 seeded CHILS workflow: run `40998546104`. The exact public 367 corpus is validated, the full 16,807-vertex graph is exported, and CHILS is running all available runner cores across the distinct public basins. This is heuristic evidence unless it finds an explicit 368 witness.
- Projected core-prize large-neighborhood workflow: run `40999375776`, queued when this note was written. It searches the same exact prize objective with moves that implicitly coordinate arbitrary core deletions/restorations.
- Exact 50-orbit ordinary decision workflow: run created from `.github/workflows/temp-science-boundary-c7p5-core-orbit-decision.yml`, queued when this note was written. Its result must be read from the corresponding run before any claim.

## Interpretation rules

1. A CHILS/projected-LS miss is heuristic only.
2. A cancelled/timeout RC2 or MiniCard run is not UNSAT.
3. If exact MaxSAT returns optimum 367, obtain an independent decision-UNSAT replay before claiming `alpha(C7^5)=367`.
4. A 368 witness must be explicitly replayed in five dimensions and its 368-square certificate must pass the upstream Few Shots p004 verifier before being called a p004 breakthrough.
5. The public literature/source state must be re-checked immediately before any novelty or exact-optimum claim.
