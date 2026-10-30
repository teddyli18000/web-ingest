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

## Biaxial row+column amplification: exact negative

The final extension of this mechanism opens both axes simultaneously. A row choice `(a,m)` replaces `{a} x C_m` by `{a} x Y_m`; independently a column choice `(b,n)` replaces `C_n x {b}` by `Y_n x {b}`.

If `a in C_n` and `b in C_m`, the two deleted core rectangles would overlap at `(a,b)`, apparently creating a `+1` overlap bonus. The exact model therefore includes:

- per-row and per-column mode partitions;
- exact shared terminal-periphery losses;
- hard row-new / column-new incompatibilities;
- an AND variable worth `+1` for every compatible core overlap.

The exact objective is

`#row choices + #column choices + #compatible core-overlap bonuses - #distinct periphery losses`.

- Workflow run: `40990263531`
- Job: `123850679964`
- All 18 terminal scenarios were solved exactly with four RC2 worker processes.
- Result: every scenario has exact optimum `delta = 0`; the best solution is empty.
- Stronger structural fact: there are **841 cross-axis incompatibilities and zero compatible overlap variables** in each reported best geometry (`overlap_vars = 0`). Every potential row/column core overlap of these five raw defects is accompanied by at least one conflict between their newly introduced points, so the hoped-for overlap bonus is never realizable.
- Runtime: about 115 seconds wall clock at about 372% CPU; peak RSS about 377 MB.
- Few Shots verifier was skipped because no positive candidate existed.

Reusable code: `code/bpz_biaxial_rowcol_defects_maxsat.py`.

## What this closes

Taken together, these exact results close the natural amplification family built from the five known 5D raw `+1` defects:

1. repeating one defect over arbitrary rows;
2. mixing all five defects independently over arbitrary rows or columns;
3. combining row and column uses while sharing exact peripheral losses and accounting for possible core-overlap savings.

The biaxial calculation removes the only obvious positive interaction missing from the one-axis models: every potential core-overlap bonus is structurally incompatible with simultaneously keeping the corresponding new row and column gadgets.

This is a family-specific exclusion, not a proof that `alpha(C7^10)=134753`.

## Current frontier

Further work should leave this five-defect amplification family. The strongest active routes are now support-product / nonrectangular core-deletion mechanisms, especially owner-support conflict graphs whose clique-cover number exceeds their independence number. Those are the cases for which the elementary product bound no longer forces multiplicativity.
