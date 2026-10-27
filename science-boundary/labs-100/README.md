# LABS length 100

## Question

Can we find a binary sequence of length 100 with LABS energy below the public best-known value 578? The Few Shots target is therefore `E <= 574` because length-100 energies satisfy `E ≡ 2 (mod 4)`.

Few Shots problem: `few-shots/few-shots`, `problems/p006-labs-100`.

## Why this may be a frontier

The Few Shots problem statement identifies 578 as the best known length-100 energy, matching Knauer's historical table and QOBLIB. It is not known optimal. A verified sequence with energy 574 or less would improve the published best-known value for this instance.

## Current state

Active. Baseline sequence and verifier rule have been independently reimplemented from the public Few Shots description. No breakthrough yet.

Known public baseline sequence:

`++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-`

Baseline energy: `578`.

Important negative result from the current search campaign: exhaustive enumeration of all Hamming-distance-1 through Hamming-distance-5 edits around the 578 incumbent found no sequence below 578 (79,375,495 candidates total). This rules out a small local edit of the incumbent through radius 5.

## What is known

- Objective: for signs `s_i ∈ {−1,+1}`, `C_k = Σ_i s_i s_{i+k}` and `E = Σ_{k=1}^{99} C_k²`.
- For `N=100`, the first possible improvement below 578 is 574.
- The historical general LABS solvers by Bošković, Brglez, Brest and collaborators use memetic/tabu local search, including constant-time-ish incremental single-bit evaluation structures.
- Public record tables around this length contain strong odd-length skew-symmetric constructions; cross-length transfer is worth testing but is not itself evidence of an `N=100` improvement.

## Hypotheses / routes

1. **Unrestricted memetic/tabu search** — likely strongest baseline route for `N≈100`; use incremental one-bit delta evaluation and many independent restarts.
2. **Incumbent basin crossing** — perturb the 578 sequence by larger Hamming jumps, then apply tabu descent; radius <=5 is exhausted and cannot help directly.
3. **Cross-length transfer** — take strong public sequences at neighboring lengths, delete/insert positions, then run unrestricted tabu search.
4. **Population recombination** — retain diverse local optima and recombine them before tabu polishing, following the memetic-search literature.

## Evidence and experiments

### 2026-10-27 — setup and baseline

- Read the Few Shots `take-a-shot` skill, repository `AGENTS.md`, p006 problem statement, verifier, baseline certificate, and generated `FEWSHOT.md`.
- Current Few Shots record chain contains only the preset baseline 578.
- GitHub account for any eventual shot submission: `teddyli18000`.
- The baseline target was checked from the exact objective definition; all scoring should be independently recomputed before any submission.

### 2026-10-27 — local-neighborhood exclusion

Exhaustively evaluated every sequence at Hamming distance 1, 2, 3, 4, or 5 from the 578 incumbent. Total candidates: 79,375,495. Best energy found: 578. Therefore no qualifying improvement exists within radius 5 of this representative (equivalently within radius 5 of any symmetry image).

This is a search-space exclusion, not a proof about larger radii.

## Dead ends

- Greedy single-bit descent from the incumbent: incumbent is already locally optimal.
- Exhaustive incumbent Hamming balls through radius 5: no improvement.
- Treating the incumbent as something that can be fixed by a handful of flips is therefore not worth repeating.

## Next steps

1. Implement a fast unrestricted tabu-search kernel with exact incremental energy updates and validate every reported candidate against a separate straightforward scorer.
2. Run many random and heavily perturbed-incumbent starts, recording best-energy distribution and any <=574 candidate.
3. Add population recombination if pure tabu stagnates.
4. Test deletion/polishing from strong public neighboring-length record sequences when exact source certificates are available.
5. If `E <= 574` is found, freeze the sequence, independently verify it, re-check the current public record, then create only `certificate.json` and `SHOT.md` under the Few Shots shot directory and run `tools/check.py` before publishing.

## Sources

- Few Shots p006 problem statement and verifier: <https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100>
- Few Shots procedure: <https://github.com/few-shots/few-shots/blob/main/skills/take-a-shot/SKILL.md>
- QOBLIB LABS benchmark/solutions: <https://github.com/ZIB-AOPT/QOBLIB/tree/main/02-labs>
- Bošković LABS solver archive: <https://github.com/borkob/git_labs>
- Packebusch & Mertens, exhaustive LABS optimization through length 66: <https://arxiv.org/abs/1512.02475>
- Bošković, Brglez & Brest, LABS heuristic search: <https://arxiv.org/abs/1406.5301>

## Work log

- **2026-10-27:** Opened durable topic. Recorded exact target, baseline, public solver leads, and the radius-5 negative result. Next work is fast unrestricted tabu/memetic search with independent exact verification.
