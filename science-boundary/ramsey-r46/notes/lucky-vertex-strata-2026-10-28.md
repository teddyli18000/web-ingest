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
catalogue would stall. It can still be valuable on the lowest edge strata,
where fixing B removes all B-internal SAT variables.

## d=12: complete orbit closure

The unique lucky-d12 branch fixes A to the unique 12-vertex `(3,6)` graph with
29 edges and B to the unique 23-vertex `(4,5)` graph with 101 edges. There are
276 cross edges.

`d12_anchor_orbit_dimacs.py` uses the unique internal-degree-10 vertex of B as
an anchor. Its cross-neighbourhood in A must satisfy the exact degree bounds
and hit every independent 5-set of A. There are 2,873 feasible labelled
12-bit masks. Quotienting by `Aut(A)` of order 576 gives exactly **118** orbit
representatives, and every full solution can be A-relabeled into one of these
branches.

The first exact Kissat campaign in `results/d12-anchor-orbits.json` decided
104 of the 118 representatives UNSAT and timed out on 14. The unresolved
ordinals were

```
0, 1, 3, 9, 17, 19, 28, 30, 46, 69, 70, 71, 73, 88
```

For each timeout, the fixed anchor mask leaves a nontrivial stabilizer in
`Aut(A)`. `d12_anchor_orbit_dimacs.py` adds exact lex-leaders for either the
whole residual stabilizer or a generator set returned by
`d12_fixed_ab_sym_sat.py::greedy_generators`; that routine explicitly verifies
that the chosen generators close back to the full group. The second campaign
`results/d12-residual-symmetry.json` closes **all 14/14** remaining branches
UNSAT. Generator lex-leaders are sound even when they are not a complete
canonicalization: the lexicographically least member of every finite group
orbit satisfies every generator inequality.

Therefore the recorded exact cover is

```
2873 feasible labelled masks
 -> 118 Aut(A) orbit branches
 -> 104 first-stage UNSAT + 14 residual-symmetry UNSAT
 -> 118/118 closed, no SAT branch
```

Subject to the recorded SAT solver results, the lucky-degree-12 stratum is
fully excluded. Together with the analytic d=11 contradiction, a hypothetical
36-vertex solution must have a lucky vertex of degree 13..17.

`verify_d12_lucky_closure.py` is the durable accounting/structure verifier. It
regenerates the 2,873-to-118 orbit manifest from the pinned A29/B101 inputs,
runs the symmetry self-tests, and checks exact first/second-stage branch
coverage. It intentionally does not pretend to be an UNSAT proof-certificate
checker; an independent/proof-producing solver rerun is the next level of
solver certification.

## d=17: exact variable-B formulation plateaued

`degree17_static_sat_v4.py` fixes each of the seven complete A types, keeps the
18-vertex B graph and cross edges variable, imposes all mixed Ramsey clauses,
global degree bounds, and the lucky window `50 <= e(B) <= e(A)+17`.

`results/degree17-lucky-v4.json` records **TIMEOUT on all seven branches after
3600 s each**. This is not negative mathematical evidence about the branch;
it is evidence that the variable-B formulation remains too broad. Do not
repeat it with a larger timeout without changing the representation.

The extreme catalogue gives a natural next split: the complete e(B)=50 layer
has 326 B graphs and the complete e(B)=51 layer has 29,160. These can be
turned into fixed-A/fixed-B cross-edge gluing instances, while e(B)>=52 remains
in a separate variable-B search space.

## d=16: weak filters and e(A)=32 pilot plateaued

A cheap cross-capacity relaxation was run over all 2,576 complete A types and
kept **2,576/2,576**. It has no pruning power and should not be extended.

The first exact split-SAT pilot fixed the five minimum-edge A types with
e(A)=32, kept B variable, imposed the exact lucky window `57 <= e(B) <= 64`,
and ran each branch for 3600 s. `results/d16-e32-exact-pilot.json` records
**TIMEOUT on all 5/5**. Again, this only rejects that formulation/time budget.

Here the public extreme B catalogue is much stronger than for d17: for n=19
it contains exactly one graph at e(B)=57 and exactly one at e(B)=58. Thus the
lowest two B strata across the five e(A)=32 types require only ten fixed-pair
gluing problems (304 cross variables each), with all B-internal variables
removed. This is the next exact d16 probe before returning to e(B)>=59.

## Priority after d12 closure

1. Independently rerun/cross-check the 118 d12 orbit branches with residual
   generator symmetry and a second solver backend; keep solver-certification
   strength distinct from logical coverage.
2. For d16, exploit the singleton B57 and B58 strata first: five A32 types x
   two fixed B graphs. Add `Aut(A) x Aut(B)`/anchor symmetry before spending
   another long SAT budget.
3. For d17, inventory automorphism/degree structure of the 326 B50 graphs
   before launching 7 x 326 fixed-pair gluings; only then decide whether B51's
   29,160 graphs are tractable directly or need another orbit/local split.
4. Treat e(B)>=59 (d16) and e(B)>=52 (d17) as different search spaces rather
   than extending the timed-out variable-B instances unchanged.

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
