# Thomson problem for 960 points

## Question

Can we find a 960-point configuration on the unit sphere with Coulomb energy low enough to beat the live Few Shots p007 record by at least `1e-6`?

## Current state

- Few Shots p007 is a minimization problem with absolute epsilon `1e-6`.
- Live merged record checked on 2026-10-27: `444368.3924061973`, shot `Ronnie2025/c3-replica-exchange-scars`.
- Therefore a valid next score must be at most `444368.3924051973`, subject to re-checking upstream immediately before any claim or submission.
- No open p007 pull request was visible at the latest check.
- The current record is a C3-symmetric arrangement with 12 `5-7-5-7-5` scars (24 dislocations). It was found by symmetry-reduced basin hopping followed by six-replica exchange in C3 orbit space, then unconstrained relaxation and Newton polishing.
- The previous record `444368.4040805305` is D2-symmetric with 20 dislocations and was found by symmetry-preserving cut-and-splice genetic search plus basin hopping.
- Live-certificate diagnostics show the C3 axis is the coordinate z axis: a +120 degree z rotation matches the rationalized point set with nearest-neighbor RMS `1.98e-9` and maximum `4.63e-9`.
- A 40-start exact-C3 smooth-deformation campaign found no lower basin; the best floating energy was the reconstructed incumbent `444368.392406197148`. Durable summary: `results/c3-smooth-summary.txt`.
- The active route is a one-cycle oscillating-size search directly from the live record (`960→959→960` and `960→961→960`) using high-contribution removals and spherical-Voronoi insertions, Actions run `40620255734`.

## Why this may be a frontier

The public p007 record already improves the 2026 Amore-Wales Cambridge Cluster Database configuration and is explicitly judged by an exact-integer verifier after rationalization. The remaining task is global optimization in a landscape with many near-degenerate local minima, where the public record chain shows that changing the global arrangement of topological scars can produce record-sized gains.

## What is known / upstream lessons

### Productive ideas

1. Reduce dimension with exact low-order symmetry (especially D2 and C3), search there, then release the symmetry.
2. Cross barriers with population or replica-exchange methods rather than ordinary local kicks.
3. Treat the global scar arrangement as the meaningful slow degree of freedom; purely local scar surgery tends to heal back.
4. Propagate good structures between neighboring N values; Amore-Wales (2026) report this as an effective large-N search strategy, ranking insertions at spherical Voronoi vertices and removals by individual energy contribution.
5. Always finish in the full unconstrained space and independently verify after rationalization.

### Public dead ends worth not repeating

- Thousands of unconstrained basin-hopping steps and local defect-targeted perturbations around the old T record did not improve it.
- The T-symmetric subspace was extensively explored and appears exhausted near the old record.
- Local transplantation of short scars heals back because the defect change is coupled to global shear.
- Caspar-Klug, broken-icosahedral, coarse subdivision, Riesz-exponent homotopy, and D5/C5 families stayed well above the current record.

## Current route

The live record certificate is the seed and comparator, never the original baseline.

The first project-specific search tested coherent exact-C3 deformations: 40 low-order `m=0,3,6` tangent-field starts over a broad amplitude range. Small and moderate moves returned to the incumbent, while larger moves reached higher minima. This move family is now deprioritized.

The current search implements one cycle of the Amore-Wales oscillating-size idea from the *new Few Shots C3 record itself*, rather than from the older CCD N=960 configuration:

- **down route:** rank five N=960 deletions by largest individual Coulomb contribution, relax each N=959 state, retain the two best parents, then rank five spherical-Voronoi insertion sites for each parent and relax back to N=960;
- **up route:** rank five spherical-Voronoi insertions from N=960 by added potential, relax N=961 states, retain the two best parents, then rank five removals and relax back to N=960.

This creates topology-changing, globally relaxed excursions without relying on unavailable guessed neighboring-N CCD files. The earlier direct CCD-neighbor probe failed at input retrieval (HTTP 404 for guessed `s_1/dat/points_N_1.dat` paths), so it produced no scientific search result and is not counted as a dead end.

If size oscillation does not reach a competitive basin, the next justified route is targeted symmetry breaking along low tangent Hessian modes, not generic random kicks.

All current search code clones Few Shots `main` at runtime and discovers the lowest merged p007 shot so stale seeds cannot silently become the baseline.

## Evidence and experiments

### Live-record diagnostic

