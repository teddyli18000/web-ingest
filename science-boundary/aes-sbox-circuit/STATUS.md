# p008 current status

Last synchronized: 2026-10-27 PDT / 2026-10-28 UTC.

## Live upstream baseline

- Few Shots `data/board.json` is at **102 gates** for p008: `huangxin-design/aes102-field-plane-offsets`, PR #25, verified 2026-10-28T03:00:31Z and merged into `main`.
- Current record chain: 106 baseline -> 105 `csbo98/aes105-nonlinear-resub` -> 104 `HeiGeAi/aes104-odc-resub` -> 103 `fancify/aes103-joint-plane-orientations` -> 102 `huangxin-design/aes102-field-plane-offsets`.
- A fresh p008 PR search found **no open p008 PR** after the 102 merge.
- Therefore any new claim must be **101 gates or fewer**, after re-checking live upstream again.

## What the 102 shot changed

The 102 certificate keeps the same abstract 18-gate / six-AND inversion core as the 103 primary circuit. Its layer accounting is

`18 prelinear + 9 norm AND + 15 middle + 18 core + 18 final AND + 24 output = 102`.

The new savings are in the surrounding linear representation: semilinear input coordinates `P(x)=0x1b*x^16`, product-plane orientations `[1,2,0,0,2,2,2,1,1]`, a five-offset middle construction, and a 24-gate output layer.

## Upstream-overlap rule

Before starting a new route, re-check the live board, open/merged p008 PRs, all merged p008 SHOTs, and any upstream code/artifacts relevant to that route. Do not spend compute reproducing a recorded dead end.

For the current five-AND-core route, the overlap check is complete:

- The 102 shot already tried 1,171,086 local root rewrites on the two 103 circuits, including equal-size substitutions, temporary increases, and up to three-gate replacements. It did not reduce the circuit.
- The 102 shot also reports a generic 17-gate core synthesis with **exactly six ANDs** timing out after 300 seconds.
- The 105 shot enumerated all 20,160 four-bit linear maps for splicing a published five-AND alternative into the **old 106 outer family**, finding compatible 106-gate circuits but no improvement.
- None of those searches covers the present route: a five-AND core aligned to the later 102/103 four-dimensional inversion interface and required to produce the current nine final-product factors.

## Reusable structure from Jain's public 32-AND circuit

Jain's public `sbox106_d34` has AND structure `9 + 5 + 18`. Its five-AND inversion region can be represented as a 17-gate network from four independent inputs spanning exactly the same four-dimensional function space as the 102/103 core inputs.

Relative to canonical current core inputs `(a,b,c,d)`, four independent Jain-side functions are

- `J51 = b XOR c` (mask 6)
- `J49 = a XOR d` (mask 9)
- `J41 = a XOR b XOR d` (mask 11)
- `J48 = c XOR d` (mask 12)

with the fifth nominal function `J50 = a XOR b XOR c` (mask 7) dependent.

Inside the Jain five-AND core, several current tail factors appear directly, but this does **not** give a 17-gate splice by input relabeling alone; see the exact GL screening below.

## Nine tail factors have rank four

For the unchanged abstract inversion core, the nine factors consumed by the final 18 AND gates are

`[w45,w59,w52,w57,w53,w49,w58,w55,w56]`.

They span only four dimensions. Using `[w45,w59,w52,w57]` as a basis, their masks are

`[1,2,4,8,9,13,6,3,14]`.

Thus any four independent factors form a basis of all nine. Once four such factor wires exist, the remaining five factors can be materialized with exactly five XORs; five is also a trivial lower bound because five distinct required factor wires are missing.

This yields a reduced sufficient route to a 17-gate core: synthesize **four independent required factors in at most 12 gates with at most five ANDs**, then append the five-XOR closure. This is a smaller exact problem than the upstream six-AND generic core timeout and than our earlier nine-output 17-gate encoding.

## Exact GL(4,2) screening of Jain `sbox106_d34`

