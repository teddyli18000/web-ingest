# LABS length 100

## Question

Can we find a binary sequence of length 100 with LABS energy below the public best-known value 578? The Few Shots target is therefore `E <= 574` because length-100 energies satisfy `E ≡ 2 (mod 4)`.

Few Shots problem: `few-shots/few-shots`, `problems/p006-labs-100`.

## Why this may be a frontier

The Few Shots problem statement identifies 578 as the best known length-100 energy, matching Knauer's historical table and QOBLIB. It is not known optimal. A verified sequence with energy 574 or less would improve the published best-known value for this instance.

A 2025 massively parallel unrestricted memetic-tabu campaign improved twelve sizes between 92 and 118 but matched, rather than improved, the existing `N=100` value 578. This is additional evidence that this particular length is unusually resistant to modern heuristic search, not evidence that 578 is optimal.

## Current state

**Active; no breakthrough yet. Current best verified energy remains 578.**

Public incumbent:

`++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-`

Major current conclusions:

- The incumbent's exact Hamming neighborhood is exhausted through **radius 6**: `1,271,427,895` non-center sequences checked over radii 1-6, with no energy below 578. Radius 6 alone contains `1,192,052,400` candidates and its shell minimum is 978.
- A new 2025 unrestricted `N=99,E=553` record transfers to length 100 only at best `E=606`; that transferred candidate also has no better sequence within Hamming radius 5.
- Historical `N=101,E=578` deletes to a symmetry copy of the incumbent; `N=102,E=567` deletes to best `E=710`; historical `N=103,E=555` deletes to best `E=714`.
- The first long-tabu and naive memetic CPU probes are far from record quality and should not receive large compute budgets unchanged.
- A direct N=100 probe of the new 2026 `n=4` isolated-subsystem kicked-descent method is also far from record quality in current calibration; the paper itself tests through N=60.
- Exact **radius 7** enumeration (`C(100,7)=16,007,560,800`) has been launched as one-shot GitHub Actions run `40561186271` using only the topic-local `code/sphere_shell.cpp`; the temporary workflow is to be removed after the result is captured and validated.

## What is known

- Objective: for signs `s_i ∈ {−1,+1}`, `C_k = Σ_i s_i s_{i+k}` and `E = Σ_{k=1}^{99} C_k²`.
- For `N=100`, the first possible improvement below 578 is 574.
- Exact optima are proved through N=66, not N=100.
- Historical unrestricted solvers use memetic/tabu local search; recent work also explores GPU-parallel unrestricted memetic search, adaptive partition prioritization followed by unrestricted refinement, and small isolated-subsystem optimization.
- Symmetry under reversal, global sign flip, and alternating sign flip gives up to eight energy-equivalent copies; Hamming-shell exclusions around the incumbent transfer to every symmetry image because these operations are Hamming isometries.

## Hypotheses / routes

1. **Exact local exclusion around the incumbent** — radius 6 is complete; radius 7 is the current exact compute campaign. A surprise `<=574` candidate in the next shells would be immediately decisive.
2. **Structured proposal -> unrestricted refinement** — motivated by the 2026 partition-prioritization paper. Use constrained/skew/partitioned searches only as proposal generators, never as an assumption about the final optimum.
3. **Stronger memetic reproduction** — only worthwhile if a CPU/GPU implementation is calibrated near the 578 regime. The current small CPU prototypes are not.
4. **Fixed-distance basin search** — because direct edits through distance 6 cannot improve the incumbent, search farther Hamming shells with swap-based or population methods rather than repeatedly polishing radius-small perturbations.
5. **Cross-length structural recombination** — simple insertion/deletion is now a dead end; any further cross-length use must preserve more structure than raw length editing.

## Evidence and experiments

### 2026-10-27 — setup and baseline

- Read the Few Shots `take-a-shot` skill, repository `AGENTS.md`, p006 problem statement, verifier, baseline certificate, and generated `FEWSHOT.md`.
- Current Few Shots record chain contains only the preset baseline 578; no open Few Shots PR for p006 was present when checked.
- GitHub account for any eventual shot submission: `teddyli18000`.
- `code/verify.py` independently reproduces baseline energy 578.

### 2026-10-27 — exact incumbent neighborhood

- Exhausted radii 1-5: 79,375,495 candidates, no improvement.
- Added and regression-tested `code/sphere_shell.cpp` for parallel exact shell enumeration.
- Exhausted radius 6: 1,192,052,400 candidates; shell minimum 978; no improvement.
- Total non-center candidates excluded through radius 6: 1,271,427,895.

Full record: [`results/2026-10-27-incumbent-shells.md`](results/2026-10-27-incumbent-shells.md).

### 2026-10-27 — neighboring-length transfers

