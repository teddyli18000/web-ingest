# Ta41 p009: independent scientist review of precompletion joint resource repair — 2026-11-10 UTC

## Primary question

> Can a scheduler, **before producing a completed better schedule**, identify the interacting resource precedences whose joint release is needed for a smaller makespan, and use that prediction for a real improvement over existing strong solvers?

**Verdict: conditional joint repairs are rigorously demonstrated, but the tested precompletion predictors have NOT shown useful prospective added value. No ta41 <=2005 schedule.** Do not mistake this negative evidence for a proof that better methods cannot exist.

This audit runs on a separate branch `research/p009-precompletion-joint-repair-audit-20261110`, started from main commit `22a238879c95446c08a83f67ebea232a46ca3140`; it does not modify main or submit a shot.

## Precise scientific object

Let `S` denote the subset of whole machines whose incumbent operation order is released. Let `F_H(S)=1` mean **there exists** some *complete* 600-operation job-shop schedule with objective at most `H`, with the other machines' original order fixed, but all resource NoOverlap and job precedences hard. It is **monotone**: `S subset T` and `F_H(S)=1` imply `F_H(T)=1`.

An inclusion-minimal sufficient subset `S` with `F_H(S)=1` and `F_H(S\{m})=0` for each `m in S` demonstrates **conditional joint necessity** within that subspace. It does not imply that all improving schedules globally change all of those machine permutations; multiple different minimal sets can exist. UNSAT cores provide necessary disjunctions of releases, but hitting them is not sufficient to complete a legal improved schedule.

## Newly audited conditional minimality of three real independent-N7 basins

Script: `precompletion_group_minimality_audit.py`. Complete CP-SAT 600 interval / 20 NoOverlap / 570 immutable job-precedence model, one solver worker, starts independent native N7 local elites. Each better machine-order witness was independently full-DAG-scored before and never supplied to the *source-only feature computation*. The witness was used afterward only to identify a sufficient set of changed machine sequences for **post-hoc deletion proofs**.

| Case | Verified objective | Conditioned inclusion-minimal machine-release set | Deletion proof |
|---|---|---|---|
| ta43js independent elite | 1888 to 1887 | {5,6,8} | 3/3 individual deletions INFEASIBLE |
| ta46js independent elite | 2044 to 2042 | {1,3,6,10,12,14,16} | original observed set of 10 reduced by 2,18,19, then 7/7 deletions INFEASIBLE |
| dmu17 independent elite | 3866 to 3861 | {0,2,7,12,13} | 5/5 individual deletions INFEASIBLE |

Original ta43 adjacent-precedence quartet {168,199,257,258} and 15/15 proper-subset exclusions is a distinct, narrower conditioned theorem: 576 other original *adjacency constraints* fixed; the group theorem pins complete orders on the other 17 machines.

Run: https://github.com/teddyli18000/web-ingest/actions/runs/42777799265
(The previous pilots reproduced identical deletion statuses; rerun outcome is the authoritative shrunk-set check.)

## Initial precompletion features and why retrospective enrichment is insufficient

The source-only feature `D(m)` is the **optimistic disjunctive DAG longest-path decrease** when all 29 original adjacent relations of machine `m` are omitted. Pairwise complementarity is

`synergy(m,n) = [C - LB(omit m,n)] - [C - LB(omit m)] - [C - LB(omit n)]`.

This **does not** enforce all machine NoOverlap alternatives, so is a lower-bound/partial-order signal, not a guaranteed successful complete repair. Features are computed before opening the known better witness.

Source-only top-k singleton-relaxation hit counts on the original observed changed sets: ta43 1/3 vs static 1/3, ta46 5/10 vs static 4/10, dmu17 1/5 vs static 1/5. Not compelling.

Retrospective joint synergy in the **shrunk** minimal groups relative to random same-cardinality expected synergy: ta43 0, ta46 4.52×, dmu17 5.59×. Selection post hoc makes the apparent enrichment potentially misleading; ta43 is a clear counterexample to a universal pair-synergy explanation.

Run: https://github.com/teddyli18000/web-ingest/actions/runs/42778090045

## Genuine source-only constructive tests (ta48–50)

Six *independent* true-source-N7 20-second initial schedules across ta48,49,50, two method seeds on each = **12 correlated paired trials per policy**. The search never receives better archived certificates. Both arms use complete CP-SAT target-bounded machine-group release, unchanged soft incumbent-orientation preservation, same initial order, seeds, budget and full independent DAG score checks. Requested ~5-second wall cap per trial (some calls may overrun marginally); CP parallelism and runtime measurements remain caveats.

