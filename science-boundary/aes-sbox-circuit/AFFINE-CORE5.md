# Affine five-AND direct-core search

## Scope

This note studies a 17-gate replacement for the merged-102 circuit's fixed four-input / nine-factor core interface using exactly five AND gates and at most twelve XOR/XNOR gates. The fixed tail observes the nine factor values exactly on all 15 nonzero core states and is completely insensitive to their values at core state `0000`.

The unrestricted zero-state relation therefore has `2^9 = 512` possible factor completions.

## Complete result 1: 496 of 512 completions need at least six ANDs

`prove_core5_rank5_completions.py` exhausts all 512 zero-state completion patterns modulo affine functions.

Action run `40640514891`, job `rank5-proof`, independently reproduced:

```text
completion patterns:                 512
nonlinear quotient rank 4:            16
nonlinear quotient rank 5:           496
distinct rank-5 target spaces:         1
possible nonzero first-AND classes:   35
intersection(first-AND classes, U):    0
```

Here `U` is the common five-dimensional nonlinear quotient space of all 496 rank-5 completions.

A five-AND circuit computing a rank-5 target space has only five AND-output nonlinear classes available, so those five classes must be independent and span `U`. In particular the first AND class must lie in `U`. Before the first AND, both operands are arbitrary affine functions of the four core inputs. Exhausting all products of such affine functions gives exactly 35 possible nonzero first-AND classes, none in `U`. Hence every one of the 496 rank-5 completions needs at least six ANDs.

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

## Complete result 2: exact nonlinear-span reduction on the remaining 16

For a rank-4 target space `T`, any five-AND circuit has five independent AND nonlinear classes. The first class `r0` is one of the 35 affine-input product classes and lies outside `T`, defining a candidate five-dimensional space

```text
N = span(T, r0).
```

`screen_core5_affine_spans.py` exactly checks whether a five-step chain of independent AND classes can remain inside each candidate `N`, with each new AND allowed arbitrary affine operands from the four inputs and previously generated classes.

The 16 jobs in Action run `40640514891` all completed successfully:

```text
completion 000000000: 30 / 35 candidate 5D spaces reachable
each other completion: 22 / 35 candidate 5D spaces reachable
```

Thus 560 nominal `(completion, first-class)` spaces reduce to exactly

```text
30 + 15*22 = 360
```

nonlinear spaces that can still contain a five-AND circuit.

## Complete result 3: all 16 rank-four completions require more than twelve mandatory linear forms

The original Python exact mandatory-form search was correct but expensive. `screen_core5_exact.cpp` implements the same necessary-condition search on exact 16-state truth tables using an optimized BFS-prefix / DFS-suffix traversal and an incremental target-form lower bound.

For one fixed rank-four completion it:

- allows arbitrary affine operands and exact XOR/XNOR phase choices;
- keeps five independent AND nonlinear classes inside a five-dimensional span containing the target space;
- records every distinct non-free affine source form required as an AND operand;
- optimistically credits future AND outputs that could directly expose target functions;
- prunes only when even that optimistic mandatory-form count exceeds twelve.

A local exhaustive run completed all 16 rank-four completions with zero `<=12` witness. Independent GitHub Actions run **`40739207093`** then completed **16/16 jobs successfully**. The program exits nonzero if any `<=12` witness exists, so the all-green matrix independently confirms zero hits.

Representative exact state counts from the independent implementation include:

```text
000000000 : 121,064 depth-3 physical prefixes; 136,760 suffix nodes; 0 hits
000010111 :  21,624 depth-3 physical prefixes;  22,968 suffix nodes; 0 hits
111010101 :  21,048 depth-3 physical prefixes;  21,288 suffix nodes; 0 hits
```

No case reaches a valid fifth-AND leaf under the optimistic twelve-linear budget; every branch is already ruled out by a safe necessary lower bound.

## Consequence

Together, Results 1 and 3 cover **all 512 zero-state completions** permitted by the complete fixed-tail don't-care relation:

- the 496 rank-five completions need at least six ANDs;
- none of the 16 rank-four completions admits a five-AND decomposition with at most twelve mandatory linear forms.

Therefore the merged-102 fixed interface has **no `5 AND + 12 XOR/XNOR = 17` direct core**, even allowing arbitrary internal XNOR phases and arbitrary values of all nine factors at core state `0000`.

This is a complete exclusion for the five-AND fixed-interface family. It is not a global lower bound for AES circuits: a 101-gate construction may still use six ANDs in the 17-gate core, change the middle/core interface, or save a gate in the retained-core outer linear construction.
