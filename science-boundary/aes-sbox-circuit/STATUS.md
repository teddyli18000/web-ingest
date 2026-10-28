# p008 current status

Last synchronized: 2026-10-28 UTC.

## Live upstream baseline

- Few Shots `data/board.json` was rechecked during this research cycle: **102 gates** remains the p008 record, `huangxin-design/aes102-field-plane-offsets`, PR #25.
- Record chain: 106 baseline -> 105 -> 104 -> 103 -> 102.
- No 101 result is known from the live board. Any new claim must therefore be **101 gates or fewer**, after another immediate upstream recheck.
- The 102 circuit is

```text
18 prelinear + 9 norm AND + 15 middle + 18 core + 18 final AND + 24 output = 102.
```

## Direct fixed-interface route

Replacing the 18-gate core by 17 gates would give a full 101-gate circuit without changing the outer construction.

Complete fixed-tail observability gives 512 zero-state completions:

```text
16 completions: nonlinear quotient rank 4
496 completions: rank 5, all sharing one common 5D space U
```

At least five AND gates are necessary.

### Completely excluded direct-core families

1. **Five AND + 12 linear**: excluded for all 512 completions. `screen_core5_exact.cpp`; independent Action **40739207093**, 16/16 rank-four jobs successful, zero witness; rank-five completions require at least six ANDs.
2. **Six AND, final quotient rank 5**: excluded by deleting the dependent AND and reducing to the five-AND results.
3. **Six independent ANDs, final quotient rank 6, rank-five completion**: all 35 first-AND envelopes excluded by `screen_core6_rank5_exact.cpp`; independent Action **40738521634**, 35/35 successful.

### Only unresolved fixed-interface 17-gate family

```text
one of 16 rank-four zero-state completions
+ six independent ANDs
+ final quotient rank six
+ at most 11 XOR/XNOR gates
```

Exact quotient census:

```text
000000000 completion: 1545 reachable rank-6 envelopes
other 15 completions: 1525 each
union: 23,970 envelopes
```

Exactly 23,940 are private to one completion and 30 are common to all 16. The 16 rank-four target spaces are hyperplanes `T_z` inside U, with any two distinct `T_z` spanning U. Representative physical screens are negative, but a complete 23,970-envelope exclusion is **not** yet proved. Loose quotient-only lower bounds were too weak; do not brute-force all envelopes independently without a stronger representation.

## Retained-18-core semilinear outer route

A 101 circuit in this family needs

```text
prelinear + middle_support + output_transpose <= 36.
```

The full cheap scan covers all 2040 semilinear transforms and all 19,683 orientations per transform. The best-LB distribution is:

```text
LB 31: 18 transforms
LB 32: 30
LB 33: 24
LB 34: 78
LB 35: 150
LB 36: 234
LB 37: 336
LB 38: 594
LB 39: 576
```

Thus 1506/2040 transforms are rigorously excluded by cheap LB alone.

### Global exact symmetry reduction

`prove_all_semilinear_orbits.py` proves the complete retained-core semilinear family splits into **340 exact six-element equivalence orbits**. Independent Action **40745501728** completed successfully.

The proof checks all **1700** representative-to-nonrepresentative maps and the complete six-element automorphism group of the live middle columns/core factors. Plane relabeling, ternary orientation relabeling, middle correction equations, prelinear target sets, output target sets, core factor covariance, helper choices and exact XOR/XNOR costs all transport unchanged.

Therefore the 534 cheap-LB<=36 survivor transforms are only **89 independent representative orbits**:

```text
LB 31: 3 orbits
LB 32: 5
LB 33: 4
LB 34: 13
LB 35: 25
LB 36: 39
```

The LB=31 representatives are:

```text
A: (0x01,0)
B: (0x9d,3)
C: (0x5b,3)
```

### LB=31 support >=6 completely excluded

Any support>=6 101 candidate would require exact `prelinear+output<=30`.

`prove_semilinear_support6_impossible.py` exhausts all 19,683 orientations of A/B/C with exact 0-helper / 1-helper linear-network closure. Independent Action **40744953469** succeeded and proved the minimum rigorous `pre+out` lower bounds:

```text
A: 31
B: 32
C: 32
```

There are zero <=30 survivors. Exact orbit equivalence transports this to all 18 LB=31 transforms.

### LB=31 support <=5 remaining bookkeeping/search gaps

The exact complementary campaigns are:

1. full-column-rank correction support <=4 (`search_semilinear_exactcorr.py`);
2. rank-four support5 (`search_semilinear_support5.py`);
3. rank-three support5 (`search_semilinear_support5_rank3.py`).

Class A/B rank-four support5 is already fully aggregated: Action **40742805378** read all 18 summaries, covering 39,366 prefix orientations, with `candidates_101=0` and no saved witnesses.

Historical runner cancellations left only bookkeeping/search gaps in exactcorr A/B/C and one Class-C rank3-support5 shard. Dedicated low-parallel workflows are filling exactly those gaps. Cancelled work is not evidence.

If all missing support<=5 summaries close with zero candidates, then the **entire LB=31 retained-core semilinear tier is excluded**: support<=5 by exact campaigns, support>=6 by theorem, all 18 transforms by exact six-orbit symmetry.

### Next tier after LB=31

LB=32 has 30 transforms but only **five exact orbits**. Convenient representatives:

```text
(0x30,3)
(0x0d,0)
(0x5e,0)
(0x65,3)
(0x33,2)
```

## Immediate next steps

1. Finish and aggregate A/B/C support<=5 gap workflows; do not infer zero candidates merely from green job status.
2. If LB=31 closes, move directly to the five LB=32 orbit representatives, first deriving their support-budget cutoffs before launching exact correction search.
3. In parallel, seek a stronger physical lower bound for the remaining direct-core rank4 / six-independent-AND frontier.
4. Recheck Few Shots board and open p008 PRs before any claim or submission.

## Validation protocol for a positive result

A candidate is not a record until it is materialized as a complete <=101-gate certificate, independently checked on all 256 AES bytes by arithmetic inversion plus the AES affine map, accepted by the unchanged Few Shots verifier, and rechecked against the live upstream record immediately before submission.
