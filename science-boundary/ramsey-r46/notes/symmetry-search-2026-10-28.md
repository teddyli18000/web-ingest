# Symmetry search notes — 2026-10-28

## Exact abelian Cayley exclusion

All undirected Cayley graphs on all four abelian group isomorphism types of order 36 were exhaustively checked and none is a `(4,6)` graph.

| group | inversion orbits | connection sets | K4-free | valid `(4,6)` |
| --- | ---: | ---: | ---: | ---: |
| `C36` | 18 | 262144 | 17859 | 0 |
| `C4 x C3 x C3` | 18 | 262144 | 25614 | 0 |
| `C2 x C2 x C9` | 19 | 524288 | 25529 | 0 |
| `C2 x C2 x C3 x C3` | 19 | 524288 | 34340 | 0 |

Total group-specific connection sets: 1,572,864. `abelian_cayley36.cpp` and the independent `abelian_cayley36_check.py` agree exactly on every row. The `C36` row independently reproduces the earlier circulant result. See `results/abelian-cayley36.json`.

This is a restricted-family exclusion only; the same abstract graph may appear in more than one group row, but duplication cannot invalidate completeness for each group type.

## Wider semiregular cyclic symmetry

`semiregular_sat.py` removes the Cayley/regular-action requirement. For each divisor `m` of 36 it fixes an automorphism consisting of `36/m` disjoint cycles of length `m`, identifies edge variables along its orbits, and adds the complete K4 / independent-6 CNF. This is an exact decision problem for that automorphism class.

Initial exact lanes use orders 6, 9, 12 and 18. Their edge-variable counts are respectively 108, 70, 54 and 36. For example:

- order 18: 36 variables, 3,093 distinct K4 clauses, 102,612 distinct independent-6 clauses;
- order 12: 54 variables, 4,806 K4 clauses, 158,002 independent-6 clauses;
- order 9: 70 variables, 6,469 K4 clauses, 211,918 independent-6 clauses;
- order 6: 108 variables, 9,771 K4 clauses, 322,787 independent-6 clauses.

The one-shot workflow `.github/workflows/temp-ramsey-r46-semiregular-sat.yml` runs pinned Kissat and automatically decodes and sends any SAT model through the authoritative Few Shots verifier. Run `40613531660` was queued when this note was written.

## Degree-17 automorphism refinement

The seven complete `(3,6,17)` neighborhood representatives have automorphism-group sizes `[1, 2, 2, 2, 2, 8, 2]` (independent NetworkX enumeration of the pinned graph6 catalogue). `degree17_static_sat_v3.py` adds a sound first-B-row Aut(A) lex leader on top of v2. Index 5 has the only substantial symmetry group (order 8), so a dedicated v3 index-5 lane was launched rather than duplicating all seven v2 jobs. Run `40613113896` was queued when this note was written.

## Tatarevic 2014 structured near-miss

Milos Tatarevic's 2014 public note gives a 35-vertex block-circulant starting matrix built from eleven `7x7` circulants. Reconstructing the red/complement graph gives exactly `K4=0` and `I6=7`, matching the note. The seven independent 6-sets were reproduced exactly.

This is a useful literature lead but not immediately a better 36-vertex basin: with the 35 old vertices frozen, a 35-binary exact attachment formulation for a new vertex is infeasible if it is required to create no new K4/I6 conflicts. A quick independent tabu experiment allowing all 36-vertex edges to move reached only 25 defects, worse than the retained 14-defect incumbent. Do not prioritize this seed without a materially stronger repair formulation.

Source: https://mtatar.wordpress.com/2014/08/21/ramsey46/
