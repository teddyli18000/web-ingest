# Strict counterfactual: hide Nagata and compare conflict-guided TSP search

Date: 2026-10-29. p010 subproject, **no record claim**.

## Experimental question

If Nagata's 5,757,191 tour had not been available, could a solver given the *legal* 5,757,199 route, six other contemporary stronger-than-random but **not-better-than-199** historical routes and three real Concorde LP primal vectors find a shorter valid tour? What edge-selection ideas generalize to other certified-optimum TSPLIB instances?

This study is **methodologically blinded**, not historically prospective: the public Concorde LP snapshots are dated 2011/2012, after Nagata's result, so upstream LP construction could have used knowledge of his incumbent. The search itself is barred from importing any Nagata tour, direct edge set, or our old Nagata-derived hotspot catalogue. The workflow physically deletes `upstream/problems/p010-mona-lisa-tsp/baseline/certificate.json` before preparing search inputs. Only a separate post-search evaluation workflow reads it.

## Pre-registered three families and resources

- `uncertainty`: historical connected-tour wiring disagreement and genuine fractional LP x, taking high-disagreement/high-ambiguity edges.
- `conflict`: historical consensus vs LP's x≈1 incompatible proposals. An initial implementation was too similar to uncertainty in small benchmarks (see **discovered redundancy** below); it has been replaced by a geometrically generated historical consensus–LP rejected-edge interface for *new* held-out cases, `conflict_v2`.
- `repair`: find lowest integer degree-two solution over the permitted old tour union (may contain subtours), identify disconnected components, score new complete-metric 2-edge cross-cut bridge proposals by exact cost, add the best novel edges and enforce a **single tour** in the final CP-SAT AddCircuit. This pilot is *one-shot degree-two oracle + repair*, **not** an exhaustive or full dynamic subtour-cut oracle.

Each of six Mona candidate runs adds exactly 64 or 192 nonparent edges to the common 103,857-edge old-tour parent union and has a **125-second wall budget / four workers** including candidate generation. No hand-picked Nagata edges are imported. Computed and independently scored with the official Few Shots p010 EUC_2D verifier. Selectors may vary in variable count because candidate-edge endpoints differ, a confounding complexity issue to track.

## Mona results — actual blinded search and independent unsealing

