# m220, n11=6, seq3 — exact exclusion by extreme packing and high-degree capacity

## Statement

There is **no** K4-free 36-vertex graph with independence number at most five,
220 edges, and degree sequence **11^6 12^18 13^10 14^2**.

This eliminates one degree sequence, **not** all graphs with 220 edges;
it is not a new Ramsey lower or upper bound.

## Sound prerequisites

The post-audit universal n11=6 low-graph census proves that the six
degree-11 vertices L induce exactly one of the two graphs with total internal
degree R=22 or 24. Their graph6 codes are Ep~o and EznW, respectively.
For both, alpha(L)=2 and there are no low-to-high edges (degrees 13 or 14).
The proven m220 local extrema imply S(v)=sum_{w in N(v)} d(w) satisfies
S(12)<=147 and S(13)<=164. An extreme degree-13 vertex with S=164 has
exactly e(A)=32 in its 13-point neighborhood and e(B)=88 in its
22-point nonneighborhood; this follows from S=m+e(A)-e(B), e(A)<=32,
e(B)>=88. The three B88 graph6 members are the complete published
edge-88 stratum of R(4,5,22). Ordered member SHA256:
cdb6bbe20c73cd578590d57d896a343fceed76f5216d2a8524ccd1afd9559fb8.

## Extreme vertex packing

For each induced six-vertex degree profile matching L, enumerate vertices of
B88 outside L that are completely anticomplete to L. Exact profile-superset
scans yield the maxima [3,2,2] for R=22 and no six-vertex candidate for R=24.
In the only R=22 type with three such vertices, **those three induce a
triangle** (12 instances, all checked). These facts hold even for the
degree-profile superset without requiring an isomorphism test.

Let v be an extreme degree-13 vertex, and k its number of degree-14 neighbors.
No low vertex is adjacent to v. Relative to degree 12,
164 = 13*12 + d_13(v) + 2k,
so d_13(v)=8-2k. Its high nonneighbors among the other nine degree-13
vertices and two degree-14 vertices number
(9-(8-2k))+(2-k) = 3+k.
They are anticomplete to L, so the B88 packing forces R=22 and k=0.
Consequently v is adjacent to eight of the other nine degree-13 vertices,
to neither degree-14 vertex, and its three high nonneighbors
{u,a,b} (u degree 13, a,b degree 14) form a triangle.

There cannot be two extreme degree-13 vertices:
- If v,w were nonadjacent, w=u would be adjacent to both a,b, contradicting
  the requirement k=0 for every extreme vertex.
- If v,w were adjacent, then at least six of the other eight degree-13 vertices
  would be common neighbors. They must be independent to avoid K4 with vw,
  contradicting alpha(G)<=5.

Thus among ten degree-13 vertices at most one is extreme. Writing
D=10*164-S_13, at least nine have deficit >=1, so D>=9. The class-edge
handshake identity below makes D even, forcing **D>=10**.

## Contradictory global capacities

Write x=e(13,13), y=e(13,14), z=e(14,14) in {0,1}.
For R in {22,24}, class handshakes give

    c=e(11,12)=66-R
    a=e(12,13)=130-2x-y
    b=e(12,14)=28-y-2z
    p=e(12,12)=(R-8)/2+x+y+z
    S_13=1560+2(x+y)
    D=1640-S_13=80-2(x+y) [even]
    S_12=11c+24p+13a+14b=2632+R+D-y-4z

By S_12<=18*147=2646,

    y+4z >= R+D-14 >= 22+10-14 = 18.            (1)

Let H be the induced graph on the ten degree-13 plus two degree-14 vertices.
Because L has an independent pair and is anticomplete to H, alpha(H)<=3.
H is also K4-free.

- If z=0, each degree-14 vertex has a triangle-free neighborhood in H
  of independence number <=3. By R(3,4)=9 each has <=8 high neighbors,
  and **y<=16**.
- If z=1, the degree-14 vertices a,b are adjacent. Their common
  degree-13 neighbors are pairwise nonadjacent (otherwise a K4).
  There are at least y-10 such vertices, while alpha(H)<=3, so
  **y<=13**.

Therefore in either case y+4z<=17, contradicting (1). QED.

## Reproduction

From science-boundary/ramsey-r46/:

    python m220_n11_6_seq3_high_packing_verify.py
    g++ -std=c++17 -O2 -Wall -Wextra m220_n11_6_seq3_independent.cpp -o /tmp/r46seq3
    /tmp/r46seq3

Independent Python (column-major graph6 bitsets) and C++ decoders both
yield B88 maxima [3,2,2], R24 zero candidates, and the 12 K3 triples.
The independent class-matrix supersets contain 170, then 10 with D>=10,
then zero meeting the high-capacity bound. The algebra above does not need
the 170 enumeration; it makes the contradiction explicit.

Frozen output: results/m220-n11-6-seq3-high-packing-post-audit.json.

No invalidated 2026-10-30 row-domain predicate, SAT timeout, or search heuristic
is used. As of this proof, only seq1 and seq2 remain within the
n11=6 / m=220 structural layer; other m220 degree classes remain open.
