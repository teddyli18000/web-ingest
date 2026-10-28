# AES S-box circuit size

## Question

Can the AES S-box be implemented with at most **101** two-input gates over the exact Few Shots basis `{AND, XOR, XNOR}`? Depth is unscored; constants and NOT gates are unavailable except as absorbed by XNOR.

## Upstream-first rule

Before launching any substantial p008 experiment, re-check:

1. live `few-shots/few-shots` `data/board.json`;
2. open/recent p008 or AES PRs;
3. every newer record's complete `SHOT.md` and dead ends;
4. recent commits touching p008;
5. public follow-up branches of the latest breakthrough author when readily available.

Do not spend compute on a family already covered upstream unless the experiment is materially broader or a later outer construction changes the accounting.

## Current state — resynced 2026-10-28 UTC

- **Live record: 102 gates**, `huangxin-design/aes102-field-plane-offsets`, merged PR #25.
- Board updated `2026-10-28T03:02:21Z`; verifier score 102, canonical hash `b47351b8c602d712efc00ec5cebbd6bdb284e1784ac732f5599bb99f985a0b68`.
- Record chain: 106 baseline → 105 → 104 → 103 → **102**.
- Re-check at approximately 03:3x UTC still found no open p008/101 PR. The 102 author's public fork exposed only `main` and the already-merged `codex/aes102-field-plane-offsets` branch at the earlier scan.
- The next valid breakthrough is **101 gates or fewer**.

## Upstream record chain

### 106 → 105 — `csbo98/aes105-nonlinear-resub`

ODC/resubstitution replaced the central inversion region by a six-AND construction. The first nine and final eighteen AND functions stayed unchanged.

Important dead end: the published five-AND alternative core was spliced through all `20160` invertible four-bit linear maps. `60` compatible maps and six 106-gate circuits were found, but no improvement in that old baseline family. Do not repeat this fixed-core/old-outer enumeration.

### 105 → 104 — `HeiGeAi/aes104-odc-resub`

An algebraic sharing identity removed one XOR with 33 ANDs unchanged. Follow-up local ODC and one fixed-template exact instance did not improve further; those are local/template-specific negatives.

### 104 → 103 — `fancify/aes103-joint-plane-orientations`

The successful step jointly changed the surrounding GF(16) representation and the operand bases of nine rank-two norm-product planes while retaining an 18-gate inversion core. Separate field-only or plane-only optimization had failed in restricted models.

Scored decomposition:

```text
17 prelinear + 9 norm AND + 16 middle + 18 core + 18 final AND + 25 output = 103.
```

A supplementary independent 103 had `19 + 9 + 14 + 18 + 18 + 25`. Exact truth-table comparison showed that the two four-wire core input interfaces span the same four-dimensional linear space.

### 103 → 102 — `huangxin-design/aes102-field-plane-offsets`

This is the current base for all new work.

The shot **retains the same 18-gate inversion core** and jointly changes:

- semilinear input coordinates using `P(x) = 0x1b * x^16`;
- orientations of the nine quadratic product planes;
- prelinear, middle and output linear networks.

Product-plane orientations:

```text
[1,2,0,0,2,2,2,1,1]
```

The middle map uses five prelinear offset injections. Scored decomposition:

```text
18 prelinear + 9 norm AND + 15 middle + 18 core + 18 final AND + 24 output = 102.
```

Recorded dead ends from the 102 shot:

- `1,171,086` local root-rewrite attempts on the two 103 circuits, including temporary increases and up to three-gate replacements: no reduction.
- Generic 17-gate core synthesis with exactly six ANDs: 300 s timeout, undecided.
- Randomized product-plane changes at the fixed starting field representation: no qualifying five-offset middle map in tested candidates.
- Most arbitrary semilinear input transforms made the outer linear maps too expensive.

These are not global lower bounds.

## Direct 101 opportunity: replace only the 18-gate core

The merged 102 certificate keeps the same abstract 18-gate inversion core topology as the 103 record. Its four independent core inputs are

```text
q34, q36, q39, q41
```

and the final AND layer consumes nine distinct core factors:

```text
q45, q59, q52, q57, q53, q49, q58, q55, q56.
```

Therefore any 17-gate network producing these nine factors from the same four inputs yields a full 101-gate S-box immediately:

```text
18 + 9 + 15 + 17 + 18 + 24 = 101.
```

This is the cleanest current route.

### Structure of the nine required factors

