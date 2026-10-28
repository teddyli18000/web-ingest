# Thomson problem for 960 points

## Question

Can we find a 960-point configuration on the unit sphere with Coulomb energy low enough to beat the live Few Shots p007 record by at least `1e-6`?

## Current state

- Few Shots p007 is a minimization problem with absolute epsilon `1e-6`.
- Live merged record checked on 2026-10-27: `444368.3924061973`, shot `Ronnie2025/c3-replica-exchange-scars`.
- Therefore a valid next score must be at most `444368.3924051973`, subject to re-checking upstream immediately before any claim or submission.
- No open p007 pull request was visible at the latest check.
- The current record is C3-symmetric with 12 `5-7-5-7-5` scars (24 dislocations). It was found upstream by symmetry-reduced basin hopping, then six-replica exchange in C3 orbit space, followed by unconstrained relaxation/Newton polishing.
- The previous record `444368.4040805305` is D2-symmetric with 20 dislocations and came from symmetry-preserving cut-and-splice genetic search plus basin hopping.
- Project diagnostics identify the record's C3 axis as coordinate z to about `2e-9` nearest-neighbor RMS under a 120° rotation.
- Two project-specific move families have now failed to improve it: 40 exact-C3 coherent smooth deformations, and one-cycle size oscillation through N=959 and N=961.
- The active route is **full 1920-dimensional physical tangent Hessian analysis**, followed by symmetry-breaking basin escapes along the lowest non-rigid modes. Diagnostic Actions run: `40623234712`.

## Why this may be a frontier

The public Few Shots record already improves the 2026 Amore-Wales Cambridge Cluster Database configuration and is judged by an exact-integer verifier after rationalization. The landscape is known to contain exponentially many local minima with shrinking energy gaps at larger N, while the public record chain shows that changing the global arrangement of topological scars can produce record-sized gains.

## What is known / upstream lessons

### Productive ideas

1. Reduce dimension with exact low-order symmetry (especially D2/C3), search there, then release the symmetry.
2. Cross barriers with population or replica-exchange methods rather than ordinary local kicks.
3. Treat global scar arrangement as the slow structural degree of freedom; purely local scar surgery tends to heal back.
4. Propagate structures between neighboring N values; Amore-Wales (2026) use spherical-Voronoi insertion candidates and high-contribution removals to propagate low minima across contiguous sizes.
5. Wales-style energy-landscape work supports following low Hessian eigenvectors to locate nearby low barriers and nearly degenerate minima; this motivates the current full-space soft-mode route.
6. Any apparent breakthrough must be released from imposed symmetry, independently polished, rationalized under p007 limits, and checked by the official verifier.

### Public dead ends worth not repeating

- Thousands of unconstrained basin-hopping/local defect moves around the old T record did not improve it.
- The T-symmetric subspace was extensively explored and appears exhausted near the old record.
- Local transplantation of short scars heals back because the defect change is coupled to global shear.
- Caspar-Klug, broken-icosahedral, coarse subdivision, Riesz-exponent homotopy, and D5/C5 families stayed well above the current record.

## Current route

The live record certificate is always the seed/comparator, never the original baseline.

The current diagnostic computes the lowest internal modes of the **full unconstrained 960-point problem**. It uses matrix-free centered finite differences of the analytic gradient, but diagonalizes the Hessian in orthonormal physical tangent coordinates `y=(dtheta, sin(theta)dphi)`, not raw longitude/latitude coordinates. The three rigid-rotation zero modes are explicitly projected/lifted before the eigensolve, and Hessian-vector symmetry plus Ritz residuals are recorded.

If the spectrum is numerically trustworthy, the next campaign will scan both signs and increasing RMS angular amplitudes along the lowest non-rigid modes, then combinations of any near-degenerate soft-mode pairs. Each perturbed configuration will be fully relaxed without symmetry. This is deliberately different from the exact-C3 smooth-field campaign: the perturbations are selected by local curvature in all 1920 tangent degrees of freedom and are allowed to break C3 immediately.

All search code clones Few Shots `main` at runtime and discovers the lowest merged p007 shot so stale seeds cannot silently become the baseline.

## Evidence and experiments

### Live-record diagnostic

Durable result: `results/diagnostic-live-record.txt`.

- Merged shot discovered dynamically: `Ronnie2025/c3-replica-exchange-scars`.
- Claimed verifier score: `444368.3924061973`.
- Direct double-precision energy of the rational certificate: `444368.392406201164704`.
- Tangent-gradient RMS on rationalized coordinates: `5.14e-6`; maximum `1.18e-5`, consistent with tiny rationalization perturbations.
- Second-moment eigenvalues: `319.997418654053`, `319.997418737504`, `320.005162608441`.
- +120° rotation about z gives nearest-neighbor RMS `1.98e-9`, maximum `4.63e-9`; the C3 action is unambiguous.

### Exact-C3 smooth global deformations

Durable result: `results/c3-smooth-summary.txt`. Actions run `40619792492`.

