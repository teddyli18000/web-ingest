# Riemann–Weil research sprint

Temporary research workspace for attacking the Riemann Hypothesis through Weil positivity, compact-window spectral theory, finite-dimensional compressions, and computational conjecture generation.

## Scope

- Work directly on `main`, as explicitly requested by the user.
- Keep all temporary notes, scripts, numerical experiments, bot outputs, and intermediate conclusions inside this workspace.
- Treat the repository and GitHub Actions output as fully public. Do not place credentials, private data, private repository contents, signed URLs, or sensitive diagnostics here.
- This is research scratch space, not a persistent ingestion task. Nothing here should modify existing collectors or recurring schedules.

## Research question

Primary target: classify a hypothetical first compact-window Weil zero mode well enough either to rule it out or turn it into a rigorous negative certificate.

The project began with a naive prime-threshold spectral-flow idea. That was falsified at operator-norm level and repaired only on bounded logarithmic-energy sets. A literature check then showed that Bombieri (2000) had already developed fixed-window minimization, variational equations, finite truncations, and numerical critical-window/boundary-concentration phenomena. The current novelty target is therefore narrower: use modern logarithmic-Laplacian compactness, boundary Hardy inequalities, and certified computation to understand Bombieri's boundary-escape transition rigorously.

## Current findings

1. **Prime-threshold continuity for fixed tests.** A newly entering prime-power term vanishes at its support threshold because the autocorrelation vanishes at the edge.
2. **Naive norm-continuity fails.** Near-full-width translations converge strongly but retain operator norm one; this kills a simple Kato/norm-continuous proof.
3. **Correct high-frequency form domain.** On every fixed window, the Weil form has logarithmic Fourier growth plus bounded fixed-window lower-order contributions, giving the logarithmic energy space as the natural compactness class.
4. **Low-energy endpoint anti-concentration.** A logarithmic boundary Hardy inequality gives boundary-strip mass `O(1/log(1/delta))` uniformly on bounded logarithmic/Weil-energy sublevels.
5. **The Hardy rate is sharp in order.** A normalized bump localized on spatial scale `delta` has logarithmic Fourier energy `log(1/delta)+O(1)`. Generic compactness alone therefore cannot prove no crossing.
6. **Bombieri prior art.** Fixed-window attainment/variational equations and a numerical critical support transition with boundary-concentrating finite-truncation eigenfunctions already appear in Bombieri's 2000 memoir; these are not new claims of this sprint.
7. **Boundary-escape diagnostic.** On a fixed interval, normalized functions converging weakly to zero cannot have bounded logarithmic energy. Thus a boundary-concentrating finite-truncation sequence necessarily escapes the true logarithmic form domain.
8. **First-crossing formulation remains useful, not novel.** If the exact lowest window eigenvalue is continuous and RH fails, one can focus on an actual critical zero mode. The useful open question is its boundary/arithmetic structure, not its mere existence as a variational minimizer.

## Notes

- `notes/001-threshold-dynamics.md` — initial prime-power threshold calculation and heuristic spectral-flow idea.
- `notes/002-operator-norm-obstruction.md` — explicit reason the naive norm-continuity route fails.
- `notes/003-low-energy-compactness-and-first-crossing.md` — logarithmic-energy decomposition, boundary Hardy control, compactness, continuity route, and critical zero-mode reduction.
- `notes/004-bombieri-boundary-escape-revisited.md` — prior-art correction, sharp edge-bump scaling, escape-to-high-energy dichotomy, and a numerical diagnostic for finite truncations.

## Immediate next targets

1. Reconcile the exact Bombieri variational equation with the additive/FFT normalization used by modern compact-window computations.
2. Instrument a finite-window numerical model with an independent logarithmic-energy and endpoint-mass diagnostic so truncation escape cannot masquerade as a true negative mode.
3. Determine whether the full critical Weil eigen-equation bootstraps an `L2` eigenfunction to bounded/log-Hölder boundary behavior despite the finite shift terms.
4. Search for structure specific to a zero mode—parity, reflection, pole-rank constraints, or arithmetic recurrence—that improves the generic sharp `1/log` boundary bound.
5. Keep adversarial testing active: every proposed inequality should be checked against one-edge, two-edge, modulated, and multiscale localized states before being trusted.

## External literature workspace

A separate Undermind workspace is being used only for scholarly search/read parallelism:

`https://app.undermind.ai/projects/b9858cac-7a0e-4f3d-93aa-8006ce5e4092`

The GitHub directory remains the authoritative scratch record for this sprint.

## Promotion

Only a validated reusable method or durable repository-level conclusion should migrate out of this workspace. Otherwise this directory is disposable and may be removed by the normal temp-work cleanup lifecycle.