Exact 16-state truth-table analysis shows that the nine factors have ordinary linear rank four. Taking `q45,q59,q52,q57` as a basis,

```text
q53 = q45 XOR q57
q49 = q45 XOR q52 XOR q57
q58 = q59 XOR q52
q55 = q45 XOR q59
q56 = q59 XOR q52 XOR q57.
```

They are all distinct, and none equals a core input. Consequently any 17-gate direct replacement must expose nine distinct target gate outputs and has room for **at most eight non-target intermediate wires**. The live 18-gate core has nine non-target intermediates. This gives a strong exact-synthesis symmetry break: a 101 core must eliminate one internal helper, not merely rename outputs.

The target space modulo affine input functions also has rank four, so this observation does **not** rule out five-AND circuits; multiplicative complexity five remains possible.

### The current interface is rigid if the outer 102 circuit is fixed

`check_102_free_core_basis.py` evaluates every input and every wire before `q42` in the merged 102 certificate. Among all pre-core wires, the only functions lying in `span(q34,q36,q39,q41)` are exactly

```text
q34, q36, q39, q41.
```

No nontrivial GL(4,2) combination of the core inputs is already available for free. Therefore a direct 101 replacement must use the current interface basis (up to wire permutation). Any nontrivial basis change must be paid for by a jointly resynthesized middle layer and cannot be counted as a free core transformation.

## Known GF(16) inverter families checked against the 102 tail

### Fixed classic Boyar-Peralta 16-gate inverter

The classic inverter has `5 AND + 11 XOR = 16` gates. `check_bp5_against_102.py` exhausts all `20160` GL(4,2) input maps. There are `60` maps whose four outputs span the required inverse-output space, matching the old 105-shot compatibility count exactly. Across all of them, at most **4 of the 9** required 102 tail factors occur as existing wires in the fixed 16-gate circuit.

Thus the known 16-gate inverter plus one appended XOR/XNOR is not a direct 17-gate replacement for the fixed 102 tail. This fixed-core family is already close to the upstream 105-shot search and should not be rerun blindly.

### Known low-depth 17-gate inverter

Boyar-Find-Peralta describe a depth-4 GF(16) inverter with `7 AND + 10 XOR = 17` gates. `check_lowdepth17_against_102.py` reconstructs the AND/XOR realization from their 15-gate NAND circuit and exhausts GL(4,2). Again there are `60` compatible inverse-output maps and the maximum direct factor coverage is only **4 of 9**. It is therefore not a direct fixed-tail 101 drop-in either.

### 2026 five-product multiplicative-complexity construction

A 2026 public exact-MC result supplies another explicit five-product GF(16) inversion decomposition. It was independently checked on all 16 field elements. Its named product/affine signals do not expose more of the nine 102 tail factors under compatible linear maps than the classic family, and realizing its multi-input affine forms with the allowed two-input gates carries substantial linear cost. It is currently not competitive for the fixed-tail 17-gate target; retain it only as a possible alternative multiplicative skeleton if a future joint linear synthesis makes it relevant.

## Jain five-AND relation

Jain's verified `sbox106_d34` has 32 ANDs and contains a 17-gate inversion region with exactly five ANDs and twelve XORs. Its nominal five incoming functions have rank four.

Relative to the abstract live-core basis `(a,b,c,d)`, one independent Jain input basis is

```text
b XOR c
a XOR d
a XOR b XOR d
c XOR d
```

with the fifth nominal input dependent. Thus a five-AND inversion architecture lives on the same four-dimensional function space. This does **not** prove that the nine factors required by the 102 tail can all be exposed within 17 gates.

An independent enumeration reproduced the predecessor's `20160 → 60` compatible-map count, validating the basis/bit-order interpretation. Fixed Jain/BP splice enumeration is upstream-covered; only materially broader free-topology synthesis is worth pursuing now.

## Experiments completed here

### Historical 103 ODC

Before the 102 merge:

- one-gate ODC: `1,349,114` attempts, `1,414` accepted 103 states, no deletion;
- two-gate boundary ODC: `651,871` attempts, `2,771` accepted 103 states, no reduction.

The 102 shot reports an even larger local-rewrite failure and escaped structurally. Do not add more generic ODC runtime to this family.

### Historical 103 movable-window SMT

Eight 1200-second instances over `15+18`, `16+17`, and `14+19` all returned `unknown / timeout`; no SAT certificate and no UNSAT proof. This route is superseded by the merged 102 outer construction and should not simply be extended.

