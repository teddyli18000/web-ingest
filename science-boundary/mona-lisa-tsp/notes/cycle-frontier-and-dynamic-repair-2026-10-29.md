# 2026-10-29 — 100K Mona Lisa: subtour topology as optimization variable

**Authoritative status: best known valid score remains Nagata 5,757,191. No new certificate submitted.**

This note continues [the blinded 5,757,199 counterfactual](blinded-counterfactual-2026-10-29.md) and [historical LP disagreement analysis](historical-tours-vs-lp-fractions-2026-10-29.md). All global record claims require original Few Shots verifier + exact integer EUC_2D score; an integer 2-factor with several disjoint cycles is NEVER a legal tour.

## Cross-field prior art and representation choice

- Karp's tour-patching via a min-cost bipartite matching is summarized [here](https://www.arl.wustl.edu/~jon.turner/gads/approxAlgorithms/tsp/tsp.html). Matching/2-opt patching is **prior art**. It restricts allowed changes; an optimal patch of a fixed 2-factor need not produce the TSP optimum (Turkensteen et al., *Iterative Patching and the Asymmetric Traveling Salesman Problem*, Discrete Optimization 2006).
- Cook, Helsgaun, Hougardy, Schroeder, [*Local elimination in the traveling salesman problem*](https://doi.org/10.1007/s12532-024-00262-y), Mathematical Programming Computation 2024, demonstrates significant LP+combinatorial edge pruning on instances as large as 115,475 cities. Candidate graph restriction has to be distinguished from true optimality.
- Our small TSPLIB benchmark: 15/15 legal tours independently rescored, 14/15 candidate-graph optimizations labeled OPTIMAL by CP-SAT, and **13/15 independently published global optimal values attained**, using full 8NN + permitted parent edges with dynamic SEC separation. [Official-score independent audit](../data/independent-tsplib-sec-15-verified.json), [run 40873542599](https://github.com/teddyli18000/web-ingest/actions/runs/40873542599). This is evidence supporting the *representation*, not a new algorithmic invention or 100K generalization theorem.

## Direct 100K disconnected-factor tests

The published Nagata tour remains the incumbent. Eight strongly competing historical/Concorde LP regions jointly admit 2,633 old alternate tour chords and 1,322 genuine extra LP fractional chords; exact cost and degree-2 optimization with separated valid SEC cuts.

- [Frontier run 40879009756](https://github.com/teddyli18000/web-ingest/actions/runs/40879009756) preserved independently recomputed degree-two factors, with their complete 100K city membership labels and altered edges. At one random-seed-realization these were:

| Factor length | Cycles | Shortest observed original-factor 2-opt component-MST patch cost | Factor + patch MST |
| ---: | ---: | ---: | ---: |
| 5,756,948 | 202 | 725 | 5,757,673 |
| 5,757,056 | 126 | 407 | 5,757,463 |
| 5,757,169 | 26 | 67 | 5,757,236 |
| 5,757,188 | 11 | 23 | 5,757,211 |
| 5,757,190 | 4 | 8 | 5,757,198 |

[Min-cost pair-patching calculation, run 40880153239](https://github.com/teddyli18000/web-ingest/actions/runs/40880153239), [reproducer](../monalisa_factor_patch_bound.py). This is a **conditional lower bound** ONLY on original-factor-edge two-opt merges over the observed 32-nearest-neighbor cross-component port graph. It does not rule out 3-opt, newly generated edges, rebreaking added edges or a different 2-factor, and should NOT be cited as a lower bound on the complete TSP. In particular the lowest 2-factor is *not* the easiest to repair.

- An independently sampled 12-cycle factor of length **5,757,188** was patched using complete-metric paired original-edge 2-opt exchanges (nearest 32) into a valid 100K tour of **5,757,218**, +30 patch cost; [run 40875009777](https://github.com/teddyli18000/web-ingest/actions/runs/40875009777). No record.
- Strict threshold `score <= 5,757,190` with original factor + cross-cycle edge/adjacent factor-edge reoptimization, at 120–1,200 new cross chords, gave **INFEASIBLE** on these four finite candidate graphs after valid SEC cuts; [run 40878374353](https://github.com/teddyli18000/web-ingest/actions/runs/40878374353).
- Joint extra interior chords, 300 cross+400 interior / 600 cross+1,000 interior, reduced the cheapest integer 2-factor to **5,757,181** and **5,757,142**, respectively, but each resulting finite graph was exactly **INFEASIBLE** for an improving connected tour. The larger 1,200 cross + 2,000 interior graph found **5,757,104** in 47 components but returned **UNKNOWN** under the 220s limit; [run 40878755030](https://github.com/teddyli18000/web-ingest/actions/runs/40878755030). The 47-cycle false improvement must NOT be called a TSP tour.
- Restoring **all Nagata edges absent from the disconnected factor** (116 missing incumbent edges for the 12-cycle parent) makes the complete known connected incumbent representable, while keeping alternate LP/historical/Euclidean candidates jointly variable. The finite graphs with 200/300 and 400/800 cross/interior edges were **INFEASIBLE** under a strict 1-unit-improvement threshold; 800/1600 returned **UNKNOWN**, [run 40880069043](https://github.com/teddyli18000/web-ingest/actions/runs/40880069043). Even a feasibility-only dynamic SEC solve on 400/800 correctly excluded a strict improvement conditional on that sparse graph. The earlier missing-incumbent representation was an artificial search restriction, now explicitly fixed.

## Counterexample-conditioned *dynamic* cycle repair

The initial 12-cycle neighborhood chooses edges based on original component labels. But new local changes create new disconnected cycles elsewhere; static ports can become irrelevant. [Feedback 40880079966](https://github.com/teddyli18000/web-ingest/actions/runs/40880079966) recomputed cross-component neighbor ports from **new factor components**, then re-solved. One trajectory:
- 12 cycles, 5,757,188 → 42 cycles, 5,757,101 (under time cap, UNKNOWN) → 6 cycles, 5,757,186 (restricted infeasible for connected strict improvement) → 5 cycles, 5,757,186 (restricted infeasible). No valid improving tour.
- A Pareto-frontier 4-cycle factor 5,757,190 allowed a new 2-cycle factor 5,757,190. Dynamic adaptation of its new ports in [run 40880661415](https://github.com/teddyli18000/web-ingest/actions/runs/40880661415) briefly created **two cycles length 5,757,189**, then returned to two cycles length 5,757,190; same-pool reoptimization became **INFEASIBLE** for a connected strict improvement, but only conditional on the candidate pool.
- [Best-factor preservation 40881188571](https://github.com/teddyli18000/web-ingest/actions/runs/40881188571) retained the previously overwritten **5,757,189 two-cycle** factor: a giant 99,763-city cycle and a minority 237-city cycle. Ordinary original-factor 2-opt merging at 64, 128, 256 or 512 nearest-neighbor radii always yielded best valid **5,757,196**, delta +7. The previous 5,757,190 two-cycle variant had 99,764+236 cities and yielded best **5,757,197**, also +7. These have gone through the original official Few Shots score/hash verifier; neither improves Nagata.

## What is and is not excluded

- A solver `INFEASIBLE` certificate excludes strict improvement **only inside the finite graph of frozen paths and admitted candidate edges**, and is conditional on CP-SAT exactness.
- A solver `UNKNOWN` excludes NOTHING. A disconnected cheap 2-factor proves nothing about whether a better full tour exists.
- A min-cost component MST based on original-cycle 2-opt connects only a restricted patch family and a sampled near-neighbor port set.
- In the best 2-cycle factor (5,757,189), a single standard 2-opt merge costs +7, while a score 5,757,190 strict record would require a net +1 or less. Hence **higher-order coordinated 3-opt/multi-port rerouting** is the next falsifiable mechanism: remove two edges from one cycle and one from the other, test all 8 connectivity-preserving perfect matchings on their three fixed paths. See [monalisa_two_cycle_3opt.py](../monalisa_two_cycle_3opt.py) and [workflow](https://github.com/teddyli18000/web-ingest/actions/workflows/temp-p010-two-cycle-higher-order-3opt.yml). Must verify actual output before asserting gain.

## Handoff

Work on `main`, no worktree/branch. New code, exact scoring, experiments and notes belong under `science-boundary/mona-lisa-tsp`; disposable Action workflows are in `.github/workflows/temp-p010-*`. No upstream Few Shots submission unless genuine <=5,757,190 tour with official verification and preserved `certificate.json`. Do not train or tune the blinded 5,757,199 split using post-hoc disclosed Nagata-only edges, and do not treat old LP snapshots as historically prospective.
