# Literature and method notes

## Scope

These notes support the length-100 LABS search in this topic. They are research context, not a claim that any listed method is novel.

## Public baseline and verification

- Few Shots p006 defines the exact objective and ships the public energy-578 sequence: <https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100>.
- QOBLIB independently lists 578 as the best-known value for `labs100`: <https://github.com/ZIB-AOPT/QOBLIB/tree/main/02-labs>.
- The Few Shots verifier is the final judge for any shot. `code/verify.py` is intentionally much simpler and is only an independent cross-check.

## Historical solver evidence

Bošković, Brglez, Brest and collaborators published/open-sourced LABS solvers using self-avoiding walks, tabu search, and memetic search:

- Paper: <https://arxiv.org/abs/1406.5301>
- Solver archive: <https://github.com/borkob/git_labs>

Relevant implementation details inspected from the public archive:

- `lssMAts-lssRRts` uses tabu local search embedded in a population-based memetic algorithm.
- Uniform per-gene parent choice is used for crossover.
- Typical archived parameters include crossover probability 0.9, mutation probability near one expected mutation per chromosome, and binary tournament selection.
- The archive also contains efficient incremental single-bit scoring logic for structured/skew searches.

These observations motivate, but do not determine, the current unrestricted length-100 search.

## Exhaustive optimum boundary

Packebusch and Mertens proved exact LABS optima through length 66 using exhaustive branch-and-bound methods:
<https://arxiv.org/abs/1512.02475>.

Length 100 is therefore outside the range covered by that exact result.

## Current search design

`code/search.cpp` is deliberately small and inspectable:

1. Maintain all 99 aperiodic correlations exactly.
2. Evaluate any one-bit flip in O(N) from the current correlation vector.
3. Use tabu tenure plus aspiration to cross shallow local minima.
4. Mix random starts with 10-50 bit perturbations of the public 578 incumbent.
5. Apply periodic random kicks after prolonged stagnation.
6. Parallelize independent runs with OpenMP.
7. In debug builds, periodically recompute energy from scratch and abort on any incremental mismatch.

This is an unrestricted search over all 100 bits; it does not assume skew symmetry.

## Negative evidence already established

The Hamming ball of radius 5 around the public 578 incumbent was exhaustively enumerated: 79,375,495 distinct edited sequences at distances 1 through 5, with no energy below 578. Therefore direct small-edit polishing of the incumbent through radius 5 is exhausted.

## Planned escalation

If the first tabu campaign does not reproduce competitive sub-700/sub-650 local optima often enough, tune tenure/kick parameters before spending large Action budgets. If it is competitive but stalls above 578, add a small diverse population with uniform crossover followed by tabu polishing, matching the broad memetic pattern in the historical solver literature.

Any candidate at energy <=574 must be frozen immediately, rescored by `code/verify.py`, then scored by the Few Shots verifier before any record claim or submission.
