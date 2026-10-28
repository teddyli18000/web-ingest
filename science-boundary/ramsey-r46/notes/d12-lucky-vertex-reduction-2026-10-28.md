# D12 lucky-vertex reduction — 2026-10-28

## Claim

Assume a Ramsey(4,6,36) graph `G` exists with maximum degree `Delta(G)=12`.
Then `G` has a degree-12 vertex `v` for which, writing

- `A = G[N(v)]`, so `|A|=12`, and
- `B = G[V(G) \ (N(v) union {v})]`, so `|B|=23`,

we necessarily have

- `e(A)=29`,
- `e(B)=101`,
- `A` is the unique 29-edge Ramsey(3,6,12) graph in McKay's complete catalogue, and
- `B` is the unique 101-edge Ramsey(4,5,23) graph in McKay's published complete low-edge tail.

Consequently the entire maximum-degree-12 branch reduces to one fixed `(A,B)` gluing instance with only the 276 `A--B` cross edges unknown.

## Inputs already established in this workspace

1. Every hypothetical Ramsey(4,6,36) graph has minimum degree at least 11. Hence under `Delta=12`, every vertex has degree 11 or 12.
2. The complete McKay Ramsey(3,6,12) catalogue has 116,792 graphs and edge maximum 29; the edge-29 stratum has exactly one graph. Reproducible evidence is in `results/endpoint-catalog-edge-extremes.json`.
3. The complete McKay Ramsey(3,6,11) catalogue has 30,395 graphs and edge maximum 26. Reproducible evidence is in `results/degree11-catalog-stats.json`.
4. For Ramsey(4,5,23), the exact minimum edge count is 101 and the minimum stratum contains one graph. `r45extreme.tar.gz` was independently inventoried in `results/r45extreme-inventory.json` (archive SHA256 `9cfac9dbd1c209cfa342e5d5424df2a7a3fbb008ca00bf0a992e5bbe72f925b6`).
5. For Ramsey(4,5,24), the exact minimum edge count is 116. Angeltveit--McKay, *R(5,5) <= 46*, J. Graph Theory (online 2026), Table 1, gives the exact `e_min=116` and the complete catalogue size 352,366.

## Lucky-vertex identity

Guo--Wan (arXiv:2610.29584, submitted 2026-10-21) explicitly uses the McKay--Radziszowski subgraph-counting identity

```
sum_v 2 e(G_v^-) = sum_v [ d(v)(n - 2 d(v)) + 2 e(G_v^+) ].
```

Therefore every graph has at least one **lucky vertex** `v` satisfying

```
2 e(G_v^-) <= d(v)(n - 2d(v)) + 2 e(G_v^+).
```

For our graph, `n=36`. Since all degrees are 11 or 12, a lucky vertex has degree 11 or 12.

## Degree-11 lucky vertex is impossible

For `d(v)=11`, `A=G_v^+` is a Ramsey(3,6,11) graph and `B=G_v^-` is a Ramsey(4,5,24) graph. The lucky inequality is

```
2 e(B) <= 11(36-22) + 2 e(A)
         = 154 + 2 e(A),
```

so

```
e(B) <= e(A) + 77.
```

But the complete A catalogue gives `e(A)<=26`, hence `e(B)<=103`, while every Ramsey(4,5,24) graph has `e(B)>=116`. Contradiction.

(The weaker Mantel bound `e(A)<=30` would already give `e(B)<=107<116`.)

Thus every lucky vertex in a hypothetical `Delta=12` counterexample must have degree 12.

## Degree-12 lucky vertex collapses to one pair

For `d(v)=12`, `A` is Ramsey(3,6,12) and `B` is Ramsey(4,5,23). The lucky inequality becomes

```
2 e(B) <= 12(36-24) + 2 e(A)
         = 144 + 2 e(A),
```

so

```
e(B) <= e(A) + 72.
```

The complete A catalogue gives `e(A)<=29`, while the exact Ramsey(4,5,23) lower edge bound is `e(B)>=101`. Hence

```
101 <= e(B) <= e(A)+72 <= 101.
```

All inequalities are equalities:

```
e(A)=29, e(B)=101.
```

Both edge strata contain exactly one isomorphism class. Therefore there is exactly one `(A,B)` isomorphism-class pair that needs a gluing test.

## Exact decision procedure

`d12_fixed_ab_sat.py` fixes both catalogue graphs and introduces one Boolean variable for each of the 276 A--B edges. It statically encodes:

- total degree 11/12 for every A and B vertex;
- every mixed K4 split (`1A+3B`, `2A+2B`);
- every mixed independent-6 split (`5A+1B`, `4A+2B`, `3A+3B`, `2A+4B`).

A SAT result is a complete 36-vertex certificate and is independently checked by exhaustive K4/I6 verification before being written. UNSAT excludes the unique lucky pair and therefore proves that no maximum-degree-12 Ramsey(4,6,36) graph exists.

## References

- W. Guo and M. Wan, *A Computer-Assisted Proof that R(5,10;5,8)=21 for the Generalized Threshold Ramsey Number*, arXiv:2610.29584 (2026), Section 2.2.
- B. D. McKay and S. P. Radziszowski, *Subgraph Counting Identities and Ramsey Numbers*, J. Combin. Theory Ser. B 69 (1997).
- V. Angeltveit and B. D. McKay, *R(5,5) <= 46*, J. Graph Theory (online 2026).
- McKay combinatorial data: https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
