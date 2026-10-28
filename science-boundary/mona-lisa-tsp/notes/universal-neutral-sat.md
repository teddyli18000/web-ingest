# Universal connectivity certificate for neutral tour switches

## Why pairwise-disjoint zero-cost swaps are not automatically independent

A p010 tour is an undirected Hamiltonian cycle on 100,000 vertices. We found
58 distinct neutral edge exchanges (each official-verifier length 5,757,191)
by enumerating all 12,281 alternating quadrilateral faces and all sparse-graph
two-edge connections of their split cycles. CP-SAT solved a maximum vertex-disjoint
subset of 51 exchanges among those 58 (the objective was `max number of moves`,
not `max number of provably commuting moves`). All exact tour evidence and
edge edits are in `../data/all-face-neutral-moves.json`.

Vertex-disjointness guarantees every switch combination still has degree two,
but **does not guarantee** that it is connected. Claiming `2^51` tours before
a universal connectivity proof would be invalid.

## An exact existential-disconnection SAT formulation

Let baseline tour be C, and suppose k available switches have baseline-removal
sets R_i and replacement sets A_i. All R_i and A_i use disjoint vertex
supports and each switch individually turns C into a different zero-cost
Hamiltonian cycle. Define Boolean `s_i` to mean switch i is applied.

1. Remove the edges in the union of all R_i from C. The remaining graph is
   a disjoint union of fixed paths; contract each path to one node.
2. Introduce a Boolean color `c_j` for each contracted node, representing
   membership in a purported proper component cut.
3. Force `c_0 = 0` and at least one other `c_j = 1`.
4. For every edge `uv` in R_i, impose `not(s_i) => c[u] == c[v]`.
   For every edge `uv` in A_i, impose `s_i => c[u] == c[v]`.

This is **satisfiable iff some subset of switches produces a disconnected
degree-two graph**. A satisfying assignment supplies an explicit counterexample:
construct the selected edge set and count its cycles. If UNSAT, *every* one
of the `2^k` subsets is connected and hence, by degree-two, a Hamiltonian
cycle.

Because all switches have disjoint edge supports and each has exact cost
delta zero, every such tour has exact EUC_2D score 5,757,191. Because each
switch changes at least one private edge, all resulting edge sets are distinct.
The number of equal-score tours is then exactly `2^k` within that family.

We do not claim this SAT encoding or the underlying topology is mathematically
novel; its usefulness is a compact universal certificate of an otherwise
astronomically large neutral set on the public Mona Lisa instance.

## Verification

- Main program: `../universal_neutral_connectivity.py`.
- CP-SAT searches existential disconnected assignments.
- Z3 independently repeats the satisfiability check before a claimed
  universal-connectivity result is accepted.
- On SAT, the program reconstructs and checks the disconnected full tour,
  prunes one implicated switch, and repeats to find a smaller provably
  universally connected family.
- An UNSAT result from finite-time exact solvers is a computational result;
  for a formal proof of UNSAT, a machine-checkable solver proof trace or a
  third independent exact solver would be a further strengthening.
- Original Few Shots official verifier is still required to score any new
  candidate as a record.

### Sources / artifacts

- [ElimTSP public sparse graph](https://github.com/bicobico2/ElimTSP/tree/main/results)
- [Complete alternating-face and repair experiment](https://github.com/teddyli18000/web-ingest/actions/runs/40696640556)
- [Independent unique-tour verification and max disjoint set](https://github.com/teddyli18000/web-ingest/actions/runs/40697064594)
