# Six-AND ODC envelope census

## Scope

This note records an exact nonlinear-quotient census for a fixed-interface 17-gate replacement of the merged 102-gate AES S-box core in the `6 AND + 11 XOR/XNOR` case.

The fixed tail requires nine factor functions exactly on the 15 nonzero four-bit core states and ignores all nine values at state `0000`. Therefore there are `2^9 = 512` zero-state completions.

`enumerate_core6_odc_envelopes.cpp` is a solver-free exhaustive computation on exact 16-state truth tables modulo affine functions. It reproduces the established split:

- 16 completion patterns have target quotient rank four;
- the other 496 patterns all share one common rank-five target space `U`.

It then enumerates every reachable six-dimensional nonlinear envelope for each rank-four completion by following the complete rank-five frontier until its first transition to join rank six.

## Exact rank-four completion result

The 16 possible rank-four completion patterns are the already established coherent patterns. Their reachable rank-six envelope counts are:

```text
000000000 : 1545
000010111 : 1525
001001011 : 1525
001011100 : 1525
010100110 : 1525
010110001 : 1525
011101101 : 1525
011111010 : 1525
100101111 : 1525
100111000 : 1525
101100100 : 1525
101110011 : 1525
110001001 : 1525
110011110 : 1525
111000010 : 1525
111010101 : 1525
```

Across all 16 cases the union contains exactly **23,970** distinct rank-six envelopes. Their completion-membership multiplicities are exactly

```text
23,940 envelopes belong to exactly one completion;
    30 envelopes belong to all 16 completions.
```

There are no intermediate multiplicities. Equivalently, every pair of distinct rank-four completion frontiers has intersection exactly **30**; all 120 pairwise intersections are the same 30 common envelopes.

This matters operationally: one representative completion cannot stand in for the other 15. Apart from the 30-envelope common core, the quotient search decomposes into 16 disjoint sectors.

## Relation to the 496 rank-five completions

Because all 496 rank-five completions share the same five-dimensional target space `U`, and every one of the 35 possible first-AND nonlinear classes lies outside `U`, any quotient-rank-six realization of a rank-five completion fixes its final envelope immediately after the first AND:

```text
E = span(U, r0).
```

The 35 possible first classes give exactly **35** such rank-six envelopes.

The exact census finds a sharp overlap:

```text
30 of those 35 envelopes = the 30 envelopes common to all 16 rank-four completions;
5 of those 35 envelopes occur in no rank-four completion frontier at all.
```

The five rank-five-only first-AND residue classes are

```text
0xa0a0
0x1428
0x8ee8
0xf660
0xcc00
```

Thus the active exact rank-five physical search over all 35 first-AND envelopes also tests the nonlinear envelopes forming the entire 30-envelope common core of the rank-four ODC search. It does **not** by itself exclude rank-four physical realizations in those envelopes, because the target affine forms/completion phases differ; the overlap is a quotient-level structural fact only.

## Reproduction

From the repository root:

```text
g++ -O3 -std=c++17 science-boundary/aes-sbox-circuit/enumerate_core6_odc_envelopes.cpp -o /tmp/p008-envelope-census
/tmp/p008-envelope-census
```

The program contains regression assertions for all counts above. A reference local run completed in about five seconds on a commodity Linux CPU.

## Consequence for search design

Do not launch one monolithic six-AND exact synthesis over all ODC completions. The exact quotient geometry supports a more disciplined decomposition:

1. finish the 35-envelope rank-five physical mandatory-form screen;
2. treat the 30 common rank-four envelopes as a distinguished shared core, but with rank-four target forms evaluated separately;
3. handle the remaining 23,940 rank-four envelopes completion-by-completion, using cheap necessary linear-form bounds before any scheduling/SAT search;
4. preserve the five rank-five-only envelopes as a separate class.

This census is a search-space theorem, not a lower bound on total AES circuit size by itself.
