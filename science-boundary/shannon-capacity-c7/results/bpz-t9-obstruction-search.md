# BPZ t=9 obstruction search

Status date: 2026-10-28.

## Target construction

The Buys--Polak--Zuiddam / Tan five-dimensional gadget yields a 10-dimensional construction of nominal size

`367^2 + 9^2 = 134,770`

provided one can supply a 367-point independent auxiliary set `X ⊂ C7^⊠5` avoiding the structural obstruction

`D = N(P_H) ∩ N(P_V)`

for one of the valid `t=9` private-pair/orientation witnesses.  Every claimed 10D candidate from this route must still be checked by the Few Shots p004 verifier.

Pinned public inputs used here:

- `tandonravi/C7-Shannon-Capacity-Heterogeneous-Recursion@c753408492dde92a239708986d16c15dbf6c3235`;
- `molind/c7-five@ae81e0d24b356aef3d388238f6fb4d02c4aa32a5`;
- Few Shots p004 verifier/baseline fetched read-only at run time.

`code/bpz_t9_aux_translation_fft.py` reconstructs the complete 243-state private-neighbour component of the BPZ 367-set, enumerates 640 raw private-pair/orientation witnesses, and deduplicates them to 160 distinct obstruction masks.  Its `build` routine replays any obstruction-free auxiliary and constructs the seven product blocks of the 134,770-point certificate.

## Exhaustive translation scan of the original 38 public auxiliary seeds

The initial library consists of BPZ `X`, BPZ `I0`, and 36 public Family-F states.  For each of 38 seeds and each of 160 obstruction masks, FFT correlation was used to evaluate all `7^5 = 16,807` translations.  Every FFT zero or near-zero used later was replayed in integer coordinates.

No zero intersection was found in the `38 × 160 = 6,080` seed/obstruction cases.  The exact minimum-hit histogram was:

- hit 1: 20 cases;
- hit 2: 30;
- hit 4: 30;
- hit 5: 60;
- hit 6: 10;
- hit 8: 58;
- hit 9: 112;
- hit 11: 144;
- hit 12: 560;
- hit 13: 2,722;
- hit 14: 2,334.

Thus the strongest public translated near states miss an obstruction-free 367-set by exactly one point.

## Exact repair of the 20 one-hit translated near states

For each unique translated near state `S`, the unique point `x ∈ S ∩ D` is mandatory to remove.  A radius-`k` repair removes `x` plus at most `k-1` other old points and adds `k` new mutually nonconfusable points outside `D`, preserving a 367-point independent set.

The following layers are exact negative results for all 20 one-hit states:

| repair radius | exact method | result |
| --- | --- | --- |
| 1-for-1 | delete the unique obstruction hit and exhaust all ambient replacements | no replacement candidate at all |
| 2-for-2 | exact support groups for each second removal | 7,320 deletion pairs; 50 candidate pools of size two; every candidate pair conflicts |
| 3-for-3 | exact support-union enumeration | 1,335,900 deletion triples; 21,400 pools with at least three candidates; 15,866 candidate triples; none works |
| 4-for-4 | exact owner-union DFS | 31,060 external candidates; 41,395 DFS nodes; no compatible terminal quadruple |
| 5-for-5 | `exchange_dfs.cpp`, blocker budget 4 | all 20 cases complete/exhausted; no witness |
| 6-for-6 | blocker budget 5 | all 20 cases complete/exhausted; no witness |
| 7-for-7 | blocker budget 6 | all 20 cases complete/exhausted; no witness |
| 8-for-8 | blocker budget 7 | all 20 cases complete/exhausted; no witness |

The blocker-budget formulation is exact.  After pre-deleting the mandatory bad point, every candidate addition is labelled by the set of retained old vertices that conflict with it.  A radius-`k` repair is exactly an independent `k`-set of candidate additions whose blocker union has size at most `k-1`.  The pinned `molind/c7-five/search/exchange_dfs.cpp` solver searches this condition directly.

Representative complexity growth:

- radius 6, case 15: 7,802 candidate additions, 333,692 DFS nodes, complete/exhausted in about 0.26 s of core search;
- radius 7, case 15: 11,500 candidates, 3,663,775 nodes, complete/exhausted in about 7.1 s;
- radius 8, case 8: 14,203 candidates, 40,839,098 nodes, complete/exhausted in about 68 s.

The exact radius-9 run (budget 8) is still in progress for the harder cases as of this note.  Completed cases have produced no witness.  Do not convert an Action timeout into an UNSAT claim: `status=exhausted` or a verified witness is required for mathematical completeness.

A separate radius-10 workflow uses blocker budget 9, the maximum accepted by the pinned C++ solver.  It uses an isolated driver patch because the durable Python driver currently validates budgets only through 8.  Its results are not included here until the jobs complete.

## Other auxiliary libraries

### Full 243-state BPZ private-neighbour component

Every state of the complete 243-state independent private-swap component of BPZ `I0` was used as an auxiliary seed, with all 160 obstructions and all translations.  This is `243 × 160 = 38,880` seed/obstruction cases.  No zero was found; the global minimum hit was 8.  The histogram was 11,340 cases at hit 8 and 27,540 at hit 9.  This component is therefore much less promising as an auxiliary family than the original hit-1 seeds.

### Wustep 108-state private-pair plateau

The eight documented private-neighbour exchanges in `wustep/maths@d1633472321b27d4a5e93a5a27ccc98a19ee5af4` generate 108 independent states among the 256 swap subsets.  Scanning all 108 states, 160 obstructions, and all translations found no zero; the global minimum hit was 8.  This family is also low priority in its tested coordinate orientation.

### Archived `c7-five` source bundle

An inventory of `archive/source.tar.gz` searched for the historical Family A/B/C/D/E/F 367-word seed files and for any standalone 367-word text file.  None of those word files are present in the portable archive, so that archive alone does not expose new explicit 367-set seeds.

A separate portable-witness extraction attempt from `core-overlap.json.gz` and `verify/u1.py` / `verify/u2.py` initially failed at the extraction/driver layer.  That failure is an engineering failure, not a combinatorial negative result; a diagnostic rerun is pending.

## Complementary construction search

`code/bpz_t9_neutral_walk.py` is a heuristic (not a proof) intended to leave the fixed-radius basin.  It performs legal neutral 1-for-1 and 2-for-2 moves among 367-point independent sets while keeping obstruction hit at most one, tracking visited states.  A zero-hit state would immediately be materialized into the 134,770 construction and sent to the Few Shots verifier.  Exact-radius negatives above motivate this basin-escaping line.

## Interpretation

The BPZ t=9 route is much closer to a breakthrough than the original strict ninth-port SAT formulation in the sense that translated public auxiliaries attain obstruction hit one.  However, those hit-one states are highly locally rigid: exact repair is now ruled out through radius eight for all 20 translated near states.

The most useful next evidence is therefore one of:

1. a new 367-point auxiliary from a different global basin / coordinate orbit whose translated obstruction hit is zero;
2. a successful far neutral walk that escapes the exact radius-eight basin while preserving 367 points;
3. a radius-nine or radius-ten exact witness, if the deeper blocker-budget searches remain computationally tractable;
4. a stronger global search for a 367-point independent set in `C7^⊠5 \ D`, preferably seeded by the hit-one states but not confined to their local exchange balls.
