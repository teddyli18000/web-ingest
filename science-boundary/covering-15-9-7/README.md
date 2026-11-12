# Covering design C(15,9,7)

## Current state — 2026-11-12
- Live Few Shots `data/board.json` and `FEWSHOT.md`: baseline/current **270**; no merged p015 shots.
- Need a **verified covering of at most 269** blocks on points 0..14, each block size 9, covering each of the 6435 7-subsets.
- Baseline: Fadlaoui and Galinier (2010), rank-decoded public 270-block construction. Independent certificate verifier is `problems/p015-covering-15-9-7/verify/verify.py`.
- Published lower bound in problem statement: 225. A target of 269 is not guaranteed feasible.
- No new candidate has yet been verified.

## Main hypothesis
Rather than changing individual blocks, freeze most of a valid design, delete 16–48 blocks, and solve the exact residual set-cover instance. This allows coordinated replacement of several old blocks with different 9-subsets. Iterating non-improving same-size replacements can reach new designs with different overlap structures. Compare with larger destroy sizes and reformulate if trapped.

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
- 2026-11-12: synchronized main, read exact problem specification and both repository rule sets; established baseline 270, target <=269; prepared residual-repair experiment.
