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
- A structural comparison of the two 103 circuits found that their four core inputs span the **same 4-dimensional linear space**, related by an explicit invertible basis change. This motivates the current movable-interface exact synthesis campaign over the 34-gate `middle + core` window.

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

## Experiments

### ODC neutral walks from 103

`search_odc.py` uses full 256-bit truth tables and exact observability care masks. Four 900-second runs (seeds 2026102701–04) completed 1,349,114 root attempts and accepted 1,414 unseen equal-size equivalents. Every run ended at 103 gates, with zero successful aliases/deletions. Accepted moves concentrated on a small set of roots with care-set sizes 136, 192, 252 and 255, indicating a narrow neutral manifold rather than broad deletion opportunities.

### Two-gate ODC boundary walks

`search_odc2.py` allows a two-gate expression to replace a root when pruning an old dependency keeps the circuit at or below the current size. Four 900-second runs (seeds 2026102711–14) completed 651,871 attempts and accepted 2,771 unseen equivalent 103-gate states. Every `reductions` list was empty. This is meaningful negative evidence for this stochastic neighborhood, not a lower bound.

### Paired-103 interface analysis

`analyze_103_pair.py` compares the primary and supplementary 103-gate certificates directly using 256-bit truth tables. It established the exact four-input basis transformation above. The nine core outputs used by the final AND layer are not mutually contained in each other's affine spans, so the opportunity is at the movable input interface / resynthesis level rather than a simple output relabeling.

## Current route

The current experiment asks a sharply defined 102 question while preserving most of the public 103 circuit:

- Keep the first 26 gates of the primary certificate fixed (`17 prelinear + 9 norm AND`).
- Keep the final 43 gates fixed (`18 final AND + 25 output`).
- Replace the current 34-gate middle/core window (`16 middle + 18 core`) by **at most 33 gates**.
- Permit four interface wires to be selected freely from a synthesized linear helper network, rather than fixing the published `w35,w33,w38,w41` basis.
- Restrict the nonlinear core to six AND gates initially, matching the known 18-gate cores, while allowing XOR/XNOR rearrangement.

`synth_window_z3.py` encodes this as bit-vector SMT over the exact 256-point truth tables. The first campaign tests the three 33-gate partitions `15 linear + 18 core`, `16 + 17`, and `14 + 19` across multiple solver seeds. Any SAT model is spliced into the full certificate and independently checked against an arithmetic AES S-box implementation before the workflow invokes the official Few Shots verifier.

## Dead ends / exclusions to preserve

- Fixed incoming/outgoing linear-stage resynthesis around the Jain 106 baseline did not improve the total.
- Restricted SAT windows and one-gate-deletion neighborhoods in the old inversion core did not improve it; larger timeouts are not impossibility results.
- Exhaustive 4-bit linear splicing of a published five-AND alternative core found compatible 106-gate constructions but no improvement.
- Post-104 local ODC search found no 103 in 183,304 root-rewrite iterations, but the later 103 circuit is structurally different.
- Fixed-template exact synthesis around the 104 core ruled out one specific alias/template configuration only.
- In the 103 work, optimizing field changes and product-plane bases separately failed in restricted models; joint optimization succeeded.
- New: 1.35M one-gate ODC root attempts from the 103 primary circuit produced no deletion.
- New: 0.65M two-gate boundary attempts from the 103 primary circuit produced no reduction.
- The two published 103 tails cannot simply be swapped: their nine core-output factor sets differ beyond affine relabeling.

## Next steps

1. Complete the movable-interface 33-gate SMT campaign for the primary `middle + core` window.
2. If SAT, independently verify the 102-gate full certificate, re-sync Few Shots main/open PRs, run the official verifier and `tools/check.py`, then prepare a shot for submission.
3. If all restricted partitions time out or are UNSAT, use the two known 18-gate cores to derive solver assumptions / partial templates rather than merely extending stochastic ODC runtime.
4. In parallel, consider the analogous 32-gate `prelinear + middle` tradeoff suggested by the two 103 decompositions (`17+16` versus `19+14`, both 33) if the middle/core route stalls.

## Sources

- Few Shots `p008` problem statement and verifier specification.
- Few Shots generated `FEWSHOT.md` and the complete merged `SHOT.md` files for the 105, 104 and 103 records.
- Few Shots live `data/board.json` and current pull-request search.
- Jain (2026), `gf2m-circuits`, cited by the problem baseline.
- FIPS-197 for the AES S-box definition.

## Work log

### 2026-10-27 PDT

- Read the Web Ingest root and Science Boundary rules and the Few Shots `take-a-shot` rules.
- Synced the live p008 board: record 103; next threshold 102.
- Read the complete merged 105/104/103 shot descriptions and their recorded dead ends.
- Ran four one-gate ODC neutral walks from 103: 1,349,114 attempts, 1,414 accepted 103 states, no deletion.
- Ran four two-gate ODC boundary walks from 103: 651,871 attempts, 2,771 accepted 103 states, no reduction.
- Compared both published 103 certificates and proved by exhaustive truth-table equality that their four core-input bases are linearly equivalent via the explicit transform recorded above.
- Launched exact movable-interface synthesis aimed directly at replacing the primary 34-gate middle/core window by 33 gates.
