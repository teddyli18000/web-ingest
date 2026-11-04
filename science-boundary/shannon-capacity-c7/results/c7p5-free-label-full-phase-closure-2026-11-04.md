# Exact full-label/full-phase closure of the 38 public C7^5 slice families

Date: **2026-11-04**. Status: **independently reproduced restricted-family optimum = 367**; no 368-point word set, no new p004 certificate.

## Source and exact objective

Fix the 38 independently checked 367-point codes supplied by:

- `tandonravi/C7-Shannon-Capacity-Heterogeneous-Recursion`, commit `c753408492dde92a239708986d16c15dbf6c3235`, `data/base_c7.json`: the `I0` and `X` codes;
- `molind/c7-five`, commit `ae81e0d24b356aef3d388238f6fb4d02c4aa32a5`, `data/family-f.json`: all 36 Family-F codes.

For each of five coordinate axes independently, extract every complete 4D slice of all 38 codes, deduplicating exact projected subsets. This gives a small template family `T_k` of between 32 and 43 distinct high-density four-dimensional independent sets.

The **free-label/full-phase family** allows the following choices jointly:

1. At *each* destination symbol `s ∈ Z7`, select *any* 4D slice template from `T_k`, without requiring it to occupy its original source symbol layer.
2. Translate the selected slice by an *arbitrary*, independent `p_s ∈ Z7^4`.
3. Form the five-dimensional union `{(s,q+p_s):q in template_s}`, using axis `k` for the first coordinate.
4. Require the complete union to be independent in `C7^5`.

There are no restrictions on which source code each destination layer uses, and a template can be reused in multiple nonadjacent destination layers. This family **does not** include deformations of the 4D pattern inside a selected slice, 4D signed coordinate permutations varying by layer, or arbitrary new source codes.

## Exhaustive relative-translation lemma

For complete projected templates `A,B subset Z7^4` and relative shift `δ=p_B-p_A`, cross-slice nonconfusability is exactly

`δ notin ⋃_{a∈A,b∈B}(a-b+{-1,0,1}^4).`

The right side can be checked by taking the union of precisely computable 4D closed neighborhood bitsets, with 2,401 possible relative shifts.

**Verified finite result:** Every ordered pair of distinct source templates (including self-pairs) across all five axis-specific template families has either **zero** permitted relative shifts or **exactly one**, which is always `δ=(0,0,0,0)`.

| Axis | Distinct 4D templates | Ordered pairs | No permitted δ | Only δ=0 permitted |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 43 | 1,849 | 1,627 | 222 |
| 1 | 32 | 1,024 | 924 | 100 |
| 2 | 33 | 1,089 | 981 | 108 |
| 3 | 34 | 1,156 | 1,046 | 110 |
| 4 | 42 | 1,764 | 1,596 | 168 |
| **Total** | — | **6,882** | **6,174** | **708** |

There are **zero** permitted nonzero relative shifts among any of the 6,882 ordered pairs. Thus every legal cycle of seven selected templates forces `p_0=p_1=⋯=p_6`: the apparent seven independent phases collapse to a common four-coordinate translation.

## Exact cycle optimum

Construct the universal template-compatibility graph for each axis, with a directed edge `A→B` iff `A,B` admit some compatible relative phase. Give vertex `A` weight `|A|`.

A full five-dimensional independent code in the family corresponds to a *closed walk of length seven* in this graph, with the additional phase-consistency requirement. Since every admissible edge forces `δ=0`, the phase condition is automatic.

Exact maximum-weight length-seven cyclic dynamic programming gives **367** in each of the five axes. The original pinned `I0` source attains 367, so the maximum within the entire free-label/full-phase family is **exactly 367**, not just bounded above by it.

Hence this large, independently-translated, freely relabeled complete-slice family yields no `C7^5` set of size 368 and consequently cannot yield a p004 breakthrough by squaring such a set.

## Independent verification and artifacts

The complete result is checked through two genuinely different enumeration kernels:

1. **Exact bitset union / weighted cycle DP**: `code/c7p5_free_label_slice_dp.py` reuses the exact 4D difference-neighborhood bitset formula, explicitly enumerates every ordered template pair, optimizes both the phase-relaxed and zero-phase cycle, and materializes the optimum for independent 5D replay. [GitHub Actions run 41856680803](https://github.com/teddyli18000/web-ingest/actions/runs/41856680803): all five axis jobs successful, each optimum 367, no nonzero permitted phase.
2. **Independent exact integer cyclic convolution**: `code/c7p5_free_label_replay_integer.py` uses `code/c7p5_full_shift_replay_integer.py` to enumerate each source 4D slice and accumulate the **integer difference histogram** over all template-word pairs. Four successive separable cyclic `[1,1,1]` convolutions using integer `numpy.roll` yield the exact number of cross-confusable pairs for each of 2,401 shifts. A completely separate weighted-cycle DP gives five exact upper values of 367. [GitHub Actions run 41857026561](https://github.com/teddyli18000/web-ingest/actions/runs/41857026561), job `126668304756`, completed success and agreed on all 6,882 pair classifications, 708 zero-only compatibilities, and five optima 367. [Result artifact](https://github.com/teddyli18000/web-ingest/actions/runs/41857026561/artifacts/13338116844).

Both computations read the same immutable, public upstream source snapshots; they do not share the phase compatibility algorithm. The integer count upper bound for a pair is at most `|A| |B| 3^4`, safely within signed 32-bit range.

The earlier fixed-original-label theorem over 994 adjacent pairs and arbitrary shifts is documented separately in `c7p5-full-phase-rigidity-2026-11-04.md`. This result strictly generalizes it by releasing the source layer labels.

## Interpretation and next direction

This is a complete negative result **for a mathematically specified structured family**, not a proof that `α(C7^5)=367`. It shows why randomly translating or rearranging entire high-density projected slices from these sources cannot work: every successful adjacent pair is forced into a common phase, and the remaining template graph itself has maximum weight 367.

**Do not spend further compute adding translation samples or relabelings within this unchanged corpus.** Candidate quality remained 367 even after exact coverage of all 2,401 phases and all 6,882 ordered template pairs.

The next meaningful decision variable must be the **internal shape** of the 4D templates or a genuinely distinct five-dimensional source basin. A promising concrete interface is to generate structural *intra-slice* replacements jointly with cyclic neighboring compatibility constraints, rather than select finished public slices. An alternative is to construct independent new five-dimensional parents outside the pinned Polak/BPZ/Family-F orbit (e.g., parametrized algebraic/circular-code families) before attempting recombination. These hypotheses remain untested.

The upstream Few Shots p004 record remains **134,753**, target **134,754**; no new candidate was submitted.
