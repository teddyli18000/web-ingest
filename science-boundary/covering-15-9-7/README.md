# Covering design C(15,9,7)

## Current state — 2026-11-12
- Live Few Shots `data/board.json` and `FEWSHOT.md`: baseline/current **270**; no merged p015 shots.
- Need a **verified covering of at most 269** blocks on points 0..14, each block size 9, covering each of the 6435 7-subsets.
- Baseline: Fadlaoui and Galinier (2010), rank-decoded public 270-block construction. Independent certificate verifier is `problems/p015-covering-15-9-7/verify/verify.py`.
- Published lower bound in problem statement: 225. A target of 269 is not guaranteed feasible.
- No new candidate has yet been verified.

## Current construction campaigns

**Search is oriented toward finding a verified <270 cover.** The 270-block baseline has 4,640 uniquely covered 7-sets. Its weakest four blocks each protect exactly 2 unique 7-sets. Every baseline block's uniquely covered 7-sets involve all nine of its points, so no block can be replaced by a *different single block* while all other blocks are frozen.

1. **CP-SAT collective repair**, `search.py`: freeze most blocks, release 12–60 at a time and optimize an exact residual covering. Seeds 15 and 1515: [Actions run](https://github.com/teddyli18000/web-ingest/actions/runs/43240551383).
2. **Decremental weighted local search**, `run_wls.py`: retrieve the public MIT-licensed 2026 `wls2` solver and try focused point swaps in four seeded, 850-second searches. [Actions run](https://github.com/teddyli18000/web-ingest/actions/runs/43241334357). All 4 runs completed and their independently verified score was **270**. This route has not produced the desired construction.
3. **Global multi-parent recombination**, `recombine.py`: merge the original covering with 1–2 relabeled high-quality coverings into a 500–800-variable set-cover instance, require genuine mixing, and optimize across the joint candidate family rather than locally swapping blocks. Four CP-SAT shards underway: [Actions run](https://github.com/teddyli18000/web-ingest/actions/runs/43244817454). The intent is either a 269 covering or a structurally distant new 270 parent for further search.
4. **Full-block and coordinated exchanges:** a separate local C++ whole-block weighted search has repeatedly approached 2 uncovered 7-sets at size 269 but not closed both. Two-for-two complete-cover exchanges do produce alternative full covers but remain only about 6 blocks distant from the published parent after hundreds of accepted swaps. Exhaustive three-for-two exchanges of the initial baseline tried all 3,244,140 triples (verified independently by removal counts) and found no 269 witness. This restricts only that particular construction's small exchange neighborhood, not the global problem. Four-for-three constructive enumeration is testing a wider neighborhood, with initial weak-block subsets unsuccessful.

The source for `wls2` and its experimental methodology is Wynand van Staden, *Local Search and a Construction Scan for Covering-Design and Lottery-Covering Tables* (posted 2026-10-29), [preprint](https://www.preprints.org/manuscript/202610.2905), [source](https://github.com/WynandVStaden/covering-design-records/).

## Reproducible experiment
`search.py` reads an existing baseline certificate, verifies the input independently, and executes randomized large-neighborhood CP-SAT residual repairs. It writes `best.json`, `history.json`, and `certificate.json` only after a full independent exhaustive coverage check. All 5005 possible 9-subsets are candidate repairs; each 7-subset has 28 covering candidate blocks. Random seed controls the experiment.

One-shot GitHub Actions workflow `.github/workflows/temp-p015-repair.yml` is for running the experiment and preserving results as an artifact; it is not a recurring schedule.

## Constraints and independent validation
Score counts entries including duplicates. Check each block has nine unique integers in 0..14; test coverage of all 6435 7-subsets from scratch. Before Few Shots submission, run its original verifier and `tools/check.py` on a shot directory. No score is claimed merely because an optimizer reports feasible.

## Sources
- [Few Shots problem](https://github.com/few-shots/few-shots/tree/main/problems/p015-covering-15-9-7)
- [Current board](https://github.com/few-shots/few-shots/blob/main/data/board.json)
- [Fadlaoui–Galinier report](https://publications.polymtl.ca/2650/1/EPM-RT-2010-01_Fadlaoui.pdf)
- [Krug (2026) lower bound](https://arxiv.org/abs/2607.23766)
- [La Jolla Coverings Repository](https://zenodo.org/records/19735294)

## Work log
- 2026-11-12: validated four WLS2 attempts at score 270, not an improvement; switched primary effort to multi-parent global recombination and coordinated multi-block construction. Exact 3→2 baseline search found no witness across all 3,244,140 triples; this is not evidence that 269 is unattainable.
- 2026-11-12: synchronized main, read exact problem specification and both repository rule sets; established baseline 270, target <=269; prepared residual-repair experiment.
