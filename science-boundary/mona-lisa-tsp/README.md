# Mona Lisa 100,000-city TSP (p010)

## Current state (2026-10-28)
- **Goal:** construct a valid 100,000-city tour of integer TSPLIB EUC_2D length **at most 5,757,190**, beating Nagata's published 5,757,191 tour by one or more units.
- **Independently documented lower bound:** 5,757,084 (Cook's Mona Lisa TSP Challenge, July 2012), leaving a gap of 107 to the baseline.
- **Few Shots accepted p010 shots:** none at initial read (FEWSHOT.md record chain contains baseline only).
- **Result status:** restricted 2-opt probes (k=32 and k=160) completed; **no new tour claimed**. Research pivots to a certified reduced planar graph and face-region formulation. First GitHub Actions experiment completed and independently verifier-checked; no 2-opt improvement.
- **Important:** scoring uses exact integer rounded EUC_2D, NOT ordinary Euclidean float length. Always check a candidate with the authoritative p010 verifier.

## Verified experiment outcomes
- **Run [40683876889](https://github.com/teddyli18000/web-ingest/actions/runs/40683876889)** (2026-10-28): baseline verifier returned `valid=true`, score `5757191`, canonical hash `3947948945204e939df8f8555ff8f926027a55af3f29f54b29eb442fb278ebfa`. k=32 nearest-neighbor probe examined 1,499,636 oriented pairs, found no positive exact 2-opt gain, and finished in 5.57 seconds. Final verifier score remained `5757191`, same hash. Workflow artifact `monalisa-p010-neighbor-probe`, ID 12813817913, contains report and unchanged tour. This proves no improvement **only among the enumerated candidate exchanges**.

## Strategic pivot: planar-dual formulation (2026-10-28)
**Evidence-backed prior art, not a claimed discovery.** Cook, Helsgaun, Hougardy and Schroeder (2024), *Local elimination in the traveling salesman problem*, [DOI](https://doi.org/10.1007/s12532-024-00262-y), reduce Mona Lisa's complete edge set to fewer than 2.5n edges and report that its reduced graph is planar. Their open-source [ElimTSP](https://github.com/bicobico2/ElimTSP) repository distributes the concrete `results/mona.248972.edg.gz` (248,972 candidate edges) and `results/mona.1635.fix.gz` (1,635 fixed edges). The sparse set was obtained by certified elimination, **not** by arbitrary k-nearest neighbors. Do not infer the public upper bound has changed from their experiments. A CPLEX bound of 5,757,132 is explicitly described as *potential*, pending numerically safe verification; it is not an established certified improvement to 5,757,084.

**New research hypothesis (not yet shown novel):** Convert the reduced primal planar graph into its dual. Any Hamiltonian cycle in the primal is a cut separating dual faces into inside/outside. A different inside/outside labeling induces a new boundary edge set, giving a new representation of TSP moves as **face-region flips** rather than sequences of k-opt swaps. Force degree exactly 2 at every primal vertex and a *single* cycle, and measure energy by exact integer edge weights. This is a constrained Ising/cut problem, not an unconstrained MaxCut. Prior work on planar Hamiltonicity and face structures (e.g. Bagheri Gh. et al., [Journal of Graph Theory 2021](https://doi.org/10.1002/jgt.22612)) makes it essential not to claim this idea's novelty without broader comparison.

**Minimal falsifiable experiment:**
1. Independently inspect the published 248,972-edge file: numbering, edge weights, planarity, and whether the known 5,757,191 tour lies entirely within it. Preserve any counterexample to the assumption that the baseline is contained; an elimination set need only contain optimal tours, not necessarily the best *known* tour.
2. If yes, enumerate facial alternating cycles in a planar embedding. Toggling boundary edges of an alternating face preserves degree 2. Classify objective change and resulting component count. Only a one-component 2-factor is an admissible new tour.
3. If single-face moves are exhausted, search **coupled face-region flips**, by exact small-boundary dynamic programming, as a fundamentally different space from bounded k-opt. Use sparse graph's certified fixings; keep global cycle connectivity explicit.
4. Use the upstream p010 verifier for any candidate; validate the sparse-graph assumption before exploiting it in any proof. Test the approach on smaller planar TSP instances with known optimum before claims of generalized benefit.

**Negative evidence from prior runs:** [k=160 probe](https://github.com/teddyli18000/web-ingest/actions/runs/40683993086) examined 7,912,269 near-neighbor oriented 2-opt candidates and again found *zero* improving exchanges; upstream verifier independently confirmed 5,757,191 (same canonical hash). This is not proof of local optimality in the full 2-opt space, much less global optimality. The k-nearest-neighbor path is now **closed as the primary research direction**; do not keep incrementing k absent a specific new hypothesis.

## Experiment 02 — verified sparse planar graph / face-flip neighborhood
[GitHub Actions run 40688199531](https://github.com/teddyli18000/web-ingest/actions/runs/40688199531) completed successfully on 2026-10-28, from `planar_face_probe.py`. The published `mona.248972.edg.gz` graph has 100,000 nodes, **248,972 edges**; all 100,000 edges of the baseline Nagata tour are present; sample candidate-edge weights match the exact upstream verifier; graph is connected and planarity tested true. Degree counts: degree 2: 188, 3: 2,833, 4: 22,912, 5: 48,995, 6: 23,087, 7: 1,956, 8: 29. There are **148,974 faces** (consistent with Euler `E - V + 2`). 12,344 face boundaries are alternating relative to the baseline tour and thus preserve the degree-two property when toggled. **At least 20 single-face flips have strictly positive exact edge gain** (best +16), but the top 20 each produce **two cycles** rather than a Hamiltonian tour. This is a *2-factor improvement*, not a p010 improvement. There are 215 zero-gain alternating face flips. Thus connectivity appears to be the blocking constraint in this representation. The public graph's elimination guarantee was **not independently certified**, so use it as a heuristic search space until its certificate is rechecked.

**Experiment 03 verified, negative:** `pair_face_search.py` searched pairs of vertex-disjoint 4-face toggles with positive combined gain and tested single-cycle connectivity in O(1) per candidate using tour-segment contraction. [Action 40688611352](https://github.com/teddyli18000/web-ingest/actions/runs/40688611352) completed: 8,918 candidate 4-faces of gain >= -16, 279 strictly positive 4-faces, 298,104 ordered positive-gain pairs tested, **zero connected improving pairs**; no new tour. A negative result only covers these pairs, not coupled regions with shared boundaries or non-facial alternating cycles. [Workflow run](https://github.com/teddyli18000/web-ingest/actions/runs/40688611352).

## Hypotheses
1. Exhaustively inspect the baseline for 2-opt improving edges among spatial nearest-neighbor candidate edges. A zero result proves only absence for the searched candidate pairs.
2. Primary next direction: independently inspect ElimTSP's planar sparse candidate graph, then test exact-cost dual face-region moves and separator-interface optimization. Larger k-opt is a baseline, not the research agenda.
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
- 2026-10-28: planar-dual pair probe negative: 298,104 positive-gain 4-face pairs tested, zero produce a valid one-component tour. Next search should jointly optimize face spins under degree-two constraints and cut connectivity, rather than enumerate more independent face pairs.
- 2026-10-28: first planar-graph experiment succeeded; 248,972 edges, all 100,000 baseline edges present, planar. Identified +16 cost-lowering 2-factor flip that splits into two cycles; recorded full face-gain distribution in Action artifact, and launched paired-face connectivity-repair test.
- 2026-10-28: rechecked primary research; identified 2024 Cook–Helsgaun–Hougardy–Schroeder certified planar reduction and public 248,972-edge/1,635-fixed-edge data. Redirected from scaling k-neighbor probes to planar-dual face-region optimization, conditional on graph/baseline validation. Verified negative k=160 action result.
- 2026-10-28: checked p010 metadata, verifier, baseline provenance, accepted shot chain, Cook challenge page and repository instructions. Baseline 5,757,191; minimum accepted improvement one unit. Established reproducible nearest-neighbor 2-opt probe, k=32 verified, negative.
