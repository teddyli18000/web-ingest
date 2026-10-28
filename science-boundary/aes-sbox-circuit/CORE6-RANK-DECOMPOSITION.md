# Six-AND fixed-interface decomposition

## Goal

The merged 102-gate circuit would fall to 101 if its 18-gate core were replaced by a 17-gate circuit exposing the same nine tail factors on the complete care set. The only gate-count splits relevant to that fixed interface are

```text
5 AND + 12 linear
or
6 AND + 11 linear.
```

The five-AND case is now completely excluded; see `AFFINE-CORE5.md`. This note records what remains of the six-AND case.

## Quotient model

Work modulo affine functions of the four fixed core inputs. The complete fixed-tail ODC frees only the nine factor values at core state `0000`.

Across all `2^9=512` zero-state completions:

- 16 completions have target quotient rank four;
- the other 496 completions all share one common target quotient space `U` of rank five.

Each AND can increase the span of raw-AND quotient classes by at most one. A six-AND candidate can therefore finish with raw-AND quotient rank five or six.

## Quotient rank five is excluded

If six AND gates have quotient rank five, one AND is quotient-dependent on the other five. Its Boolean function is an affine form of the inputs and five independent raw-AND outputs.

For the 496 rank-five target completions, deleting that dependent AND would leave a five-AND circuit computing a rank-five target space. `prove_core5_rank5_completions.py` proves that impossible: every such completion needs at least six independent AND classes.

For the 16 rank-four completions, deleting the dependent AND and replacing its value by its affine expression turns any hypothetical `6 AND + 11 linear` witness into a five-independent-AND mandatory-form witness using at most one additional distinct affine form. It would therefore give a `5 AND + <=12 mandatory forms` witness. `screen_core5_exact.cpp`, independently verified by all 16 jobs of Action run `40739207093`, proves that no such witness exists.

Hence **all quotient-rank-five `6 AND + 11 linear` fixed-interface cores are excluded**.

## Quotient rank six for the 496 rank-five completions is excluded

For a rank-five completion, let `U` be the common five-dimensional target quotient space. The first AND class must lie outside `U`; exactly 35 nonzero first-AND classes are possible from affine input operands. In a six-independent-AND circuit the first class therefore fixes the final six-dimensional envelope

```text
E = span(U, r0).
```

`screen_core6_rank5_exact.cpp` exhausts all 35 such envelopes on exact 16-state truth tables. It models arbitrary XOR/XNOR phases, exact AND operands, every distinct non-free affine form, and all 496 rank-five zero-state completions simultaneously. It prunes only when an optimistic lower bound already exceeds the eleven-linear budget.

A local unrestricted run completed **35/35 envelopes with zero hits**. The heaviest envelope visited only 22,752 DFS suffix nodes after the optimized incremental coordinate-map reduction.

Independent GitHub Actions run **`40738521634`** then completed **35/35 jobs successfully**. The program exits nonzero if a `<=11` mandatory-form witness is found, so the all-green matrix independently reproduces the zero-hit result.

Therefore quotient-rank-six `6 AND + 11 linear` cores are excluded for **all 496 rank-five completions**.

## What remains: rank-four completion + quotient rank six

The only unresolved fixed-interface 17-gate core family is now

```text
rank-four zero-state completion
+ six independent ANDs
+ final raw-AND quotient rank six
+ at most eleven XOR/XNOR gates.
```

An exact quotient-level census is in `enumerate_core6_odc_envelopes.cpp` and `CORE6-ODC-ENVELOPES.md`.

For the 16 rank-four completions:

```text
completion 000000000: 1545 reachable rank-six envelopes
each other completion: 1525 reachable rank-six envelopes
```

The union has exactly **23,970** distinct envelopes:

```text
23,940 belong to exactly one completion;
    30 belong to all 16 completions.
```

There are no intermediate multiplicities. The common 30 envelopes are exactly 30 of the 35 spaces `span(U,r0)` from the rank-five-completion analysis; five of those 35 are rank-five-only.

This is a search-space theorem, not an impossibility proof. Physical mandatory-form screening has already closed many representative common-envelope pairs, but some combinations remain computationally heavy. The next direct-core work should improve the physical necessary lower bound or exploit the hyperplane structure of the 16 rank-four completions rather than brute-force all 23,970 envelopes independently.

## Parallel 101 route

The direct-core frontier is now narrow but difficult. In parallel, the retained-18-core outer family remains credible: a 101 circuit needs

```text
prelinear + middle_support + output_transpose <= 36.
```

All 2040 semilinear transforms have been cheaply screened; 1506 are excluded by a rigorous lower bound and 534 remain. Exact Class A/B/C searches and the rank-three support-five completion campaign are the current complementary route. See `SEMILINEAR-CLASSES.md`, `EXACT-SCREENS-2026-10-28.md`, and `RANK3-SUPPORT5.md`.
