# Nine-factor fractional owner-charge obstruction and exact 10D prize audit

Date: **2026-11-04**. Status: **new, narrow exact obstruction and negative restricted-product result; no new p004 certificate**.

## Pinned geometry and source state

- Fixed BPZ/Tandon source `tandonravi/C7-Shannon-Capacity-Heterogeneous-Recursion` commit `c753408492dde92a239708986d16c15dbf6c3235`, input `data/base_c7.json`.
- `I0` is a 367-point independent subset of `C7^5`; remove the eight first entries of `private_pairs` to get the 359-point core `B`.
- For outside factor `z`, let `S(z)=N[z]∩B`. Independent implementation reproduces the pinned count **50** factors of support 1, **375** of support 2, and **1,581** of support 3.
- Upstream Few Shots p004 public baseline remains **134,753**. This research does not claim any improvement.

## New fractional charge test

The integer owner-clique assignment fails at support size 3, as established in `outside-outside-support3-obstruction.md`. We tested the stronger possibility of **fractional owner-clique covering**.

A fractional cover assigns nonnegative mass `lambda_(b,C)` to cliques `C` of the confusability graph induced by `{z:b∈S(z)}`, with:

- per owner: `sum_C lambda_(b,C) <= 1`;
- per factor: `sum_{b,C:z∈C} lambda_(b,C) >= 1`.

If a fractional cover exists, the tensor products of these cliques give a fractional charging certificate for all pairs of factors: each selected independent 10D point receives total charge at least one, and each activated core cell receives charge at most one. Consequently, no positive raw core gain is possible in that product family. This is a **sufficient certificate**, not an equivalence.

### Exact nine-factor dual obstruction

A compact nine-factor subset is:

```text
F9 = [1012, 1025, 1285, 1299, 3722, 6501, 13109, 13359, 15759]
```

Give every factor dual weight `1/2` except `13359` with weight `1`. Give the eight eligible core owners `983,1292,1360,3420,3680,4106,15468` weight `1/2` each and `15712` weight `1`.

The factor weights sum to **5**, while owner capacities sum to **4.5**. For every owner, an exhaustive enumeration of all subsets of the eligible nine factors verifies that every pairwise-confusable clique has weight no larger than that owner's capacity. Hence any fractional owner-clique cover would imply `5 <= 4.5`, a contradiction.

This proves **no fractional owner-clique cover exists even for these nine factors**, with an integer-arithmetic dual contradiction of **1/2**. It does **not** prove a positive construction. A local SciPy/HiGHS elastic-cover LP also returned minimum unmet coverage 0.5; the portable exact dual checker establishes the lower bound without trusting that LP.

## Independent ten-dimensional prize test

For `F×F`, candidates are ordered pairs `(u,v)`, with obligatory old-core deletions `S(u)×S(v)`. Binary MILP variables select candidates and charge each distinct deleted core cell once. Hard constraints prohibit selecting two candidates when both five-dimensional coordinates are confusable. Objective:

`max (#selected candidates - #distinct deleted core cells)`.

The model **ignores terminal periphery losses**, making its optimum an upper bound on achievable full-score change for this restricted addition universe.

| Exactly optimized universe | Cases | Result |
| --- | ---: | --- |
| `F9×F9` (81 candidate points, 64 core cells, 44 new-new conflict pairs) | 1 | maximum gain **0** |
| `(F9∪{z})²` for every support≤2 factor `z` whose support touches one of the eight obstruction owners | 38 | all maximum gain **0** |
| `(F9∪{x,y})²` for all pairs among the six support≤2 factors touching **two** obstruction owners | 15 | all maximum gain **0** |

The objective, all selected points' pairwise compatibility, the deletion footprint and the solver optimum are replayed by the script. Each MILP returned HiGHS optimal status (`status=0`); no positive raw core gain was found.

**Critical scope:** These results exclude only the listed factor-product universes, with a fixed 359×359 core. They are not an upper bound on `α(C7^10)`, nor do they exclude mixed universes that combine many more factors or change the core itself.

## Verification and reproduction

- Reusable code: `../code/bpz_fractional_nine_charge.py`.
- Run with: `python code/bpz_fractional_nine_charge.py /path/to/pinned/data/base_c7.json /tmp/fractional-nine-results.json` (from this topic directory).
- Python 3.12, NumPy 2.5.4, SciPy 1.18.1 on GitHub Actions.
- Independent hosted replay: [GitHub Actions run 41849969593](https://github.com/teddyli18000/web-ingest/actions/runs/41849969593), job `126643333191`, completed successfully, pinned upstream source SHA checked before replay.
- Run artifact: [c7-fractional-nine-exact](https://github.com/teddyli18000/web-ingest/actions/runs/41849969593/artifacts/13333875450).
- Job summary reports `base.gain=0`, `shell=38`, `pairs=15`, `positive=0`, and `all_exact=true`.

## What changed scientifically / next formulation

Factorwise *fractional* ownership already fails on a tiny nine-point kernel, yet exact ten-dimensional compatibility collapses its prize to zero. The explanatory object is therefore not merely an unsatisfied owner list or a fractional-cover integrality gap: **a valid positive construction must beat the joint compatibility-and-shared-deletion tradeoff**.

Because the 38 nearest one-factor and 15 most-coupled two-factor extensions all stay at zero, do **not** spend the next campaign repeatedly enlarging this identical kernel one or two factors at a time. The next distinct formulation should either:

1. vary the five-dimensional parent/core itself jointly with new ten-dimensional endpoints, not just add fixed-core factors; or
2. return to the `α(C7^5) >= 368` exact core-prize/alternative-basin line, whose 368-point witness immediately squares to a p004 score **135,424**.

As always, any positive candidate must be replayed through the upstream Few Shots p004 verifier before a record claim.
