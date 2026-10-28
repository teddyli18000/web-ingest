# Thomson problem for 960 points

## Question

Can we find a 960-point configuration on the unit sphere with Coulomb energy low enough to beat the live Few Shots p007 record by at least `1e-6`?

## Current state

- Few Shots p007 is a minimization problem with absolute epsilon `1e-6`.
- Live merged record checked on 2026-10-27: `444368.3924061973`, shot `Ronnie2025/c3-replica-exchange-scars`.
- Therefore a valid next score must be at most `444368.3924051973`, subject to re-checking upstream immediately before any claim or submission.
- No open p007 pull request was visible when this workspace was opened.
- The current record is a C3-symmetric arrangement with 12 `5-7-5-7-5` scars (24 dislocations). It was found by symmetry-reduced basin hopping followed by six-replica exchange in C3 orbit space, then unconstrained relaxation and Newton polishing.
- The previous record `444368.4040805305` is D2-symmetric with 20 dislocations and was found by symmetry-preserving cut-and-splice genetic search plus basin hopping.

## Why this may be a frontier

The public p007 record already improves the 2026 Amore-Wales Cambridge Cluster Database configuration and is explicitly judged by an exact-integer verifier after rationalization. The remaining task is global optimization in a landscape with many near-degenerate local minima, where the public record chain shows that changing the global arrangement of topological scars can produce record-sized gains.

## What is known / upstream lessons

### Productive ideas

1. Reduce dimension with exact low-order symmetry (especially D2 and C3), search there, then release the symmetry.
2. Cross barriers with population or replica-exchange methods rather than ordinary local kicks.
3. Treat the global scar arrangement as the meaningful slow degree of freedom; purely local scar surgery tends to heal back.
4. Always finish in the full unconstrained space and independently verify after rationalization.

### Public dead ends worth not repeating

- Thousands of unconstrained basin-hopping steps and local defect-targeted perturbations around the old T record did not improve it.
- The T-symmetric subspace was extensively explored and appears exhausted near the old record.
- Local transplantation of short scars heals back because the defect change is coupled to global shear.
- Caspar-Klug, broken-icosahedral, coarse subdivision, Riesz-exponent homotopy, and D5/C5 families stayed well above the current record.

## Current route

Start from the live record certificate, not from the original baseline. First diagnose its numerical stationarity, symmetry orientation, and soft modes. Then use those observations to choose between:

- a second-generation C3 orbit-space search with more global crossover/twist moves and tempering; or
- symmetry-breaking excursions targeted along the lowest tangent Hessian modes, with re-minimization and basin deduplication.

The search code must pull Few Shots `main` at runtime and discover the live p007 record so stale seeds cannot silently become the baseline.

## Evidence and experiments

No search result yet. Initial diagnostic infrastructure is being added under `code/` and run through a temporary GitHub Actions workflow.

## Dead ends

None from this project yet; see the upstream dead ends above.

## Next steps

1. Run the live-record diagnostic and record C3-axis / gradient / local-mode findings.
2. Implement the most justified reduced-space or soft-mode search.
3. Preserve every distinct near-record minimum and compare defect structure where practical.
4. If a candidate crosses the live threshold, rationalize it, run the Few Shots verifier and `tools/check.py`, re-check current upstream record/PRs, and only then prepare/submit a shot.

## Sources

- Few Shots p007 problem and verifier: https://github.com/few-shots/few-shots/tree/main/problems/p007-thomson-problem
- Few Shots p007 generated record chain: https://github.com/few-shots/few-shots/blob/main/problems/p007-thomson-problem/FEWSHOT.md
- D2 record shot: https://github.com/few-shots/few-shots/tree/main/problems/p007-thomson-problem/shots/Abreto/thomson960-d2-ga
- C3 current-record shot: https://github.com/few-shots/few-shots/tree/main/problems/p007-thomson-problem/shots/Ronnie2025/c3-replica-exchange-scars
- P. Amore and D. J. Wales (2026), Cambridge Cluster Database work: https://arxiv.org/abs/2610.08122
- Cambridge Cluster Database, Riesz s=1: https://www-wales.ch.cam.ac.uk/~wales/CCD/Thomson/site/s_1/index.html
- Kuznetsov and Sahinidis (2026), deterministic global optimization for small Thomson/Tammes instances: https://doi.org/10.1016/j.dam.2026.05.015

## Work log

### 2026-10-27

Opened this durable direction after reading repository rules, the Few Shots skill/problem, the full merged p007 record chain, and both merged p007 shot descriptions. Confirmed live merged record `444368.3924061973` and no open p007 PR at that check. Literature/current-web review also noted the 2026 deterministic global-optimization paper (relevant mainly as small-N context, not directly scalable to N=960) and new experimental Thomson realizations; neither supplies a lower N=960 configuration.
