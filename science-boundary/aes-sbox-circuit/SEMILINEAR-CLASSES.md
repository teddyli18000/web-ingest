# Semilinear lower-bound frontier for p008

## Full 2040-transform scan

For every semilinear AES input transform

```text
P(x) = c * x^(2^k),   c != 0,   k in {0,...,7},
```

`scan_semilinear_frontier.py` exhaustively evaluates all `3^9 = 19,683` product-plane orientations. This is all `255*8 = 2040` semilinear transforms in the searched family.

For each orientation it computes the rigorous retained-core lower bound

```text
prelinear non-input target count
+ unrestricted minimum middle correction support
+ output-transpose non-input target count.
```

The minimum middle support is exact as a finite-dimensional column-span question: for each orientation, the eight bit-slice right-hand sides define a subspace of `GF(2)^4`, and the cost is the smallest number of the nine fixed middle columns whose span contains that subspace. The pre/output terms are distinct-target counts and can only underestimate actual two-input XOR/XNOR synthesis cost.

Action run `40638593824` completed all 32 shards. Aggregation run `40640996806` loaded all 2040 transform records and obtained the exact per-transform best-LB distribution:

```text
best outer-variable lower bound | transforms
31                              | 18
32                              | 30
33                              | 24
34                              | 78
35                              | 150
36                              | 234
37                              | 336
38                              | 594
39                              | 576
--------------------------------+-----------
total                           | 2040
```

A retained-18-gate-core 101 construction needs actual outer-variable cost at most 36. Therefore **1506 / 2040 transforms are rigorously excluded from 101 by this cheap lower bound alone**; exactly **534 transforms** retain at least one orientation with lower bound <=36.

The global lower-bound minimum is **31**, attained by exactly **18 transforms**. Every LB=31 witness has the component count

```text
15 prelinear targets + 3 middle-support positions + 13 output targets = 31.
```

This is a lower bound, not a 96-gate construction: exact XOR/XNOR synthesis can cost substantially more than distinct-target counts.

## The 18 global-best transforms

Grouping the 18 transforms by the complete distribution over all 19,683 orientations of

```text
(prelinear target count,
 output-transpose target count,
 unrestricted minimum middle correction support)
```

gives three six-member classes.

### Class A

```text
(c,k) =
(0x01,0), (0xbc,0), (0xbd,0),
(0x1b,4), (0x66,4), (0x7d,4)
```

Representative: identity `(0x01,0)`. Each Class-A transform has 17,191 orientations with cheap lower bound <=36.

### Class B

```text
(c,k) =
(0x6b,3), (0x9d,3), (0xf6,3),
(0x13,7), (0xea,7), (0xf9,7)
```

Representative: `(0x9d,3)`. Each has 17,028 orientations with cheap lower bound <=36.

### Class C

```text
(c,k) =
(0x5b,3), (0xa9,3), (0xf2,3),
(0x7e,7), (0xb9,7), (0xc7,7)
```

Representative: `(0x5b,3)`. Each has 17,033 orientations with cheap lower bound <=36.

## Exact class automorphisms

The three six-member classes are now proved to be **exact retained-core outer-construction equivalence orbits**, not merely equal cheap-LB distributions.

`prove_semilinear_class_automorphisms.py` takes one representative from each class and, for every one of the five nonrepresentative members, constructs:

1. a permutation of the nine product planes;
2. a per-plane permutation of the three orientation choices;
3. an invertible four-bit middle-coordinate map `M`.

For every one of all `3^9 = 19,683` orientations per member it checks exactly that:

- the selected prelinear operand target set is identical after plane/orientation relabeling;
- the selected transposed-output target set is identical after the same plane relabeling;
- the middle correction equation is transported by `M`;
- the retained 18-gate core has the matching factor covariance

```text
F_{sigma(i)}(M y) = F_i(y)
```

for all nine factors and all 16 four-bit core states.

Only three plane permutations occur:

```text
identity
(1,7,5,6,2,4,8,0,3)
(7,0,4,8,5,2,3,1,6)
```

and the corresponding middle maps have column tuples

```text
(1,2,4,8)
(5,8,1,10)
(4,10,5,2).
```

The two nontrivial transformations have order three. Since the prelinear target sets are literally the same after relabeling, arbitrary helper-wire choices and exact linear-network costs transport without change; the same holds for output networks and middle-support corrections.

Independent GitHub Actions run **`40743531094`** completed successfully and checked all 15 nonrepresentative members, each over all 19,683 orientations.

### Consequence

Within the retained-18-core semilinear family, exact search of one representative is sufficient for the entire six-member class:

- identity `(0x01,0)` covers all Class A members, including the live `(0x1b,4)` transform;
- `(0x9d,3)` covers all Class B members;
- `(0x5b,3)` covers all Class C members.

This equivalence is specific to the retained-core outer construction. It is not a statement about arbitrary AES circuits or about constructions that change the nonlinear core/interface.

## Exact searches layered on the frontier

For the Class A/B/C representatives, the exact-correction campaigns cover complementary middle-correction families:

- `search_semilinear_exactcorr.py`: full-column-rank correction supports of size <=4;
- `search_semilinear_support5.py`: all 117 five-position supports whose fixed middle columns have rank four, including the free-byte family;
- `search_semilinear_support5_rank3.py`: the remaining nine five-position supports of rank three, using a complete two-free-byte event enumeration under the 101 target-count budget.

The rank-3 event reduction is independently checked against full `2^16` `(z,w)` brute force on 135 random synthetic cases with no misses; details are in `RANK3-SUPPORT5.md`.

Class A/B rank-four support-5 evidence has also been aggregated independently: Action run `40742805378` loaded all 18 shard summaries from historical run `40638295317`, covering 39,366 orientations in total, and verified `candidates_101 = 0` and zero saved witnesses.

Historical runner cancellations left exact-correction gaps in Class A/B and Class C, plus one Class-C rank-three-support-5 shard. Dedicated low-parallel gap workflows are closing only those missing shards; cancelled work is not treated as a negative result.

## Support >=6

A retained-core 101 construction with middle support at least six would require

```text
prelinear + output_transpose <= 30.
```

A separate exact 0/1-helper linear-network lower-bound proof (`prove_semilinear_support6_impossible.py`) has been added for the three class representatives. The local exhaustive computation finds no orientation meeting this budget; independent Action verification is pending at the time of this update. Until that Action completes, keep the support>=6 exclusion labeled as locally verified rather than independently reproduced.

## How to use this frontier

Do not launch expensive exact synthesis uniformly over all 2040 transforms. For the LB=31 tier, search only the three exact class representatives. Once their complete 101 budget is closed, the next genuinely new retained-core search space is the LB=32 tier of 30 transforms, subject to any analogous automorphism reduction.

A transform with best cheap lower bound >=37 is already excluded from 101 in the retained-18-core family and should not receive further exact-synthesis budget unless the nonlinear core/interface itself changes.
