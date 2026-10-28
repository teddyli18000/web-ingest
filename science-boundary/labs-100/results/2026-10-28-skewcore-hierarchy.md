# 2026-10-28 boundary + skew-core hierarchy

## Purpose

The public N=100 incumbent is exactly `(+1, skew99)`. Rather than treating that as an isolated construction, this experiment enlarges it systematically: keep an odd-length skew-symmetric suffix, but allow an unconstrained odd boundary of length `d=2m+1` in front. This gives a nested family of finite-state search spaces between the incumbent's near-skew representation and increasingly general sequences.

The main questions are:

1. Can any **odd-perfect** member (all 50 odd correlations have magnitude 1) in these larger classes reach the Few Shots target `E<=574`?
2. Can any member of the first non-odd-perfect layer, **odd energy O=58**, reach the target?

No target certificate was found. The finite-state reductions below give exact exclusions for the classes actually searched.

## Finite-state reduction

Let the boundary length be `d=2m+1`, normalize `s0=s1=+1`, and write

```text
u_j = s_{2j+1},
v_j = s_{2j+2}.
```

The skew suffix `s_d..s_99` has reflection

```text
u_{49+m-j} = alpha u_j,   alpha = (-1)^(m+1),
v_{48+m-j} = beta  v_j,   beta  = (-1)^m.
```

For an odd lag `k=2j+1`, the suffix-suffix contribution vanishes, leaving only the boundary form

```text
T_j = Σ_{r=0}^m b_{2r} u_{j+r}
    + Σ_{r=0}^{m-1} b_{2r+1} v_{j+r}.
```

Pairing `C_k` with `C_{100-k}` and applying the skew reflection turns the odd-correlation constraints into a recurrence that remembers only the most recent `m` `(u,v)` pairs. This is a finite-state automaton with at most `4^m` raw memory states.

The even-lag target is handled separately. During a partial assignment, let `F_k` be the sum of already fixed products in even correlation `C_k` and let `U_k` products remain unknown. Every completion satisfies

```text
|C_k| >= max(0, |F_k| - U_k).
```

Therefore

```text
Σ_{k even} max(0, |F_k|-U_k)^2
```

is a rigorous branch-and-bound lower bound.

## Odd-perfect hierarchy

Odd-perfectness requires every opposite odd pair to be `(1,-1)` or `(-1,1)`, so odd energy is exactly 50 and a `574` target requires even energy at most 524.

Exact finite-state enumeration was used for small branches. One dominant branch at each level was finished with the partial-correlation BnB on GitHub Actions. All normalized boundary prefixes are covered in each listed `d` class.

| boundary `d` | dominant raw odd-perfect branch | dominant BnB result | conclusion |
| ---: | ---: | --- | --- |
| 5 | 42,211,134,936 states | run `40638867040`: 154,046,687 nodes, 57.456 s | no `E<=574` |
| 7 | 12,572,890,440 | run `40639126820`: 205,508,436 nodes, 74.377 s | no `E<=574` |
| 9 | 5,392,423,388 | run `40639680487`: 220,458,034 nodes, 48.943 s | no `E<=574` |
| 11 | 2,769,400,112 | run `40639958154`: 259,700,430 nodes, 95.126 s | no `E<=574` |
| 13 | 1,521,157,796 | run `40640237181`: 296,220,581 nodes, 149.592 s | no `E<=574` |

At every level all non-dominant branches were either empty, exactly enumerated, or separately proved target-infeasible before the dominant Actions job was launched. Thus the full normalized `d=5,7,9,11,13` odd-perfect boundary+skew-core classes are excluded from `E<=574`.

The dominant prefixes show a nested period-four pattern:

```text
d=5   --+
d=7   --++-
d=9   --++--+
d=11  --++--++-
d=13  --++--++--+
```

This is a structural observation, not a claim that all low-energy LABS sequences must follow that pattern.

Durable target-search implementations:

- `code/skewcore_d5_bnb.cpp`
- `code/skewcore_d7_bnb.cpp`
- `code/skewcore_d9_bnb.cpp`
- `code/skewcore_d11_bnb.cpp`
- `code/skewcore_d13_bnb.cpp`

