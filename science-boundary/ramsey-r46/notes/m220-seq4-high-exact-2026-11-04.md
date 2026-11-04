# m220 n11=6 seq4 — complete post-audit high-subgraph exclusion

## Statement

No (4,6)-graph on 36 vertices with exactly 220 edges has degree
sequence **11^6 12^18 13^11 15** (seq4 in the n11=6 catalogue).

This is an exclusion of **one degree sequence**, not of every 220-edge
graph and not an improvement of the public lower bound for R(4,6).

## Reproduction

From science-boundary/ramsey-r46:

    python m220_n11_6_seq4_t_catalog_verify.py
    python m220_n11_6_seq4_b88_embed_verify.py
    g++ -O3 -std=c++17 m220_n11_6_seq4_high_exact.cpp -o /tmp/m220_seq4
    /tmp/m220_seq4

The local compile/run of the exact C++ verifier completed in approximately
8.3 seconds. Frozen output: results/m220-n11-6-seq4-high-exact-post-audit.json.

## Earlier certified inputs

1. The post-audit n11=6 low-graph census permits only R=22 and R=24,
   represented by Ep~o and EznW. In both, the six 11-degree vertices
   have no edges to the degree-13 or degree-15 classes, and include
   an independent pair.
2. The previous exact class-edge/anchor verifier
   m220_n11_6_seq4_high_anchor_verify.py excludes 28 of 32 patterns,
   leaving four patterns with (x,y)=(e13_13,e13_15):
   (29,8), (30,8), (31,7), (30,8). The duplicated (30,8)
   has two different low-class connection matrices.
3. The unique extreme 13-point neighborhood A32 and the complete three
   B88 non-neighborhood graphs were checked in
   m220_n11_6_seq4_b88_embed_verify.py. Precisely four sites in one B88
   graph are compatible with another nonadjacent extreme degree-13
   vertex, and these four sites induce 2K2; the other two B88 graphs
   have no eligible sites. Their ordered graph6 member SHA256 is
   cdb6bbe20c73cd578590d57d896a343fceed76f5216d2a8524ccd1afd9559fb8.
4. The complete (3,4)-graph catalogue contains nine 7-vertex types
   and three 8-vertex types. The separate Python verifier reconstructs
   them from the complete 7-vertex graph atlas (and all 2^7
   eighth-vertex neighborhoods), rather than trusting hardcoded
   enumeration alone.

## Sound necessary conditions

Let H be the graph induced on the eleven degree-13 vertices and the
unique degree-15 vertex z. Since the low set has an independent pair
and has no H edges, alpha(H)<=3; H is also K4-free. Write
T=N_H(z), |T|=y, and U=V(H)\(T union {z}).
Then H[T] is triangle-free with alpha<=3, so T is one of the
complete nine or three catalogue types.

For a degree-13 vertex v of H, the full-graph neighbor-degree sum is

    S(v)=156+d_{H[13]}(v)+3*[vz] <=164.

Call v extreme if equality holds. If w is another extreme 13-vertex
not adjacent to v, then w lies in the B88 non-neighborhood of v,
and B88[N_B(w)] must embed as an induced subgraph of the unique A32.
Hence all such w, for a fixed extreme v, lie inside the four eligible
sites inducing 2K2. Thus the extreme non-neighbors of v must form an
induced subset of 2K2: size<=4, any triple induces exactly one edge,
and any four induce two disjoint edges.

For each (x,y), the C++ verifier considers every H[T] type, every
graph on U, and every bipartite T--U adjacency matrix with exactly x
13--13 edges and the above individual S(v) caps. It checks the exact
K4/I4 obstruction on H (every four vertices have 1..5 induced
edges), then the induced 2K2 condition. This is a relaxation of the
full 36-vertex problem, so a zero-survivor result is sound.

| x | y | T types | Degree-feasible labelled configurations | K4/I4 feasible | B88-compatible |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 29 | 8 | 3 | 770466 | 13647 | **0** |
| 30 | 8 | 3 | 125628 | 708 | **0** |
| 31 | 7 | 9 | 15577688 | 2256 | **0** |

The two x=30,y=8 class matrices share the same high-only subproblem.
All four class matrices are therefore excluded.

## Independent checks and limitations

The Python graph-atlas verifier independently proves the 7/8-vertex
catalogue lists complete. The B88 verifier tests all three complete
source graphs by two independent induced-isomorphism methods. A
separate Python high-graph enumeration also reproduces the C++
(x,y)=(30,8) pre-B88 count of 708 and the first T-type of
(29,8) (912 K4/I4 candidates). The complete C++ enumeration
covers all three subproblems.

One unsuccessful alternative was a direct 77-binary-variable MILP
with activation constraints for extreme vertices. It timed out and
is not used as proof.

**Do not resurrect the withdrawn row-domain tf() predicate.**
The present exclusion uses no inference from that code, no broad
36-vertex SAT, and no unverified external compute job.

## Next frontier

Among the fourteen m220,n11=6 degree sequences, indices 6–14 and
now index 4 are excluded; **1,2,3,5 remain**. The global m220
edge layer remains unclosed, and no 36-vertex witness was found.
For those remaining sequences, repeat the same small H/T/U
decomposition only where the class-edge data force many extreme
vertices. Otherwise reconsider the graph decomposition rather than
running further high-neighborhood SAT timeouts.

## Sources

- Brendan McKay, complete Ramsey (3,4) catalogues and extremal
  (4,5) graphs: https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
- Repository certificates:
  results/m220-n11-6-seq4-high-anchor-post-audit.json,
  results/m220-n11-6-seq4-b88-embedding-post-audit.json,
  results/m220-n11-6-seq4-high-exact-post-audit.json.
