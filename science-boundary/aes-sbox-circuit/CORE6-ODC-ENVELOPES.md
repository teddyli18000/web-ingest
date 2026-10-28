# Six-AND ODC envelope census

## Scope

This note records an exact nonlinear-quotient census for a fixed-interface 17-gate replacement of the merged 102-gate AES S-box core in the `6 AND + 11 XOR/XNOR` case.

The fixed tail requires nine factor functions exactly on the 15 nonzero four-bit core states and ignores all nine values at state `0000`. Therefore there are `2^9 = 512` zero-state completions.

`enumerate_core6_odc_envelopes.cpp` is a solver-free exhaustive computation on exact 16-state truth tables modulo affine functions. It reproduces the established split:

- 16 completion patterns have target quotient rank four;
- the other 496 patterns all share one common rank-five target space `U`.

It then enumerates every reachable six-dimensional nonlinear envelope for each rank-four completion by following the complete rank-five frontier until its first transition to join rank six.

## The 16 rank-four completions are a hyperplane family

Using the four independent factor basis `[q45,q59,q52,q57]`, the nine required factors have coefficient masks

```text
[1,2,4,8,9,13,6,3,14].
```

For each `z in GF(2)^4`, assign the zero-state phase of factor `i` by

```text
phase_i = <mask_i,z>.
```

As `z` ranges over all 16 four-bit vectors this generates exactly the 16 rank-four completion patterns found by exhaustive enumeration.

Let `T_z` be the nonlinear quotient target space for completion `z`. Changing a factor only at state zero contributes one extra nonlinear class, so all sixteen `T_z` are distinct four-dimensional hyperplanes inside the same five-dimensional space `U`. In particular, for any distinct `z,z'`,

```text
span(T_z,T_z') = U.
```

This explains the intersection pattern below: if one rank-six envelope works at quotient level for two distinct rank-four completions, it must contain `U`; consequently every pairwise intersection collapses to the same common family.

## Exact rank-four completion result

The 16 completion patterns and reachable rank-six envelope counts are:

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

Thus one representative completion cannot stand in for the other 15. Apart from the 30-envelope common core, the quotient search decomposes into 16 disjoint sectors.

## Relation to the 496 rank-five completions

Because all 496 rank-five completions share `U`, and every one of the 35 possible first-AND nonlinear classes lies outside `U`, any quotient-rank-six realization of a rank-five completion fixes its final envelope immediately after the first AND:

```text
E = span(U, r0).
```

The 35 possible first classes give exactly **35** such rank-six envelopes.

The exact census finds

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

The 35-envelope physical search in `screen_core6_rank5_exact.cpp`, independently reproduced by Action run `40738521634`, excludes all 496 rank-five completions with `6 AND + <=11 linear`. That result does **not** automatically exclude rank-four physical realizations in the 30 common quotient envelopes because the required target affine forms and phases differ.

## Reproduction

From the repository root:

```text
g++ -O3 -std=c++17 science-boundary/aes-sbox-circuit/enumerate_core6_odc_envelopes.cpp -o /tmp/p008-envelope-census
/tmp/p008-envelope-census
```

The program contains regression assertions for all counts above. A reference local run completed in about five seconds on a commodity Linux CPU.

## Consequence for search design

The only unresolved fixed-interface 17-gate family is now the 16 rank-four completions with six independent ANDs and final quotient rank six. Do not launch one monolithic synthesis over all 23,970 envelopes. Useful decompositions are:

1. exploit the 30-envelope common core, which is exactly the family of rank-six spaces containing `U`;
2. treat each completion's remaining envelopes as its private sector;
3. improve the physical linear-form lower bound before scheduling/SAT; a loose quotient-mask bound was tested and was too weak;
4. use the hyperplane relation among the `T_z` when searching for a completion-independent obstruction.

This census is a search-space theorem, not a lower bound on total AES circuit size by itself.
