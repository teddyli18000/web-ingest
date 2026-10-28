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
- Live-certificate diagnostics show the C3 axis is the coordinate z axis: a +120 degree z rotation matches the rationalized point set with nearest-neighbor RMS `1.98e-9` and maximum `4.63e-9`. This makes exact 320-orbit reconstruction straightforward.
- Two compute campaigns are active: four independent C3 smooth global-deformation searches (Actions run `40619792492`) and four neighboring-N transfer searches from CCD N=958,959,961,962 (run `40619870207`).

## Why this may be a frontier

The public p007 record already improves the 2026 Amore-Wales Cambridge Cluster Database configuration and is explicitly judged by an exact-integer verifier after rationalization. The remaining task is global optimization in a landscape with many near-degenerate local minima, where the public record chain shows that changing the global arrangement of topological scars can produce record-sized gains.

## What is known / upstream lessons

### Productive ideas

1. Reduce dimension with exact low-order symmetry (especially D2 and C3), search there, then release the symmetry.
2. Cross barriers with population or replica-exchange methods rather than ordinary local kicks.
3. Treat the global scar arrangement as the meaningful slow degree of freedom; purely local scar surgery tends to heal back.
4. Propagate good structures between neighboring N values; Amore-Wales (2026) report this as an effective large-N search strategy.
5. Always finish in the full unconstrained space and independently verify after rationalization.

### Public dead ends worth not repeating

- Thousands of unconstrained basin-hopping steps and local defect-targeted perturbations around the old T record did not improve it.
- The T-symmetric subspace was extensively explored and appears exhausted near the old record.
- Local transplantation of short scars heals back because the defect change is coupled to global shear.
- Caspar-Klug, broken-icosahedral, coarse subdivision, Riesz-exponent homotopy, and D5/C5 families stayed well above the current record.

## Current route

The live record certificate is the seed and comparator, never the original baseline. Two deliberately different search families are now running:

- **Exact-C3 global smooth deformations.** Regroup the rationalized record into 320 exact z-axis C3 orbits, polish it, then apply random low-order `m=0,3,6` tangent fields with amplitudes spanning roughly 0.008-0.20 rad and re-minimize each start in C3 orbit space. This targets coherent global shear/scar rearrangements rather than the local kicks already reported as dead ends.
- **Neighboring-N transfer.** Pull current CCD structures at N=958,959,961,962, greedily add/remove points to N=960, then perform full unconstrained angular L-BFGS relaxation. This directly tests the newest Amore-Wales neighboring-size propagation idea against the newer Few Shots record.

If neither route reaches a competitive basin, the next justified route is symmetry-breaking excursions targeted along the lowest tangent Hessian modes of the polished current record, with basin deduplication.

The search code pulls Few Shots `main` at runtime and discovers the lowest merged p007 shot so stale seeds cannot silently become the baseline.

## Evidence and experiments

### Live-record diagnostic

Durable result: `results/diagnostic-live-record.txt`.

- Merged shot discovered dynamically: `Ronnie2025/c3-replica-exchange-scars`.
- Claimed verifier score: `444368.3924061973`.
- Direct double-precision energy of the rational certificate: `444368.392406201164704` (ordinary summation is a few `1e-9` above the rigorous verifier score, as expected from floating summation differences).
- Tangent-gradient RMS on the rationalized coordinates: `5.14e-6`; maximum `1.18e-5`. This is consistent with tiny stereographic rationalization perturbations, not evidence that the published floating minimum was unpolished.
- Second-moment eigenvalues: `319.997418654053`, `319.997418737504`, `320.005162608441`; the unique eigenvector is essentially z.
- +120 degree rotation about z gives nearest-neighbor RMS `1.98e-9`, maximum `4.63e-9`; x/y axes fail by about `4.6e-2`. Thus the exact C3 group action is unambiguous.

### Active compute

- GitHub Actions run `40619792492`: seeds 101/202/303/404, 10 C3 smooth-field basin starts each.
- GitHub Actions run `40619870207`: independent transfer/relaxation from CCD N=958,959,961,962.

## Dead ends

None from this project yet; the first two campaigns are still running. See the upstream dead ends above.

## Next steps

1. Collect both active campaigns and preserve the best energies / distinct basins.
2. If a competitive floating candidate appears, release symmetry, polish in all 1920 tangent degrees of freedom, rationalize with denominator limits matching p007, and run the Few Shots verifier independently.
3. If current routes fail, compute low tangent Hessian modes and launch mode-following symmetry-breaking basin escapes rather than generic random kicks.
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

Ran and preserved a live-record diagnostic. It dynamically selected the current merged shot, confirmed the z-axis C3 action to nanometric-coordinate precision (`~2e-9` RMS in unit-sphere chord distance after 120-degree rotation), and measured only the expected small rationalization residual gradient. Added reproducible C3 smooth-field and neighboring-N transfer search code, then launched the two independent GitHub Actions campaigns listed above.
