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

Inside the Jain five-AND core, current tail factors `w57`, `w56`, `w58`, and `w53` appear directly; these four have rank three, so one additional independent current factor is still needed for a direct four-factor basis.

## Nine tail factors have rank four

For the unchanged abstract inversion core, the nine factors consumed by the final 18 AND gates are

`[w45,w59,w52,w57,w53,w49,w58,w55,w56]`.

They span only four dimensions. Using `[w45,w59,w52,w57]` as a basis, their masks are

`[1,2,4,8,9,13,6,3,14]`.

Thus any four independent factors form a basis of all nine. Once four such factor wires exist, the remaining five factors can be materialized with exactly five XORs; five is also a trivial lower bound because five distinct required factor wires are missing.

This yields a reduced sufficient route to a 17-gate core: synthesize **four independent required factors in at most 12 gates with at most five ANDs**, then append the five-XOR closure. This is a smaller exact problem than the upstream six-AND generic core timeout and than our earlier nine-output 17-gate encoding.

## Fixed-output-layer exclusion

For the 102 certificate's fixed output matrix, the transposed `8 -> 18` problem has 18 required targets, five already equal to inputs. A hypothetical 13-XOR implementation would therefore have no room for helper gates: every one of the 13 remaining targets would have to be produced directly, one per gate. Closure over the required-target set cannot generate all 13 under that constraint, so 13 XORs is impossible for that fixed matrix. The known 14-XOR transpose, hence the 24-gate original output network, is optimal for the fixed matrix. Any output-layer saving must change the surrounding representation rather than resynthesize that same matrix.

## Running exact searches

1. `temp-aes-sbox-core5-template`: four Jain-topology rewiring instances, including current, Jain, and cheap interface bases.
2. `temp-aes-sbox-core5-min`: symmetry-broken 17-gate / five-AND searches over several input bases.
3. `temp-aes-sbox-basis12` (run 40626627456): eight reduced 12-gate four-factor searches on the **current identity input basis**, followed by a deterministic five-XOR closure if SAT. Six of the eight target bases were chosen to reuse as much of the Jain factor structure as possible.

Older exact linear-interface runs aimed at the 103 outer representation are retained as evidence but are not treated as searches over the new 102 outer representation.

## Validation requirement

Any SAT core is only an intermediate candidate. A 101 claim requires: splice into the live 102 certificate; independently evaluate all 256 AES inputs using arithmetic GF(2^8) inversion plus the AES affine map; run the unchanged official p008 verifier; re-sync live board/open PRs; and run Few Shots `tools/check.py` before submission.
