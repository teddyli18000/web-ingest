# Full relative-translation rigidity of the public 367-word slice family

Date: 2026-11-04. Status: **exact, independently replayed exclusion for a specific structured family; no new p004 record**.

## Scope

Use 38 publicly available, independently verified 367-word `C7^5` independent sets: BPZ/Tandon `I0`, companion `X`, and all 36 `molind/c7-five` Family-F states. Pinned sources:

- BPZ/Tandon `c753408492dde92a239708986d16c15dbf6c3235`, `data/base_c7.json`.
- molind/c7-five `ae81e0d24b356aef3d388238f6fb4d02c4aa32a5`, `data/family-f.json`.

For each of five coordinate axes `k`, split every public code into its seven projected `C7^4` slices, maintaining their **original** symbol labels `s in Z7`. At each symbol label independently choose any one original slice template available at that label, then apply an **arbitrary** translation of all its four remaining coordinates, `p_s in Z7^4`. These shifts may vary separately with `s`; hence the family is strictly larger than global automorphism or fixed-seed choices.

Question: can any such 7-slice reconstruction have 368 or more points?

## Exact compatibility calculation

Let `A,B subset Z7^4` be two projected slice templates to be assigned to adjacent symbols `s,s+1`. With relative translation `delta=p_(s+1)-p_s`, the two translated slices have no cross-confusable pair iff

`delta notin union_{a in A,b in B} (a-b+{-1,0,1}^4)`.

This set is computed exactly as a 2,401-bit exclusion mask; no SAT or heuristic approximation is involved. Enumerating all 2,401 relative phases for each unique adjacent base-template pair gives:

| axis | base-template pairs | no permitted shift | exactly one permitted shift | permitted nonzero shifts |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 286 | 175 | 111 | 0 |
| 1 | 148 | 98 | 50 | 0 |
| 2 | 156 | 102 | 54 | 0 |
| 3 | 153 | 98 | 55 | 0 |
| 4 | 251 | 167 | 84 | 0 |
| **total** | **994** | **640** | **354** | **0** |

In every one of the 354 compatible cases, the **sole permitted relative translation is zero**. No adjacent base-template pair in this corpus is compatible after any nonzero relative translation.

## Maximum-size consequence

For each axis, build a seven-partite compatibility graph: nodes are original-label projected slice templates, weighted by slice size, and an edge between consecutive labels means that at least one relative translation is compatible.

The exact maximum-weight closed 7-layer path is **367 for each of the five axes**, even if we **relax** the normally necessary cyclic phase-sum consistency constraint. Since this relaxed graph contains the complete original-label arbitrary-translation family, it is a rigorous upper bound. The source 367-word code attains the bound. Therefore:

> For the 38 pinned source codes, with each projected slice still placed at its original cyclic symbol label, allowing an arbitrary independent four-coordinate translation at each of the seven layers cannot produce 368 words in `C7^5` on any of the five axes.

The rigidity result is stronger than the initial 49-translation pilot in `c7p5-whole-layer-blocks-2026-11-04.md`. It is **not** a global upper bound on `alpha(C7^5)` or `alpha(C7^10)`. In particular, replacing only *part* of a slice, changing coordinate reflection/permutation, or reassigning an original template to a *different* first-coordinate symbol lies outside this theorem.

## Independent verification

Two distinct exact implementations replay the entire census from pinned sources:

1. `code/c7p5_full_shift_compatibility.py` computes forbidden translation masks using union of translated 81-neighborhood bitsets, and then an exact seven-layer dynamic program. [Five-axis Actions run 41855855535](https://github.com/teddyli18000/web-ingest/actions/runs/41855855535), all five jobs `success` and all five relaxed bounds exactly 367.
2. `code/c7p5_full_shift_replay_integer.py` instead builds the full integer 4D histogram of differences `a-b` and applies separable cyclic `[1,1,1]` convolutions with `numpy.roll`. The resulting integer entries count every cross-confusable pair for each phase; zero entries are exactly the compatible phases. It independently builds the relaxed dynamic program. [Actions run 41856250571](https://github.com/teddyli18000/web-ingest/actions/runs/41856250571), successful. All **994** allowed-phase classifications, all **zero nonzero-phase** outcomes, and all five maxima **367** agree.
3. The earlier explicitly materialized shifted-template DP `code/c7p5_slice_stitch_dp.py` independently replayed all candidate five-dimensional words and found maxima 367 for five axes under its 49-translation pilot. [Run 41855395790](https://github.com/teddyli18000/web-ingest/actions/runs/41855395790).

No p004 verifier was invoked in these experiments because no 368-word witness or 134,754-point ten-dimensional candidate was generated.

## Immediate next search space

The above result shows **phase rigidity** under fixed original symbol labels, not merely resistance to a fixed shift sample. Further scaling the same 38-code translated-slice family is unproductive. The next independent variable to release is the source **layer label** itself: assign a source four-dimensional template to an arbitrary destination symbol and solve the corresponding weighted cycle. This distinct family is implemented by `code/c7p5_free_label_slice_dp.py` and was launched in [Actions run 41856680803](https://github.com/teddyli18000/web-ingest/actions/runs/41856680803). It has not yet been adjudicated at the time of writing this note.
