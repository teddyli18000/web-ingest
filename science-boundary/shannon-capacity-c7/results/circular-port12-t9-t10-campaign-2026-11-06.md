# p004 circular 12-owner port campaign — 2026-11-06

**Status:** verified new 367-word parent structures and exhaustive restricted t=9/t=10 auxiliary scans; **no new C7^10 score**, no Few Shots shot.

## Objective and public baseline

The [Few Shots p004 board](https://github.com/few-shots/few-shots/blob/main/data/board.json) still displays 134,753 (target >=134,754). Recent literature checks include Itty–Rosin–Carstensen–Reichman arXiv:2607.21517, Gao arXiv:2607.27869 and Tandon arXiv:2608.30273. A ten-dimensional construction of 134,754 improves the finite-power lower bound, but on its own does not exceed the published Tandon asymptotic Shannon-capacity bound.

The classical two-sided port gadget for a 367-point five-dimensional independent code I, an oriented set of t distinct private-neighbor pairs and an independent auxiliary X of size m, disjoint from D=N[PH]∩N[PV], has score

`(367-t)^2+2tm = 367^2+t^2-2t(367-m)`.

**Key constructive relaxation:** For t=10, even **m=366** gives **134,769**, 16 more than the current p004 record. The ideal m=367 gives **134,789**. For t=9, m=367 gives 134,770, but m=366 gives 134,752 and is insufficient by one point. Thus the next question is *not* strictly whether a 367-word X avoids D; a 366-word X suffices for t=10.

## Durable new 367-word five-dimensional witnesses

The two independent 367-word codes from the port-aware neutral 4D block-search run [42024771296](https://github.com/teddyli18000/web-ingest/actions/runs/42024771296) have been frozen as independently hash-checked little-endian uint16/base64 files:

- `data/circular-port12-port12a-2026-11-05.json` — source job seed 2026110552, raw-byte SHA256 `1ee9c6617e08b9142f0c75d31d760e58e1b0de65709a0eb652d147e4a151b8ed`.
- `data/circular-port12-port12b-2026-11-05.json` — source job seed 2026110554, raw-byte SHA256 `3615859351e12a1aee140fd7bf3a3057732c929c545b26fcaca1f5489fc95629`.

Both have 367 distinct words, all 67,161 unordered pairs independently checked nonconfusable, and **12 distinct private-neighbor owners**. Source A has 13 distinct private-neighbor vertices; B has 12.

An exhaustive owner/pair/side-orientation backtracking check gave:

| Parent | Valid nine-port oriented choices | Valid ten-port oriented choices | Valid eleven-port choices |
| --- | ---: | ---: | ---: |
| A | 672 | 48 | 0 |
| B | 4,032 | 576 | 0 |

For distinct private pairs `(a_i,v_i)`, `v_i` is nonconfusable with all other old owners `a_j`. Hence orientation is equivalent to a **2-coloring of the graph of confusabilities among chosen private neighbors `v_i`**. This is a useful exact simplification, separating private-neighbor selection from port-side coloring. In B, the 12-private-neighbor graph has two vertex-disjoint triangles, e.g. owner triples `(831,1074,15434)` and `(5391,6806,9603)`; at least two owners must be excluded, so t<=10 in this pinned parent. This does *not* imply t<=10 in other 367-word codes.

## Exhaustive translation scans over 41 auxiliaries

Each code was used as a parent and scanned against 41 independently valid 367-word auxiliary codes: pinned BPZ/Tandon I0 and X, molind Family-F (36 states), original circular 367, and the two newly frozen 12-owner witnesses. For every oriented t-port choice and auxiliary code, a cyclic 5D FFT evaluated all `7^5=16,807` relative translations. The numeric correlations were checked to be within `1e-6` of integers and every new global minimum was recomputed by actual integer point intersection. This is a complete **finite input family** scan, not an `α(C7^5)` exclusion.

| Parent | t | Oriented choices | Orientation × auxiliary cases | Minimum forbidden intersections | Best auxiliary |
| --- | ---: | ---: | ---: | ---: | --- |
| A | 10 | 48 | 1,968 | **8** | A itself |
| B | 10 | 576 | 23,616 | **9** | BPZ I0 |
| A | 9 | 672 | 27,552 | **5** | A itself |
| B | 9 | 4,032 | 165,312 | **7** | BPZ I0 |

All cases exhausted, **no zero intersection**, so no new ten-dimensional certificate. Specifically, for A at t=10 the best port orientation index 9 and relative phase `(5,5,6,2,5)` has `|D|=1229`, and its shifted A auxiliary intersects D in exactly eight five-dimensional words: `1075,2552,3481,4897,7989,9764,10000,12060`.

Reproducer: `code/c7p5_port12_auxiliary_scan.py`, pinned BPZ/Tandon commit `c753408492dde92a239708986d16c15dbf6c3235`, molind Family-F commit `ae81e0d24b356aef3d388238f6fb4d02c4aa32a5`.

- [t=10 hosted scan](https://github.com/teddyli18000/web-ingest/actions/runs/42250561147), all two jobs success, input and minimum consistency assertions passed.
- [t=9 hosted scan](https://github.com/teddyli18000/web-ingest/actions/runs/42251306345), both jobs success, all orientation/auxiliary cases exhausted.

## Construction-oriented diagnostic probes

The eight-hit t=10 near miss is the most promising *specific* repair target: keeping only its D-free auxiliary points yields a valid **359-word** code. We ran exploratory independent local calculations:

1. The complete restricted MIP allowing outside candidates with at most **two** conflicts against those 359 fixed points has exact gain **0**. The expanded support<=3 MIP with 1,727 candidates hit its runtime limit and **is not a proof**.
2. Three sweeps of exact two-adjacent-slice 4D MIS reoptimization, enforcing D-free words, remained at **359**. This tests a narrow block neighborhood only.
3. A direct induced 10D gadget-conflict MILP retained the 357×357 core and optimized the selectable port fibers, rather than simply discarding every bad auxiliary point. For A t=10 best eight-hit orientation/phase, exact maximum in this fixed candidate universe was **134,684** (not a record). The sampled t=9 five-hit case reached **134,703**. Allowing **two different auxiliaries** on the two port arms was also tested in 12 small exact-MILP cases, best **134,689**. All independently replayed selected candidates within their fixed graphs; these are narrow sampled results, not broad exclusions.
4. Exact 1→1 private swaps around A/B can expose as many as **14 private owners** while retaining 367 words, but a limited depth-500 search found no 11-port orientation. Immediate exact 2→2 neutral neighbors: 65 around A and 63 around B, no 11-port orientation. Do not extrapolate these local results to arbitrary multi-point-neutral changes.

The local direct-MILP and D-free probes are documented as diagnostic evidence; unlike the 41-auxiliary scans, their scripts are not yet incorporated into the hosted reproducible campaign.

## What to do next

1. Prioritize **a D-free 366-point auxiliary**, not the harder D-free 367-point target. A constructive code would immediately yield 134,769 points and must be submitted to the official Few Shots verifier. Search representation should jointly release many internal 5D words; two-layer optimizations are trapped at 359 in the best pinned near miss. A longer search at identical radius would not address that.
2. Jointly alter the private-neighbor graph itself to eliminate the independent odd cycles and obtain a bona fide **t=11** orientation (then an auxiliary of size 365 would suffice for score 134,766), rather than counting private owners alone.
3. Treat full port-fiber gadget selection as a separate joint optimization objective; 10D direct repair of a fixed eight-hit X still loses >35 points, so simply selecting among the same restricted fibers is not enough. Consider changing the source 5D parent and auxiliary simultaneously.

**No improved p004 verifier score exists yet; no shot submitted.**