A complete 20,160-map input-GL enumeration was run on exact 16-state truth tables.

- If the three post-core factor XORs are included, the Jain nine-factor set is in the same GL(4,2) orbit as the current nine-factor set for exactly **six** input maps. One map is just the permutation `(J41,J48,J49,J51)=(a,c,d,b)`.
- However, three of Jain's nine final factors are *outside* its 17-gate / five-AND core: `j86=j59 XOR j66`, `j87=j86 XOR j64`, `j88=j87 XOR j67`. Therefore the complete nine-factor exposure is 20 gates, not 17.
- Enumerating **all 17 wires of the original Jain core** under all 20,160 input GL maps proves the unchanged core can directly contain at most **6 of the 9** current factors. The hit distribution is: 0→19,812 maps; 1→294; 2→6; 3→18; 4→12; 5→12; 6→6.
- Consequently, `input basis change + unchanged Jain 17-gate core` is exhaustively ruled out as a 101 route. A successful five-AND 17-gate core must change the five-AND decomposition and/or its operand linear forms, not merely relabel Jain's inputs or linear tail.

This result corrects an initially tempting but invalid direct-splice interpretation: the nine-factor set equivalence is real, but the last three factor XORs were not inside the 17-gate core.

## Public five-AND cores being exhausted before original synthesis

The released `ahrazzle/gf2m-circuits` forward S-box pack has two verified **32-AND** points found so far: `sbox106_d34` and `sbox110_d38`; the other released forward points checked (`sbox106_d24`, 111/112/113/116/121 depth points) use 34 ANDs.

Both released inverse-S-box 109-gate points, `invsbox109_d30` and `invsbox109_d31`, also use **32 ANDs**. Because AES S-box and inverse S-box share inversion up to affine layers, these are legitimate sources of alternate five-AND decompositions.

`analyze_public5_cores.py` was added to identify `9 + 5 + 18` by AND ancestry, extract each four-dimensional core boundary and nine final factors, and screen all 20,160 GL(4,2) input changes against the live-102 factor set. This upstream-reuse screen is prioritized before inventing a new five-AND decomposition.

## Fixed-output-layer exclusion

For the 102 certificate's fixed output matrix, the transposed `8 -> 18` problem has 18 required targets, five already equal to inputs. A hypothetical 13-XOR implementation would therefore have no room for helper gates: every one of the 13 remaining targets would have to be produced directly, one per gate. Closure over the required-target set cannot generate all 13 under that constraint, so 13 XORs is impossible for that fixed matrix. The known 14-XOR transpose, hence the 24-gate original output network, is optimal for the fixed matrix. Any output-layer saving must change the surrounding representation rather than resynthesize that same matrix.

## Running exact searches

1. `temp-aes-sbox-core5-template`: four Jain-topology rewiring instances; completed as solver `unknown`/timeouts, not UNSAT.
2. `temp-aes-sbox-core5-min` (run 40626122929): symmetry-broken 17-gate / five-AND searches over several input bases.
3. `temp-aes-sbox-basis12` (run 40626627456): eight reduced 12-gate four-factor searches on the **current identity input basis**, followed by a deterministic five-XOR closure if SAT.
4. `temp-aes-sbox-core5-set`: a smaller target-set encoding of the 17-gate / five-AND problem using Jain's five-AND time positions and no nine separate output selectors.
5. `temp-aes-public5-orbits`: exact GL(4,2) orbit screening of all four released 32-AND forward/inverse constructions before any new nonlinear decomposition is invented.

Older exact linear-interface runs aimed at the 103 outer representation are retained as evidence but are not treated as searches over the new 102 outer representation.

## Validation requirement

Any SAT core is only an intermediate candidate. A 101 claim requires: splice into the live 102 certificate; independently evaluate all 256 AES inputs using arithmetic GF(2^8) inversion plus the AES affine map; run the unchanged official p008 verifier; re-sync live board/open PRs; and run Few Shots `tools/check.py` before submission.
