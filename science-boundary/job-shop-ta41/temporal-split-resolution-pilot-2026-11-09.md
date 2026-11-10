# Time-window failure information on partially constrained machines — 2026-11-09

## Mechanism and exact claim

The 2015 Vilím/Laborie/Shaw FDS algorithm works with \`startOf(op) <= t\` versus \`startOf(op) >= t+1\` integer-time domain choices and aggressive first-fail / strong branching. Inspired by these *two-sided* choices, the new \`temporal_split_resource_cores.py\` tests a **sound machine-release clause inference** before any new complete schedule:

Let \`F\` be the target-Cmax job shop with all 600 intervals, all 570 immutable job arcs and all 20 NoOverlap constraints, but without original machine precedence guards. Let \`k_m\` mean *retain every adjacent precedence on original machine m*. If CP-SAT proves

\`F AND (start[u] <= t) AND (AND_{m in A} k_m)\` **INFEASIBLE**

and separately proves

\`F AND (start[u] >= t+1) AND (AND_{m in B} k_m)\` **INFEASIBLE**,

then the full integer time domain is partitioned, so it follows logically that

\`F AND (AND_{m in A UNION B} k_m)\` is **INFEASIBLE**.

Consequently at least one machine in \`A UNION B\` must be *opened* in any improved full schedule. Both conditional branch cores are independently solver-proven; whenever both branches finish INFEASIBLE, an **independent unsplit 600-operation solver** is also run with only the inferred union group keeps. This is standard Boolean case splitting / resolution, **not a novel theorem** and not a reproduction of 2015 FDS's dynamic branching, rating decay and restarts.

Test source A: original verified ta41=2006, true independent author N7 elite ta43=1888 and ta46=2044. For every initial source-only critical operation selected, split at its original critical earliest start time. No hidden target machine orders, no original paper CPO 2005 certificate, and no target plan are supplied.

## Verified pilot

All **3×24 = 72** sampled two-sided time splits produced two INFEASIBLE conditional branch statuses and all **72 union clauses were independently re-proved INFEASIBLE** in unsplit full-resource models.

| Source | Direct baseline keep-all machine sufficient core | Independently reverified temporal union clauses | Clauses NOT dominated by that *single* baseline core |
|---|---|---|---|
| ta41 2006, target 2005 | {1,16} | 24/24 | 4/24 |
| independent source N7 ta43 1888→1887 | {6,8,12,15,17,18} | 24/24 | 0/24 |
| independent source N7 ta46 2044→2043 | {0,10,14,19} | 24/24 | 0/24 |

For ta41 the four non-dominated union clause occurrences correspond to:
- source-critical operation 290: union machines **{1,2,5,6}**;
- operations 467 and 552: union **{3,5,11,15}**;
- operation 477: union **{1,3,5,11}**.

**All four of these still have a previously independently solver-proved smaller machine-core subset already present in BOTH \`machine-fast-2026\` and \`machine-fast-4107\` archives** (2,543 archived inclusion-minimal machine group clauses). Hence the actual \`ta41\` full machine-core-hitting-set model already implies all 24 temporal union clauses: **zero nonredundant novel constraints**. The ta43/ta46 time unions were all dominated by each source's single unbranched core. Although the two-sided construction is logically valid, it gives **no incremental precompletion selector information in this source state**.

## Decision

Do **not** scale the same 20-keep critical-time splits or add those union clauses to the existing ta41 machine master: the entire method would repackage known UNSAT information, not provide a novel feasible candidate. The central failure is testing temporal alternatives **in a partially ordered graph that already has an easy contradiction even before the time split**. The CP solver can ignore the specific time branch and rediscover the existing keep-machine UNSAT core.

If revisiting FDS, change the *state* being branched on: operate after freeing a nontrivial set of machine relations / close to a target-feasible partial schedule, or actually implement persistent FDS choice ratings and strong branching with full NoOverlap. Only demand construction and objective-quality gains under the same resources compared to native N7 and random CP, not growth of redundant conflict cores.

## Provenance

- Primary original FDS paper: https://vilim.eu/petr/cpaior2015.pdf
- Primary 2015 detailed results with historical ta41 UB **2005** (page 2): https://vilim.eu/petr/cpaior2015-results.pdf. It reports a bound, not a replayable schedule.
- Strongest public 2026 CP comparative benchmark: https://www.mdpi.com/2227-7390/14/12/2179; scheduling 2015 paper's modern descendants use FDS/LNS portfolios with different resources, and such architectures are prior art.
- Search and proof implementation: \`temporal_split_resource_cores.py\`, \`.github/workflows/temp-ta41-fds-temporal-split-conflict-resolution.yml\`, GitHub Actions run \`42774509446\`, exact results \`results/time-split-conflict-{ta41,ta43js-n7elite1711,ta46js-n7elite1701}.json\`.
- Python OR-Tools \`9.14.6206\`; all 3 action jobs completed successfully.
