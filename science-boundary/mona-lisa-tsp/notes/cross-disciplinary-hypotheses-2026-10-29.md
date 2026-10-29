# Cross-disciplinary hypothesis audit — 2026-10-29

## Decision

**Do not queue another sweep of larger k, larger geographic radii, or more one-/two-motif pairings yet.** Across the recorded tests those mostly increase excluded space without improving the best tour. Pause and change the *variable and interface selection process*. Baseline best is still 5,757,191 (TSPLIB EUC_2D); score 5,757,190 would be a verified improvement. The 51-dimensional neutral family and cheap disconnected 2-factors are important observations, but not evidence of a new record.

### Critical problem representation

Let x_e denote tour edge incidence, b_e an incumbent tour, and F the degree-two equations. There are cheap integral points of F (2-factors with disconnected small cycles), but the single-cycle/topological constraint forbids them. The observed problem is therefore the *gap between the disconnected degree-2 manifold and the connected tour manifold*, not merely an absence of negative reduced-cost edges.

We should rank candidate interventions by their ability to change the connectivity obstruction and its associated dual price. A new method must simultaneously expose profitable disconnections **and** their cheapest nonlocal connectivity compensation rather than performing the two operations in isolation. The known neutral cube gives distinct incumbent bases against which to measure sensitivity.

## Prior art checked

1. Cook, Helsgaun, Hougardy, Schroeder (2024), *Local elimination in the traveling salesman problem*, Mathematical Programming Computation, https://doi.org/10.1007/s12532-024-00262-y. Public graph reduction under 2.5n edges on large Euclidean instances, certificates and LP reduced-cost elimination. Advantage: proven candidate pruning; caveat: we did not independently validate all elimination certificates.
2. Jaziri, Cuvelier, De Backer (ICML 2026), *Generative Large Neighborhood Search: Scalable Set Cover Optimization via Discrete Diffusion*, https://proceedings.mlr.press/v306/jaziri26a.html . Diffusion prediction instability is used to choose neighborhoods for exact repair. This was demonstrated on **set cover**, not 100k TSP; importing it needs new evidence.
3. Deza, Khalil, Fan, Zhou, Zhang (AAAI 2025), *Learn2Aggregate: Supervised Generation of Chvátal–Gomory Cuts Using Graph Neural Networks*, https://doi.org/10.1609/aaai.v39i25.34900 . Rank useful aggregation constraints; preserve exact downstream mathematical solver. No direct evidence of useful p010 cut learning.
4. Zhao, Wang, Zeng (2026 preprint), *G-LNS: Generative Large Neighborhood Search for LLM-Based Automatic Heuristic Design*, https://arxiv.org/abs/2602.08253 . Co-evolve destroy and repair policies, not independent operators; TSP/CVRP evaluation, though author claims need benchmark inspection.
5. Heimann, Hoang, Hougardy (2026), *Closing All-Exp Gaps in Local Search for the Traveling Salesman Problem and Maximum Constraint Assignment*, https://arxiv.org/abs/2610.31513 . The all-exp property even for 2-opt is a theoretical reason not to assume longer sequential improving moves solve the plateau, but it does NOT prove anything about this particular Euclidean instance.
6. Karalias et al. (NeurIPS 2025), *Geometric Algorithms for Neural Combinatorial Optimization with Constraints*, https://papers.nips.cc/paper_files/paper/2025/hash/713939ee5a7b14a6fecf69e692ec3799-Abstract-Conference.html . Feasibility-preserving decomposition of neural outputs; experimental applicability to tour polytope remains unproven.
7. Previously verified p010 experiments: 51-switch universal connectivity SAT + Z3 (run 40697459440); all 12,281 alternating quadrilateral faces with global sparse two-edge repair (run 40696640556); symbolic motifs and exact circuit tests (run 40830451326); complete-graph remote 8/12/16 path-interface experiments (run 40833359687).

## Ranked falsifiable research hypotheses

