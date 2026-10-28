# AES S-box circuit size

## Question

Can the AES S-box be implemented with at most 102 two-input gates over the exact Few Shots basis `{AND, XOR, XNOR}`? Depth is unscored; constants and NOT gates are unavailable except as absorbed by XNOR.

## Current state

- Live Few Shots record re-checked at `data/board.json` updated 2026-10-28T02:14:59Z: **103 gates**, `fancify/aes103-joint-plane-orientations` (PR #16). A contemporaneous search found no open p008 pull request.
- Therefore the next valid breakthrough is **102 gates or fewer**.
- Record chain: Jain baseline 106 → `csbo98/aes105-nonlinear-resub` 105 → `HeiGeAi/aes104-odc-resub` 104 → `fancify/aes103-joint-plane-orientations` 103.
- The 103 primary circuit has 33 AND, 64 XOR, 6 XNOR gates and decomposes as `17 prelinear + 9 norm AND + 16 middle + 18 core + 18 final AND + 25 output = 103`.
- The same shot supplies an independently constructed second 103-gate circuit with decomposition `19 + 9 + 14 + 18 + 18 + 25` and gate counts 33 AND, 60 XOR, 10 XNOR.
- Two fresh local-search campaigns from the 103 primary circuit did **not** reach 102: four one-gate ODC walks explored 1,349,114 root attempts / 1,414 accepted distinct 103 states with zero alias deletions; four two-gate boundary walks explored 651,871 attempts / 2,771 accepted distinct 103 states with no reduction.
- A structural comparison of the two 103 circuits found that their four core inputs span the **same 4-dimensional linear space**, related by an explicit invertible basis change.
- A second structural comparison found that Jain's published 106-gate / **32-AND** `sbox106_d34` circuit contains a **17-gate, 5-AND inversion core whose independent inputs span exactly this same 4D function space**. This opens a direct 102 route not excluded by the old 106-baseline five-AND splice experiment: keep the current 103 circuit's 16-gate middle and 43-gate tail, and synthesize the current nine tail factors with a 17-gate / 5-AND core.

No 102-gate claim has been found in the merged record chain or current open p008 PRs. Re-check the live board immediately before any claim or submission.

## Why this may be a frontier

The Few Shots verifier exhaustively checks the fixed AES S-box on all 256 inputs in the same AND/XOR/XNOR model used by the Boyar–Peralta/Circuit Minimization Team/NIST line of work. Recent public progress moved from 106 to 103 in a single day through materially different constructions, so 102 is plausibly reachable but not implied.

## What is known

### 106 → 105

`csbo98/aes105-nonlinear-resub` used exact 256-bit truth tables and observability-don't-care resubstitution. It reduced the central inversion computation from seven AND gates to six while retaining the outer nine and eighteen AND products. Fixed linear-layer resynthesis, restricted SAT windows and a five-AND splice family did not beat 106.

### 105 → 104

`HeiGeAi/aes104-odc-resub` found an algebraic sharing identity in the nonlinear core, removing one XOR while keeping 33 AND gates. A further 500-second ODC search from that 104 circuit did not improve it; a fixed-template 18-node core alias instance was UNSAT. These are local/template-specific negatives, not global lower bounds.

### 104 → 103

`fancify/aes103-joint-plane-orientations` changed the surrounding GF(16) representation jointly with independent bases for nine rank-two norm-product planes. Exact linear synthesis then produced the 103-gate primary circuit. Separate optimization of only the field representation or only the plane choices had failed; the successful construction required joint optimization.

### Relation between the two 103 constructions

The primary core inputs are `w35,w33,w38,w41`; the supplementary mixed-core inputs are `g34,g39,g37,g41`. Exhaustive truth-table comparison gives the invertible linear map

```text
g34 = w35 XOR w33
g39 = w33
g37 = w35 XOR w38 XOR w41
g41 = w41
```

and inverse

```text
w35 = g34 XOR g39
w33 = g39
w38 = g34 XOR g39 XOR g37 XOR g41
w41 = g41.
```

Thus both 18-gate cores sit on the same four-dimensional input function space, even though their nine used core-output factors are not the same affine span and their final-product factor multisets differ. A trivial cross-splice of one prefix with the other tail is therefore not valid, but the shared input space makes a movable interface basis a concrete search degree of freedom.

### Jain 32-AND / five-AND core relation

The public `ahrazzle/gf2m-circuits` file `sbox/circuits/sbox106_d34.json` is a verified 106-gate AES S-box with 32 AND, 71 XOR and 3 XNOR gates. Its AND structure is `9 + 5 + 18`: nine outer norm products, a five-AND inversion core, then eighteen final products.

After aligning Jain's `U0..U7` convention with Few Shots `x7..x0`, exact 256-point truth-table comparison shows that the five-AND core's nominal five incoming functions have rank four. Relative to the current primary 103 core basis

```text
a = w35
b = w33
c = w38
d = w41
```

four independent Jain inputs are

```text
J51 = b XOR c       # mask 6
J49 = a XOR d       # mask 9
J41 = a XOR b XOR d # mask 11
J48 = c XOR d       # mask 12
```

and the fifth nominal input is dependent:

```text
J50 = a XOR b XOR c # mask 7
```

The Jain inversion region can therefore be expressed as a **17-gate network from four independent inputs**, using exactly five AND and twelve XOR gates. This does not immediately splice into the 103 tail: its available factor set overlaps but does not equal the nine factors consumed by the primary final-AND layer. In particular it directly exposes several current factors (`w57`, `w56`, `w58`, `w53`, and after its nearby linear combinations also `w52`, `w49`) but not the full required set. The new exact question is whether some 17-gate / five-AND network on the same four-dimensional input space can produce all nine current factors simultaneously.

This is materially broader than the old 105-shot five-AND splice exclusion. That exclusion enumerated linear maps while splicing a published five-AND alternative into the **106 baseline family** and found no circuit below 106; it did not include the later 103 joint field/product-plane reparameterization and its cheaper outer layers.

## Experiments

### ODC neutral walks from 103

`search_odc.py` uses full 256-bit truth tables and exact observability care masks. Four 900-second runs (seeds 2026102701–04) completed 1,349,114 root attempts and accepted 1,414 unseen equal-size equivalents. Every run ended at 103 gates, with zero successful aliases/deletions. Accepted moves concentrated on a small set of roots with care-set sizes 136, 192, 252 and 255, indicating a narrow neutral manifold rather than broad deletion opportunities.

### Two-gate ODC boundary walks

`search_odc2.py` allows a two-gate expression to replace a root when pruning an old dependency keeps the circuit at or below the current size. Four 900-second runs (seeds 2026102711–14) completed 651,871 attempts and accepted 2,771 unseen equivalent 103-gate states. Every `reductions` list was empty. This is meaningful negative evidence for this stochastic neighborhood, not a lower bound.

### Paired-103 interface analysis

`analyze_103_pair.py` compares the primary and supplementary 103-gate certificates directly using 256-bit truth tables. It established the exact four-input basis transformation above. The nine core outputs used by the final AND layer are not mutually contained in each other's affine spans, so the opportunity is at the movable input interface / resynthesis level rather than a simple output relabeling.

### Linear interface profile

`linear_interface_profile.py` exhaustively enumerated all `2^15` XOR combinations of the 15 external signals entering the primary middle layer. Several independent bases of the core-input 4-space have a lower separate-XOR-tree upper bound than the published basis: the current basis scores 24 by that crude measure, while bases such as masks `(1,2,7,11)`, `(2,7,8,11)` and `(2,7,10,11)` score 20. This is only a ranking heuristic because an optimized shared linear network can change the true gate count; exact 15/16-gate linear synthesis is running for these candidates.

### Final-plane orientation check

The eighteen final AND gates occur in nine pairs sharing the same nine core factors, and their left-factor pairs are exactly the same nine two-dimensional planes used by the first nine norm ANDs. None of the nine third directions `L XOR M` is already present for free in the current 17-gate prelayer. Therefore independently re-orienting the final planes is not a new zero-cost freedom; it re-enters the same joint plane/prelayer optimization already exploited by the 103 shot.

## Current route

Three exact routes are running in parallel.

1. **Movable 33-gate middle/core window.** Keep the first 26 and final 43 gates fixed and replace the current `16 middle + 18 core = 34` region by 33 gates. `synth_window_z3.py` tests `15+18`, `16+17`, and `14+19` partitions with a movable four-wire interface and six ANDs.
2. **Split exact synthesis.** `synth_linear4_z3.py` searches 15/16-gate linear networks for selected interface bases while `synth_core4_z3.py` searches 17/18-gate six-AND cores over exact 16-state truth tables.
3. **Five-AND direct-102 route.** `synth_core4_z3.py` is also searching 17-gate networks with exactly five ANDs for the nine current tail factors, both fully freely and with the AND-position topology of Jain's `sbox106_d34` core fixed while operands and XOR/XNOR orientations can change. If the current 16-gate middle is retained and any such 17-gate core exists, the full circuit is immediately `17 + 9 + 16 + 17 + 18 + 25 = 102` gates.

Any SAT model must be reconstructed into a full certificate, checked independently against arithmetic GF(2^8) inversion + AES affine transformation on all 256 bytes, then passed through the unchanged Few Shots verifier and `tools/check.py` after re-syncing live main.

## Dead ends / exclusions to preserve

- Fixed incoming/outgoing linear-stage resynthesis around the Jain 106 baseline did not improve the total.
- Restricted SAT windows and one-gate-deletion neighborhoods in the old inversion core did not improve it; larger timeouts are not impossibility results.
- Exhaustive 4-bit linear splicing of a published five-AND alternative core into the old 106 family found compatible 106-gate constructions but no improvement; this does **not** exclude five-AND cores combined with the later 103 outer representation.
- Post-104 local ODC search found no 103 in 183,304 root-rewrite iterations, but the later 103 circuit is structurally different.
- Fixed-template exact synthesis around the 104 core ruled out one specific alias/template configuration only.
- In the 103 work, optimizing field changes and product-plane bases separately failed in restricted models; joint optimization succeeded.
- New: 1.35M one-gate ODC root attempts from the 103 primary circuit produced no deletion.
- New: 0.65M two-gate boundary attempts from the 103 primary circuit produced no reduction.
- The two published 103 tails cannot simply be swapped: their nine core-output factor sets differ beyond affine relabeling.
- Re-orienting only the final nine product planes is not free in the current 17-gate prelayer and is not an independent unexplored symmetry.

## Next steps

1. Prioritize the 17-gate / five-AND exact core search because it gives the cleanest direct 102 construction while preserving all outer gates of the live record.
2. Complete the movable-interface 33-gate SMT campaign and exact 15/16-gate linear-interface campaign.
3. If a candidate is SAT, freeze it immediately, independently verify all 256 AES inputs, re-sync Few Shots main/open PRs, run the official verifier and `tools/check.py`, then prepare and publish the shot under the Few Shots rules.
4. If all current exact searches are unknown/UNSAT in their restricted models, use the known Jain five-AND dependency skeleton to enlarge the boundary jointly with the final factor map instead of returning to long stochastic ODC walks.

## Sources

- Few Shots `p008` problem statement and verifier specification.
- Few Shots generated `FEWSHOT.md` and the complete merged `SHOT.md` files for the 105, 104 and 103 records.
- Few Shots live `data/board.json` and current pull-request search.
- Jain (2026), public `ahrazzle/gf2m-circuits`, especially `sbox/circuits/sbox106_d24.json` and `sbox106_d34.json`.
- NIST Circuit Complexity AES S-box list, checked against the current public page.
- FIPS-197 for the AES S-box definition.

## Work log

### 2026-10-27 PDT

- Read the Web Ingest root and Science Boundary rules and the Few Shots `take-a-shot` rules.
- Synced the live p008 board: record 103; next threshold 102.
- Read the complete merged 105/104/103 shot descriptions and their recorded dead ends.
- Ran four one-gate ODC neutral walks from 103: 1,349,114 attempts, 1,414 accepted 103 states, no deletion.
- Ran four two-gate ODC boundary walks from 103: 651,871 attempts, 2,771 accepted 103 states, no reduction.
- Compared both published 103 certificates and proved by exhaustive truth-table equality that their four core-input bases are linearly equivalent via the explicit transform recorded above.
- Exhaustively profiled the 15-signal linear cut and identified lower-weight alternative core bases.
- Verified that the final-product plane orientations are coupled to the same nine prelinear planes and are not an independent free search family.
- Parsed Jain's public 106-gate / 32-AND circuit, isolated its 17-gate / five-AND inversion core, and established by exact truth-table comparison that its independent inputs span the same 4D function space as the live 103 core.
- Launched exact movable-window, split linear/core, unrestricted five-AND, and Jain-topology five-AND synthesis campaigns aimed directly at a 102-gate certificate.
