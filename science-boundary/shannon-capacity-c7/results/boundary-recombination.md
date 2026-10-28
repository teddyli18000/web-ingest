# Exact recombination of 134,753-point C7^10 boundary states

Status: 2026-10-28.  These are exact negative results for the stated union families, not a proof that `alpha(C7^10)=134753`.

## Formulation

For two independent sets `A,B`, every conflict edge inside `A union B` lies between `L=A\B` and `R=B\A`.  Hence the difference conflict graph is bipartite and

`alpha(A union B) = |A union B| - nu`,

where `nu` is the exact maximum matching size (Konig's theorem).  The durable solver `code/recombine_two_independent_sets.py` enumerates every cross-conflict edge by a base-7 confusability trie, computes an exact Hopcroft-Karp maximum matching and alternating minimum vertex cover, and replays every kept cross edge before materializing a candidate.

## Public pre-exchange J vs J+

The pinned Tan/BPZ source constructs `J+` from the pre-exchange 134,753-point `J` by exactly eight exchanges.  Its own construction code verifies each inserted point conflicts in the raw pre-exchange `J` with exactly the corresponding removed point.  Therefore the difference conflict graph is exactly eight disjoint edges and has matching size 8.  Exact recombination remains 134,753.

Reusable materializer: `code/bpz_j_jplus_pair.py`.

## Few Shots baseline vs J+

Action run `40650228212`, job `122688333663` independently Few-Shots-verified both inputs at 134,753 and then computed:

```json
{"common":1027,"cross_conflict_edges":3931176,"left_only":133726,"right_only":133726,"matching_size":133726,"min_vertex_cover_size":133726,"recombined_score":134753,"gain_over_best_input":0,"unmatched_left":0,"unmatched_right":0}
```

The matching is perfect on the complete difference sets, so this union cannot beat the record.

Input canonical hashes:

- Few Shots baseline: `650b05567deb26a339a788674dce5a36cba3beaeafe2c6daae631bed481b0df8`
- J+: `ac593f1040cef29621bfe705305359360ca58cb47fa1482ae810a51ca9b16b95`

## Few Shots baseline vs pre-exchange J

Action run `40650506846`, job `122689218100` independently Few-Shots-verified both inputs at 134,753 and computed:

```json
{"common":1024,"cross_conflict_edges":3931291,"left_only":133729,"right_only":133729,"matching_size":133729,"min_vertex_cover_size":133729,"recombined_score":134753,"gain_over_best_input":0,"unmatched_left":0,"unmatched_right":0}
```

Again the difference matching is perfect.

Pre-exchange J canonical hash: `d2c7b31da0d20e22345b212729c29feaabd8d5fa74442ccc9316f220895c9345`.

## Neutral2 exact rank-3 tie vs Few Shots baseline

`code/neutral2_rank3_tie_seed.py` deterministically rebuilt the historical rank-3 MaxSAT optimum using pinned `R367.txt`, exact RC2, and forced score 134,753.  The resulting certificate was independently accepted by the Few Shots verifier with canonical hash

`3b3a3a6c08418d604c530e3dccd188e8b4beabf986016af08040e19b6fd59e81`.

Action run `40650437576`, job `122689008049` computed:

```json
{"common":131281,"cross_conflict_edges":14307,"left_only":3472,"right_only":3472,"matching_size":3472,"min_vertex_cover_size":3472,"recombined_score":134753,"gain_over_best_input":0,"unmatched_left":0,"unmatched_right":0}
```

This is a much closer boundary pair than the BPZ/Few-Shots pairs, but its matching is still perfect.

## Neutral2 exact rank-3 tie vs J+

The same Action run computed:

```json
{"common":1088,"cross_conflict_edges":3903373,"left_only":133665,"right_only":133665,"matching_size":133665,"min_vertex_cover_size":133665,"recombined_score":134753,"gain_over_best_input":0,"unmatched_left":0,"unmatched_right":0}
```

Again exact perfect matching, no pairwise gain.

## New direction: multi-state union

Pairwise perfect matchings do **not** imply that the union of three or more independent sets has maximum independent set 134,753; the difference conflict graph is no longer bipartite in general.  This is a genuinely different search space from bounded exchanges.

`code/recombine_multi_independent_sets_maxsat.py` therefore removes the universal intersection (which is provably isolated in the whole union), constructs the exact remaining conflict graph with the same base-7 trie, and solves maximum independent set exactly with weighted MaxSAT/RC2.

The active experiment generates four distant 134,753 tie states by the deterministic private-pair-guided neutral plateau walk and solves the exact union MIS of `baseline + 4 ties`.  The original walk accepts thousands of legal neutral swaps (seed 48101 accepted 2,264 / 10,000 proposals and improved the radius-1 potential from 26 to 32), so these are not tiny one-exchange variants.
