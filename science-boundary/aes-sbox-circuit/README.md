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
- Re-checks after the 102 merge found no open p008/101 PR. The record author's public fork exposed only `main` and the already-merged `codex/aes102-field-plane-offsets` branch at the scan time.
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

Therefore any 17-gate network producing observationally valid versions of these nine factors from the same four inputs yields a full 101-gate S-box immediately:

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

They are all distinct, and none equals a core input. Consequently any 17-gate direct replacement must expose nine distinct target gate outputs on the care set and has room for **at most eight non-target intermediate wires**. The live 18-gate core has nine non-target intermediates. A 101 core must eliminate one internal helper, not merely rename outputs.

### Complete fixed-tail observability relation

`analyze_102_factor_odc.py` reconstructs the full merged-102 certificate, independently checks all 256 AES bytes, and then treats the nine core factors as a boundary into the fixed `q60..q101` tail.

The four-bit core state `(q34,q36,q39,q41)` occurs with this distribution over the 256 AES inputs:

```text
0000: 1 preimage
all 15 nonzero states: 17 preimages each
```

For each core state the script flips each of the nine boundary factors, re-evaluates all eight final outputs, and forms the linear error map from nine factor-error bits to observable tail-output errors. The exact joint result is:

```text
core state 0000: error-map rank 0, kernel dimension 9
core states 0001..1111: error-map rank 9, kernel dimension 0
```

So at `0000` **all 511 nonzero coordinated factor-error patterns are unobservable**; at every nonzero state no nonzero coordinated factor error is hidden. The complete fixed-tail relation is therefore exactly:

- all nine factors arbitrary at core state `0000`;
- all nine factors exact on the other 15 core states.

Equivalently, every target has care mask `0xfffe`. This is a complete joint ODC characterization, not a one-factor heuristic.

### ODC does not reduce the multiplicative-complexity lower bound below five

`prove_102_odc_mc5.py` gives a solver-free lower bound. Take the independent factor basis `(q45,q59,q52,q57)`. Each of its four outputs may independently choose its value at `0000`, giving 16 possible completions of the four-output partial function.

The script exhausts all 16 completions and verifies:

- nonlinear quotient rank modulo affine functions is always 4;
- every nonzero scalar combination has algebraic degree at least 3.

A function computable modulo affine terms with at most one AND has degree at most 2. Therefore every nonzero class in the four-dimensional target nonlinear space needs at least two ANDs. In a minimal `r`-AND XAG, the first AND-output class cannot lie in that target subspace; packing that independent one-dimensional class together with the four-dimensional target space gives

```text
r >= 4 + 1 = 5.
```

Thus even with the complete zero-state don't-care, **at least five AND gates are necessary**. The interesting minimal 17-gate case is consequently `5 AND + at most 12 XOR/XNOR`. A `6 AND + 11 linear` 17-gate solution remains possible as well.

### The current interface is rigid if the outer 102 circuit is fixed

`check_102_free_core_basis.py` evaluates every input and every wire before `q42` in the merged 102 certificate. Among all pre-core wires, the only functions lying in `span(q34,q36,q39,q41)` are exactly

```text
q34, q36, q39, q41.
```

No nontrivial GL(4,2) combination of the core inputs is already available for free. Therefore a direct 101 replacement must use the current interface basis (up to wire permutation). Any nontrivial basis change must be paid for by a jointly resynthesized middle layer and cannot be counted as a free core transformation.

## Known GF(16) inverter families checked against the 102 tail

### Tay et al. 15-gate inverter — strongest fixed published total-size baseline found

Tay et al., *Construction of a Low Multiplicative Complexity GF(2^4) Inversion Circuit for Compact AES S-Box* (TENCON 2018), publish the full inversion equations `M23..M37`. Reconstructed directly from the paper, the inverter uses

```text
5 AND + 10 XOR = 15 gates.
```

`check_tay15_against_102.py` exhausts all `20160` GL(4,2) input maps. Exactly `60` maps have inverter-output span compatible with the merged-102 inverse-output space. Across those maps:

- maximum exact coverage of the nine fixed-tail factors by existing Tay15 wires: **4/9**;
- maximum coverage under the complete `0xfffe` care projection: **4/9**.

Therefore the **fixed published Tay15 network plus only two appended gates cannot be a direct 17-gate replacement**: two extra gates can expose at most two additional distinct factor functions, for at most six of nine. The value of Tay15 is structural: inversion itself needs only 15 total gates in this representation, so a 17-gate solution—if it exists—has only two gates of overhead for exposing the special AES-tail factor set. It likely requires a different member of the multiplicatively optimal inverter family, not post-processing this fixed network.

### Fixed classic Boyar-Peralta 16-gate inverter

The classic inverter has `5 AND + 11 XOR = 16` gates. `check_bp5_against_102.py` exhausts all `20160` GL(4,2) input maps. There are `60` maps whose four outputs span the required inverse-output space, matching the old 105-shot compatibility count exactly. Across all of them, at most **4 of the 9** required 102 tail factors occur as existing wires; the complete ODC projection does not improve this maximum.

Thus the known 16-gate inverter plus one appended XOR/XNOR is not a direct 17-gate replacement. This fixed-core family is already close to the upstream 105-shot search and should not be rerun blindly.

### Known low-depth 17-gate inverter

Boyar-Find-Peralta describe a depth-4 GF(16) inverter with `7 AND + 10 XOR = 17` gates. `check_lowdepth17_against_102.py` reconstructs the AND/XOR realization from their 15-gate NAND circuit and exhausts GL(4,2). Again there are `60` compatible inverse-output maps and the maximum direct factor coverage is only **4/9**, exact or care-projected. It is therefore not a direct fixed-tail 101 drop-in.

### Jain five-AND relation

Jain's verified `sbox106_d34` has 32 ANDs and contains a 17-gate inversion region with exactly five ANDs and twelve XORs. Its nominal five incoming functions have rank four. Relative to the abstract live-core basis `(a,b,c,d)`, one independent Jain input basis is

```text
b XOR c
a XOR d
a XOR b XOR d
c XOR d
```

with the fifth nominal input dependent. An independent enumeration reproduced the predecessor's `20160 → 60` compatible-map count, validating basis/bit ordering. Fixed Jain/BP splice enumeration is upstream-covered; only materially broader free-topology synthesis is worth pursuing.

### 2026 five-product multiplicative-complexity construction

A 2026 public exact-MC result supplies another explicit five-product GF(16) inversion decomposition. It was independently checked on all 16 field elements. Its named product/affine signals do not expose more of the nine 102 tail factors under compatible linear maps than the older families, and realizing its multi-input affine forms with the allowed two-input gates carries substantial linear cost. Retain it only as an alternative multiplicative skeleton if future joint linear synthesis makes it relevant.

## Experiments completed here

### Historical 103 ODC and window searches

Before the 102 merge:

- one-gate ODC: `1,349,114` attempts, `1,414` accepted 103 states, no deletion;
- two-gate boundary ODC: `651,871` attempts, `2,771` accepted 103 states, no reduction;
- eight 1200-second movable-window SMT instances over `15+18`, `16+17`, and `14+19`: all `unknown / timeout`;
- old-cut linear-interface searches.

The 102 shot reports an even larger local-rewrite failure and escaped structurally. These 103-specific routes are superseded; do not add runtime to them.

### Fixed five-AND position templates

Four 600-second Z3 instances using the Jain five-AND gate-position pattern with rewired operands all returned `unknown / timeout`. In light of the upstream fixed-core GL(4,2) work, this template family is secondary; do not extend it merely with more seeds.

### Focused strict 17-gate search

The first strict current-interface `6 AND + XOR-only` focused instance was extended to 900 seconds and returned `unknown / timeout`, not UNSAT. This confirms the upstream six-AND 300-second case remains difficult rather than ruled out. Do not simply lengthen the same encoding again.

## Current route toward 101

### Priority 1 — focused free-topology 17-gate core search on the merged 102

