# Riemann–Weil research sprint

Temporary research workspace for attacking the Riemann Hypothesis through Weil positivity, compact-window spectral theory, finite-dimensional compressions, and computational conjecture generation.

## Scope

- Work directly on `main`, as explicitly requested by the user.
- Keep all temporary notes, scripts, numerical experiments, bot outputs, and intermediate conclusions inside this workspace.
- Treat the repository and GitHub Actions output as fully public. Do not place credentials, private data, private repository contents, signed URLs, or sensitive diagnostics here.
- This is research scratch space, not a persistent ingestion task. Nothing here should modify existing collectors or recurring schedules.

## Research question

Primary target: determine whether the compact-window Weil ground state admits enough structure to prevent its lowest eigenvalue from crossing zero as support grows, or conversely to construct a rigorous negative test function.

Current emphasis is no longer a naive operator-norm spectral-flow argument. The near-edge shift operators have norm one even as a prime-power threshold is approached. Instead we work on bounded logarithmic-energy sublevels, where compactness and logarithmic boundary Hardy inequalities restore uniform control.

## Current findings

1. **Prime-threshold continuity for fixed tests.** A newly entering prime-power term vanishes at its support threshold because the autocorrelation vanishes at the edge.
2. **Naive norm-continuity fails.** Near-full-width translations converge strongly but retain operator norm one; this kills a simple Kato/norm-continuous proof.
3. **Correct form domain identified.** On every fixed window, the Weil form is a Dirichlet logarithmic Fourier-energy form plus bounded prime-shift / multiplier terms and a finite-rank pole term.
4. **Compact-resolvent route.** The logarithmic energy space embeds compactly into `L2` on a bounded interval, so the Weil window infimum is attained and the spectrum is discrete.
5. **Low-energy endpoint anti-concentration.** A logarithmic boundary Hardy inequality gives boundary-strip mass `O(1/log(1/delta))` uniformly on bounded Weil-energy sublevels. This repairs the operator-norm obstruction at the quadratic-form level.
6. **First-crossing reduction.** Combining nested windows, compactness, and the expected standard continuity argument for `lambda*(L)`, any hypothetical RH failure reduces to an actual critical zero eigenmode at a first support radius `Lc > 0.8`.

## Notes

- `notes/001-threshold-dynamics.md` — initial prime-power threshold calculation and heuristic spectral-flow idea.
- `notes/002-operator-norm-obstruction.md` — explicit reason the naive norm-continuity route fails.
- `notes/003-low-energy-compactness-and-first-crossing.md` — logarithmic-energy decomposition, boundary Hardy control, compactness, continuity route, and critical zero-mode reduction.

## Immediate next targets

1. Write the critical zero-mode Euler–Lagrange equation precisely in even and odd sectors.
2. Determine whether the specific archimedean multiplier plus prime shifts preserves enough boundary regularity to upgrade the `1/log` boundary-mass estimate to pointwise/log-Hölder decay for the zero mode.
3. Search for a relative form inequality near zero energy, not merely an absolute bounded-perturbation estimate.
4. Test whether parity, reflection positivity, or the rank-one pole term excludes a critical zero eigenmode before attacking larger numerical matrices.
5. Keep adversarial counterexample searches active: every proposed inequality should first be tested against edge-localized and multiscale trial functions.

## External literature workspace

A separate Undermind workspace is being used only for scholarly search/read parallelism:

`https://app.undermind.ai/projects/b9858cac-7a0e-4f3d-93aa-8006ce5e4092`

The GitHub directory remains the authoritative scratch record for this sprint.

## Promotion

Only a validated reusable method or durable repository-level conclusion should migrate out of this workspace. Otherwise this directory is disposable and may be removed by the normal temp-work cleanup lifecycle.
