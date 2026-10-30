# AES S-box circuit size

## Question

Can the AES S-box be implemented with at most **100** two-input gates over the exact Few Shots basis `{AND, XOR, XNOR}`? Depth is unscored; constants and NOT gates are unavailable except as absorbed by XNOR.

## Upstream-first rule

Before substantial p008 work, re-check the live Few Shots board, recent/open p008 PRs, and every newer record's complete `SHOT.md` including dead ends. Do not extrapolate a restricted exact exclusion into a global lower bound.

## Current state — resynced 2026-10-29 PDT

- **Live verified record: 101 gates**, `chunfeng11221/aes101-nist-interface-resub`, merged PR #31.
- Official board: score 101, verified `2026-10-29T10:51:03Z`, recorded `2026-10-29T10:52:38Z`.
- Circuit: **33 AND + 40 XOR + 28 XNOR = 101**, depth 44.
- Canonical hash reported by the merged shot/verifier: `9371891b3eb422ac1514f067212a5c42d6f07d0a378deb37dad0941de7220093`.
- Record chain: 106 → 105 → 104 → 103 → 102 → **101**.
- Next valid breakthrough: **100 gates or fewer**.

The search strategy has been reset around **architecture diversity + whole-circuit interfaces**, not deeper local search around the old merged 102.

## Main lesson from 101

The 101 breakthrough invalidates our previous search prioritization, not our old exact calculations.

Our recent work fixed the merged 102 architecture too aggressively: the four-wire core interface, the nine fixed tail factors, the old inversion-core family, and the separation between middle/core/final multiplication. Exact screens around that representation remain valid **only for that represented family**.

The successful work first moved to a different high-quality seed lineage and only then used full-circuit observability:

1. Start from the public NIST `aes-sbox-a32-ad5-g104-gd30-xx72-5` circuit, with 32 ANDs and a 19-gate five-AND inversion core exposing a different set of native output forms.
2. Native-core ODC/resub gives an 18-gate six-AND core and a 103-gate full circuit.
3. Joint field/product-plane optimization uses field map `P(x)=0x3f*x^32`, chooses the nine product-plane orientations, and resynthesizes surrounding linear maps with offset injections. This creates an **independent 102 seed**:

```text
17 prelinear + 9 norm AND + 15 middle + 18 core + 18 final AND + 25 output = 102.
```

4. Full-circuit observability/resubstitution then finds 101 after 92,027 root-rewrite iterations. The saving crosses a boundary the earlier decomposition treated as separate. In the final circuit:

```text
g29 = g23 AND g28
g30 = XNOR(g12, g29)
g29 AND g55 = 0  on all 256 inputs
```

Hence `g30 AND g55 = (1 XOR g12) AND g55`; `g30`, already needed by the core-side logic, can also feed the final multiplication side and one linear gate disappears.

The durable research principle is now: **seed architecture and interface placement are optimization variables**. ODC/resub is a second-stage operator after producing a structurally useful seed, not the primary search space by itself.

## PR #31 dead ends — preserve their scope

The complete 101 shot records these negatives:

- extensive local rewriting/function-space enumeration/gate-level synthesis around the earlier 102 core did not find the breakthrough;
- reducing AND count alone was insufficient: a five-AND abstract core materialized into a larger full circuit after XOR cost was charged;
- keeping the old nine core outputs made the NIST core expensive to substitute directly;
- for the new native output forms, fixed-core search over **2,040 semilinear input transforms × all `3^9` product-plane orientations** did not construct 101 under the bounded linear-network synthesis used, although it did construct the independent 102 seed;
- small exact core windows excluded restricted replacements; larger windows and fixed-AND-position problems timed out;
- two bounded beam searches in selected nonlinear function spaces found no 17-gate core.

None is a global lower bound for 100.

## Scope of our pre-101 exact exclusions

The existing documents in this directory remain useful evidence, but they are explicitly scoped to old represented families:

- `EXACT-SCREENS-2026-10-28.md` and the `JOINT-DECOUPLED-*` notes: fixed/transported interfaces around the old 102 decomposition;
- `AFFINE-CORE5.md`, `CORE6-*`, `RANK3-SUPPORT5.md`: restricted old-interface core families and their exact screens;
- old ODC/window runs: neighborhoods of the previous 103/102 lineages.

In particular, the old merged-102 fixed-tail results remain true for that architecture: complete zero-state ODC (`0xfffe` care), the five-AND lower bound for that partial target, no free nontrivial GL(4,2) core-basis wire in that prefix, and the limited factor coverage of published 15–17 gate GF(16) inverter networks. They do **not** rule out a 100-gate circuit whose interfaces, nonlinear forms, or seed lineage differ.

## Seed-family census

