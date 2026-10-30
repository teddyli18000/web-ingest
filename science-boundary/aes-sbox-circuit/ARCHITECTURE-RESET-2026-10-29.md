# AES p008 architecture reset after the 101-gate record

Date: 2026-10-29 PDT (GitHub UTC activity 2026-10-30)

## Upstream state

Few Shots PR #31, `chunfeng11221/aes101-nist-interface-resub`, is merged and verified at **101 gates** (`33 AND + 40 XOR + 28 XNOR`, depth 44). The canonical certificate hash is `9371891b3eb422ac1514f067212a5c42d6f07d0a378deb37dad0941de7220093`. A fresh board/open-PR check after the merge found no public p008 score below 101 and no open p008/AES PR.

The shot starts from NIST's public 104-gate, 32-AND circuit `aes-sbox-a32-ad5-g104-gd30-xx72-5`, not from the earlier Few Shots 102 architecture. It first obtains a different 102 seed by optimizing the NIST-native inversion/output interface under a joint semilinear field transform and nine product-plane choices. Full-circuit observability rewriting then finds a saving that crosses the previously separated middle/core/final-multiplier boundary.

The final identity reuses `g30` in a final product because `g29 AND g55 = 0` on all 256 AES inputs, so `g30 AND g55 = (1 XOR g12) AND g55`. This is a complete-circuit saving; it is not evidence for a standalone 17-gate core under the old interface.

## Consequence for our prior exact work

All prior exact exclusions around the merged 102 core remain valid **only for the represented old family**. In particular, the following are useful family-local facts, not global AES lower bounds:

- the old fixed-tail nine-factor ODC relation (`0xfffe` care per factor);
- the five-AND lower bound for that partial core target;
- no free nontrivial GL(4,2) basis wire in that fixed prefix;
- fixed Tay/Boyar-Peralta/Jain inverter splice coverage results;
- exact or bounded searches with the old nine outputs, fixed AND positions, fixed core interface, or old middle/core cuts.

Do not extend those searches merely by increasing timeout or random seeds. PR #31 is direct evidence that a different seed/interface can expose a saving outside those represented spaces.

## Seed-family census

`seed_family_census.py` independently verifies all 256 AES inputs for public seeds and compares exact intermediate functions, AND functions, depth profiles, and a recursive nonlinear-dependency fingerprint.

Validated seeds include:

| seed | gates | AND | linear | AND depth | interpretation |
|---|---:|---:|---:|---:|---|
| Few Shots 101 | 101 | 33 | 68 | 8 | current record, NIST-derived transformed family |
| Few Shots 102 | 102 | 33 | 69 | 7 | preceding field/plane family |
| NIST A32/G103 | 103 | 32 | 71 | 7 | close raw NIST variant |
| NIST A32/G104 | 104 | 32 | 72 | 5 | PR #31 raw starting family |
| NIST A32/G105 | 105 | 32 | 73 | 5 | close raw NIST variant |
| NIST A33/G105 | 105 | 33 | 72 | 4 | close raw NIST variant |
| Jain d24 | 106 | 34 | 72 | 4 | Jain lineage |
| Jain d34 | 106 | 32 | 74 | 6 | Jain lineage |
| NIST A28/G124 | 124 | 28 | 96 | 5 | genuinely different low-AND architecture |

Important correction: the apparent NIST G103 alternative is **not a qualitatively independent family** from G104. Exact truth-table comparison finds G103/G104 share 30 of 32 AND functions and 91 intermediate wire functions. NIST A33/G105 likewise shares 29 AND functions and 96 wires with G104; A32/G105 shares 28 AND functions and 95 wires. These are useful variants of one broad raw NIST family, not independent high-quality seeds.

The Jain d24/d34 variants are also near-identical at the function level (32 shared AND functions, 88 shared wires). The A28/G124 circuit is genuinely distant from both strong lineages, but it is 24 gates above the 100 target, so it is presently an architecture source rather than a direct local-search seed.

## Local full-circuit rewrite check

A full-circuit 1/2-gate observability walk was run on the current 101 and NIST G103 with neutral rewrites and temporary one-gate increases. The 101 shard executed roughly 0.95 million root iterations across four workers and remained at 101. A G103 shard executed roughly 0.94 million iterations and remained at 103; additional G103 shards also completed without a reduction.

These are neighborhood results only. They justify stopping this local representation, not rejecting the seed families globally.

## New construction target

There is no obvious public third 101/102 family ready for local search. We therefore need to *construct* a new high-quality seed by relaxing an architectural boundary.

The first active experiment keeps only an ordered AND skeleton and erases every named linear-layer boundary. `resynth_linear_skeleton.py` represents each AND operand and final AES output as an affine form of primary inputs and prior AND outputs, then globally re-synthesizes all XOR/XNOR helpers across the full staged circuit. Helpers may cross what were previously called prelinear, middle, core, final-multiplier, and output layers.

This is particularly sharp for NIST G103:

```text
32 AND + 71 linear = 103.
```

A globally shared realization with **68 linear gates** would be a 100-gate circuit while retaining the same 32 nonlinear functions. G104 needs four linear savings; A33/G105 needs five; Jain d34 needs six. A failure is only evidence about the selected fixed AND skeleton plus the synthesis heuristic.

## Next representation changes if fixed-skeleton global linear synthesis is flat

1. **Relax AND operands under observability, not only linear materialization.** Treat each nonlinear node's two affine operands as variables constrained only by the complete reachable-state behavior needed downstream. This changes the nonlinear skeleton while retaining its stage count.
2. **Jointly optimize core output forms and the final multiplier.** Do not demand the old nine inverter outputs. Search for a five-AND or six-AND GF(16) inversion realization whose internal wires are chosen for total AES cost, including final products and affine output sharing.
3. **Cross-family hybridization.** Use the NIST-native output family, old Few Shots field/plane transforms, and alternative five-AND inverter skeletons as jointly selectable components rather than fixed modules.
4. **28-AND architecture as a qualitatively different decomposition.** Its current `28 + 96 = 124` cost is too high, but its `10 | 5 | 13` nonlinear split is a distinct search space. Only pursue it with a mechanism capable of removing large linear overhead, not local ODC.

## Public-source context checked

- Few Shots merged PR #31, full SHOT, certificate, verifier/referee discussion, board, and open PR state.
- NIST Circuit Complexity repository current AES S-box tables and SLPs, including A32/G103, A32/G104, A33/G105, and the 28-AND externally contributed family.
- Jain `ahrazzle/gf2m-circuits` verified 106-gate circuits.
- Current NIST Circuit Complexity research page: exact AND optimization remains difficult for vectorial Boolean functions; published circuit search is heuristic/computational.
- Public 2026 exact GF(16)-inversion multiplicative-complexity result: five ANDs is optimal for the 4-bit inversion subproblem. This constrains AND count but does not settle complete AES total gate size or cross-boundary linear sharing.