### H1 — Cut-dual-guided region selection (first priority)
**Cross-field transfer:** dual sensitivity / adversarial witness generation / learned constraint aggregation. Solve a *relaxed* minimum-cost 2-factor or sparse-graph LP with progressively separated subtour cuts. Analyze the exact small disconnected cycles and their cheapest merge-interface cuts. Rather than picking faces by local gain or graph radius, select a **paired set of nonlocal interfaces maximizing gain minus a connectivity-repair lower bound**, e.g., dual-weighted cut capacity from a flow/min-cut oracle.

- First test requires **no neural training**: produce and compare three selectors at equal solver wall time: geographic k-nearest patch, random nonlocal patch, and dual-priced connectivity patch.
- Measurement: valid tour improvement (primary), fraction of tested patches with a feasible connected negative delta, quality of LP bound and solver infeasibility/time, transfer across several incumbent neutral states.
- Falsifier: learned/dual selector adds no feasible candidates or reduces no search time against matched controls.
- Critical caveat: cut-dual multipliers have gauge/nonuniqueness; do not assume large multiplier is causally informative. Multiple LP perturbations needed to test stability.

### H2 — Neutral plateau as a quotient/latent symmetry
**Cross-field transfer:** statistical mechanics flat energy landscapes, gauge freedom and residual parameterizations. The 51 binary switches are exact zero-integer-cost commuting generators; represent search states by **(neutral bit mask, nonneutral residual edge set)**, and optimize only the residual. This quotient removes irrelevant variation and reduces branching complexity while preserving all actual tours in the selected family.

- No blanket claim that these switches are symmetries of *all* TSP solutions; they are valid only on their established submanifold.
- Test a residual-aware connected exact model vs original unstructured AddCircuit under identical candidate pool and wall time. Measure bound, conflicts, feasibility and best score.
- Falsifier: quotient encoding gives no speedup, or transitions leave the neutral submanifold before obtaining improvements.

### H3 — Co-evolve disconnection and repair operators
**Cross-field transfer:** adversarial generators, ejection chains, G-LNS destroy/repair co-design. One agent/candidate family proposes profitable 2-factors; another predicts which **costly** connectors permit global reconstruction, trained against exact small patch outcomes. Optimize a joint reward based on *connected* verified improvement, not raw 2-factor saving.
- Start with ranking/beam selection using handcrafted exact graph features, not an expensive diffusion model. Only introduce learned model if labels and held-out improvements justify it.
- Baselines: best local gain, geometric radius, random, classical LKH/EAX candidates.
- Falsifier: joint candidate selection fails to beat exact search on the same budget.

## Why not start with a GAN / backpropagation directly?

A GAN or diffusion sampler for edge incidence does not preserve degree-2 and one-component connectivity by construction. A differentiable surrogate may improve continuous objectives while worsening integer-rounded p010 score; gradient estimates through a discrete Hamiltonicity projection could be misleading. Use learning for **selection/prediction**, exact solvers for **construction/validation**. Residual architectures inspire a useful perturbation-relative-to-a-verified-tour parameterization but do not themselves solve the integer optimization problem.

## Active public search

An Undermind literature audit has been launched in the connected account:
https://app.undermind.ai/projects/477f9f30-0501-4438-b709-18024e0871ec?path=/Mona%20Lisa%20TSP%20cross%20disciplinary%20frontier%20mechanisms

It may provide additional leads later; do not claim its pending results have been read.

## Next actions and release gate

1. Recheck the running neutral-conditioned path-interface action; label timeouts/UNKNOWN accurately. Reassess based on outcomes, not just more samples.
2. Obtain a reproducible LP/cut dual benchmark on the **published reduced planar graph** with independently validated edge weights and baseline; start with a subset or perturbation to understand dual stability.
3. Implement deterministic, equal-budget H1 selector comparison before training neural models. A strict improvement requires official Few Shots verifier and upstream submission; no manuscript or shot claiming victory until then.

**Status:** literature/decision audit completed; no record improvement or new computational proof claimed in this note.
