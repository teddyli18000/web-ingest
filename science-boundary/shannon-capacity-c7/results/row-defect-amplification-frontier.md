# Exact row-defect amplification frontier

Date: 2026-10-30

This note records the exact status of the BPZ/Tan `B x B` core amplification route based on the five known 5D raw `+1` support defects. It is deliberately narrower than the full `C7^⊠10` problem.

## Pinned geometry

Source: `tandonravi/C7-Shannon-Capacity-Heterogeneous-Recursion` at commit `c753408492dde92a239708986d16c15dbf6c3235`.

- `B` has 359 points.
- The core `B x B` has `359^2 = 128881` points.
- Each of the 18 public terminal configurations contributes a 5872-point periphery, for total score 134753.
- The exact connected-support census found five raw `+1` 5D defects relevant here: one `5 -> 6` replacement and four `6 -> 7` replacements.

## Fixed-mode amplification: exact negative

For a fixed defect `C -> Y` and arbitrary row set `A subseteq B`, replace

`A x C` by `A x Y`.

Before periphery losses, every selected row contributes exactly `+1`. Let `L_a` be the exact set of old terminal-periphery points that conflict with the new points on row `a`. The true score increment within this family is

`|A| - |union_{a in A} L_a|`.

This is an exact maximum-weight closure / minimum-cut problem. We solved all

`5 defects x 18 terminals x 2 axes = 180`

scenarios in one Action.

- Workflow run: `40989311545`
- Result: every scenario has exact optimum `delta = 0`.
- The best solution is the empty row set; no candidate certificate is materialized.

Reusable code: `code/bpz_amplify_row_defects.py`.

## Mixed-mode one-axis amplification: exact negative

The next model lets every physical row independently choose at most one of the five raw `+1` defects, or choose none. Different rows may use different defect modes and may share the same periphery losses.

For one terminal and one axis, the exact weighted-MaxSAT objective is

`#selected row/mode choices - #distinct periphery losses`.

Hard clauses enforce the per-row partition and every exact implication from a selected mode to the old periphery points it forces us to delete.

All

`18 terminals x 2 axes = 36`

scenarios were solved exactly with RC2 using four worker processes in one Action.

- Workflow run: `40989638714`
- Job: `123848646454`
- Result: every scenario has exact optimum `delta = 0`.
- Representative best scenario: `q=O, r=O, terminal_orientation=0, axis=row`, with `selected_count=0`, `loss_count=0`, `delta=0`.
- Runtime: about 108 seconds wall clock at about 394% CPU; peak RSS about 350 MB.
- Few Shots verifier was skipped because no positive candidate existed.

Reusable code: `code/bpz_joint_row_defects_maxsat.py`.

## What this closes

These two results rule out a superficially attractive mechanism: taking any of the five known raw 5D `+1` defects and amortizing its peripheral cost over many independent `B` rows, even when different rows are free to choose different defect modes and all losses are shared exactly.

They do **not** rule out simultaneous row and column use. When a row defect and a column defect are selected together, their deleted core rectangles can overlap. Each compatible overlap saves one core deletion, producing a new positive interaction term that is absent from the one-axis models; row-new and column-new points can also conflict.

## Current next layer

`code/bpz_biaxial_rowcol_defects_maxsat.py` models both axes simultaneously. Its exact objective is

`#row choices + #column choices + #compatible core-overlap bonuses - #distinct periphery losses`,

with exact cross-axis incompatibilities and AND variables for overlap bonuses. A positive optimum is replayed structurally, materialized as a full 10D certificate, and must pass the upstream Few Shots verifier.

This biaxial layer is the smallest remaining extension of the row-defect mechanism; if it is also nonpositive, further work should move to genuinely different support-product / nonrectangular core-deletion families rather than enlarging the same one-axis search.
