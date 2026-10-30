# Neutral five-owner support products: analytic closure

Status: **closed** for the 2,003 connected neutral nonperfect five-owner support graphs identified in the pinned BPZ/Tan geometry.

The exact clique-cover census at pinned source commit `c753408492dde92a239708986d16c15dbf6c3235` found:

- 121,192 connected five-owner support sets;
- exactly one support graph with independence number at least 6 (the known raw 5->6 defect);
- 2,003 further connected support graphs with `alpha = 5` and an induced `C5`;
- for every one of those 2,003 neutral graphs, the minimum clique-cover number is also exactly `theta = 5`.

The last fact closes every pairwise strong product without needing a pair-by-pair SAT calculation.

Let `G` and `H` be any two of the 2,003 neutral support conflict graphs. Cover `V(G)` by five cliques `K_1,...,K_5`; assign each vertex of `G` to one covering clique to obtain a partition into at most five cliques. For an independent set `S` in the strong product `G ⊠ H`, consider the vertices whose first coordinate lies in one fixed clique `K_i`. Since every two first coordinates in `K_i` are adjacent or equal in the conflict graph, their second coordinates must form an independent set in `H`. Therefore each part contributes at most

`alpha(H) = 5`.

Summing over the five clique parts gives

`alpha(G ⊠ H) <= 5 * 5 = 25`.

The Cartesian product of maximum independent sets gives the matching lower bound 25, hence

`alpha(G ⊠ H) = 25`

for every pair of these neutral five-owner support graphs.

Consequently no neutral-5 x neutral-5 support rectangle can reach 26 unlocked vertices after deleting 25 core cells, so this family cannot produce a net +1 core-release improvement.

A previously launched exact SAT product-26 screen (`bpz_neutral5_product26_types.py`, Action run `40990007793`) is retained only as an independent computational cross-check; the mathematical closure above no longer depends on its completion.
