# Mona Lisa 100,000-city TSP (p010)

## Current state (2026-10-28)
- **Goal:** construct a valid 100,000-city tour of integer TSPLIB EUC_2D length **at most 5,757,190**, beating Nagata's published 5,757,191 tour by one or more units.
- **Independently documented lower bound:** 5,757,084 (Cook's Mona Lisa TSP Challenge, July 2012), leaving a gap of 107 to the baseline.
- **Few Shots accepted p010 shots:** none at initial read (FEWSHOT.md record chain contains baseline only).
- **Latest verified status:** no improvement below **5,757,191**. A maximal disjoint family of **13 exact zero-cost 4-edge exchanges** yields **8,192 distinct Hamiltonian cycles** at score 5,757,191 (verified via 103-vertex contraction, representative full tours via upstream scorer; [run 40693948494](https://github.com/teddyli18000/web-ingest/actions/runs/40693948494)). **14** neutral mutations were harvested in total; only one pair shares city endpoints ([data/neutral-harvest.json](data/neutral-harvest.json)). Their best known secondary continuous Euclidean gain is about 4.757, *not* an integer score breakthrough.
- **Important:** scoring uses exact integer rounded EUC_2D, NOT ordinary Euclidean float length. Always check a candidate with the authoritative p010 verifier.

## October 28 checkpoint — neutral-state frontier
- [Run 40693410570](https://github.com/teddyli18000/web-ingest/actions/runs/40693410570) scanned every one of the **279** profitable single 4-face flips. Global two-edge repair produced **14 distinct nontrivial, independently length-checked neutral 4-opt transformations**, zero strictly improving transformations in that restricted family; recorded exact four removed / four added edges for each in [data/neutral-harvest.json](data/neutral-harvest.json).
- [Run 40693948494](https://github.com/teddyli18000/web-ingest/actions/runs/40693948494) contracted unchanged baseline segments to a **103-vertex multigraph** and checked **all 8,192 combinations** of 13 vertex-disjoint transformations. Every combination is a connected degree-two cycle and score remains 5,757,191; extreme tours and secondary-Euclidean optimum checked by original verifier. The 13 toggles yield distinct edge sets by construction.
- [Run 40693578373](https://github.com/teddyli18000/web-ingest/actions/runs/40693578373) exactly evaluated sparse-chord 2-opt endpoints on the earlier 64-state subset: no integer improvement; **not** an exhaustive 2-opt proof on complete graph.
- [Run 40691875884](https://github.com/teddyli18000/web-ingest/actions/runs/40691875884): 45 conditional exact distant paired face patches returned CP-SAT INFEASIBLE, but each restricts face-label changes outside its patch and thus cannot rule out a global improvement.
- [Run 40692021956](https://github.com/teddyli18000/web-ingest/actions/runs/40692021956) verified two dual trees on the sparse planar graph, with 74,761 and 74,213 faces respectively. Measured max baseline-ordered crossing widths of 3,044 and 1,583 (large), showing that naive path-sweep DP is not viable.
- Current research must move past single-face split+one-merge or increasing geographic radius. Key candidates: **multi-face coupled flips plus nonlocal repairs**, circuit-level exact branching on sparse edges, and parameterized exchange search on the neutral equivalence family. Distinguish original dense TSP from the public reduced graph (elimination proof not independently rechecked).
- A search of Cook's official challenge page on 2026-10-28 still listed 5,757,191 / 5,757,084. Newer related literature includes Arslanoğlu's 2026 surface-based formulation (arXiv:2603.00075) and 2025 DualOpt (AAAI); none establishes a new p010 record. The surface formulation itself is prior art.

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

### Why the dual-face representation is mathematically complete (conditional on sparse graph)
Let `G` be the connected plane graph of allowed edges, and `T0` its known Hamiltonian cycle. For any other Hamiltonian cycle `T` supported on `G`, the symmetric difference `T Δ T0` has **even degree at every vertex**, since both tours have degree 2. It is therefore an element of the `GF(2)` cycle space of `G`. In a connected plane graph, facial boundaries span this cycle space, so there exist binary face labels `x_f` such that each primal edge's new incidence equals `old_edge XOR x_left XOR x_right`. Complementing all face labels leaves the edge set unchanged.

This is not merely a heuristic move generator: **every** alternative Hamiltonian tour in the reduced planar graph can be represented in these variables. The difficult conditions are (i) exactly two selected edges per city, and (ii) exactly one connected cycle. A local subset of face variables gives a sharply defined, finite, *exact* search restriction. Next: select overlapping face patches around the +16 disconnected move, optimize with CP-SAT or MIP under degree-two parity constraints, and iteratively add connectivity cuts. For a fixed patch, solver infeasibility would rule out *all* improving tours expressible by that patch (if the model and solve are independently verified), rather than only particular k-opt sequences.

## October 2026 deeper prior-art audit and exact formulation

**Do not claim novelty for "TSP as a surface boundary."** Yılmaz Arslanoğlu's 2026 preprint [*A Surface-Based Formulation of the Traveling Salesman Problem*](https://optimization-online.org/wp-content/uploads/2026/02/arslanoglu-surface-based-tsp-formulation.pdf) explicitly uses this viewpoint with triangle-incidence complexes, connectivity / tree constraints and an Euler-characteristic filter. It demonstrates advantages on small and medium instances but does not provide a new Mona Lisa tour. A substantive distinction worth testing, not asserted to be novel, is **relative face-spin optimization on Cook et al.'s published, provably reduced planar Mona Lisa graph**. Our graph has nontriangular faces; the existing 100,000-edge tour gives a feasible reference spin assignment and a **zero-cost reference state**, so model cost differences are signed integers without rebuilding a full 100,000-city MILP.

For each sparse edge e=(u,v), fix baseline membership b_e in {0,1} and faces f,g. With Boolean relative face labels y_f, set t_e=y_f XOR y_g and x_e=b_e XOR t_e. The length change is exactly
\`\`\`
Delta = sum_e [ (1 - 2*b_e) * w_e * t_e ]
\`\`\`
and baseline degree-two makes each vertex constraint
\`\`\`
sum_{e incident v} (1 - 2*b_e)*t_e = 0.
\`\`\`
The model adds \`Delta <= -1\` and minimizes Delta; when a returned 2-factor has multiple cycles, its subtours yield **valid global cuts** \`sum_{e crossing S} x_e >= 2\`. All costs and cuts are integral. Critically, infeasibility with a fully solved patch only rules out improvements whose face labels are zero **outside that patch**; this is a conditional exact *patch* result, not a global optimality claim.

**Topological cross-check:** in a connected planar embedded graph, with selected boundary degree two at every vertex, the selected edges form one Jordan cycle iff the regions of each of the two face colors are both connected through unselected-edge dual adjacencies. Disconnected selected 2-factors generate multiple alternating nested boundaries, disconnecting at least one color. This gives an alternative way to separate invalid solutions by **dual connectedness**, and an independent checking invariant to investigate after the primal-cut solver.

**Current experiment:** \`dual_patch_search.py\` builds the complete reduced graph embedding, chooses the highest-positive 4-faces from Experiment 02, grows dual radius-3/4/5 patches, then runs OR-Tools CP-SAT with exact XOR/degree constraints and iterative subtour separation. All candidate tours are recomputed with the original upstream verifier. A four-job one-shot [Action](https://github.com/teddyli18000/web-ingest/actions/runs/40690007833) tests eight seeds, with independent per-patch time limits. This is the first attempt here that actually searches entire face-variable patches, rather than enumerating isolated swaps. Solver timeouts remain inconclusive; infeasibility is meaningful only when reported by CP-SAT after cuts.

**Complementary lines to explore after measuring the exact patches:** connectivity cuts in the **dual face-color domains**; separator-based dynamic programming with boundary pairings and winding information; and exact region exchange along the existing tour's two sides. Stop brute-force neighborhood growth if topology/cut formulation dominates the difficulty.

## Hypotheses
1. Exhaustively inspect the baseline for 2-opt improving edges among spatial nearest-neighbor candidate edges. A zero result proves only absence for the searched candidate pairs.
2. Primary next direction: optimize overlapping face patches under degree-two and single-cycle constraints using local exact solvers; explore separator-interface optimization after validating patches. Larger k-opt is a baseline, not the research agenda.
3. Discrete rounding may create plateaus: preserve equal-score moves, use lexicographic secondary structural cost, and evaluate exact integer gains before publishing.

## Experiment 01: nearest-neighbor 2-opt diagnostic
Run `python science-boundary/mona-lisa-tsp/nn_two_opt.py --input <baseline-certificate.json> --output <candidate.json> --report <report.json> --k 32` with `FEWSHOTS_ROOT` set to the local Few Shots checkout. Requires numpy and scipy. It imports the upstream verifier for exact coordinates and exact integer distances.
- Uses scipy cKDTree to generate spatial nearest-neighbor candidate pairs, then examines the standard 2-opt reversal.
- Scores each enumerated candidate with the exact integer TSPLIB distance function imported from the upstream verifier; no floating-point gain decisions.
- Iteratively applies a best sampled improving move until the candidate set is exhausted or the move budget is reached.
- A 2-opt move changes only two edges; the script tracks the exact local gain and rechecks the final tour with the upstream verifier.
- This is a **restricted 2-opt neighborhood**, not a complete search over O(n²) edge pairs.

## How to reproduce
All one-shot workflows were removed after completion; their validated run logs and artifacts remain linked above. For reproduction, check out both `few-shots/few-shots` and `bicobico2/ElimTSP` separately, install `numpy scipy networkx`, set `FEWSHOTS_ROOT` to the Few Shots checkout, and use the three retained scripts under this topic directory. The structural commands are:

```bash
python science-boundary/mona-lisa-tsp/planar_face_probe.py \
  --edges <ElimTSP>/results/mona.248972.edg.gz \
  --baseline <FewShots>/problems/p010-mona-lisa-tsp/baseline/certificate.json \
  --report planar-report.json
python science-boundary/mona-lisa-tsp/pair_face_search.py \
  --edges <ElimTSP>/results/mona.248972.edg.gz \
  --baseline <FewShots>/problems/p010-mona-lisa-tsp/baseline/certificate.json \
  --report pair-face-report.json --output certificate.json
```

The scripts produce no new tour unless a candidate passes exact integer scoring. A candidate must be placed in a directory as `certificate.json` and validated with the **upstream** p010 verifier before any claim or shot.

## Sources
- [Challenge and current tour/bound](https://www.math.uwaterloo.ca/tsp/data/ml/monalisa.html)
- [Few Shots problem](https://github.com/few-shots/few-shots/blob/main/problems/p010-mona-lisa-tsp/PROBLEM.md)
- [Few Shots verifier](https://github.com/few-shots/few-shots/blob/main/problems/p010-mona-lisa-tsp/verify/verify.py)
- [Published baseline certificate](https://github.com/few-shots/few-shots/blob/main/problems/p010-mona-lisa-tsp/baseline/certificate.json)

## Work log
- 2026-10-28: audit/restart checkpoint: 13-dimensional exact neutral family confirmed; shifted aim to coordinated topological moves crossing local barriers. Source links and firm limitations recorded above.
- 2026-10-28: audited 2026 Arslanoğlu surface-based MILP preprint, which independently establishes surface formulation as prior art. Derived exact integer face-spin patch model with degree-two and iteratively separated subtour connectivity; launched four-job matrix CP-SAT evaluation.
- 2026-10-28: planar-dual pair probe negative: 298,104 positive-gain 4-face pairs tested, zero produce a valid one-component tour. Next search should jointly optimize face spins under degree-two constraints and cut connectivity, rather than enumerate more independent face pairs.
- 2026-10-28: first planar-graph experiment succeeded; 248,972 edges, all 100,000 baseline edges present, planar. Identified +16 cost-lowering 2-factor flip that splits into two cycles; recorded full face-gain distribution in Action artifact, and launched paired-face connectivity-repair test.
- 2026-10-28: rechecked primary research; identified 2024 Cook–Helsgaun–Hougardy–Schroeder certified planar reduction and public 248,972-edge/1,635-fixed-edge data. Redirected from scaling k-neighbor probes to planar-dual face-region optimization, conditional on graph/baseline validation. Verified negative k=160 action result.
- 2026-10-28: checked p010 metadata, verifier, baseline provenance, accepted shot chain, Cook challenge page and repository instructions. Baseline 5,757,191; minimum accepted improvement one unit. Established reproducible nearest-neighbor 2-opt probe, k=32 verified, negative.
