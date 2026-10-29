# Endpoint-support path structure

The reflection inversion for an odd-perfect endpoint deletion has a simple graph interpretation that is useful for exact-search complexity.

Let the 49 possible odd defect lags be `h=1,3,...,97`. Map each lag to one edge of the path with vertices `0,1,...,49`:

```text
e(h) = h-1    for h <= 49,
e(h) = 98-h   for h > 49.
```

Thus `e(h)` runs bijectively through the 49 path edges `(0,1),(1,2),...,(48,49)`.

For one supported lag, the reflection inversion toggles exactly the endpoints of this edge, except that vertex 49 is the fixed center reflection coordinate and is not stored as a free bad coordinate. For an arbitrary support set, XOR linearity therefore says:

> the bad reflection coordinates are exactly the odd-degree vertices of the selected path-edge subgraph, with fixed vertex 49 omitted.

If the selected support edges form `c` connected runs, then the number `r` of bad reflection coordinates is

```text
r = 2c      if edge (48,49) is not selected,
r = 2c - 1  if edge (48,49) is selected.
```

The support-linearized solver enumerates `2^(r-1)` bad-coordinate ratios and two endpoint ratios, so it has exactly `2^r` small anchor cases before branching on good coordinates.

For defect 2:

- adjacent support edges form one run: `r=2`, or `r=1` if the run touches fixed vertex 49; anchor cases `4` or `2`;
- separated support edges form two runs: `r=4`, or `r=3` if one is the final edge; anchor cases `16` or `8`.

For larger defects the same rule shows that anchor complexity is controlled by the number of support runs, not directly by support cardinality. Long contiguous defect blocks can therefore be substantially cheaper than sparse isolated supports of the same defect size.

This path coordinate is only a complexity/representation fact; it does not identify supports as equivalent for the full LABS energy, because the corresponding physical lags still enter the even-correlation objective differently. It is nevertheless a natural basis for sharding future defect-2/3 exact sweeps: schedule by run count / bad-coordinate count so the hardest sparse supports do not dominate a few shards.
