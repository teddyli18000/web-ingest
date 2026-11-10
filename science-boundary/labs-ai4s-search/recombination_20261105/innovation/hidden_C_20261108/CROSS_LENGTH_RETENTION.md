# Predeclared cross-length replication of classical two-state history — 2026-11-09

## What was learned on N50, and what is now held fixed

The original strictly heldout N50 test was negative, and later exploratory no-noop and branch-history interventions exposed N50 target orbits. Therefore this experiment tests whether the **classical search-state representation** effect is consistent over lengths and different *state seeds*, not whether a trained model generalizes to completely unseen optimal source populations.

Frozen source tuple A,B,C rotations from `make_scenarios.py`; keep the script, binary source `hidden_repair.cpp`, candidate generation, 16-dimensional frozen model, masked random number generation, real/fake B cardinality and repair acceptance unchanged. The model was fitted N46, selected N47, and has SHA256 `2abb727677b9c065b624322f1446fc950987d2c64fc41396e4b90e80c5ad576b`. No model refit or hyperparameter changes.

**Two independent state-seed cohorts, frozen before running:**

- N46: 3 distinct optimum C orbits, 8 state seeds/rotation **rep=8–15** never included in the N46 training repairs (rep=0–7); 144 contexts (72 A/B-blind, 72 C-shell), 6 candidate policies and 2 state-management methods. This tests **unseen damaged states but seen C/A/B orbits**.
- N47: 6 distinct optimum C orbits, 4 state seeds/rotation **rep=4–7** never included in the N47 model-selection repairs (rep=0–3); same 144 contexts/6×2 methods. This is **unseen damaged states but hyperparameters were selected using this length and its optimum orbits**.
- N50 exploratory seed8–15 already independently verified as [baseline comparison](results/branch_deploy_v1/retention_search_verdict.json); do not rerun or pool as independent fresh holdout.

At each N, the exact same scenario-input.tsv is given to each arm, no vault. The six candidate policies are A-only raw-E ranking, real B raw-E, matched-random fake B raw-E, frozen joint+history reranking, frozen cheap history reranking, and single-source ILS. All arms initially execute the identical native `steepest→64 accepted Tabu7→steepest` repair(X). Search-state representations: (a) discard X and propose only from greedy repaired incumbent, or (b) **retain X and alternate proposal roots every other iteration**. In either arm, five nonzero Hamming-2/4/6/8/10 candidates per bank except same ILS k-policy, same 150ms total wall-time INCLUDING exact energies, features, repair and all search dynamics. The C target vault is read **only after both campaigns complete**, by an independent O(N)-native-popcount LABS exact scorer which verifies every raw and repaired spin sequence and eightfold orbit.

Report per N, each source C identity (N46 only 3, N47 only 6), each damage k=4/8/12, and the A/B-blind vs C-shell state generator **separately**:
- incremental C hit in states for which shared first direct repair failed, and total C including the shared first repair;
- recovered given B orbit versus **genuine third C orbit**;
- best E and number of full Tabu repairs under equal actual wall-time;
- A-only versus true B versus fake B; cheap learned versus joint learned; source-cluster uncertainty rather than declaring all 72 seeds independent target structures.

**Falsification gate:** if source-retention gains in C-shell are strong across N46 and N47 for *all* classical donor conditions, the representation effect is reproducible; that is not evidence of unique learned joint information. If A/B-blind C recovery is absent, the real ability to synthesize C from A+B remains unestablished. Independent target-level generalization requires another isolated source population not previously used in model choice, with favorable same-budget classical baselines.

Reproduce with `make_scenarios.py`, `run_retention_by_length.py`, `analyze_branch_deploy_by_length.py`, and the one-shot Actions workflow. Raw 150ms event data is committed only in SHA-verified losslessly gzipped form per policy, to stay below GitHub per-file limits. Preserve N50 and all negative pilot experiments. No `labs-100/` changes.
