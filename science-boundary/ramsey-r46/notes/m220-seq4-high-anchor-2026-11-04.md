# m220 seq4: high-anchor obstruction (2026-11-04)

**Scope.** A hypothetical 36-vertex (4,6)-graph with 220 edges and degree
sequence `11^6 12^18 13^11 15`. This is a partial *necessary-condition*
reduction, **not** an exclusion of the whole degree sequence.

**Reproduce.** Run `python m220_n11_6_seq4_high_anchor_verify.py` from this
topic directory (requires NetworkX). Durable compact output:
`results/m220-n11-6-seq4-high-anchor-post-audit.json`.

## Certified inputs

- The post-audit low-graph census (file
  `results/m220-n11-6-universal-low-post-audit.json`) forces the six
  degree-11 vertices to induce either `Ep~o` (R=22) or `EznW` (R=24).
  In both, the low set sends **no** edges to degree-13 or degree-15 vertices.
  It contains an independent pair, so the induced high graph H
  (11 degree-13 vertices plus one degree-15 vertex) has alpha(H)<=3.
- For a degree-13 vertex v with S(v)=164, its neighbourhood is the unique
  (3,6,13) graph A32 (certified in
  `results/m220-a32-reconstruction-post-audit.json`). An independent
  8-subset of A32 with alpha<=3 is always cubic with 12 edges:
  1287 induced 8-subsets checked, 32 qualify, one degree/edge profile.
- R(3,4)=9.

## Exact reduction

The degree-class handshake and S caps give exactly **32** integer patterns
over R=22 or R=24. Let x=e(13,13), y=e(13,15), and
D=11*164-S13. At most D of the eleven degree-13 vertices have S<164.

**First obstruction:** y>=9 is impossible. The high neighbourhood of the
degree-15 vertex would be a triangle-free graph of order >=9 with alpha<=3.
This excludes 7 patterns.

**Second obstruction:** If 11-y>D, there is an extreme degree-13 vertex v
not adjacent to the degree-15 vertex z. The eight other degree-13 neighbours
W of v induce a cubic graph of 12 edges; the remaining degree-13 vertices
are p,q. Set s=e(z,W), h=e(z,{p,q}), t=e(W,{p,q}), b=e(p,q).
From the per-vertex S<=164 cap, t<=16-s. Hence

    e(H)=20+t+b+s+h <= 36+b+h <=39.

Equality would force b=1, h=2, t=16-s. Since S(z)<=189,
y=s+2<=9, giving s<=7 and t>=9. But the caps at p and q
force each to meet at most four W vertices, giving t<=8.
Contradiction; thus e(H)<=38. All 21 patterns with y<=8 and
11-y>D have x+y>=39 and are excluded.

Therefore exactly **four** class-edge patterns remain, with
(R,x,y,D)=(22,29,8,6),(22,30,8,4),(22,31,7,5),(24,30,8,4).

## Next target

For y=8, the high-neighbourhood of z is an 8-point (3,4)-graph, with
three isomorphism types (10/11/12 edges). For y=7 it is a 7-point
(3,4)-graph. Analyze each fixed high graph and its three/four
non-neighbours via exact high-only K4/I4 constraints and the near-extreme
d15-neighbourhood e(A)=35..37. Preserve every surviving pattern:
existence at this relaxed level does not certify a 36-point graph.

No claims from the withdrawn row-domain `tf()` CSP are used.
