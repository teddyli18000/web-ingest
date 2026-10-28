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

gives three six-member lower-bound classes.

### Class A

```text
(c,k) =
(0x01,0), (0xbc,0), (0xbd,0),
(0x1b,4), (0x66,4), (0x7d,4)
```

Representative searches use identity `(0x01,0)` and, independently, the live-102 field transform `(0x1b,4)`. Each Class-A transform has 17,191 orientations with cheap lower bound <=36.

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

Important scope: equality of the cheap orientation distributions is **not** a proof that exact XOR/XNOR synthesis costs are identical within a class. The classification is a search-priority device, not a permanent exclusion of nonrepresentatives.

## Exact searches layered on the frontier

For Class A/B/C representatives, the current exact-correction campaigns cover complementary middle-correction families:

- `search_semilinear_exactcorr.py`: full-column-rank correction supports of size <=4;
- `search_semilinear_support5.py`: all 117 five-position supports whose fixed middle columns have rank four, including the free-byte family;
- `search_semilinear_support5_rank3.py`: the remaining nine five-position supports of rank three, using a complete two-free-byte event enumeration under the 101 target-count budget.

The rank-3 event reduction is independently checked against full `2^16` `(z,w)` brute force on 135 random synthetic cases with no misses; details are in `RANK3-SUPPORT5.md`.

At the current live 102 transform and identity, completed rank-3 prefixes have produced no 101 candidate; many orientations are already eliminated by exact pre/output budget before correction enumeration. The Class-B/Class-C rank-3 matrix is still being completed.

## How to use this frontier

Do not launch expensive exact synthesis uniformly over all 2040 transforms. First prioritize the three structurally distinct LB=31 classes and then the LB=32 tier if the representative exact searches saturate. A transform with best cheap lower bound >=37 is already excluded from 101 in the retained-18-core family and should not receive further exact-synthesis budget unless the nonlinear core/interface itself changes.
