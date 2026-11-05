# Archived ta41=2005 certificate recovery request (prepared, not sent)

Status: **NOT SENT**. GitHub issue creation at third-party `ScheduleOpt/benchmarks` returned 403 `Resource not accessible by integration` on 2026-11-05. Do not report successful contact.

## Proposed recipients / archival sources

- Original CPO2015 authors: Petr Vilím, Philippe Laborie, Paul Shaw, original [2015 paper](https://vilim.eu/petr/cpaior2015.pdf) and [detailed experiments](https://vilim.eu/petr/cpaior2015-results.pdf).
- Original 2013 attribution: Nagata & Ono, cited as [88] for ta41 2005 in Van Hoorn's 2016 dissertation, Appendix B, p166; possible connections to Nagata & Ono (2018) [IEBO](https://doi.org/10.1016/j.cor.2017.09.017). Exact older technical report and full 2005 witness remain to be located.
- Current BKS maintainers: [ScheduleOpt/benchmarks](https://github.com/ScheduleOpt/benchmarks), whose [bks.json](https://github.com/ScheduleOpt/benchmarks/blob/main/jobshop/solutions/bks.json) marks both 2005 upper bounds `certificate:"no"`.

## Exact archival request (copy/send after user authorizes delivery)

Subject: Request for archived 30x20 Taillard ta41 makespan-2005 schedule (NO2013 / CPO2015)

Hello,

I'm trying to recover and independently verify the historical **Taillard ta41 (30 jobs × 20 machines), makespan 2005** schedule. ScheduleOpt's `jobshop/solutions/bks.json` credits 2005 to NO2013 and CPO2015, but both are marked `certificate: no`. The 2015 detailed experimental-results paper confirms the ta41 2005 objective, but neither it nor the available public `solutions.json` appears to include the 600-operation schedule (the latter currently has only a score-2006 witness).

Do you still have the **primal machine-order sequence** (20 lines × 30 jobs each), **start/end time log** for all 600 operations, or a reproducible solver solution file/archive from that experiment? A raw artifact in any format is sufficient: I can reconstruct all machine orders and verify every job precedence, machine capacity and the Cmax score against the original Taillard instance.

This would preserve an important historical benchmark witness and enable research on which coupled machine precedences actually distinguish a 2005 schedule from publicly reproducible 2006 schedules. Even a pointer to supplementary data, archived run logs, or the original researcher who held the output would help.

Thank you.

## Required handling of any reply

1. Preserve source provenance/license. Never publish private correspondence without permission.
2. Verify the instance's exact 600 machine assignments/durations against Few Shots p009, independent of its public source label.
3. Convert timestamps to canonical 20x30 machine job orders, check no conflicting simultaneous operations.
4. Run Few Shots `problems/p009-job-shop-ta41/verify/verify.py` and independent `search.evaluate()`.
5. If valid <=2005, freeze immutable certificate with source permission, compute symmetric Kendall distances vs existing elite 2006s, identify critical-path replacements and coordinated arc reversal sets; then submit a new Few Shots shot when authorized by repository instructions.
