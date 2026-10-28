# p008 current status

Last synchronized: 2026-10-28 UTC.

## Live upstream baseline

- Few Shots `data/board.json` was rechecked at update time: **102 gates** remains the p008 record, `huangxin-design/aes102-field-plane-offsets`, PR #25.
- Record chain: 106 baseline -> 105 -> 104 -> 103 -> 102.
- No 101 result is known from the live board. Any new claim must therefore be **101 gates or fewer**, after another immediate upstream recheck.
- The 102 circuit is

```text
18 prelinear + 9 norm AND + 15 middle + 18 core + 18 final AND + 24 output = 102.
```

The retained core has six ANDs and consumes four independent middle signals; the fixed tail consumes nine core factors.

## Direct fixed-interface route: now almost completely classified

Replacing the 18-gate core by 17 gates would give a 101-gate full circuit without changing the outer construction.

Complete fixed-tail observability analysis shows:

- the nine factors are exact on all 15 nonzero four-bit core states;
- all nine factor values are arbitrary at core state `0000`;
- therefore there are exactly `2^9 = 512` zero-state completions.

Their nonlinear quotient ranks split as:

```text
16 completions: rank 4
496 completions: rank 5, all sharing one common 5D space U
```

At least five AND gates are necessary.

### Five-AND 17-gate core: completely excluded

`prove_core5_rank5_completions.py` proves all 496 rank-five completions need at least six ANDs.

For the remaining 16 rank-four completions, `screen_core5_exact.cpp` exhausts exact 16-state physical states with arbitrary XOR/XNOR phases and a safe optimistic mandatory-linear-form lower bound. Independent GitHub Actions run **40739207093 completed 16/16 jobs successfully with zero <=12 witness**.

Therefore there is **no fixed-interface `5 AND + 12 linear = 17` core** under the complete zero-state don't-care.

### Six-AND final quotient rank 5: completely excluded

If six ANDs have final quotient rank five, one AND is quotient-dependent. Deleting it yields a five-independent-AND representation and can increase the mandatory affine-form count by at most one.

The rank-five completions are impossible with five independent ANDs, and the 16 rank-four completions have no five-AND witness with <=12 mandatory forms. Hence **no quotient-rank-five `6 AND + 11 linear` core exists**.

### Six-AND final quotient rank 6 for the 496 rank-five completions: completely excluded

For the common rank-five target space `U`, the first AND class must lie outside `U` and fixes the final six-dimensional envelope `E=span(U,r0)`. There are exactly 35 such first-class envelopes.

`screen_core6_rank5_exact.cpp` exhausts all 35 on exact truth tables, phases and physical affine operand forms. Local unrestricted runs found zero <=11 witness. Independent GitHub Actions run **40738521634 completed 35/35 jobs successfully**, independently confirming the exclusion.

### Only unresolved fixed-interface family

The sole remaining 17-gate direct-core family is

```text
one of the 16 rank-four zero-state completions
+ six independent ANDs
+ final quotient rank six
+ at most 11 XOR/XNOR gates.
```

`enumerate_core6_odc_envelopes.cpp` gives the complete quotient frontier:

```text
000000000 completion: 1545 reachable rank-6 envelopes
other 15 completions: 1525 each
union: 23,970 envelopes
```

Exactly 23,940 envelopes belong to one completion only; 30 belong to all 16. The 16 rank-four completion spaces are distinct hyperplanes `T_z` inside the common 5D space `U`, and any two distinct `T_z` span `U`. This explains why every pairwise envelope intersection is the same 30-space common core.

Representative exact physical screens in the 30 common envelopes are negative, but a complete 23,970-envelope exclusion has **not** been proved. High-parallel batch timeouts were treated only as implementation evidence, never as exclusions. Loose quotient-mask lower bounds were tested and were too weak.

## Parallel route: retained 18-gate core, cheaper outer linear construction

With the nonlinear core retained, a 101 circuit requires

```text
prelinear + middle_support + output_transpose <= 36.
```

A complete cheap lower-bound scan covers all `255*8 = 2040` semilinear transforms and all `3^9` plane orientations per transform. Exactly **1506 / 2040 transforms are rigorously excluded** by this lower bound; **534 transforms remain**.

The global lower-bound minimum is 31, attained by 18 transforms in three six-member classes. Current exact campaigns prioritize representatives:

- Class A: identity / live transform;
- Class B: `(c,k)=(0x9d,3)`;
- Class C: `(0x5b,3)`.

Complementary exact searches cover:

1. full-column-rank middle correction supports of size <=4;
2. all 117 rank-four support-5 position sets;
3. the remaining nine rank-three support-5 position sets using a complete event reduction over the two free correction bytes.

The rank-three support-5 campaign had one historical cancellation at Class-C prefix 3; that shard is being rerun. The older Class-C main campaign also had cancellations at exact-correction prefixes 0/3/6 and rank-four support-5 prefix 3. A dedicated temporary workflow now reruns the remaining unclean gaps rather than repeating completed shards.

No 101 component candidate has been established from these exact campaigns so far.

## Current next steps

1. Finish and aggregate the missing Class-C semilinear shards; if all summaries have `candidates_101=0`, close the Class-C support<=5 representative search cleanly.
2. Aggregate Class A/B/C exact campaign summaries rather than infer results from workflow success alone.
3. On the direct-core side, seek a stronger physical linear-network lower bound for the remaining rank-four / six-independent-AND frontier; do not brute-force all 23,970 envelopes independently without a better representation.
4. Recheck Few Shots live board and open p008 PRs before any 101 claim.

## Validation requirement for any positive candidate

A candidate is not a record until it is materialized as a complete <=101-gate certificate, independently checked on all 256 AES bytes by arithmetic inversion plus the AES affine map, accepted by the unchanged Few Shots verifier, and rechecked against the live upstream record immediately before submission.
