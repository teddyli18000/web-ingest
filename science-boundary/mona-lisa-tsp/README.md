# Mona Lisa 100,000-city TSP (p010)

## Current state (2026-10-28)
- **Goal:** construct a valid 100,000-city tour of integer TSPLIB EUC_2D length **at most 5,757,190**, beating Nagata's published 5,757,191 tour by one or more units.
- **Independently documented lower bound:** 5,757,084 (Cook's Mona Lisa TSP Challenge, July 2012), leaving a gap of 107 to the baseline.
- **Few Shots accepted p010 shots:** none at initial read (FEWSHOT.md record chain contains baseline only).
- **Result status:** restricted 2-opt search completed; **no new tour claimed**. First GitHub Actions experiment completed and independently verifier-checked; no 2-opt improvement.
- **Important:** scoring uses exact integer rounded EUC_2D, NOT ordinary Euclidean float length. Always check a candidate with the authoritative p010 verifier.

## Verified experiment outcomes
- **Run [40683876889](https://github.com/teddyli18000/web-ingest/actions/runs/40683876889)** (2026-10-28): baseline verifier returned `valid=true`, score `5757191`, canonical hash `3947948945204e939df8f8555ff8f926027a55af3f29f54b29eb442fb278ebfa`. k=32 nearest-neighbor probe examined 1,499,636 oriented pairs, found no positive exact 2-opt gain, and finished in 5.57 seconds. Final verifier score remained `5757191`, same hash. Workflow artifact `monalisa-p010-neighbor-probe`, ID 12813817913, contains report and unchanged tour. This proves no improvement **only among the enumerated candidate exchanges**.

## Hypotheses
1. Exhaustively inspect the baseline for 2-opt improving edges among spatial nearest-neighbor candidate edges. A zero result proves only absence for the searched candidate pairs.
2. If 2-opt is saturated, investigate complementary representations: alternating-cycle exchanges on a near-optimal base tour; constrained 3/4/5-opt; exact small-region dynamic programming / MIP with boundary interfaces; and crossover between structurally different near-optimal tours.
3. Discrete rounding may create plateaus: preserve equal-score moves, use lexicographic secondary structural cost, and evaluate exact integer gains before publishing.

## Experiment 01: nearest-neighbor 2-opt diagnostic
Run `python science-boundary/mona-lisa-tsp/nn_two_opt.py --input <baseline-certificate.json> --output <candidate.json> --report <report.json> --k 32` from a checkout of few-shots with `PYTHONPATH` pointing at that checkout. Requires numpy and scipy. It imports the upstream verifier for exact coordinates and exact integer distances.
- Uses scipy cKDTree to generate spatial nearest-neighbor candidate pairs, then examines the standard 2-opt reversal.
- Scores candidate moves with exact integer metric via cached `math.isqrt` only when the vectorized Euclidean proxy is sufficiently close to improving (margin 3 units).
- Iteratively applies a best sampled improving move until the candidate set is exhausted or the move budget is reached.
- A 2-opt move changes only two edges; the script tracks the exact local gain and rechecks the final tour with the upstream verifier.
- This is a **restricted 2-opt neighborhood**, not a complete search over O(n²) edge pairs.

## How to reproduce
The one-shot workflow `.github/workflows/temp-monalisa-p010-probe.yml` clones the public upstream repo, verifies baseline, runs the diagnostic, invokes the upstream verifier again, and uploads the machine-readable report/candidate artifacts. It does not submit a shot automatically.

## Sources
- [Challenge and current tour/bound](https://www.math.uwaterloo.ca/tsp/data/ml/monalisa.html)
- [Few Shots problem](https://github.com/few-shots/few-shots/blob/main/problems/p010-mona-lisa-tsp/PROBLEM.md)
- [Few Shots verifier](https://github.com/few-shots/few-shots/blob/main/problems/p010-mona-lisa-tsp/verify/verify.py)
- [Published baseline certificate](https://github.com/few-shots/few-shots/blob/main/problems/p010-mona-lisa-tsp/baseline/certificate.json)

## Work log
- 2026-10-28: checked p010 metadata, verifier, baseline provenance, accepted shot chain, Cook challenge page and repository instructions. Baseline 5,757,191; minimum accepted improvement one unit. Established reproducible nearest-neighbor 2-opt probe, k=32 verified, negative.