Durable result: `results/diagnostic-live-record.txt`.

- Merged shot discovered dynamically: `Ronnie2025/c3-replica-exchange-scars`.
- Claimed verifier score: `444368.3924061973`.
- Direct double-precision energy of the rational certificate: `444368.392406201164704`.
- Tangent-gradient RMS on the rationalized coordinates: `5.14e-6`; maximum `1.18e-5`, consistent with tiny rationalization perturbations.
- Second-moment eigenvalues: `319.997418654053`, `319.997418737504`, `320.005162608441`; the unique eigenvector is essentially z.
- +120 degree rotation about z gives nearest-neighbor RMS `1.98e-9`, maximum `4.63e-9`; thus the exact C3 group action is unambiguous.

### Exact-C3 smooth global deformations

Durable result: `results/c3-smooth-summary.txt`. GitHub Actions run `40619792492`.

Four independent seeds, ten starts each. All 40 starts failed to improve the incumbent. Small/moderate deformations returned to `444368.39240620...`; larger moves found higher distinct minima from roughly `444368.4114` upward. This is evidence that the present C3 basin is robust under coherent low-order smooth fields, not an exhaustion result for C3 space.

### Active oscillating-size search

GitHub Actions run `40620255734`, two independent routes (`down`, `up`). It starts dynamically from the live Few Shots record and uses full unconstrained L-BFGS relaxation at every intermediate size and return state.

## Dead ends

- **Project-specific:** 40 exact-C3 low-order smooth global deformations (roughly 0.007--0.30 rad) produced no lower basin. Do not repeat this move family without a materially different crossover/tempering mechanism.
- **Infrastructure-only failure, not scientific evidence:** guessed neighboring CCD `s_1/dat/points_N_1.dat` URLs for N=958,959,961,962 returned HTTP 404. Replaced by direct size oscillation from the current record.
- See also the upstream dead ends above.

## Next steps

1. Collect the active `960↔959/961` bounce campaign and preserve its best returned minima.
2. If a floating candidate improves by comfortably more than `1e-6`, polish in all 1920 tangent degrees of freedom, rationalize under p007 denominator limits, and run the Few Shots verifier independently.
3. If size oscillation fails, compute low tangent Hessian modes and launch mode-following symmetry-breaking basin escapes with basin deduplication.
4. Before any claim or submission, re-check Few Shots main plus open p007 PRs and compare against the then-live threshold.

## Sources

- Few Shots p007 problem and verifier: https://github.com/few-shots/few-shots/tree/main/problems/p007-thomson-problem
- Few Shots p007 generated record chain: https://github.com/few-shots/few-shots/blob/main/problems/p007-thomson-problem/FEWSHOT.md
- D2 record shot: https://github.com/few-shots/few-shots/tree/main/problems/p007-thomson-problem/shots/Abreto/thomson960-d2-ga
- C3 current-record shot: https://github.com/few-shots/few-shots/tree/main/problems/p007-thomson-problem/shots/Ronnie2025/c3-replica-exchange-scars
- P. Amore and D. J. Wales (2026), Cambridge Cluster Database work: https://arxiv.org/abs/2610.08122
- Journal version: https://doi.org/10.1063/5.0355867
- Cambridge Cluster Database, Riesz s=1: https://www-wales.ch.cam.ac.uk/~wales/CCD/Thomson/site/s_1/index.html
- Kuznetsov and Sahinidis (2026), deterministic global optimization for small Thomson/Tammes instances: https://doi.org/10.1016/j.dam.2026.05.015

## Work log

### 2026-10-27

Opened this durable direction after reading repository rules, the Few Shots skill/problem, the full merged p007 record chain, and both merged p007 shot descriptions. Confirmed live merged record `444368.3924061973` and no open p007 PR at that check. Literature/current-web review found the Amore-Wales large-N propagation method and the new deterministic small-N global-optimization paper; neither supplies a lower public N=960 configuration than Few Shots.

Ran and preserved a live-record diagnostic, confirming the z-axis C3 action to about `2e-9` RMS after 120-degree rotation. A 40-start exact-C3 smooth-field campaign then found no improvement and was recorded as a negative result. An initial attempt to pull guessed adjacent-N files from the CCD `s_1/dat` tree failed with HTTP 404 before any optimization occurred. Replaced that probe with a direct one-cycle oscillating-size search from the current C3 record, following the insertion/removal ranking logic described by Amore-Wales.
