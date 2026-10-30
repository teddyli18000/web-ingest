# AES S-box circuit size

## Question

Can the AES S-box be implemented with at most **100** two-input gates over the exact Few Shots basis `{AND, XOR, XNOR}`? Depth is unscored; constants and NOT gates are unavailable except as absorbed by XNOR.

## Upstream-first rule

Before substantial p008 work, re-check the live Few Shots board, recent/open p008 PRs, and every newer record's complete `SHOT.md` including dead ends. Do not extrapolate a restricted exact exclusion into a global lower bound.

## Current state — resynced 2026-10-29 PDT

- **Live verified record: 101 gates**, `chunfeng11221/aes101-nist-interface-resub`, merged PR #31.
- Official board: score 101, verified `2026-10-29T10:51:03Z`, recorded `2026-10-29T10:52:38Z`.
- Circuit: **33 AND + 40 XOR + 28 XNOR = 101**, depth 44.
- Canonical hash reported by the shot/verifier: `9371891b3eb422ac1514f067212a5c42d6f07d0a378deb37dad0941de7220093`.
- Record chain: 106 → 105 → 104 → 103 → 102 → **101**.
- Next valid breakthrough: **100 gates or fewer**.

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

`seed_family_census_extended.py` expands this comparison to near-best NIST A32/A33/A34 circuits plus an A28 remote control family.

## Current hypotheses toward 100

### H1 — alternate near-best seed families can expose a different cross-boundary saving

A seed need not already beat 101. A 102–105 circuit with a different nonlinear dependency skeleton can be more valuable than another neutral mutation of the record if full-circuit rewriting can cross boundaries unavailable in the current representation.

The first active branch is NIST A32/G103. It is only one gate smaller than the G104 seed used by PR #31, retains 32 ANDs, but changes two AND functions and reorganizes the nonlinear depth from 5 to 7. It is close enough to the frontier to be useful while exposing different observability paths.

### H2 — search architecture diversity before local depth

For each candidate family, measure:

- exact AND-function overlap with known records;
- nonlinear dependency/AND-depth profile;
- intermediate-function overlap with the 101 circuit;
- where affine/nonlinear boundaries occur and whether factors consumed downstream are already available elsewhere;
- full-circuit observability masks, especially identities involving signals on opposite sides of an apparent decomposition boundary.

Only then spend large local-search compute.

### H3 — the current 101 itself is a new architecture and still deserves full-circuit search, but not as the only seed

The 101 shot's successful basin was reached only after the new NIST-derived 102 construction. Further full-circuit neutral/+1 walks from 101 are legitimate, but they are run in parallel with alternate seed families rather than treated as evidence that the old fixed-core frontier is globally saturated.

## Active experiments

### Alternate-seed full-circuit resubstitution

`search_arch_seed.py` is boundary-free: it accepts a complete verified seed, computes exact 256-bit observability masks, allows neutral moves and bounded temporary `+1` expansions, keeps searching after intermediate improvements, and stops only at target 100.

Workflow `.github/workflows/temp-aes-arch-seed-resub.yml` runs four CPU workers per runner over both NIST G103 and the merged 101. Every job independently rechecks all 256 AES inputs and invokes the official Few Shots verifier on its best certificate. Initial run: `40991271507`.

This experiment is intentionally different from extending the old fixed-core ODC campaign: the primary new branch begins from a different complete circuit representation and does not preserve any core/tail boundary.

### Extended seed census

`.github/workflows/temp-aes-seed-census-extended.yml` classifies the near-best NIST A32/A33/A34 circuits and an A28 control by exact nonlinear-function overlap and dependency shape. The goal is to select subsequent seed-construction campaigns by structural diversity, not merely gate count.

## What not to do next

- Do not extend old fixed-102 core SAT/ODC merely because a timeout was inconclusive.
- Do not treat growing exact-exclusion coverage around one interface as progress toward a global 100 lower bound.
- Do not optimize AND count independently of linear/interface cost.
- Do not preserve `prelinear | middle | core | final multipliers | output` as a hard partition when searching for rewrites.
- Do not call NIST G103 a wholly independent family: the census shows 30/32 AND functions shared with G104.

## Verification protocol for any ≤100 candidate

1. Re-sync live Few Shots main/board/open p008 PRs.
2. Independently evaluate all 256 bytes against arithmetic AES inversion modulo `0x11b` plus the affine map.
3. Run the unchanged Few Shots p008 verifier.
4. Freeze the exact certificate and search seed/provenance.
5. Run the repository submission checks required by Few Shots.
6. Only then prepare/publish the shot.

## Sources

- Few Shots live `data/board.json` and merged PR #31.
- `aes101-nist-interface-resub/SHOT.md` and certificate.
- Earlier Few Shots 105/104/103/102 shots and certificates.
- NIST `usnistgov/Circuits` AES S-box NCFF files and README.
- Existing topic-local exact-screen notes, retained with their represented-family scope.

## Work log

### 2026-10-29 PDT

- Re-synced after PR #31 merged; board confirms verified live score 101.
- Read the complete 101 shot and recorded its dead ends and the cross-boundary identity responsible for the final saving.
- Reclassified all old fixed-interface/core exact results as family-scoped negatives, not global evidence against 100.
- Added `seed_family_census.py`; Action `40991160742` independently verified NIST G103/G104 and Few Shots 101/102/103 on all 256 inputs and measured nonlinear-function overlap.
- Found that NIST G103/G104 are close siblings (30/32 AND functions shared) while the 101 field-transformed circuit shares zero AND functions with either NIST seed.
- Added extended census across near-best NIST families.
- Added boundary-free `search_arch_seed.py` and launched run `40991271507` with 4 CPU workers per runner, using NIST G103 and the merged 101 as separate complete seeds, target 100.