Search exact 16-state / complete-ODC truth tables from the **current** interface `q34,q36,q39,q41` for a 17-gate DAG exposing all nine required care-restricted factors.

The main live cases are:

- `5 AND + 12 XOR/XNOR` — five ANDs is the proven nonlinear minimum;
- `6 AND + 11 XOR/XNOR` — logically possible; upstream and one local strict instance timed out, not disproved.

`synth_core17_array_z3.py` uses an Array/Select truth-table encoding, explicit distinct target-wire selectors, no duplicate wire functions and no dead gates. `--odc-zero` enforces the complete fixed-tail relation by comparing target truth tables only on care mask `0xfffe`. Any SAT model is passed to `splice_core_into_102.py`, which constructs a 101-gate full certificate and independently checks all 256 AES bytes before the official Few Shots verifier runs.

The key structural interpretation from the prior-art survey is now sharper: Tay15 proves ordinary inversion can be done in 15 gates, so the open problem is not “find a small inverter.” It is **jointly synthesize a near-minimum inverter while exposing nine specific AES-tail factors as internal wires with only two gates of total overhead**.

### Exact-synthesis tooling cross-check

Alan Mishchenko's current `resub` repository exposes ABC `twoexact`, a true multi-output exact XAIG synthesizer that accepts Boolean relations. `make_102_core_relation.py` generates both the exact 4-input/9-output relation and the complete zero-state ODC relation. A 17-node `twoexact` cross-check is running as a topology hint.

Caution: ABC XAIG/AIG nodes allow complemented AND edges for free, which is a strictly wider gate model than p008. A `twoexact` 17-node SAT result is therefore only a candidate/topology generator; it must be translated and re-costed in `{AND,XOR,XNOR}` before it can count.

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
- Tay et al., *Construction of a Low Multiplicative Complexity GF(2^4) Inversion Circuit for Compact AES S-Box*, TENCON 2018; full published M23–M37 equations were independently reconstructed and checked.
- Boyar-Peralta, *Logic Minimization Techniques with Applications to Cryptology*.
- Boyar-Find-Peralta, *Small Low-Depth Circuits for Cryptographic Applications*.
- 2026 public exact multiplicative-complexity work on GF(16) inversion, used after independent truth-table verification.
- Alan Mishchenko et al. `resub` / ABC `twoexact` exact-synthesis resources.
- NIST Circuit Complexity / `usnistgov/Circuits` AES resources.
- FIPS-197.

## Work log

### 2026-10-27 PDT

- Synced through the 103 record; ran ODC and movable-window experiments with no reduction.
- Re-synced upstream during the work and found merged PR #25 at 102 gates. Immediately changed target to 101 and marked 103-specific search routes as superseded.
- Read the full 102 shot, certificate structure, PR verifier result, and old 105 five-AND dead end.
- Confirmed the 102 certificate retains the same 18-gate inversion core and nine abstract tail factors, so a 17-gate core replacement is a direct 101 route.
- Proved the nine factors have rank four with explicit XOR relations; a 17-gate direct replacement has at most eight non-target intermediates.
- Proved no alternate nontrivial core-basis wire is already free in the 102 prefix.
- Exhausted classic BP16, low-depth BFP17, Jain-related and newer five-product inverter families where concrete equations were available; none is a direct fixed-tail replacement.
- Recovered the full Tay et al. 15-gate `5 AND + 10 XOR` GF(16) inverter from the published paper. Exhaustive GL(4,2) checking found 60 compatible maps but at most 4/9 tail factors exposed, exact or ODC.
- Proved the complete merged-102 boundary ODC: all nine factors arbitrary only at core state `0000`, exact jointly at all 15 nonzero states.
- Proved solver-free that the partial/ODC inversion target still needs at least five AND gates; 4-AND search is theoretically redundant.
- Launched focused strict and ODC current-interface 17-gate searches for 5-AND and 6-AND cases, with automatic 101 splicing and official verification on SAT.
- Launched ABC `twoexact` exact/ODC relation cross-check only as a wider-gate-model topology hint.