- [Blind compute 40867628330](https://github.com/teddyli18000/web-ingest/actions/runs/40867628330): all six methods × budgets jobs executed, but all CP-SAT statuses were **UNKNOWN** at ~125 seconds. There are **zero verified improvements**, and NO proof of infeasibility. The repair method's initial degree-two oracle found a -374-cost 2-factor with ~225–229 disconnected cycles, not a legal tour.
- [Independent unsealing 40868003912](https://github.com/teddyli18000/web-ingest/actions/runs/40868003912): Nagata vs old reference have **2,687 differing tour edges**. Across all six selected new-edge groups, exactly **zero** selected chords matched any target-only Nagata edge. No winning candidate tours existed to compare.
- [Postmortem-only observability 40869098503](https://github.com/teddyli18000/web-ingest/actions/runs/40869098503): **1,978 Nagata edges were absent from all seven old parent routes**. Of these 1,978 previously unrepresented edges, 1,936 appear with x>0 in at least one true LP solution; 1,886 have fractional x in at least one LP; **1,978/1,978** are in the geometric 8 nearest neighbors of at least one endpoint, and 1,912 are in the 4 nearest neighbors. These statistics were calculated ONLY AFTER the blind search and are not available as selector training labels on the same split. With just 64/192 novel chords it would be impossible even to reproduce Nagata exactly, regardless of ranking; a *different* shorter legal tour might still exist in the tested graph.
- This shows a **search representation and global coordination bottleneck**, not a lack of near-geometry or LP-positive edge coverage. Do not claim the blind experiment proves a selector inferior or establishes an optimum.

## Independent TSPLIB checks and essential ablations

Source instances are byte-identical TSPLIB95 copies from [mastqe/tsplib](https://github.com/mastqe/tsplib), optimal scores from the [official Heidelberg TSPLIB best-values page](https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/TSP-BEST.html). All costs use exact TSPLIB `floor(hypot+0.5)` integer distances. Smaller cases construct their own **valid degree-two LP with some iteratively separated subtour cuts** using HiGHS: not all exponentially many subtour constraints and not the original Concorde 100K LP. Exact resulting Hamiltonian cycles were optimized with CP-SAT and independently scored.

### First five cases: 3 historical-like independently generated parents, plus zero-new-edge control

[Run 40869449446](https://github.com/teddyli18000/web-ingest/actions/runs/40869449446), [parent-only ablation on preceding 10-parent pilot](https://github.com/teddyli18000/web-ingest/actions/runs/40868832388).

| Instance (TSPLIB optimum) | Hidden reference | Parent-only | Uncertainty | Original conflict | Repair |
| --- | ---: | ---: | ---: | ---: | ---: |
| eil51 (426) | 433 | 431 | 429 | 429 | 431 |
| berlin52 (7,542) | 7,734 | 7,542 | 7,542 | 7,542 | 7,542 |
| st70 (675) | 684 | 681 | 680 | 680 | 681 |
| eil76 (538) | 552 | 551 | 541 | 541 | 551 |
| kroA100 (21,282) | 21,811 | 21,473 | 21,470 | 21,470 | **21,443** |

All methods admitted the same three parent tours plus the reference. Every method added 12 novel chords except zero-chord control. All restricted exact solve statuses OPTIMAL. Crucial independent [selection-overlap audit 40869848599](https://github.com/teddyli18000/web-ingest/actions/runs/40869848599) showed the **two LP strategies chose the exact same 12 chords on every one of five cases**. Thus they are empirically ONE strategy, not two independent confirmations. Their extra gains against zero-chord control were 2, 0, 1, 10, 3; repair gained 0, 0, 0, 0, 30. Berlin52 is a trivial parent-union success, NOT a learned-selector success; the primal LP after cut separation was already integral and at the certified optimum.

The reference and hidden local-search winner were generated deterministically without using the published optimal tours or scores. However, the *very first 10-parent pilot* [run 40868459085](https://github.com/teddyli18000/web-ingest/actions/runs/40868459085) generated some parents by perturbing the best hidden generator tour; that is a data-generation leakage issue and that pilot is **excluded from claims**. The five-case 3-parent rerun removed this leak before selecting a held-out winner.

### New five instances: prespecified corrected conflict signal

[Unseen-instance Action 40870221063](https://github.com/teddyli18000/web-ingest/actions/runs/40870221063), five held-out certified-optimum instances `rat99, ch130, eil101, pr76, kroB100`, each with three independently generated old parents, explicit zero-chord control and the same 12-chord/wall-clock cap. `conflict_v2` now uses **historically agreed edges rejected by the LP** as *ports* to propose distinct short complete-graph alternate edges, prioritizing any x≈1 alternative absent all parents; it cannot trivially collapse to the same LP-positive candidate pool as uncertainty. All candidates are generated without reading the withheld local-search winner or certified optimum; those appear only in separate `evaluate` jobs. Results must be retrieved from the final Action, not guessed.

## Current scientific assessment and next method gate

1. Predicting *cheap disconnected degree-two* structures is easier than constructing a legal improved Hamiltonian tour; huge negative 2-factor deltas must not be counted as score gains.
2. Target-edge recall, feasibility, exact tour cost and elapsed compute are **separate** measurements. In 100K Mona at 64/192 edges, selected **zero** of 1,978 missing target edges: the selectors fail a core retrieval diagnostic on this split, but their solver was also computationally inconclusive.
3. LP fractionality and historical conflict can be redundant in a small candidate pool; never claim synergy without edge-set overlap and a matched parent-only control.
4. Use failure against true held-out routes to formulate a *new* representation in which a group of roughly 2,000 new near-neighbor edges may be switched **coherently** rather than choosing 192 isolated edges. The next preregistered test should derive variable-size sparse connector sets with explicit subtour-cut duals/SEC feedback, compare at equal time with nearest-neighbor and parent-only baselines, and verify on **new unseen instances before touching this disclosed Nagata holdout again**.

## Implementations

- [blind_counterfactual_199.py](../blind_counterfactual_199.py), [blind_counterfactual_eval.py](../blind_counterfactual_eval.py), [blind199_hidden_support_audit.py](../blind199_hidden_support_audit.py)
- [tsplib_counterfactual_bench.py](../tsplib_counterfactual_bench.py), [tsplib_selector_redundancy.py](../tsplib_selector_redundancy.py)
- All workflows named `temp-p010-blind*`, `temp-p010-tsplib-*` are disposable one-shot orchestration and must be retired once output is preserved.

## Ten-instance geometric negative controls and coherent-pair repair (post-hoc)

Geometric controls [run 40871195577](https://github.com/teddyli18000/web-ingest/actions/runs/40871195577) introduce 12 truly novel chords by (i) absolute nearest distance, (ii) short edges adjusted by already-selected tour-neighbor lengths, or (iii) seeded random from 8-nearest-neighbor candidate graph. Same parent tours, exact metric and single-thread AddCircuit. The locally cost-adjusted near-neighbor heuristic sometimes equals the more elaborate LP methods; an LP-specific superiority claim is unsupported by these ten cases.

The proposed **coupled 2-edge cross-subtour repairs** explicitly rank complete 2-opt reconnection pairs across disconnected 2-factor components by `d(u,v)+d(a,b)-d(u,a)-d(v,b)` rather than scoring the two new chords independently. Exact same 12-edge budget and single-thread AddCircuit [run 40871463432](https://github.com/teddyli18000/web-ingest/actions/runs/40871463432). On these ten previously examined splits, paired reconstruction **ties the original single-chord repair in 9/10 cases** and is better by 1 on `eil101` (636 vs 637). Thus the change improves *coherence of the proposal representation* but has little demonstrated incumbent-score benefit yet.

| Case | Parent only | LP ambiguity | Real LP conflict v2 when available | One-chord defect repair | Two-edge paired repair | Nearest / local-surplus / random 8nn |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| eil51 | 431 | 429 | 429 (original, redundant) | 431 | 431 | 431 / 431 / 430 |
| berlin52 | 7542 | 7542 | 7542 (original, redundant) | 7542 | 7542 | 7542 / 7542 / 7542 |
| st70 | 681 | 680 | 680 (original, redundant) | 681 | 681 | 681 / 681 / 681 |
| eil76 | 551 | 541 | 541 (original, redundant) | 551 | 551 | 551 / 549 / 551 |
| kroA100 | 21473 | 21470 | 21470 (original, redundant) | 21443 | 21443 | 21473 / 21473 / 21473 |
| rat99 | 1233 | 1226 | 1224 | 1216 | 1216 | 1227 / 1218 / 1233 |
| ch130 | 6214 | 6214 | 6214 | 6209 | 6209 | 6214 / 6214 / 6214 |
| eil101 | 637 | 634 | 634 | 637 | **636** | 637 / 637 / 637 |
| pr76 | 109110 | 109110 | 109110 | 108830 | 108830 | 109110 / 109110 / 109110 |
| kroB100 | 22569 | 22569 | 22485 | 22531 | 22531 | 22552 / **22485** / 22569 |

**Evidentiary limits**: two entirely different generation regimes (Mona original published LP vs small-instance HiGHS degree+some SEC relaxations), correlated TSPLIB problems, deterministic single parent-generation seed, and only ten post-hoc cases. `berlin52` is degenerate (parent-only reaches known optimum). None of the above implies a globally optimal model or a statistically established win rate. The truly new `conflict_v2` method has only five evaluated instances in this table.

### Preregistered separate third fold

[Third-fold Action 40871715238](https://github.com/teddyli18000/web-ingest/actions/runs/40871715238) freezes **five unused certified TSPLIB cases** `kroC100, kroD100, kroE100, rd100, lin105` and compares all **eight** now distinct methods (zero-chord parent union, LP uncertainty, real consensus-vs-LP conflict, independent one-chord repairs, coherent two-chord repairs, absolute nearest, adjusted near-neighbor, random 8nn) at 12 novel edges and an 18-second inclusive search budget per method. Per-instance search receives only public parents, local coordinates and a full *independently generated* LP relaxation. Better hidden tour and official optimum are in a separate post-search job. This fold is the next honest generalization test, not a re-run tuned on exposed results.

### Relevant methods literature reviewed before follow-on

- Cook, Helsgaun, Hougardy, Schroeder, *Local elimination in the traveling salesman problem*, Mathematical Programming Computation (2024): https://doi.org/10.1007/s12532-024-00262-y — verified edge elimination, local exchange and LP reduced costs; useful for principled candidate pruning, but not a promise that kNN implies optimality.
- Akcay, Delorme and Pferschy, *Machine-learning-enhanced strategies to generate subtour elimination constraints* (2026): https://optimization-online.org/2026/04/machine-learning-enhanced-strategies-to-generate-subtour-elimination-constraints-for-the-symmetric-traveling-salesman-problem/ — which SECs must be added early, with reported benefits and distribution-shift caveats. Prior art for counterexample-conditioned cut prioritization.
- Fang, Weng and Ban, *ASAP: Exploiting the Satisficing Generalization Edge in Neural Combinatorial Optimization*, ICML 2026: https://proceedings.mlr.press/v306/fang26t.html — **proposal/selection** decomposition: first protect broad solution coverage, then optimize under the current constraints. It favors preserving many plausible hidden edges rather than hard top-12 candidate filtering.
- Song et al., *DualCert: A Solver for the TSP with Constraint-Coupled Learning* (2026 preprint): https://arxiv.org/abs/2608.09042 — SEC-coupled guidance with deterministic verification, experiments on TSP1000; no evidence of a record improvement on Mona Lisa 100K.

**Representation pivot:** a 12-edge-only rigid score ranking fails especially on Mona, where 1,978 Nagata-only edges are outside old parent union. A viable next model must admit a much broader candidate reservoir and *let Hamiltonian connectivity + admissible cuts jointly select coordinated edges*, rather than adding ever more isolated "best" edges. A diversity-preserving proposal stage is a plausible testable direction, not a demonstrated breakthrough.