### Pilot A: collapse pair synergies into per-machine marginal weights

`prospective_pair_synergy_transfer.py`: pair feature **9/12** strict improvements, makespan aggregate gain **15**; original static **8/12**, aggregate gain **14**. Exactly **one** score difference: ta49 case seed4107 1993→1992 for feature but no static improvement. Other 11 paired outcomes identical. It is NOT evidence of robust value.

Run: https://github.com/teddyli18000/web-ingest/actions/runs/42778527706

### Pilot B: true joint pair selection

A crucial conceptual control: A's interaction had been flattened into an additive degree per individual machine, so it never actually rewarded a *pair selected together*. `prospective_joint_pair_master.py` now adds explicit Boolean `y_mn = x_m AND x_n` in the **machine selection master**, with the original static machine scores retained, and rewards the observed pair-synergy `y_mn` only if both machines are opened. The full downstream CP completion is unchanged.

On the same 12 test trials (now a mechanism diagnostic, **no longer entirely untouched evaluation data**):

| Instance | Joint: improved /4; aggregate gain | Original static: improved /4; aggregate gain |
|---|---|---|
| ta48 | 4/4; 10 | 4/4; 10 |
| ta49 | 0/4; 0 | 0/4; 0 |
| ta50 | 4/4; 4 | 4/4; 4 |
| TOTAL | **8/12; 14** | **8/12; 14** |

No score advantage whatsoever from genuinely joint pair selection. The earlier single +1 win from additive marginalization did **not** survive the actual pairwise model. Do not overstate results from these few clustered cases, but do not scale this signal without a new scientific reason.

Run: https://github.com/teddyli18000/web-ingest/actions/runs/42779042544

## Historical corroborating negatives already on main

- FDS-inspired two-sided time splits: 72/72 sound, independently replayed machine-core disjunctions, but **0 nonredundant machine clauses** beyond the earlier 2,543 archived group cores. The time split was applied in an already-obstructed partial ordering: it rediscovered existing machine conflicts, not newly useful joint effects.
- **441/441** optimizer-returned group assumption cores on 20 DMU independent sources were the entire set of currently closed machines, not minimized explanations. Separate feasibility-only reproof extracts smaller cores but costs time and currently loses to novelty-only controls.
- 76 pooled matched tests: core-weighting 53/76 improvements, novelty-only 56/76, no useful incremental source-core feature established.
- Genuine native N7 remains a strong comparator on both Taillard and independent DMU instances. Whole-machine group CP often makes a first 1-point improvement but has substantially lower mean objective gain than strong original N7.
- No valid 2005 ta41 machine-order witness is constructed. Historic Nagata/Ono 2013 and CPO2015 2005 citations still have no independently replayable certificate. Original Few Shots p009 verified board is 2006.

## Scientific decision and clean handoff

**Stop** using number of cores, core novelty, extra static criticality, pair release graph degrees, or ever larger 2006-neutral portfolios as success proxies. In particular, the prospective pair experiment is a well-formed failure of incremental prediction value even though post-hoc synergy was 4–5× in two witnesses.

Next substantive hypothesis is **target-conditioned constraint compatibility**, not more pure-DAG release scoring. To test it, move from ranking individual machines or pairwise DAG relaxations to a *stateful partial scheduling failure-and-repair decision* under hard target `H`. Use CP feasibility and bound propagation to answer which *joint release sets* admit useful completions, represent these as a monotone Boolean set-function or adaptive repair actions; treat UNKNOWN as censored, not infeasible. Learn from multiple confirmed positive and negative **subset evaluations** per independent incumbent rather than treating one improved certificate as the unique label. Cache lower-bound and CP costs to compare actual **value of precompletion information per CPU-second**.

A meaningful next checkpoint is a **prospective algorithmic test**: target-conditioned joint repair beats *both* static and novelty/random matched-size CP releases, and yields useful objective gain competitive with genuine native N7 (or a proper equal-CPU hybrid), on **new independent source-N7 elite basins**. If that cannot be demonstrated, stop this representation instead of pouring time into ta41 <=2005 UNKNOWN runs. A numerical record claim always needs a complete full machine order and independent Few Shots verification.

Not a background automation: this note describes evidence actually verified by completed Actions and explicitly leaves the stronger mechanism unimplemented rather than asserting nonexistent progress.
