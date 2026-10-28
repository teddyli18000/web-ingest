# AES S-box circuit size

## Question

Can the AES S-box be implemented with at most 102 two-input gates over the exact Few Shots basis `{AND, XOR, XNOR}`? Depth is unscored; constants and NOT gates are unavailable except as absorbed by XNOR.

## Current state

- Live Few Shots record checked at `data/board.json` updated 2026-10-28T01:42:53Z: **103 gates**, `fancify/aes103-joint-plane-orientations` (PR #16).
- Therefore the next valid breakthrough is **102 gates or fewer**.
- Record chain: Jain baseline 106 → `csbo98/aes105-nonlinear-resub` 105 → `HeiGeAi/aes104-odc-resub` 104 → `fancify/aes103-joint-plane-orientations` 103.
- The 103 primary circuit has 33 AND, 64 XOR, 6 XNOR gates and decomposes as `17 prelinear + 9 norm AND + 16 middle + 18 core + 18 final AND + 25 output = 103`.
- The same shot supplies an independently constructed second 103-gate circuit with decomposition `19 + 9 + 14 + 18 + 18 + 25` and gate counts 33 AND, 60 XOR, 10 XNOR.

No 102-gate claim has been found in the merged record chain. Re-check the live board before any claim or submission.

## Why this may be a frontier

The Few Shots verifier exhaustively checks the fixed AES S-box on all 256 inputs in the same AND/XOR/XNOR model used by the Boyar–Peralta/Circuit Minimization Team/NIST line of work. Recent public progress moved from 106 to 103 in a single day through materially different constructions, so 102 is plausibly reachable but not implied.

## What is known

### 106 → 105

`csbo98/aes105-nonlinear-resub` used exact 256-bit truth tables and observability-don't-care resubstitution. It reduced the central inversion computation from seven AND gates to six while retaining the outer nine and eighteen AND products. Fixed linear-layer resynthesis, restricted SAT windows and a five-AND splice family did not beat 106.

### 105 → 104

`HeiGeAi/aes104-odc-resub` found an algebraic sharing identity in the nonlinear core, removing one XOR while keeping 33 AND gates. A further 500-second ODC search from that 104 circuit did not improve it; a fixed-template 18-node core alias instance was UNSAT. These are local/template-specific negatives, not global lower bounds.

### 104 → 103

`fancify/aes103-joint-plane-orientations` changed the surrounding GF(16) representation jointly with independent bases for nine rank-two norm-product planes. Exact linear synthesis then produced the 103-gate primary circuit. Separate optimization of only the field representation or only the plane choices had failed; the successful construction required joint optimization.

## Current route

The first experiment is an ODC neutral random walk **starting from the new 103-gate circuit itself**. This is distinct from the documented post-104 ODC search: the 103 construction has a different field representation, product-plane orientation and surrounding linear network, so its observability don't-care structure is different.

`search_odc.py` uses full 256-bit truth tables. For a selected root gate it flips the root on all assignments and propagates the change to compute the exact output-observability care mask. It then tries:

1. replacing the root by an already available wire on its care set (which can immediately delete a gate), and
2. neutral one-gate AND/XOR/XNOR replacements on the care set, accepting only circuits whose eight outputs remain exactly equal and pruning newly dead gates.

The walk retains unseen equal-size circuits so that a neutral rewrite can expose a later deletion. Multiple seeds are intended. Any candidate below 103 must pass both the official Few Shots verifier and an independent scalar AES implementation before it is considered a result.

## Dead ends / exclusions to preserve

- Fixed incoming/outgoing linear-stage resynthesis around the Jain 106 baseline did not improve the total.
- Restricted SAT windows and one-gate-deletion neighborhoods in the old inversion core did not improve it; larger timeouts are not impossibility results.
- Exhaustive 4-bit linear splicing of a published five-AND alternative core found compatible 106-gate constructions but no improvement.
- Post-104 local ODC search found no 103 in 183,304 root-rewrite iterations, but the later 103 circuit is structurally different.
- Fixed-template exact synthesis around the 104 core ruled out one specific alias/template configuration only.
- In the 103 work, optimizing field changes and product-plane bases separately failed in restricted models; joint optimization succeeded.

## Next steps

1. Run multi-seed ODC neutral walks directly from the live 103 primary circuit.
2. If this yields only alternate 103s, compare their care-mask statistics and nonlinear boundaries; use them as seeds for two-gate/window resubstitution rather than simply extending runtime.
3. In parallel, inspect whether the 16-gate middle layer and 18-gate core can be co-synthesized across their boundary; prior exact negatives fixed too much of that interface.
4. Re-check Few Shots main and current PRs immediately before any 102 claim.

## Sources

- Few Shots `p008` problem statement and verifier specification.
- Few Shots generated `FEWSHOT.md` and the complete merged `SHOT.md` files for the 105, 104 and 103 records.
- Few Shots live `data/board.json`.
- Jain (2026), `gf2m-circuits`, cited by the problem baseline.
- FIPS-197 for the AES S-box definition.

## Work log

### 2026-10-27 PDT

- Read the Web Ingest root and Science Boundary rules and the Few Shots `take-a-shot` rules.
- Synced the live p008 board: record 103; next threshold 102.
- Read the complete merged 105/104/103 shot descriptions and their recorded dead ends.
- Chose the first non-duplicative experiment: ODC neutral random walks from the newly merged 103 construction itself.
