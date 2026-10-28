# p008 exact screens and semilinear frontier — 2026-10-28

This note records the strongest new evidence after the upstream 102-gate merge. It deliberately separates complete exclusions from candidate-oriented searches.

## Live baseline

Few Shots p008 is at **102 gates** (`huangxin-design/aes102-field-plane-offsets`, merged PR #25). A valid new record therefore requires **101 gates or fewer**. Re-check the live board and open PRs before any claim.

The live 102 decomposition is

```text
18 prelinear + 9 first AND + 15 middle + 18 core + 18 final AND + 24 output = 102.
```

The retained inversion core costs 18 gates. With that core fixed, the outer variable cost can be written

```text
prelinear + middle_support + output_transpose,
```

where middle has ten fixed transpose-combine XORs plus `middle_support` offset injections, and output costs `10 + output_transpose` by transposition. A 101 construction in this family needs

```text
prelinear + middle_support + output_transpose <= 36.
```

## Complete result 1: zero-preserving five-AND direct core needs at least 13 mandatory linear forms

`search_core5_exact_mandatory.py` exhausts every non-dominated physical witness through four AND gates, then streams the complete fifth-AND layer. For every five-AND decomposition spanning the live nine-factor target space it counts the distinct non-unit linear source masks that must exist either as AND operands or factor outputs.

Action run `40633525759` completed successfully in eight shards. Every shard obtained exact minimum **13** and saved zero witnesses with count <=12:

| shard | fifth candidates | minimum | minimum witnesses | <=12 hits |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 4,666,770 | 13 | 72 | 0 |
| 1 | 4,666,554 | 13 | 118 | 0 |
| 2 | 4,666,428 | 13 | 124 | 0 |
| 3 | 4,666,248 | 13 | 36 | 0 |
| 4 | 4,666,266 | 13 | 104 | 0 |
| 5 | 4,666,644 | 13 | 60 | 0 |
| 6 | 4,666,770 | 13 | 104 | 0 |
| 7 | 4,666,896 | 13 | 54 | 0 |

Therefore a **zero-preserving** direct core with exactly five AND gates cannot fit in `5 AND + 12 XOR = 17` gates for the current fixed interface. This is a complete exclusion for that family, not a beam-search observation.

It does **not** exclude:

- affine/XNOR five-AND circuits exploiting the complete zero-state don't-care;
- six-AND + eleven-linear 17-gate circuits;
- a changed middle/core interface.

## Complete result 2: exact 17-gate prelinear networks are abundant at the live field transform

`search_plane_prelinear17.py` exhausts all `3^9 = 19,683` product-plane orientations for the live field transform `P(x)=0x1b*x^16` and exactly decides whether their operand target set has a <=17-gate XOR/XNOR linear network.

Action run `40633366881` completed all nine prefixes. Exact hit counts were:

```text
prefix 0: 120
prefix 1: 194
prefix 2: 172
prefix 3: 303
prefix 4: 696
prefix 5: 681
prefix 6: 484
prefix 7: 398
prefix 8: 475
----------------
total:   3523
```

Thus the live 18-gate prelayer is not individually minimal over plane orientations. The difficulty is coupled cost: changing orientation also changes middle offsets and the dual final-product/output columns.

## Important corrected false lead

Orientation

```text
[1,1,2,0,2,2,2,1,0]
```

admits a 17-gate prelinear network and a five-injection middle correction, apparently suggesting

```text
17 + 9 + 15 + 18 + 18 + 24 = 101.
```

This count is invalid because plane orientation also changes the final-product/output linear map. After the required dual column transform, the output transpose target set for this candidate cannot be synthesized in 14 gates, so the output is no longer 24 gates.

Do not count pre/middle savings without simultaneously recomputing the dual output map.

## Fixed-field joint screen: strong negative, with helper-realization caveat

`search_plane_joint101.py` combines exact prelinear synthesis, dual output-column synthesis, and middle correction solving for the live field transform. The exact Action run `40634496429` completed successfully.

A separate local joint screen over the returned minimum prelinear witnesses found no orientation satisfying the full outer variable budget <=36. In particular, among all 3523 exact 17-prelinear hits there is no output-transpose cost 13, and the simple `pre=17 + support<=4 + output_transpose<=15` route produced no 101 candidate.

Caveat: when a prelinear target set has helper slack, `search_plane_prelinear17.feasible()` returns one exact helper realization. A different equal-cost helper may expose a better middle correction. Therefore this is a strong fixed-field screen but should not be advertised as a global proof over every equal-cost helper realization unless that helper-choice space is explicitly exhausted.

## Semilinear transport formulation

To move beyond the saturated live representation, transport the entire retained nonlinear construction through

```text
P(x) = c * x^(2^k),   c != 0,  k in {0,...,7}.
```

For an internal linear functional mask `m`, its AES-input mask is the pullback through `P`. Starting from the live `P0(x)=0x1b*x^16`, any live prelinear mask can therefore be transported by recovering its internal functional and pulling it back through the new `P`.

The AES output compensation is

```text
Q(c,k) = L o Frobenius^(8-k) o multiplication_by_c o L^-1,
```

where `L` is the constant-free AES affine map. Relative to the live transform, output columns are transported by

```text
R = Q(c,k) o Q(P0)^-1.
```

For a product plane with local orientation

```text
0: (a,b)
1: (a,a+b)
2: (a+b,b),
```

orientation 1 adds linear middle offset `a` and transforms a dual output-column pair `(u,v)` to `(u XOR v, v)`; orientation 2 adds offset `b` and transforms the dual pair to `(u, u XOR v)`.

This gives a self-contained way to score prelinear, middle and output costs jointly for any of the 2040 semilinear field transforms.

## `P(x)=0x9d*x^8` probe

A cheap all-orientation screen of this transform found unusually small target sets. Across all 19,683 orientations, `(pre-target-count, output-transpose-target-count)` reaches `(15,13)`. Distribution at the low end includes:

```text
(15,13): 1944
(15,14): 2916
(15,15): 972
(16,14): 3888
(16,15): 3888
(16,16): 972
(17,15): 2430
```

Exact output synthesis then established that **no orientation has output-transpose cost 13 or 14**. The next unresolved tier is output-transpose cost 15, where a 101 construction requires

```text
prelinear + middle_support <= 21.
```

For example, `pre=17,support=4` or `pre=18,support=3` would suffice.

`search_semilinear_outer.py` now implements the transported joint search, and `.github/workflows/temp-aes-semilinear-9d.yml` shards the `0x9d,k=3` family over the first two plane orientations. It exactly synthesizes pre/output networks for the selected target sets and exactly solves middle corrections over the wires of the selected minimum prelinear realization. Positive witnesses are concrete component candidates; negative results retain the same equal-cost-helper caveat as above.

## Direct-core route after the exact five-AND exclusion

The remaining direct 17-gate core families worth serious effort are now narrower:

1. **five AND + twelve XOR/XNOR with affine zero-state completion**, which is not covered by the zero-preserving exact lower bound;
2. **six AND + eleven XOR/XNOR**, for which earlier generic synthesis timed out but did not prove UNSAT;
3. a jointly changed middle/core interface rather than the fixed `q34,q36,q39,q41` boundary.

Do not spend further compute on zero-preserving five-AND beams: that family now has an exact mandatory-form lower bound of 13.