`seed_family_census.py` independently parses NIST NCFF circuits and Few Shots JSON certificates, normalizes bit order, checks all 256 AES inputs, and compares exact intermediate truth functions plus nonlinear dependency shapes.

First validated census (Action run `40991160742`):

- NIST A32/G103: 103 gates = 32 AND + 61 XOR + 10 XNOR, AND depth 7;
- NIST A32/G104: 104 gates = 32 AND + 67 XOR + 5 XNOR, AND depth 5;
- Few Shots 101: 33 AND + 40 XOR + 28 XNOR, AND depth 8;
- old Few Shots 102/103: 33 AND with identical AND-shape hash in this census.

Exact-function overlap gives a useful calibration:

- NIST G103 vs G104 share **30/32 AND functions** (Jaccard `0.882353`) but have different dependency shapes. G103 is therefore a strongly re-interleaved sibling of the NIST lineage, not a wholly independent nonlinear family.
- Few Shots 101 vs NIST G103: **0 shared AND functions**.
- Few Shots 101 vs NIST G104: **0 shared AND functions**.
- old Few Shots 102 vs 103: 15 shared AND functions and the same AND-shape hash.

So the successful field/representation change in PR #31 genuinely moved the full circuit into a different nonlinear function basis. This is exactly the kind of architecture shift future search should seek.

### Extended census

Action `40991496201` validated the near-frontier NIST A32/A33/A34 set. A32/G103,G104,G105,G109 and A33/G105,G108 form one high-overlap nonlinear family; for example:

- A32/G103 vs G104: `30/34` AND Jaccard `0.882353`;
- A32/G103 vs G105: `27/37`, `0.729730`;
- A32/G104 vs A33/G105: `29/36`, `0.805556`;
- A32/G105 vs G109 use the same 32 AND functions and dependency-shape hash;
- A33/G105 vs G108 use the same 33 AND functions and dependency-shape hash.

NIST A34/G110 is a distinct nonlinear family:

- 110 gates = 34 AND + 73 XOR + 3 XNOR;
- AND depth 4, profile `9,3,4,18`;
- exact AND overlap with A32/G103: **0**;
- overlap with A32/G104: **1**;
- overlap with A32/G105/G109 or A33/G105/G108: **3**;
- overlap with merged 101: **0**.

The first extended-census attempt also included an A28 control, but that file uses NIST `U/S` naming rather than the `x/y` convention handled by the initial parser. The A28 entry was removed rather than treating a parser failure as scientific evidence. Current extended results refer only to the uniformly parsed A32/A33/A34 set.

At least three useful representation domains are therefore distinguished:

1. NIST main A32/A33 near-frontier family;
2. PR #31's field/plane transformed 101 family;
3. NIST A34/G110 nonlinear family.

See `ARCHITECTURE-CENSUS-2026-10-29.md`.

## Whole-circuit released-AND representation

`released_and_skeleton.py` removes named linear boundaries from a circuit. Any `{AND,XOR,XNOR}` circuit is represented as:

- eight primary inputs;
- an ordered sequence of AND atoms `A_i`;
- two affine operand forms for every `A_i`, over the primary inputs and already released `A_j`;
- eight final affine output forms.

Thus an XOR/XNOR helper is an implementation choice, not intrinsically a `prelinear`, `middle`, `core`, `final multiplier`, or `output` wire. A helper can in principle persist across all those boundaries.

A first released/deadline greedy synthesizer was deliberately calibrated before any large transform sweep. It failed calibration badly:

- merged FS101: reconstructed only **120** gates versus 101;
- NIST G103: reconstructed only **135** versus 103.

Therefore this greedy is **not** used to infer that any transported skeleton is expensive. The representation remains useful; that synthesizer is rejected as too weak.

### Semilinear whole-skeleton proxy

`scan_semilinear_skeletons.py` scans all 2,040 maps `P(x)=c*x^(2^k)` and measures affine-support / common-pair structure of all AND operand and final-output forms. This is only a seed generator, not a real linear-gate cost oracle.

Action `40992444133` found:

- NIST G103 best structural proxy: `(c=57,k=6)`;
- NIST G104 independently selects the same `(57,6)`;
- merged FS101 best: `(92,4)`, identity rank 11;
- A34/G110 best: `(197,1)`, identity rank 187.

Crucially, PR #31's actually successful map `(0x3f,5)` ranks poorly under this proxy (roughly 1509 on FS101 and 1372 on G103). Therefore support sparsity cannot replace real synthesis. The repeated `(57,6)` selection inside the NIST-main family is only a candidate-generation signal.

## Exact AND-care transfer around 101

