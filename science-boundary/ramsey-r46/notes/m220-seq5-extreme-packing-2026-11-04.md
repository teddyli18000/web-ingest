# m220, n11=6, sequence 5 — exact extreme-packing exclusion

## Statement (2026-11-04)

There is no 36-vertex graph with 220 edges, no K4 or independent
6-set, and degree sequence **11^6 12^19 13^8 14^3**.

This excludes **one degree sequence**, not every graph with 220 edges.
No construction or improved public Ramsey bound is claimed.

## Validated prerequisites

- The post-audit universal six-low-vertex census forces
  R = Σ_(d(v)=11) (132-S(v)) to equal **22** or **24**, with
  the unique induced low graphs respectively graph6 Ep~o and EznW.
  In both cases, R equals the total degree within the low induced
  graph, so no low vertex meets a degree-13 or degree-14 vertex.
- The independently certified endpoint caps at m=220 are
  S(12)≤147, S(13)≤164, S(14)≤178.
- For a degree-13 vertex with S=164, its 13-neighborhood has
  exactly 32 edges, and its 22-nonneighborhood has exactly 88 edges.
  All three nonisomorphic B88 possibilities come from McKay's
  complete extreme-edge (4,5,22) catalogue, with ordered graph6
  member SHA256:
  `cdb6bbe20c73cd578590d57d896a343fceed76f5216d2a8524ccd1afd9559fb8`.

## New packing lemma

The six low vertices all lie in B, the nonneighborhood of any
degree-13 vertex. For any induced copy of the R=22 low graph
(degree sequence 3,3,4,4,4,4) inside a B88 graph, enumerate the
vertices of B outside that copy having no edges to any low vertex.
Across the complete three B88 graphs the maximum number is
respectively **3, 2, 2**.

For the R=24 low graph (degree sequence 4^6), there are **no**
induced degree-profile candidates in any B88 member.

Let v be a degree-13 vertex with S(v)=164, and let k be the number
of its degree-14 neighbors. Since all other neighbors have degrees
12 or 13 (never 11), and its S(v)=164,

    164 = 13*12 + d_13(v) + 2*k,
    d_13(v) = 8-2*k.

There are exactly ten other vertices in the high induced graph H
(8 degree-13 and 3 degree-14 vertices altogether). Exactly

    10 - (d_13(v)+k) = 2+k

of those ten are nonneighbors of v. All these high nonneighbors lie
in B and are anticomplete to the six low vertices. The B88 packing
bound is three, so k≤1. Since there are only seven other degree-13
vertices, k=0 would require d_13(v)=8 and is impossible. Hence
**every extreme degree-13 vertex has exactly one degree-14 neighbor**.

## Class-handshake exhaustion

Write x=e(13,13), y=e(13,14), z=e(14,14).

    e(11,12)=66-R
    e(12,13)=104-2*x-y
    e(12,14)=42-y-2*z
    2*e(12,12)=228-e(11,12)-e(12,13)-e(12,14)
    S_12=11*e(11,12)+24*e(12,12)+13*e(12,13)+14*e(12,14)
    S_13=1248+2*x+2*y
    S_14=504+y+4*z

Enumerate all nonnegative integer edge-class counts satisfying the
handshakes and endpoint S intervals. Exactly **84** matrices remain:
54 at R=22 and 30 at R=24.

Define the nonnegative integer deficit

    D=8*164-S_13=64-2*(x+y).

Every surviving matrix has D in {0,2,4,6}. Therefore at least
8-D of the eight degree-13 vertices have S=164. Each such
extreme vertex has exactly one degree-14 neighbor. Counting
13–14 edges gives

    y ≤ (8-D)*1 + D*3 = 8+2*D.

When z=3, the degree-14 vertices form a triangle; K4-freeness
then prohibits any degree-13 vertex from meeting all three, and

    y ≤ (8-D)*1 + D*2 = 8+D.

**All 84** class matrices violate the applicable inequality.
The smallest excess y minus its upper bound is exactly **1**.
Thus every class matrix is excluded.

## Reproduction and independence

From `science-boundary/ramsey-r46/`:

    python m220_n11_6_seq5_extreme_packing_verify.py > /tmp/seq5.json
    g++ -O2 -std=c++17 m220_n11_6_seq5_independent.cpp -o /tmp/seq5_verify
    /tmp/seq5_verify

The Python verifier checks exact induced copies by NetworkX graph
isomorphism; the independent C++ verifier decodes graph6 bits
itself and scans the degree-profile *superset* of possible induced
copies. Both give profile counts 28,22,44 (R=22) and zero (R=24),
with anticomplete maxima 3,2,2. Both independently enumerate all
84 class matrices and check the positive contradiction margin.

Frozen detailed output:
`results/m220-n11-6-seq5-extreme-packing-post-audit.json`.

No withdrawn row-domain `tf()` predicate, SAT timeout,
or unvalidated whole-graph search result is used.

## Frontier

Among fourteen m220 candidates with exactly six degree-11 vertices,
only **seq1, seq2, and seq3** remain. Many other m220
degree-class layers are still open, and no verified 36-point
construction has been obtained.
