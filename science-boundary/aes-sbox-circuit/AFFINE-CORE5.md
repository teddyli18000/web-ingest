# Affine five-AND direct-core search

## Scope

This note studies a 17-gate replacement for the merged-102 circuit's fixed four-input / nine-factor core interface using exactly five AND gates and at most twelve XOR/XNOR gates. The fixed tail observes the nine factor values exactly on all 15 nonzero core states and is completely insensitive to their values at core state `0000`.

The unrestricted zero-state relation therefore has `2^9 = 512` possible factor completions. Earlier affine beam code searched only 16 coherent completions. The results below now justify that restriction for **five-AND** circuits and reduce the exact physical search further.

## Verified complete result: 496 of 512 completions need at least six ANDs

`prove_core5_rank5_completions.py` exhausts all 512 zero-state completion patterns modulo affine functions.

Action run `40640514891`, job `rank5-proof`, completed successfully and independently reproduced:

```text
completion patterns:                 512
nonlinear quotient rank 4:            16
nonlinear quotient rank 5:           496
distinct rank-5 target spaces:         1
possible nonzero first-AND classes:   35
intersection(first-AND classes, U):    0
```

Here `U` is the common five-dimensional nonlinear quotient space of all 496 rank-5 completions.

Why this is a proof: a five-AND circuit computing a rank-5 target space has only five AND-output nonlinear classes available, so those five classes must be independent and span `U` exactly. In particular the first AND class must lie in `U`. Before the first AND, both operands are arbitrary affine functions of the four core inputs. Exhausting all products of such affine functions gives exactly 35 possible nonzero first-AND classes, none in `U`. Hence every one of the 496 rank-5 completions needs at least six ANDs.

The only possible five-AND completions are therefore the following 16 rank-4 patterns:

```text
000000000
000010111
001001011
001011100
010100110
010110001
011101101
011111010
100101111
100111000
101100100
101110011
110001001
110011110
111000010
111010101
```

This closes the logical gap in `search_core5_odc_affine.py`: for five-AND circuits, searching only its 16 coherent completions is complete with respect to the fixed tail's full `0000` don't-care.

## Verified exact nonlinear-span reduction on the remaining 16

For a rank-4 target space `T`, any five-AND circuit has five independent AND nonlinear classes. The first class `r0` is one of the 35 affine-input product classes and lies outside `T`, defining a candidate five-dimensional space

```text
N = span(T, r0).
```

`screen_core5_affine_spans.py` exactly checks whether a five-step chain of independent AND classes can remain inside each candidate `N`, with each new AND allowed arbitrary affine operands from the four inputs and previously generated classes.

The 16 jobs in Action run `40640514891` all completed successfully. The exact pattern is:

```text
completion 000000000: 30 / 35 candidate 5D spaces reachable
each other completion: 22 / 35 candidate 5D spaces reachable
```

Thus 560 nominal `(completion, first-class)` spaces reduce to exactly

```text
30 + 15*22 = 360
```

nonlinear spaces that can still contain a five-AND circuit. This is a complete multiplicative-span reduction, not a beam search. It does not yet account for the twelve-linear-gate budget.

## Heuristic affine beam evidence

The pre-existing `search_core5_odc_affine.py` is a beam heuristic, not an exclusion proof. Its original Action run `40633465765` was partially cancelled under runner pressure; several completions did finish. For example completion 9 (`100111000` in the script's completion index convention) completed at beam 8 with best observed full mandatory count 14 and no `<=12` candidate or complete closure. Treat these results only as search evidence.

## Exact affine mandatory-form search now running

`search_core5_affine_mandatory.py` removes the beam truncation and models internal XNOR/complement phases exactly.

Every wire is normalized as

```text
f' = f XOR f(0000)
```

and its actual phase `f(0000)` is tracked separately. XOR and XNOR have the same normalized XOR source mask but different phase; AND is evaluated on the actual affine operands and its normalized output and phase are propagated exactly.

A physical state records the normalized raw AND outputs, their phases, and every distinct affine source form `(source-XOR mask, phase)` that must be materialized as an AND operand. An affine form is free only when it is exactly an already existing source wire with its actual phase. At the fifth AND, the selected completion's nine target forms are added to the mandatory set.

Therefore:

- exact minimum mandatory count `>=13` rules out `5 AND + 12 linear = 17` for that completion;
- a count `<=12` is only a necessary-count witness and still requires gate scheduling/closure before it becomes a circuit.

Smoke Action run `40640637350` is currently evaluating rank-4 cases 0 and 1 without beam truncation. If healthy, the search should be sharded/scaled over all 16 rank-4 completions rather than adding runtime to SAT encodings that previously returned `unknown`.

## Consequence if all 16 exact minima are at least 13

Together with the verified 496-completion rank-5 exclusion, this would completely rule out a fixed-interface 17-gate core with five AND gates, even allowing arbitrary XOR/XNOR constants and the full zero-state don't-care. The remaining direct-core route would then require a genuinely different six-AND / eleven-linear decomposition or a changed middle/core interface.