The final PR #31 saving suggests the exact identity for an AND `y=u&v`: replacing `u` with `w` is legal iff `(u XOR w)&v=0` on all 256 inputs.

`mine_and_care_aliases.py` exhaustively searched every AND operand in three structural domains, including every earlier existing wire and every one-new-XOR/XNOR helper.

Action `40992283892`:

- A34/G110: no direct alias; about 90 one-helper care matches, none strictly reduce 110;
- NIST G103: no direct alias; 76 one-helper care matches, none strictly reduce 103;
- merged FS101: exactly one direct neutral alias and 107 one-helper care matches, none strictly reduce 101.

The unique FS101 alias is:

```text
AND gate index 53, second operand: g52 -> g50
care states: 68 / 256
```

`make_fs101_care53_seed.py` freezes this variant. Action `40992848614` independently checks all 256 inputs and the unchanged Few Shots verifier returns:

```json
{"valid":true,"score":"101","canonical_hash":"809241a987d8fb986125782715485ed2e2975233b4c16d5196c57842b8975a23","message":"ok"}
```

This differs from the merged 101 hash and is therefore a second official-valid structural 101 seed, not a renaming.

`enumerate_and_care_neutral.py` then exhaustively enumerated the same direct/one-helper ≤101 neighborhood around both seeds (Action `40992895931`):

- original 101: 298,896 helper expressions tested; the only kept ≤101 neighbor is `g52 -> g50`;
- care53 101: 298,896 helper expressions tested; the only kept ≤101 neighbor is the reverse `g50 -> g52`;
- neither side contains a 100-gate candidate.

So this exact one-helper AND-care graph is a **two-node island**. Do not spend more compute extending this same neighborhood. This says nothing about wider multi-gate or architecture-changing rewrites.

## Hybrid nonlinear-atom pool

`hybrid_and_pool.py` aligns the NIST G103 and G104 AND outputs by exact Boolean truth function, pools their known affine factorizations, and asks whether a 32-atom subset can be topologically realized and linearly span all AES outputs.

Action `40993221045`:

- union: 34 distinct AND functions;
- shared: 30;
- all 30 shared atoms have multiple source factorizations;
- all `C(34,32)=561` 32-atom subsets tested;
- exactly **2** atom subsets are feasible under the pooled known factorizations: the original G103 set and the original G104 set.

Thus there is no third 32-atom **subset** hybrid in this restricted pool. This does not exclude new AND functions or new factorizations. It instead exposes the next freedom: transfer the alternate G103/G104 factorization of a shared atom while keeping the nonlinear atom set fixed.

`transfer_and_factorizations.py` implements that cross-seed transfer, allowing the alternate factors when they are already earlier target wires or can be synthesized by at most two new XOR/XNOR helpers, followed by pruning. Action `40993326479` is active.

## Current hypotheses toward 100

### H1 — architecture diversity before local depth

A 102–110 circuit with a meaningfully different nonlinear skeleton can be more valuable than another neutral mutation of the record if it exposes a new whole-circuit linear sharing opportunity. Current descriptors include exact AND-function overlap, AND dependency shape/depth, semilinear coordinate, and cross-boundary care identities.

### H2 — 33 AND + 67 linear gates within the current transformed skeleton

The merged record has 33 AND + 68 linear gates. `synthesize_fixed_and_schedule_z3.py` removes the hand-written linear boundaries and asks Z3 to synthesize all affine interfaces globally for the fixed ordered 33-AND skeleton.

The first exact family preserves the original AND-release schedule but deletes one linear slot from one nonempty interval at a time. A SAT instance yields 67 linears + 33 AND = **100**; UNSAT excludes only that release/schedule template; timeout/`unknown` is only a solver limitation.

Workflow `temp-aes-fs101-z3-67linear.yml`, run **`40992776375`**, uses 8 runner shards and up to four Z3 processes per runner. Any SAT model is reconstructed as a full circuit, independently checked on all 256 inputs, and sent to the official Few Shots verifier.

If this fixed schedule is exhausted, the next search will move linear slots between adjacent AND-release intervals while keeping total linear cost 67, rather than treating the original schedule as architectural truth.

### H3 — 32 AND + 68 linear gates from a NIST-family representation

NIST G103 is already 32 AND + 71 linear. Reaching 100 requires three linear savings rather than changing AND count. The current boundary-free full-circuit search uses G103 as a complete seed; factorization transfer and semilinear transport are additional ways to generate structurally different 32-AND seeds before applying compression.

### H4 — search an archive of representation niches, not one incumbent

The 2026-10-14 Yoshan work on S-box co-synthesis independently supports a quality-diversity view: maintain multiple algebraic/circuit seed classes, evolve DAGs, then compress with cross-DAG CSE and SMT sub-DAG shaving. Yoshan optimizes a broader S-box design problem and does not solve fixed AES G≤100, so its results are not imported as a record claim. Its search-space lesson is directly relevant: preserve structurally distinct complete representations instead of collapsing all compute onto one best circuit.

