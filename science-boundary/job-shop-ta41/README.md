# Job-shop scheduling — Taillard ta41 (Few Shots p009)

## Current state (2026-10-28)
- **Goal:** Find feasible machine orders with makespan <=2005, against the verified Few Shots baseline of **2006**. Benchmark is 30 jobs x 20 machines.
- Official [problem and verifier](https://github.com/few-shots/few-shots/tree/main/problems/p009-job-shop-ta41), [baseline certificate](https://github.com/few-shots/few-shots/blob/main/problems/p009-job-shop-ta41/baseline/certificate.json).
- Published lower bound **1915** (Coupvent des Graviers et al. 2025, arXiv:2504.16106). Do not confuse it with a feasible upper bound.
- [Few Shots record chain](https://github.com/few-shots/few-shots/blob/main/problems/p009-job-shop-ta41/FEWSHOT.md) had no merged improvements at initial read.
- No new result is claimed until verified using the upstream verifier and `tools/check.py`.

## Approach / reproducibility
`search.py` downloads immutable-shape upstream instance and baseline (instance SHA256 checked), asserts baseline makespan 2006, and evaluates a candidate by topologically sorting all 600 operations with job and machine arcs; cyclic candidates are rejected. It explores adjacent critical-path machine swaps, tabu tenure and diversified restarts. Local output includes `certificate.json` and `search-result.json`.

```sh
python3 science-boundary/job-shop-ta41/search.py --seconds 300 --seed 41 --output science-boundary/job-shop-ta41/results/run
# Independent verification, from a clone of few-shots:
python3 problems/p009-job-shop-ta41/verify/verify.py /path/to/web-ingest/science-boundary/job-shop-ta41/results/run
```

The one-shot GitHub Action `temp-ta41-search.yml` runs fixed-seed experiments and uses the upstream verifier independently before publishing output. Its successful run is not itself a new record. On any breakthrough, also run Few Shots `tools/check.py` on the correctly packaged shot with the live record.

## Evidence / literature
- Taillard (1993), *Benchmarks for basic scheduling problems*, EJOR.
- Shylo & Pardalos (2008), published upper bound 2006, machine order reproduced in Few Shots baseline.
- Coupvent des Graviers et al. (2025), arXiv:2504.16106, improved LB 1915.
- [Optimizizer benchmark record](https://optimizizer.com/TA.php).
- [JSPLIB ta41 instance](https://github.com/tamy0612/JSPLIB/blob/master/instances/ta41).
- [ZeroThesis challenge brief](https://zerothesis.com/challenges/jobshop-taillard-open) summarizes historical algorithms, but is not an authoritative Few Shots record.

## Search limitations / next research
Critical-path N1 adjacent moves can stall in local optima; a lack of improvement says nothing about global optimality. Next: richer N5/N6 block moves, path-relinking and elite pool, time-window CP-SAT/LNS, and stronger backbone/cut analysis. Avoid repeating identical seeds/tenures without changing the representation.

## Work log
- 2026-10-28: Read all repository and Few Shots instructions; inspected source instance, verifier and baseline. Implemented first reproducible critical-path tabu exploration. Outcome pending Action execution and official independent verification.
