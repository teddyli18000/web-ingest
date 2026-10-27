# AlphaEvolve Algorithm 22 calibration

Date: 2026-10-27

## Source finding

Nagda, Raghavan, and Thakurta, *Reinforced Generation of Combinatorial Structures: Ramsey Numbers*, arXiv:2603.09172v5, explicitly summarize their recovered search algorithm for `R(4,6)` as Algorithm 22. The relevant ingredients are:

- initialize from the best cyclic graph found in a short search;
- minimize the unweighted objective `E(G) = #K4 + #I6`;
- use tabu edge flips, with tenure approximately `N`;
- compute exact edge-flip deltas through the common neighborhood and common non-neighborhood;
- after stagnation on a scale based on `N^2`, use a medium perturbation that flips about 25% of all edges when the current cost is low, or restart from a fresh cyclic seed at high cost;
- for sequential growth, add the new vertex at density about 0.4 before refinement.

Primary source: https://arxiv.org/abs/2603.09172 (v5, 2026-04-21). The public full-text rendering labels this as Algorithm 22.

This independently validates the objective and delta formulas used in `walksat36.cpp`, and suggests that the first local parameters were too conservative in tabu tenure and perturbation size.

## Delta verification

Before using the C++ incremental formulas, a local `--self-test` generated random 36-vertex graphs, chose random edge flips, and compared the predicted `(delta #K4, delta #I6)` with complete recounts after each flip. All tested flips agreed exactly.

For an edge `uv`:

- if adding `uv`, new K4s are exactly the edges induced by `N(u) intersect N(v)`;
- if removing `uv`, the same count is the number of K4s destroyed;
- if removing `uv`, new independent 6-sets are exactly the independent 4-sets in the common non-neighborhood of `u,v`;
- if adding `uv`, the same count is the number of independent 6-sets destroyed.

## Local calibration on Few Shots baseline

The frozen 35-vertex Few Shots baseline was extended by a new vertex, with the new neighborhood first optimized under the safe degree range 11..17.

- initial tabu parameters (short tenure 7..25, tiny three-edge perturbation) repeatedly reached objective 18 and did not improve it in the short calibration run;
- changing the full-graph search to an Algorithm-22-like tenure of 24..48 and a stagnation kick of 25% of the 630 edges produced a best objective **14 = 10 K4 + 4 independent-6 sets** in a 200,000-step / 4-restart local calibration (`seed=4`);
- runtime for that calibration was about 7.25 seconds on the local container CPU.

This is only a near-miss, not a certificate. It is evidence that the larger perturbation materially improves exploration and should be used in the next production sweep. The all-37-core Action launched just before this calibration uses the earlier conservative parameters; preserve its result as a baseline, then run the calibrated variant rather than conflating the two campaigns.

## Next experiment

After the first all-core WalkSAT sweep lands:

1. identify the best cores from both the sweep and exact extension-MaxSAT ranking;
2. run the calibrated Algorithm-22-style variant on those cores with tabu tenure near `N` and 25% perturbations;
3. retain the exact objective recount and best adjacency for each campaign;
4. immediately run the Few Shots p003 verifier on any zero-defect candidate.
