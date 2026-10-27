# 2026-10-27 heuristic calibration

## Purpose

Before spending large GitHub Actions budgets, test whether small CPU implementations of unrestricted tabu/memetic ideas are in the right quality regime for `N=100`.

These runs are calibration, not record searches. The current public best remains `578`.

## Long tabu walks

`code/search.cpp` maintains all correlations exactly and evaluates one-bit moves incrementally. Debug smoke tests separately recomputed the full energy periodically without finding an incremental mismatch.

A 32-run random-start calibration using 50,000 tabu steps per run produced:

```text
min=834  p10=874  median=886  p90=918  max=934
```

Best sequence from that batch had energy `834`.

A 32-run calibration seeded by 10-40 bit perturbations of the `578` incumbent, again at 50,000 steps per run, produced:

```text
min=806  p10=846  median=890  p90=914  max=934
```

Best sequence from that batch had energy `806`.

These distributions are far from the incumbent. Running this exact long-walk design at much larger scale would therefore be a poor use of compute.

## Naive memetic prototype

A temporary local prototype implemented the broad historical pattern of a population, uniform crossover, mutation, and short tabu polishing. A representative partial calibration with population 40 and thousands of generations reached energies around `810-840` before the local execution limit. This prototype was not an exact reproduction of the 2009/2025 solver and is not retained as durable code because its calibration did not justify further use.

The negative conclusion is narrow: this first CPU memetic implementation was not competitive. It does not imply that the published massively parallel memetic tabu algorithm is ineffective; Zhang et al. (2025) demonstrated new records at multiple nearby lengths using a heavily optimized Nvidia A100 implementation.

## 2026 isolated-subsystem method probe

Lau and Gangat (arXiv:2610.14361v2, 2026-10-14) propose exact optimization of isolated `n=4` subsystems plus a global-energy acceptance rule. Their kicked-descent method uses a forced base update after a tuned number of failed improvements (`X=80`), and their strongest scaling variant additionally uses tracked subsystems and multiple proposals.

A direct local implementation of the simpler `n=4`, `X=80` kicked-descent mechanism was tested at `N=100`:

- 16 random starts × 200,000 global candidate evaluations: best `1026`, median `1098`.
- 16 random starts × 5,000,000 evaluations: best `970`, median `1014`.
- 16 runs starting exactly from the public `578` incumbent × 1,000,000 evaluations: best remained `578` in every run.

The isolated-subsystem Hamiltonian was independently checked on small systems by averaging the full LABS energy over all assignments of the environment; its assignment-dependent part matched the implemented two-/four-body subsystem objective up to an additive constant.

This direct extrapolation is therefore not competitive at `N=100` in its present form. The paper itself reports scaling experiments only through `N=60`, so this negative result does not contradict its claims.

## Decision

Do not launch large Actions campaigns for either the current long-tabu kernel or the direct `IsoSubsys_KD` reproduction. Actions should instead be used for exact or otherwise well-calibrated computations. The next exact campaign is the incumbent Hamming shell at radius 6, whose 1,192,052,400 candidates can be checked in parallel with `code/sphere_shell.cpp`.

## Sources

- Historical memetic/tabu solver archive: <https://github.com/borkob/git_labs>
- Zhang et al. (2025), arXiv:2504.00987: <https://arxiv.org/abs/2504.00987>
- Lau & Gangat (2026), arXiv:2610.14361: <https://arxiv.org/abs/2610.14361>