Four independent seeds, ten starts each. All 40 starts failed to improve the incumbent. Small/moderate deformations returned to `444368.39240620...`; larger moves found higher distinct minima from roughly `444368.4114` upward. This is evidence that the present C3 basin is robust under coherent low-order smooth fields, not an exhaustion result for all C3 space.

### Oscillating-size search from the live C3 record

Actions run `40620255734`.

- `960→959→960`: five high-contribution removals, two best N=959 parents, five Voronoi insertion returns per parent. Best returned N=960 energy: `444368.392406207859`, about `1.07e-8` **above** the polished record.
- `960→961→960`: five lowest-potential Voronoi insertions, two best N=961 parents, five high-contribution deletion returns per parent. Best returned N=960 energy: `444368.392406216473`, about `1.93e-8` above.
- Several return branches reproduce the incumbent basin to ordinary double-precision accuracy; other branches land distinctly higher (`+0.0033`, `+0.167`, etc.).

Conclusion: a single ±1-particle size cycle using these top-ranked branches does not escape to a lower basin from the new C3 record. This does not rule out deeper/multi-cycle size propagation.

### Full-space soft-mode diagnostic

Active Actions run `40623234712`. Code: `code/diagnose_soft_modes.py`.

Goal: obtain 14 lowest non-rigid physical tangent Hessian modes, with explicit checks of finite-difference Hessian symmetry and eigenpair residuals. No scientific conclusion until the diagnostic completes.

## Dead ends

- **Project-specific:** 40 exact-C3 low-order smooth global deformations (roughly 0.007–0.30 rad) produced no lower basin. Do not repeat this move family without materially different crossover/tempering.
- **Project-specific:** one top-ranked single-cycle `960↔959` and `960↔961` oscillation returned to the record basin or higher minima. Deeper/multi-cycle propagation remains open.
- **Infrastructure-only failure, not scientific evidence:** guessed CCD `s_1/dat/points_N_1.dat` URLs for N=958,959,961,962 returned HTTP 404 before optimization.
- See also the upstream dead ends above.

## Next steps

1. Validate the full-space soft-mode spectrum numerically.
2. Scan low non-rigid modes in both directions over increasing physical RMS amplitudes; fully relax each start and deduplicate returned basins by energy/structure.
3. For near-degenerate low modes, scan phase combinations rather than only individual eigenvectors.
4. If a floating candidate improves by comfortably more than `1e-6`, independently polish, rationalize, run the Few Shots verifier and `tools/check.py`, then re-check live main/open PRs before preparing a shot.

## Sources

- Few Shots p007 problem/verifier: https://github.com/few-shots/few-shots/tree/main/problems/p007-thomson-problem
- Few Shots p007 record chain: https://github.com/few-shots/few-shots/blob/main/problems/p007-thomson-problem/FEWSHOT.md
- D2 record shot: https://github.com/few-shots/few-shots/tree/main/problems/p007-thomson-problem/shots/Abreto/thomson960-d2-ga
- C3 current-record shot: https://github.com/few-shots/few-shots/tree/main/problems/p007-thomson-problem/shots/Ronnie2025/c3-replica-exchange-scars
- P. Amore and D. J. Wales (2026), arXiv:2610.08122: https://arxiv.org/abs/2610.08122
- Journal version, J. Chem. Phys. 165, 164104 (2026): https://doi.org/10.1063/5.0355867
- Cambridge Cluster Database, Riesz s=1: https://www-wales.ch.cam.ac.uk/~wales/CCD/Thomson/site/s_1/index.html
- D. J. Wales and S. Ulker (2006), Thomson landscape/rearrangements: https://doi.org/10.1103/PhysRevB.74.212101
- T. F. Middleton and D. J. Wales (2001), soft-mode eigenvector-following to low-lying transition states: https://doi.org/10.1103/PhysRevB.64.024205
- D. J. Wales and J. P. K. Doye (1997), basin hopping: https://doi.org/10.1021/jp970984n
- P. Amore et al. (2025), Thomson local minima/stationary-state landscape: https://arxiv.org/abs/2506.08398
- Kuznetsov and Sahinidis (2026), deterministic global optimization for small Thomson/Tammes instances: https://doi.org/10.1016/j.dam.2026.05.015

## Work log

### 2026-10-27

Opened this durable direction after reading repository rules, the Few Shots skill/problem, the complete merged p007 record chain, and both merged p007 shot descriptions. Confirmed live merged record `444368.3924061973` and no open p007 PR at the latest checks.

Ran and preserved a live-record diagnostic, confirming the z-axis C3 action to about `2e-9` RMS after 120° rotation. A 40-start exact-C3 smooth-field campaign found no improvement. A direct one-cycle oscillating-size search through N=959 and N=961 also failed to beat the record, with its best returns only `~1e-8` above the incumbent and several branches falling back into the same basin.

Current-literature review re-checked the newly published Amore-Wales JCP paper and older Wales landscape work. The latter gives a specific justification for following low Hessian eigenvectors: soft modes often lead efficiently to low-lying transition states and nearly degenerate neighboring minima. Added a full-space physical-tangent Hessian diagnostic and launched it as Actions run `40623234712`.
