# Positive-control transfer and archival 2005 pursuit — 2026-11-05

## Research objectives and current status

1. **Demonstrate constructive transfer to 30×20 Job-shop instances with known, verifiable strong schedules hidden from the algorithm**. This is a positive-control experiment to avoid overfitting search methods to the hard ta41 plateau.
2. **Recover the actual 600-operation makespan-2005 ta41 certificate** credited to NO2013/CPO2015, then compare it structurally against archived certified 2006 elite schedules.

**No newly verified ta41 <=2005 certificate.** The 2005 historical score is an established reported upper bound, **not** a machine-order witness already in this repository. Do not submit a leaderboard claim based only on a reported score.

## Independent ground-truth archive and blind fixture design

Upstream source: [ScheduleOpt/benchmarks](https://github.com/ScheduleOpt/benchmarks) source SHA `8a6e36ef31263d36975e56fb481e0ba04e188d6f` checked on 2026-11-05. Source `jobshop/solutions/solutions.json` publishes full 20×30 machine-operation sequences, and `jobshop/instances/json/{ta42js,...,ta47js}.json` publishes their 600 operations. All six oracle solutions were reconstructed and independently DAG scored against the machine assignment and job routing.

| Instance | Archive verified complete oracle makespan |
|---|---:|
| ta42js | 1939 |
| ta43js | 1846 |
| ta44js | 1978 |
| ta45js | 1997 |
| ta46js | 2002 |
| ta47js | 1889 |

These are **archived valid scores**, not necessarily the current best known scores: for instance ScheduleOpt's summary currently reports 1937 for ta42js although `solutions.json` only exposes the 1939 machine orders. This experiment deliberately uses **source-verifiable** oracle schedules, not best-known *unverified* numerical bounds.

Program `create_hidden_positive_cases.py` produced 12 simpler start states via one to three legal local swaps; `create_multishift_positive_cases.py` produced another 12 starts via **16** adjacent swaps on 16 distinct machines or **32** swaps across all 20 machines. The latter have proven starting gaps **47–77** above their respective archived oracle and are genuinely multi-resource cases.

Files `positive-control-data/{ta42js,...,ta47js}-{gap12,gap35,multi16,multi32}/start.txt` contain **only the problem and degraded valid machine orders**. Search executables do not read the manifest or upstream oracle; `positive-control-data/manifest.json` stores oracle score and SHA for an *independent after-the-fact judge*. This is a programmatic blinded test, **not secrecy**: oracle scores/hashes are public and the exact target orders exist upstream. Never tune policy on the evaluation targets and then label them out-of-sample.

## Matched number of full-DAG candidate evaluations — exact results

Original C++ algorithm `predictive_cascade_search.cpp` built with only hardcoded ta41 incumbent/stop values replaced by runtime initial values and unreachable stop; all neighbor generation/selection and exact acyclic-DAG scoring unchanged. Each policy got exactly **350,000 full candidate evaluations per trial**; 24 starts × seeds 4107/4113 = 48 trials per policy. The full native 20×30 output for each trial was independently rescored with `search.evaluate()`.

| Policy | Starting state improved | Recovered source oracle score or better | Recovered on 16/32-move subset | Mean wall seconds/trial | Mean score above oracle |
|---|---:|---:|---:|---:|---:|
| critical-block N7-inspired tabu | 48/48 | 45/48 | 21/24 | 1.188 | 0.0625 |
| static three-move coordinated macro | 48/48 | 43/48 | 19/24 | 1.540 | 0.8125 |
| dynamic replacement three-move coordinated macro | 48/48 | **47/48** | **24/24** | 2.170 | 0.3333 |

This is **positive constructive transfer**, not proof of dynamic algorithmic superiority. Paired exact-score dynamic3 vs tabu: 3 wins, 1 loss, 44 ties; vs static3: 5 wins, 1 loss, 42 ties. Tabu's aggregate residual above oracle is actually **smaller** than dynamic3's due to dynamic3's score-1905 loss on ta47js-gap35 seed 4107. Avoid cherry-picking success counts. Files `results/positive-cascade-{tabu,static3,dynamic3}/results.json`.

## Strong original N7 comparison, not a mislabeled surrogate

Original, published source `Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8` (AGPLv3), original Zhang et al. 2007-style tabu N7 search engine, only existing transparent warmstart graph patch plus external driver initial-score guard and termination threshold adjustment. No change to authors' N7 neighbor generator, evaluation, legality, tabu-memory logic or tenure. Complete operation start/end times independently checked against the source operations and full DAG.

**48/48 valid constructive improvements**, **41/48 recovered source oracle or better**, **17/24** recovered in multi-machine subset, mean remaining above oracle **0.9375**; every trial ran **5.006s** (native 5s). Source `results/positive-original-n7/results.json`.

Paired dynamic3 vs genuine N7: **7 wins / 1 loss / 40 ties** on best score. But this does **not prove superior performance**: original N7 received a five-second wall-clock budget while dynamic3 got a 350k candidate budget averaging 2.17s; their evaluation counts and acceptance semantics differ. A **separate strict five-second wall-clock comparison** for in-house policies is launched under `temp-ta41-5sec-matched-hidden-positive.yml`; inspect `results/positive-5sec-{tabu,static3,dynamic3}/results.json` before making time-normalized claims. The first set already has 75–92% near-target saturation, so stronger/harder negative controls or additional instances would be needed to assert transfer statistically.

Independent after-the-fact judge: `grade_hidden_positive.py` and saved `results/positive-blind-compare.json`; 192 paired, independently verified schedule scores across four methods. Workflow `temp-ta41-judge-hidden-positive-comparison.yml` run `42042890988`, success.

## Historical ta41 2005: provenance and archive recovery

1. [ScheduleOpt bks.json](https://github.com/ScheduleOpt/benchmarks/blob/main/jobshop/solutions/bks.json) lists ta41js UB=2005 twice, first `NO2013` and again `CPO2015`; **both `certificate: "no"`**. It now lists LB=1926 credited to OptalCP without a full dual certificate.
2. [Vilím, Laborie, Shaw (2015), *Failure-directed Search for Constraint-based Scheduling — Detailed Experimental Results*](https://vilim.eu/petr/cpaior2015-results.pdf), original appendix table lists `tail41` UB 2005 / LB 1906. The publication PDF is **only aggregate bounds and runtime statistics**, not the machine permutations. Original paper https://vilim.eu/petr/cpaior2015.pdf.
3. [Thomas Weise's literature compilation](https://github.com/thomasWeise/jsspInstancesAndResults) independently records the reported UB 2005 attributed to VLS2015 and links the same appendix, but does not embed the 600-operation schedule.
4. [Van Hoorn's doctoral dissertation](https://research.vu.nl/files/42163578/complete%20dissertation.pdf) independently lists `ta41 UB2005 [88]`, where reference [88] is **Nagata & Ono (2013)**. The exact 2013 item needs bibliographic recovery; do not mistake unrelated 2013 Japanese papers for the 2005 source.
5. A particularly relevant **primary prior algorithm** by **Yuichi Nagata and Isao Ono (2018)**, [*A guided local search with iterative ejections of bottleneck operations for the job shop scheduling problem*](https://doi.org/10.1016/j.cor.2017.09.017), works directly in an incomplete/partial schedule, **alternating removal and reinsertion of bottleneck machine-ordering decisions** rather than freezing a survivor set at the start; it uses dynamic programming for local partial-neighborhood enumeration and tabu reoptimization. This is **strikingly close to the user's proposed dynamic critical-path replacement**, and should become a first-priority algorithm and archival lead, not be reinvented. Its preliminary IEBO genealogy is Nagata & Tojo (2009), [*Guided Ejection Search for the Job Shop Scheduling Problem*](https://doi.org/10.1007/978-3-642-01009-5_15). Nagata & Ono's public publications page is https://yokaisen1994.wixsite.com/nagata/publications ; search publicly released implementation/score logs.
6. The **2015 authors' original primary PDF** contains their named affiliations and public research email addresses, but the issue is archival preservation rather than asking the user for credentials. Attempted to open public GitHub issue to ask ScheduleOpt maintainers for the 2005 primal certificate, but the current GitHub integration returned **403 FORBIDDEN** to create issue in third-party repo. **No issue, email, or request was actually sent**. Further direct outreach must use a permitted channel or explicitly give the user a draft to send.
7. Multiple GitHub-wide code searches `ta41 2005`, `ta41js 2005`, `cpaior2015 ta41 solution` surfaced **only historical BKS tables**, no public 20×30 2005 actual order. A potentially independent [ZeroThesis problem brief](https://zerothesis.com/challenges/jobshop-taillard-open?tab=brief) likewise notes 2005 and 1937 values are not available as complete downloadable schedules, and uses 2006/1939 *verified* instead. This is not a proof such schedules are gone; targeted author/supplementary archive contact is warranted.

## What should be done next

- Finish and inspect true **5-second per-trial** matched budget results. If all methods saturate the 24 positive starts, strengthen test difficulties **without touching the actual hidden oracle before searching**: construct 50–100 swaps across all 20 machines and multiple independent high-quality oracle schedules, preregister evaluation budgets and reserve truly held-out instances. The key metric is whether dynamic machine-bottleneck repair uniquely recovers known improvements at fixed cost. Report paired score comparisons, not vague quality claims.
- Follow the **Nagata/Ono IEBO 2018** partial-schedule method and search its original code/experiment archives. It is a strong, relevant prior art for coupled bottleneck ejections and a possible source of an actual ta41=2005 witness (but this connection is a *hypothesis*).
- Pursue 2015 CPO original raw solution via ScheduleOpt maintainers/Petr Vilím/Philippe Laborie/Paul Shaw, and 2013 Nagata/Ono raw solution via authors; independent Few Shots verifier on any recovered witness **before** marking score 2005.
- Do **not** simply increase ta41 N7/deconstruction runs. Compare constructive recovery on hidden-answer positive controls first.

## Reproduction

- `create_hidden_positive_cases.py`, `create_multishift_positive_cases.py` and `positive-control-data/`.
- `benchmark_hidden_positive.py`, `benchmark_true_n7_positive.py`, `grade_hidden_positive.py`.
- Source C++ search `predictive_cascade_search.cpp`, original N7 author source pinned and init patch `patch_original_n7_warmstart.py`.
- Action runs: fixture 42040812383 + 42041267676; in-house blind score 42041646195; original N7 42041871547; independent result judge 42042890988; equal-time follow-up check workflow `temp-ta41-5sec-matched-hidden-positive.yml`.