Tested new 2025 unrestricted N=98/N=99 records and historical N=101/N=102/N=103 sequences. Best simple transfer is `N=99,E=553 -> N=100,E=606`; its radius-5 neighborhood is also exhausted without improvement.

Full record: [`results/2026-10-27-cross-length.md`](results/2026-10-27-cross-length.md).

### 2026-10-27 — heuristic calibration

- Long one-bit tabu: random/perturbed-start batches typically end around 800-900+, far from 578.
- A naive CPU memetic prototype was similarly noncompetitive.
- Independent N=100 implementation of the 2026 isolated `n=4` kicked-descent idea remained around ~970+ from random starts even after millions of proposal evaluations, while incumbent-start runs retained 578 as their best seen value.

Full record: [`results/2026-10-27-search-benchmarks.md`](results/2026-10-27-search-benchmarks.md).

## Dead ends / constraints learned

- Greedy single-bit descent from the incumbent: incumbent is already locally optimal.
- Any direct edit of up to six bits from the incumbent: exhaustively ruled out as an improvement.
- Treating the incumbent as something repairable by a handful of flips is no longer worth repeating.
- Raw insertion/deletion from excellent neighboring-length records: best found is 606 and already locally deep.
- Scaling the current simple long-tabu, naive memetic, or direct isolated-subsystem probes without algorithmic improvement: poor calibration makes this compute-inefficient.

## Next steps

1. Validate and record the running exact radius-7 Action result; remove its temporary workflow afterward.
2. If radius 7 is negative, decide whether radius 8 is computationally justified from the measured Action throughput; do not assume local throughput transfers exactly to hosted runners.
3. Build a fixed-Hamming-distance search that moves by swapping one flipped and one unflipped position, targeting shells beyond the exhausted local ball while maintaining exact incremental correlations.
4. Explore the 2026 two-stage partitioned/skew proposal strategy on N=100, followed by unrestricted polishing, with small calibration runs before any large Action campaign.
5. Re-check the current public record immediately before any record claim.
6. If `E <= 574` is found, freeze the sequence, independently rescore with `code/verify.py`, verify with the Few Shots verifier, create only `certificate.json` and `SHOT.md` in the shot directory, run `tools/check.py`, and publish under `teddyli18000` as authorized.

## Durable artifacts

- [`code/`](code/) — exact scorer, tabu probe, Hamming scanners, neighboring-length transfer script, isolated-subsystem probe.
- [`notes/literature-and-methods.md`](notes/literature-and-methods.md) — literature/method decisions and derivations.
- [`results/2026-10-27-smoke.md`](results/2026-10-27-smoke.md) — initial incremental-score validation.
- [`results/2026-10-27-search-benchmarks.md`](results/2026-10-27-search-benchmarks.md) — heuristic calibration and negative results.
- [`results/2026-10-27-cross-length.md`](results/2026-10-27-cross-length.md) — neighboring-length transfer results.
- [`results/2026-10-27-incumbent-shells.md`](results/2026-10-27-incumbent-shells.md) — exact local-shell exclusions.

## Sources

- Few Shots p006 problem statement and verifier: <https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100>
- Few Shots procedure: <https://github.com/few-shots/few-shots/blob/main/skills/take-a-shot/SKILL.md>
- QOBLIB LABS benchmark/solutions: <https://github.com/ZIB-AOPT/QOBLIB/tree/main/02-labs>
- Knauer record table mirror / historical solver archive: <https://github.com/borkob/git_labs>
- Packebusch & Mertens, exact optimization through length 66: <https://arxiv.org/abs/1512.02475>
- Bošković, Brglez & Brest, LABS heuristic search: <https://arxiv.org/abs/1406.5301>
- Zhang et al., massively parallel unrestricted memetic tabu (2025): <https://arxiv.org/abs/2504.00987>
- Pšeničnik et al., search-space region prioritization / two-stage refinement (2026): <https://arxiv.org/abs/2607.09688>
- Lau & Gangat, small isolated-subsystem optimization (2026): <https://arxiv.org/abs/2610.14361>

## Work log

- **2026-10-27:** Opened durable topic. Recorded exact target, baseline, public solver leads, and incumbent radius-5 exclusion.
- **2026-10-27:** Added independent scorer and exact incremental tabu kernel; smoke-tested incremental scoring. Calibration showed the first long-tabu/memetic designs are far from record quality.
- **2026-10-27:** Surveyed 2025-2026 primary literature. Reproduced neighboring-length transfers from the new N=98/N=99 records and historical N=101-103 records; no competitive N=100 candidate emerged.
- **2026-10-27:** Extended exact incumbent exclusion through Hamming radius 6 (1.192 billion candidates in that shell). Launched one-shot Action run `40561186271` for exact radius 7.
