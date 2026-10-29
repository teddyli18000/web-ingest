# Global exclusion of the retained-core semilinear joint-decoupled family

Date: 2026-10-29 (+08:00)

## Statement

Within the retained 18-gate inversion-core construction, consider every semilinear AES input transform

```text
P(x) = c * x^(2^k),  c != 0,  k=0,...,7,
```

and allow the nine rank-two product-plane orientations before the core and the nine final-product/output plane orientations after the core to be chosen **independently**. The prelinear network must synthesize the union of the operands required by both orientation vectors; the middle correction is determined by the front orientation vector; and the output transpose is determined by the final orientation vector.

No member of this entire family attains the variable linear cost <=36 required for a 101-gate AES S-box with the retained 18-gate core.

This family strictly contains the earlier same-orientation semilinear search.

## Exact orbit reduction

The previously proved semilinear automorphism theorem partitions all 2040 transforms into 340 exact six-element retained-core orbits. A local independent cheap-LB scanner regenerated all 340 representatives and exactly reproduced the verified orbit histogram:

```text
LB31:  3 orbits
LB32:  5
LB33:  4
LB34: 13
LB35: 25
LB36: 39
LB37: 56
LB38: 99
LB39: 96
----------------
total 340
```

The scanner used the fact that GF(2)^4 has only 67 linear subspaces: the exact minimum middle-support size was precomputed for every possible RHS subspace, reducing the full 340 * 19,683 same-orientation cheap scan to about 6.7 million lightweight states. The complete histogram reproduced in about 1.3 seconds on five local CPU threads.

## Why LB37–39 cannot be rescued by front/final decoupling

For a front orientation `f` and final orientation `g`, let

- `pre_union(f,g)` be the non-input operand target set required by both front and final product planes;
- `pre(f)` be the front-only operand target set;
- `mid(f)` be the exact unrestricted minimum middle-correction support size;
- `out(g)` be the non-input output-transpose target set.

Then trivially

```text
|pre_union(f,g)| >= |pre(f)|.
```

Therefore every decoupled pair obeys the rigorous target-count lower bound

```text
cost(f,g)
  >= |pre(f)| + mid(f) + |out(g)|
  >= min_f (|pre(f)| + mid(f)) + min_g |out(g)|.
```

The 340-orbit scanner computed this separated lower bound in addition to the original same-orientation best LB. For **every one of the 340 exact orbits**, the separated lower bound is exactly equal to the original best LB:

```text
same LB tier   separated-LB range   orbits with separated LB <=36
31             31..31               3
32             32..32               5
33             33..33               4
34             34..34              13
35             35..35              25
36             36..36              39
37             37..37               0
38             38..38               0
39             39..39               0
```

Thus all 251 orbits in tiers LB37–39 are excluded from a 101 retained-core circuit even after complete front/final orientation decoupling, before any helper-network reasoning is needed.

## Exact treatment of the 89 separated-LB <=36 orbits

The only potentially relevant orbits are exactly the original 89 same-orientation survivor orbits in tiers 31–36.

### LB31 — 3 orbits

- A/live representative: already excluded by `prove_joint_decoupled_frontier.cpp`; its regression is independently Action-verified.
- B/C representatives: locally exact exclusion recorded in `JOINT-DECOUPLED-LB31-BC.md`.
- The broader front/final orientation vectors were independent.

### LB32 — 5 orbits

Recorded in `JOINT-DECOUPLED-LB32.md`.

All five helper-aware frontiers contained only score-36, distance-zero rows. A generic exact score-36 checker (`prove_joint_decoupled_score36_instance.cpp`) restored exact correction bytes and exact <=2-helper linear closure. All 206 frontier rows were excluded. A separately written Python implementation reproduced every final statistic exactly.

### LB33 — 4 orbits

Recorded in `JOINT-DECOUPLED-LB33.md`.

The initial zero-helper screen left 3,549 / 4,801 / 5,287 / 5,689 decoupled pairs for the four representatives, but exact one-helper target closure eliminated all of them:

```text
helper_frontier = 0  for all four representatives.
```

### LB34 — 13 orbits

All 13 representatives were scanned locally with the same generic exact helper-aware frontier. Their zero-helper `pass0` counts were:

```text
36, 48, 69, 24, 54, 53, 39, 71, 66, 60, 36, 44, 102.
```

Every representative had

```text
helper_frontier = 0.
```

### LB35 — 25 orbits

All 25 representatives had already

```text
pass0 = 0,
helper_frontier = 0.
```

No exact helper or correction search was needed.

### LB36 — 39 orbits

Likewise, every one of the 39 representatives had

```text
pass0 = 0,
helper_frontier = 0.
```

## Consequence

The complete 2040-transform semilinear retained-core family is excluded from 101 gates not only in the original same-orientation formulation, but in the strictly broader formulation where the front norm-product orientations and final-product/output orientations are chosen independently.

This is a search-space exclusion, not a global lower bound for the AES S-box. It keeps fixed:

- the retained 18-gate inversion core;
- the underlying nine rank-two product planes associated with that construction;
- the semilinear field-transform family `c*x^(2^k)`;
- the middle-column/core-factor interface up to the already proved exact automorphisms.

A 101-gate circuit can still exist outside this representation.

## Research implication

Further scaling of the same semilinear/product-plane outer search is no longer justified. The next work should change the search space. The main live directions are:

1. the unresolved fixed-interface 17-gate core family: one of 16 rank-four zero-state completions, six independent ANDs, final nonlinear quotient rank six, and at most 11 XOR/XNOR gates (23,970 reachable envelope union); or
2. a genuinely joint middle/core/interface redesign in which the four core inputs and/or final factor interface are allowed to change and their linear costs are optimized together; or
3. a different algebraic decomposition of inversion rather than the retained nine-product / 18-core / eighteen-final-product architecture.

The direct-core route should not be attacked by brute-forcing all 23,970 envelopes independently; existing handoff notes show that quotient-only lower bounds are too weak. A stronger representation of physical linear-form cost is needed.
