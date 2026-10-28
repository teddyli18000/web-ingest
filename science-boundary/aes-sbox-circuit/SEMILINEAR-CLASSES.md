# Semilinear lower-bound classes for p008

For the 18 transforms that attain the best cheap outer target-count lower bound,
I exhaustively evaluated all `3^9 = 19,683` plane orientations and grouped transforms
by the complete distribution of

```text
(prelinear non-input target count,
 output-transpose non-input target count,
 unrestricted minimum middle correction support).
```

The minimum middle support is exact as a finite-dimensional column-span question:
for each orientation, the eight bit-slice right-hand sides define a subspace of
`GF(2)^4`, and the cost is the smallest number of the nine fixed middle columns
whose span contains that subspace.

This partitions the 18 transforms into **three six-member lower-bound classes**:

```text
Class A (identity representative P(x)=x):
(c,k) =
(0x01,0), (0x1b,4), (0x66,4), (0x7d,4), (0xbc,0), (0xbd,0)

Class B (0x9d representative P(x)=0x9d*x^8):
(0x13,7), (0x6b,3), (0x9d,3), (0xea,7), (0xf6,3), (0xf9,7)

Class C (0x5b representative P(x)=0x5b*x^8):
(0x5b,3), (0x7e,7), (0xa9,3), (0xb9,7), (0xc7,7), (0xf2,3)
```

Here `P(x)=c*x^(2^k)` in `GF(2^8)`.

Important scope: equality of these cheap orientation distributions is **not yet a
proof that exact XOR/XNOR synthesis costs are identical within a class**. The
classification is used to choose structurally distinct representatives for the
expensive searches, not to discard the other transforms permanently.

Current representative searches:

- Class A: `c=0x01,k=0` (identity)
- Class B: `c=0x9d,k=3`
- Class C: `c=0x5b,k=3`

For each representative, the active exact-correction search covers full-column-rank
middle supports of size <=4, while the companion support-5 search exhausts all
117 rank-4 five-position supports and their 256 free-byte assignments. Rank-3
five-position supports remain a small explicit gap.
