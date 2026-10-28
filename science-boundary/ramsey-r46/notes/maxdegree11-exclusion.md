# Exact exclusion of maximum degree 11

## Claim

A `(4,6)` graph on 36 vertices cannot have maximum degree 11. Hence every hypothetical `(4,6,36)` graph has maximum degree at least 12.

## Proof

Every vertex of a `(4,6,36)` graph has degree at least 11: for a vertex `v`, its non-neighbours induce a `(4,5)` graph, and `R(4,5)=25`.

Assume the maximum degree is 11. Then the graph is 11-regular. Fix a vertex `v` and write

- `A = N(v)`, so `|A|=11`;
- `B = V \ (A union {v})`, so `|B|=24`;
- `e_A`, `e_B` for the numbers of edges induced by `A`, `B`;
- `c` for the number of edges between `A` and `B`.

Summing degrees over `A` gives

`11*11 = 11 + 2 e_A + c`, hence `c = 110 - 2 e_A`.

Summing degrees over `B` gives

`24*11 = 2 e_B + c`.

Eliminating `c` yields

`e_B = e_A + 77`.

Because the whole graph is K4-free, `A=N(v)` is triangle-free. By Mantel's theorem,

`e_A <= floor(11^2/4) = 30`,

so `e_B <= 107`.

But `B` is a `(4,5,24)` graph: it has no K4, and an independent 5-set in `B` together with `v` would be an independent 6-set in the original graph. McKay's complete catalogue contains all 352,366 `(4,5,24)` graphs. The authenticated catalogue statistics in `results/degree11-catalog-stats.json` show that their edge counts range from 116 to 132. Thus `e_B >= 116`, contradiction.

Therefore maximum degree 11 is impossible.

## Evidence

- Complete `(4,5,24)` catalogue size: 352,366.
- Exact edge histogram and authenticated source SHA256: `results/degree11-catalog-stats.json`.
- Source catalogue: `https://users.cecs.anu.edu.au/~bdm/data/r45_24.g6`.

This exclusion is independent of the SAT branch `maxdegree_sat.py`; the D=11 SAT branch, if completed, is only a redundant computational cross-check.
