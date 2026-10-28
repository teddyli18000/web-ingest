# Two-page / two-tree structural decomposition of p010

## Statement (standard planar topology, specialized to the published instance)

Let G be the connected plane graph of the 248,972 candidate edges in Cook–Helsgaun–Hougardy–Schroeder's ElimTSP reduction, and let C be Nagata's known Hamiltonian cycle (100,000 edges). The 2026-10-28 action verified G is planar and contains every edge of C.

Because C is a Jordan curve through **all** vertices, every remaining edge is a noncrossing chord **on exactly one of its two sides**. Thus G is a two-page book embedding with the cyclic vertex order fixed by C. The two-page characterization of planar Hamiltonian graphs is classical, not claimed as a novel theorem (Bernhart–Kainen 1979 and later book-embedding literature).

A more useful equivalent statement is that removing from the planar dual G* the 100,000 edges dual to C splits G* into **exactly two trees**, one per side of C.

**Proof.** Jordan's theorem says interior and exterior of C are two disks. The dual faces in each disk are connected through non-C edges: a path staying in one disk can cross candidate chords but not C. Every non-C chord splits exactly one disk face into two, and in the dual adds one vertex and one tree edge; induction shows the induced dual on each side is a tree. Alternatively, dual restricted to non-C edges has two connected components, contains |E|-|C|=148,972 edges, and |F|=|E|-|V|+2=148,974 vertices; hence it is a forest with exactly two trees.

This uses only the **embedding and the existence of C**; it does **not** assert the original complete metric TSP was solved, or prove the elimination certificates correct. It gives an exact reparameterization of *all tours contained in this sparse graph*.

## Why this is relevant after exact negative patches

Single-face improvements produce 2-factors with two subtours. Exact radius-3/4/5 dual patches around top positive faces (18 solved instances) were infeasible for any strictly improved tour, even though their unconstrained 2-factors were cheaper. Since each face graph of non-C edges is a tree, **growing a radius ball around a single favorable face is a structurally poor choice**: it may omit distant compensating changes across the two face trees. The first global two-edge reconnect search found multiple equal-score tours that differ in the baseline edge set and thus expose a neutral network for traversing barriers.

Proposed next formulation (not yet evaluated): solve a *paired subtree* problem on the inside and outside dual trees. Decision: choose face-spin labels on two small but possibly **nonlocal** subtrees. Objective: exact integer difference sum_e (1-2b_e) w_e (y_left XOR y_right). Local degree: sum_incident (1-2b_e)(y_left XOR y_right)=0. Global constraint: boundary consists of exactly one cycle. State decomposition may use noncrossing boundary pairings / Catalan-type connectivity states, rather than generic subtour cuts.

A diagnostic worth computing before an algorithmic campaign: distribution of tree depths, branching, and how strongly the candidate chords couple the two sides along the cyclic order. This would inform separators rather than guessing geographic patch radii.

## Important distinction from 2026 prior art

Arslanoğlu (2026), *A Surface-Based Formulation of the Traveling Salesman Problem*, already develops an exact triangle-surface boundary MILP with connectivity and Euler-characteristic constraints. We are **not** claiming the surface or duality viewpoint as new. This direction targets a stronger *instance-specific decomposition*: an elimination-certified planar graph **with a known spanning Jordan cycle** provides two actual dual trees and an integral reference solution, potentially enabling nonlocal coupled-subtree DP. Novelty/performance would need independent comparison, not rhetoric.

## Evidence and sources

- Public graph: https://github.com/bicobico2/ElimTSP/blob/main/results/mona.248972.edg.gz
- Independent graph/route audit: https://github.com/teddyli18000/web-ingest/actions/runs/40688199531
- Exact local face-patch negative results: https://github.com/teddyli18000/web-ingest/actions/runs/40690007833
- Distinct equal-score alternate tours: https://github.com/teddyli18000/web-ingest/actions/runs/40690889447
- Cook et al. (2024), https://doi.org/10.1007/s12532-024-00262-y
- Arslanoğlu (2026), https://arxiv.org/abs/2603.00075
- Book thickness / two-page characterization: https://mathworld.wolfram.com/BookThickness.html

## Falsifiers and limitations

- A nonplanar graph or an omitted baseline edge would invalidate the precise two-tree decomposition; neither occurred in the cited full-graph test.
- Two trees do **not** imply bounded treewidth of G or a polynomial-time exact TSP algorithm.
- The published elimination graph is only a usable heuristic restriction for an upper-bound search until its globally valid elimination guarantees are independently checked; the original p010 verifier remains the judge for any tour.