### Historical 103 linear-interface search

Alternative four-wire bases were found on the old 15-signal middle cut, but the 102 shot already improved the joint prelinear/middle/output design. These old-cut searches are no longer primary.

### Fixed five-AND position templates

Four 600-second Z3 instances using the Jain five-AND gate-position pattern with rewired operands all returned `unknown / timeout`. In light of the upstream fixed-core GL(4,2) work, this template family is now secondary; do not extend it merely with more seeds.

## Current route toward 101

### Priority 1 — focused free-topology 17-gate core search on the merged 102

Search exact 16-state truth tables from the **current** interface `q34,q36,q39,q41` for a 17-gate DAG exposing all nine required factors.

Do not restrict to five ANDs: a 101 core only needs 17 total gates. The current 18-gate core has six ANDs, so both of these are live cases:

- 17 gates with exactly 5 ANDs;
- 17 gates with exactly 6 ANDs (the upstream 300-second attempt timed out, so this remains undecided).

`synth_core17_array_z3.py` uses an Array/Select truth-table encoding, explicit distinct target-wire selectors, no duplicate wire functions and no dead gates. The first focused campaign runs 5-AND and 6-AND cases with and without XNOR. Any SAT model is automatically passed to `splice_core_into_102.py`, which constructs a 101-gate full certificate and independently checks all 256 AES bytes before the official Few Shots verifier runs.

### Priority 2 — extend the 102 field/plane-offset search only if needed

If the direct current-interface core route stalls, broaden the 102 joint search over:

- semilinear input transforms;
- nine product-plane orientations;
- prelinear cost;
- middle offset count;
- transposed output cost;
- and, if justified, a different core input basis together with its actual middle-layer cost.

Target a net one-gate saving from `18 prelinear + 15 middle + 24 output`, or a joint middle/core saving. Do not retry random plane changes at a fixed field representation; upstream already recorded that as a dead end.

## Verification protocol for any 101 candidate

1. Start from merged `huangxin-design/aes102-field-plane-offsets/certificate.json`.
2. Independently evaluate all 256 bytes against arithmetic AES inversion modulo `0x11b` plus the affine map.
3. Run the unchanged Few Shots p008 verifier.
4. Re-sync live main, board, recent commits and open p008 PRs immediately before claiming.
5. Run `tools/check.py` under the Few Shots submission rules.
6. Only then prepare/publish a shot.

## Sources

- Few Shots live `data/board.json`.
- Merged p008 105/104/103/102 `SHOT.md` files and certificates.
- Few Shots PR #25 and verification/referee discussion.
- Jain public `ahrazzle/gf2m-circuits`, especially `sbox106_d34.json`.
- Boyar-Peralta, *Logic Minimization Techniques with Applications to Cryptology* (classic 5-AND/11-XOR GF(16) inverter).
- Boyar-Find-Peralta, *Small Low-Depth Circuits for Cryptographic Applications* (7-AND/10-XOR low-depth GF(16) inverter and NAND form).
- 2026 public work on exact multiplicative complexity of GF(16) inversion, used only after independent truth-table verification.
- NIST Circuit Complexity / `usnistgov/Circuits` AES resources.
- FIPS-197.

## Work log

### 2026-10-27 PDT

- Synced through the 103 record; ran ODC and movable-window experiments with no reduction.
- Re-synced upstream during the work and found merged PR #25 at 102 gates. Immediately changed target to 101 and marked 103-specific search routes as superseded.
- Read the full 102 shot, certificate structure, PR verifier result, and old 105 five-AND dead end.
- Confirmed the 102 certificate retains the same 18-gate inversion core and same nine abstract tail factors, so a 17-gate core replacement is a direct 101 route.
- Proved the nine factors have rank four with the explicit XOR relations above; a 17-gate direct replacement has at most eight non-target intermediates.
- Proved no alternate nontrivial core-basis wire is already free in the 102 prefix.
- Exhausted the classic 16-gate and known low-depth 17-gate GF(16) inverter families under all GL(4,2) input maps; neither directly exposes more than four of the nine fixed-tail factors.
- Independently verified a newer 2026 five-product GF(16) decomposition and found no immediate fixed-tail size advantage.
- Re-checked the live board/open PRs before continuing; record remained 102 with no open p008 PR.
- Launched the focused exact current-interface 17-gate search for both 5-AND and 6-AND cases, with automatic 101 splicing and verification on SAT.