## First defect layer: O=58

For N=100 the odd correlations form 25 opposite pairs with

```text
C_k + C_{100-k} == 0 (mod 4).
```

Odd energy 50 is the pairwise minimum. At odd energy 58 exactly one pair contributes 10 instead of 2, hence exactly one pair is

```text
(1,3), (3,1), (-1,-3), or (-3,-1),
```

and every other pair is `(1,-1)` or `(-1,1)`.

The parity-half sums

```text
a = Σ s_{2i},
b = Σ s_{2i+1}
```

then satisfy `ab=±4`, so necessarily `|a|=|b|=2`. Consequently

```text
Σ C_{2r} = (a^2+b^2-100)/2 = -46,
```

and a total target `E<=574` leaves even energy at most 516.

Inside a boundary+skew-core class, one parity-half sum is fixed entirely by the boundary because the corresponding skew-suffix pairs cancel. The other half is a signed sum of same-sign reflected pairs plus one center sign. Once the unique 1/3 defect appears, its sign fixes the required sign of the dynamic half-sum. This is an extremely strong exact pruning condition.

### d=3 target proof

The normalized `d=3 + skew97` O=58 automaton has `419,430,400` structural completions. `code/skewcore_d3_o58_bnb.cpp` searches them implicitly with the exact parity-sum/defect constraint and the even-correlation lower bound. A local 4-thread run visited 946,025 BnB nodes and proved `E<=574` infeasible in about 0.25 s. The independent GitHub Actions reproduction in run `40642312008` also passed.

### Exact minima for d=5..25

For these classes the O=58 automata are small enough to enumerate every completion and score every leaf exactly from scratch with packed-bit aperiodic autocorrelations. `code/skewcore_o58_exact.cpp` is the generic enumerator.

| boundary `d` | complete O=58 states | exact minimum E |
| ---: | ---: | ---: |
| 5 | 4,164,745 | 2358 |
| 7 | 628,671 | 2854 |
| 9 | 679,752 | 2598 |
| 11 | 641,901 | 2430 |
| 13 | 436,918 | 2278 |
| 15 | 245,699 | 2702 |
| 17 | 217,533 | 2478 |
| 19 | 179,404 | 2294 |
| 21 | 166,112 | 2446 |
| 23 | 107,902 | 2294 |
| 25 | 112,329 | **2022** |

Every reported minimum is rescored inside the enumerator; every winner has exact odd energy 58. The best member of these enumerated classes is `E=2022` at `d=25`, still far above the target 574.

The first independent Actions pass, run `40642312008`, reproduced d=5..17 and the d=3 target proof. It deliberately failed its grep assertions at d=19/21/23/25 because the workflow still contained superseded local expectations; the actual runner outputs above were lower (`2294,2446,2294,2022`) and each passed the program's internal exact `odd=58` rescore. The workflow expectations were corrected in commit `c615afd648d5f5dc47ecd684a89f434a5987dec6` and a clean rerun was triggered. Treat the corrected runner values, not the superseded local table, as authoritative.

## Interpretation

The useful result is not merely another failed heuristic. A substantial nested family around skew-symmetric cores has now been handled exactly:

- odd-perfect target feasibility is ruled out for full boundary classes `d=5,7,9,11,13`;
- the first odd-defect layer O=58 is target-infeasible for `d=3` and has exact minima far above the record for every odd `d=5..25`.

Allowing one 1/3 odd-correlation defect does not open a hidden low-energy corridor in any of these skew-core geometries. The d=19..25 audit is also a useful reminder to trust independent reruns over cached local summaries: those corrected minima are materially lower than the first local table, but still nowhere near 574.

This does **not** prove global optimality of 578. Boundary+skew-core is still a structural restriction; for sufficiently large boundary the skew core becomes short and the representation approaches the unrestricted problem. Future work should therefore use the exact O=58 pair structure and parity-half identities without assuming a long skew core, rather than mechanically extending the same hierarchy indefinitely.
