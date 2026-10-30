# Exact joint amplification of the known minimum-killer k8 defects

Status: **closed at gain zero for the four distinct known minimum-killer k8 defect modes across all 36 pinned terminal/orientation/axis scenarios. No verifier-valid score above 134,753.**

The known-pool k8 audit produced seven witnesses with the minimum observed four killed private-pair colors. After deduplication by `(owners, additions)`, these are four distinct `8 -> 9` defect modes; all kill colors `{0,4,5,6}`.

A single defect has raw core gain `+1`, but multiple defects on different rows or columns could in principle share peripheral blocker losses. `code/bpz_k8_min4_joint_amplify.py` therefore optimizes the true ten-dimensional net gain jointly:

- one mode or none may be selected on each of the 359 independent core rows/columns;
- selecting a mode removes its eight core cells and inserts its nine outside points;
- every conflicting terminal-periphery point is charged once globally, so losses can be shared across arbitrarily many selected rows;
- the objective is exactly `number_of_selected_row_defects - number_of_distinct_deleted_periphery_points`.

GitHub Actions run `41042052057`, job `124016971455`, solved all
`3 x 3 x 2 x 2 = 36` terminal scenarios exactly with RC2 using four worker processes.

Result:

- best delta: **0**;
- best selected defect rows: **0**;
- best peripheral losses: **0**;
- every nonempty combination is therefore strictly negative in every audited scenario;
- candidate materialized: false;
- Few Shots verifier step: skipped because no positive-gain candidate existed.

The exact optimization took about 3m22s wall time at about 383% CPU, peak RSS about 0.64 GiB.

This closes the natural “amortize the same four killer colors across many rows/columns” mechanism for the four currently known minimum-killer k8 modes. It does not close unknown k8 defects outside the completed k6/k7 pool union. The active exact question is whether any global k8 positive defect can use at most three killer colors; a separate exact SAT search addresses that stronger frontier.
