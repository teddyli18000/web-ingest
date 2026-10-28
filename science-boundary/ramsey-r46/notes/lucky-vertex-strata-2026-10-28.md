# Lucky-vertex degree strata — 2026-10-28

## Purpose

Use the McKay--Radziszowski edge identity to replace the old strategy of
solving a monolithic 36-vertex SAT instance under a maximum-degree assumption.
Every hypothetical Ramsey `(4,6,36)` graph has a **lucky vertex** `v` with

```
2 e(B) <= d(36 - 2d) + 2 e(A),
```

where `d=deg(v)`, `A=G[N(v)]` is a Ramsey `(3,6,d)` graph, and `B` is a Ramsey
`(4,5,35-d)` graph. Equivalently,

```
e(B) <= e(A) + d(18-d).
```

The structural Ramsey bounds give `11 <= d <= 17`. The complete McKay
`R(3,6,d)` catalogues and exact `R(4,5,n)` minimum edge counts therefore give
a finite hierarchy of local branches.

## Exact edge-stratum map

| lucky `d` | `|B|` | `c=d(18-d)` | complete A edge range | exact `e_min(B)` | necessary A edges | surviving A types | possible B-edge union |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 11 | 24 | 77 | 8..26 | 116 | `>=39` | **0** | none |
| 12 | 23 | 72 | 11..29 | 101 | `>=29` | **1** | **101 only** |
| 13 | 22 | 65 | 15..32 | 88 | `>=23` | 182,920 | 88..97 |
| 14 | 21 | 56 | 20..35 | 77 | `>=21` | 263,519 | 77..91 |
| 15 | 20 | 45 | 25..37 | 68 | all | 64,732 | 68..82 |
| 16 | 19 | 32 | 32..40 | 57 | all | 2,576 | 57..72 |
| 17 | 18 | 17 | 40..42 | 50 | all | **7** | **50..59** |

`surviving A types` is counted directly from the complete edge histograms in
`results/endpoint-catalog-edge-extremes.json`. In particular:

- `d=11` is impossible before any gluing computation.
- `d=12` collapses to the unique 29-edge A and unique 101-edge B.
- after `d=12`, **lucky d=17 is the next branch by a huge margin**: seven A
  types versus 2,576 for d=16 and tens/hundreds of thousands below that.

The possible B-edge union is only a coarse union over all surviving A types;
each fixed A has the sharper upper bound `e(B)<=e(A)+c`. For example, at
`d=17` the two 40-edge A types allow only `50..57`, the three 41-edge types
allow `50..58`, and the two 42-edge types allow `50..59`.

## Public extreme B catalogues

The independently inventoried McKay archive `r45extreme.tar.gz` contains the
following complete low-edge strata relevant here:

- n=18: e=50 (326), e=51 (29,160)
- n=19: e=57 (1), e=58 (1)
- n=20: e=68 (2,016), e=69 (213,961)
- n=21: e=77 (83), e=78 (5,940)
- n=22: e=88 (3), e=89 (94)
- n=23: e=101 (1), e=102 (76), e=103 (4,424), e=104 (160,676)

The archive does **not** contain all intermediate edge strata in the lucky
windows for d=13..17. Therefore an approach that requires a complete B
catalogue would stall. The better formulation is to fix A, keep B internal
edges as SAT variables, and impose the exact B edge window directly.

## Active exact formulations

### d=12

`d12_fixed_ab_sat.py` fixes both unique graphs A29 and B101. Only the 276
cross edges remain. A SAT model is exhaustively checked as a 36-vertex
certificate; UNSAT eliminates lucky degree 12 entirely (with degree range
11..17) and, in particular, eliminates the whole global `Delta=12` branch.

### d=17

The earlier `degree17_static_sat_v3.py` fixed each of the seven complete A
types, left the 18-vertex B graph and cross edges free, and added global degree
bounds plus symmetry breaking. Its hard branch timed out after 90 minutes
because B was allowed to range over essentially its entire Ramsey-feasible
edge spectrum.

`degree17_static_sat_v4.py` changes the search space by adding the lucky-edge
window `50 <= e(B) <= e(A)+17`. This is a sound exact restriction on the lucky
degree-17 branch and shrinks the 153 free B-internal edge variables to a very
narrow cardinality band. The seven A types are run independently.

## Priority after current runs

1. Decide the unique lucky-d12 fixed pair.
2. Decide the seven lucky-d17 v4 branches.
3. If both are UNSAT, the guaranteed lucky vertex of any hypothetical graph
   must have degree 13..16. Attack d=16 next: its complete A catalogue has only
   2,576 types, orders of magnitude smaller than d=13..15.
4. For d=16, use the same formulation principle (fixed A, variable 19-vertex
   B, exact `57 <= e(B) <= e(A)+32`, full mixed Ramsey clauses), then add
   catalogue automorphism symmetry and cheap local capacity filters before
   spending large SAT time.

## Sources

- W. Guo and M. Wan, *A Computer-Assisted Proof that R(5,10;5,8)=21 for the
  Generalized Threshold Ramsey Number*, arXiv:2610.29584 (submitted
  2026-10-21). This recent proof explicitly uses good-graph catalogues,
  McKay--Radziszowski lucky-vertex filtering, and SAT gluing.
- B. D. McKay and S. P. Radziszowski, *Subgraph Counting Identities and Ramsey
  Numbers*, J. Combin. Theory Ser. B 69 (1997).
- V. Angeltveit and B. D. McKay, *R(5,5) <= 46*, J. Graph Theory (online 2026),
  Table 1 for exact R(4,5,n) edge minima.
- Brendan McKay Ramsey data: https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
