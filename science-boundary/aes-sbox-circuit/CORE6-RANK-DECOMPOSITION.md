# Six-AND fixed-interface decomposition

## Goal

The merged 102-gate circuit would fall to 101 if its 18-gate core were replaced by a 17-gate circuit exposing the same nine tail factors on the complete care set.  The only gate-count split not already excluded by the five-AND multiplicative lower bound is

```text
5 AND + 12 linear
or
6 AND + 11 linear.
```

This note decomposes the second case by nonlinear quotient rank.

## Quotient model

Work modulo affine functions of the four fixed core inputs.  The nine required factors span a four-dimensional nonlinear quotient space `T`.  The complete fixed-tail ODC only frees the value at core state `0000`; it does not change the requirement on the other 15 states.

Each AND can increase the dimension of the span of raw-AND quotient classes by at most one.  The previously established ODC multiplicative-complexity lower bound says at least five ANDs are necessary, so a six-AND candidate can have final raw-AND quotient rank only five or six.

## Rank five: one dependent AND

If six AND gates have quotient rank five, exactly one AND is quotient-dependent on earlier raw ANDs.  Its actual Boolean output is therefore an affine form of the four inputs and the earlier independent raw-AND outputs (including its phase/constant term in the affine form).

Delete that dependent AND and substitute the corresponding affine form at every use.  What remains is a five-independent-AND decomposition of the same nine partial target functions.  In the five-AND mandatory-form model, every non-free affine form needed as an AND operand or exposed target must be materialized by a linear gate.  Re-introducing the deleted dependent AND can make at most **one distinct affine function** free: the function computed by that gate.  It cannot make two distinct truth functions into primitive sources.

Therefore, if a zero-state completion has five-AND mandatory-form minimum `m`, every six-AND realization of quotient rank five for that completion needs at least

```text
6 AND + (m - 1) linear gates.
```

In particular, once the ongoing affine/XNOR exact campaign establishes `m >= 13` for all 16 rank-four zero-state completions, **every quotient-rank-five six-AND direct core will need at least 18 gates**.  This implication is conditional until all 16 completion cases finish.

## Rank six: all six ANDs independent

If the raw-AND quotient rank is six, every AND adds a new nonlinear class.  Let `E` be the final six-dimensional nonlinear span.  Necessarily

```text
T subset E,  dim(T)=4,  dim(E)=6.
```

The exact quotient-level census in `enumerate_core6_envelopes.py` gives:

```text
first-AND spans: 35
first step join-rank distribution: rank 5 -> 35
second-AND spans: 2485
second step join-rank distribution: rank 5 -> 60, rank 6 -> 2425
unique rank-6 envelopes E after two steps: 585
```

Once `span(T,current)` has rank six, every later independent nonlinear class must lie in that same envelope `E`; otherwise the final six-AND span could not contain both the target space and all six independent AND classes.  Thus the 585 envelopes are complete natural shards for the quotient-rank-six search after the first two nonlinear steps.

This is only a search-space decomposition, not a 101 construction or an impossibility proof.  The remaining task is to test whether any envelope admits a physical six-AND witness whose AND operands plus nine target forms can be scheduled with at most eleven XOR/XNOR gates.

## Current implication

The direct fixed-interface route is now split cleanly:

1. finish the 16-case affine five-AND exact mandatory-form campaign;
2. if every case has minimum at least 13, discard both `5+12` and quotient-rank-five `6+11`;
3. search only quotient-rank-six `6+11`, sharded by the 585 reachable nonlinear envelopes;
4. if that also fails, the remaining credible 101 routes require changing the middle/core interface or reducing the retained-core outer linear cost.
