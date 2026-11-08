# p008 constructive nonlinear-basis synthesis — 2026-11-07/08

## Objective

Find an actually verified <=100-gate forward AES S-box in the exact Few Shots AND/XOR/XNOR basis. The Few Shots live board checked on 2026-11-07 still lists 101 gates (merged PR #31), and no new open p008 PR was found. Maintain constructive candidates and compare full-circuit gate counts; do not confuse repeated near-seed exact exclusions with progress toward the record.

## Genuine 102-gate nonlinear seed

Script: [make_and_shear_102.py](../make_and_shear_102.py). A fully verified 102-gate, 33-AND circuit is obtained by the exact bilinear identity

  (a AND b) XOR (a AND c) = a AND (b XOR c).

In the canonical FS101 seed, the mutation uses AND gates 46 and 48, replaces a nonlinear atom with a different 256-bit function, then propagates the complementary XOR/XNOR phase into the downstream linear network. It differs from the 101-gate baseline in **two elements of the unordered AND-function set**, not merely in their order. The resulting 102-gate certificate was also independently checked on all 256 AES inputs by a separate local truth-table evaluator.

This is a new architecture exploration *seed*, not a public record improvement.

## Multiple genuinely nonlinear changes

A separate local constructive generator enumerated 37 shared-factor AND pairs. Plain single shear normally adds 2 gates; complement-aware CSE saves one gate on the 46/48 case, yielding the known 102 seed. Two successive shears yielded **1,273 structurally distinct fully checked circuits** with at least one true AND-function-set change, including 69 raw 104-gate instances with symmetric difference 4 from the original 33-AND set. The minimum observed with two nontrivial shears was 104, not 101.

Reusable audited implementation: [double_and_shear_construction.py](../double_and_shear_construction.py). Independent Actions rerun: [42456579731](https://github.com/teddyli18000/web-ingest/actions/runs/42456579731). The raw local counts describe the local reference implementation; confirm the new Actions summary before treating the repository implementation as completely calibrated.

## Global multi-parent recombination, not individual local shaving

Action [42455846885](https://github.com/teddyli18000/web-ingest/actions/runs/42455846885) used [semantic_broad_architecture.py](../semantic_broad_architecture.py) to merge the 101 archive, approximately 756 stored 102-AND-refactor parent files and the explicit 102 shear. The 756 stored files became 512 distinct valid parent circuits. Parent-union CP-SAT globally selected complete gate hypergraphs, rather than independently shaving each parent. At 101 gates it recovered the old AND basis; requiring a novel AND function in <=101 was UNSAT *for these finite old-parent gate edges only*. This revealed a constructive limitation: every new nonlinear atom requires at least one genuinely new shared intermediate expression somewhere outside the old parent union.

Action [42456007862](https://github.com/teddyli18000/web-ingest/actions/runs/42456007862) added 48–180 entirely new one-gate helpers to that union with both original and changed AND atoms. All four CPU jobs ended UNKNOWN at the 450s budget without a novel 101 witness. This is solver/search failure, not an impossibility result.

## Second-generation nonlinear factorization seeds

From the explicit shear 102 circuit, [enumerate_joint_and_factorizations.py](../enumerate_joint_and_factorizations.py) independently varied both operands of later ANDs under full-output care. Action [42456112245](https://github.com/teddyli18000/web-ingest/actions/runs/42456112245) generated **11 additional independently verified 102-gate circuits**. Their AND-function sets are all identical to the first shear (symmetric difference 2 from FS101) but their linear networks/topologies vary. Keep them as new recombination parents, not as 11 distinct nonlinear bases.

## Next synthesis-space changes

1. [semantic_two_level_helpers.py](../semantic_two_level_helpers.py) creates two dependent *new* XOR/XNOR helper functions, then allows them to feed AND operands and multiple linear targets. This represents networks unavailable in the one-helper closure; Action [42456435193](https://github.com/teddyli18000/web-ingest/actions/runs/42456435193) was launched.
2. [semantic_shear_warmstart.py](../semantic_shear_warmstart.py) seeds the global CP-SAT model with the already checked 102-gate new-AND witness. The model permits 102 initially and minimizes total gates under changed-AND constraint, instead of asking it to discover the feasible changed-AND region from scratch. Action [42456706490](https://github.com/teddyli18000/web-ingest/actions/runs/42456706490) was launched.
3. Use double-shear 104 seeds as additional *two-nonlinear-shift* parents if their independent workflow reproduces the local experiment. The present parent union contains only 101 and 102 sources and cannot express a multi-shift parent requiring several coordinated AND changes.
4. On any constructed <=100, freeze certificate, independently run all 256 AES input checks, run the unchanged Few Shots official verifier and submit a shot.

## Caution

- An alternative topological order of AND gates is not a distinct nonlinear function set. Record both ordered hashes and unordered truth-set symmetric difference.
- CP-SAT UNKNOWN and any algorithm that fails to recover a known baseline have no exclusion meaning.
- A 102- or 104-gate altered-basis seed is evidence of a valid different representation but not progress in the best-known score. Candidate quality and eventual size improvement are still the primary objectives.