A future p008 archive should keep the best complete AES circuits per nonlinear family / coordinate / dependency-shape niche and use ODC or sub-DAG shaving only after the archive has architecture diversity.

## Active experiments

### Alternate-seed full-circuit resubstitution

`search_arch_seed.py` is boundary-free: it accepts a complete verified seed, computes exact 256-bit observability masks, allows neutral moves and bounded temporary `+1` expansions, keeps searching after intermediate improvements, and stops only at target 100.

Workflow `.github/workflows/temp-aes-arch-seed-resub.yml`, run **`40991271507`**, runs four CPU workers per runner over NIST G103 and the merged 101. This is a second-stage probe, not the main search-space definition. If it returns no improvement, do not simply scale the same random walk.

### Global 67-linear Z3 synthesis

Run **`40992776375`** is the main direct 100 campaign at this checkpoint: 8 runner shards × up to four Z3 processes, fixed 33-AND functions/order but no named linear stage boundaries.

### Cross-seed AND factorization transfer

Run **`40993326479`** transfers alternate factorizations of the 30 shared G103/G104 nonlinear atoms into the other complete circuit and prunes. This tests whether two high-quality sibling architectures contain compatible local nonlinear forms that neither original circuit exploited globally.

## What not to do next

- Do not extend old fixed-102 core SAT/ODC merely because a timeout was inconclusive.
- Do not treat growing exact-exclusion coverage around one interface as progress toward a global 100 lower bound.
- Do not optimize AND count independently of linear/interface cost.
- Do not preserve `prelinear | middle | core | final multipliers | output` as a hard partition when searching for rewrites.
- Do not call NIST G103 a wholly independent family: the census shows 30/32 AND functions shared with G104.
- Do not use affine-support sparsity as a surrogate for physical gate count: it ranks PR #31's successful map poorly.
- Do not extend the exact one-helper care-neutral graph: it is already a two-node island.
- Do not infer anything from released-AND greedy failures until a synthesis method reproduces the baseline linear cost.

## Verification protocol for any ≤100 candidate

1. Re-sync live Few Shots main/board/open p008 PRs.
2. Independently evaluate all 256 bytes against arithmetic AES inversion modulo `0x11b` plus the affine map.
3. Run the unchanged Few Shots p008 verifier.
4. Freeze the exact certificate and search seed/provenance.
5. Run the repository submission checks required by Few Shots.
6. Only then prepare/publish the shot.

For an exact UNSAT claim that materially narrows the frontier, prefer a proof-producing/checkable encoding when practical; a solver timeout is never an exclusion.

## Sources

- Few Shots live `data/board.json` and merged PR #31.
- `aes101-nist-interface-resub/SHOT.md` and certificate.
- Earlier Few Shots 105/104/103/102 shots and certificates.
- NIST `usnistgov/Circuits` AES S-box NCFF files and README.
- NIST Boyar–Peralta implementation sources and current AES circuit challenge page.
- Yoshan, IACR ePrint 2026/2488, for architecture-diverse co-synthesis methodology.
- Existing topic-local exact-screen notes, retained with their represented-family scope.

## Work log

### 2026-10-29 PDT

- Re-synced after PR #31 merged; board confirms verified live score 101.
- Read the complete 101 shot and recorded its dead ends and the cross-boundary identity responsible for the final saving.
- Reclassified all old fixed-interface/core exact results as family-scoped negatives, not global evidence against 100.
- Added seed-family census and independently verified NIST G103/G104 plus Few Shots 101/102/103 on all 256 inputs.
- Extended census to NIST A32/A33/A34 and identified A34/G110 as a third distinct nonlinear family.
- Added a released-AND whole-circuit representation; rejected its first greedy synthesizer after baseline calibration failed (FS101→120, G103→135).
- Scanned all 2,040 semilinear coordinates structurally; NIST G103/G104 both select `(57,6)` under the proxy, but the proxy is explicitly not a gate-cost oracle.
- Exhaustively mined direct/one-helper AND-care substitutions; found and officially verified a second 101 seed (`g52→g50`, canonical hash `809241...a23`).
- Exhaustively closed that one-helper neutral family and proved it is a two-node island under the represented move set.
- Pooled G103/G104 nonlinear atoms: 561 32-atom subsets tested, only the two original atom sets feasible under known factorizations.
- Launched cross-seed factorization transfer, global 67-linear fixed-AND-schedule Z3 synthesis, and boundary-free full-circuit search on architecture-diverse seeds.
