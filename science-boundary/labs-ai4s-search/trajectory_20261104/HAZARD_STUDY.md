# Prospective native-Tabu improvement hazard — 2026-11-04

## Motivation

Previous native [compensation prediction](results/native_plateau_v1/pretransition_compensation_transfer.json) achieved AUC≈0.874 on *conditional successful transitions*. This is not a deployed decision: the future improvement and long gap were known to the dataset builder. Here we explicitly target **whether a native Tabu best improvement will occur in the next H accepted moves**, without choosing only future-positive states.

## Source and nonleaking event definition

All data from the pinned original historical public lMAts (native GA/Tabu) on 12 seed-distinct runs across N48/64/80/92/99/100. Its exact events were [independently scored](results/native_mini_v1/exact_verification.json). For each `TS_STEP` trace snapshot with already-observed time since last native `TS_BEST` ≥S, require that the episode runs at least H more accepted moves; otherwise censor it. The label is 1 iff a later `TS_BEST` occurs in that next H moves. Feature values are from the present spin sequence, present native tabu recency vector, present current/best energies, current stall age and correlations. Future events are used **only** to construct label and censor filter, never as features. One thread per source run, and test lengths N92/99/100 never occur in training N48/64/80.

Feature ablations: constant event rate; current and best energies + history; plus cheap parity-share/Dodd; plus 12 bins of normalized per-lag correlation energy; plus simple bit autocorrelation/imbalance; full combination. Common fixed regularized logistic regression, standardization fit only on training. No neural model trained and no operator changed.

## Exact 12-run experiment

[Validated outputs](results/) and [source](prospective_hazard.py). Planned four observation regimes, unadjusted exploratory metrics:

| Stall S | Future H | eligible states | training/test positive | Energy+history AUC | +spectrum AUC | Energy+history log-loss | +spectrum log-loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 16 | 3,909 | 679/434 | 0.84746 | 0.84966 | **0.41120** | 0.41193 |
| 16 | 32 | 1,450 | 283/257 | **0.88246** | 0.87906 | **0.41423** | 0.41957 |
| 32 | 64 | 121 | 0/43 | N/A | N/A | N/A | N/A |
| 64 | 64 | 6 | 0/1 | N/A | N/A | N/A | N/A |

For S8,H16, adding spectral bins yields per-independent-heldout-run mean log-loss gain **−0.000735**, 95% run bootstrap interval **[−0.00686,+0.00519]**. Parity-scalar arm −0.00208 [−0.00428,+0.00031]. Full spectrum+bit arm −0.00368 [−0.00977,+0.00166]. For S16,H32, spectrum −0.00539 [−0.01358,+0.00222]; full features −0.01184 [−0.02202,−0.00397]. Positive means the richer representation helps; these values do **not** show an advantage.

At S32,H64, **training contains only 3 observations and no positives**. At S64,H64, training contains **zero** eligible observations. Neither is an algorithmic negative result: this dataset has been censored by short native local Tabu episodes. Do not invent generalization metrics there.

**Conclusion:** With actual prospective improvement-occurrence labels, there is no validated incremental value from the binned spectrum or current cheap bit statistics over energy+history. The former high conditional-direction AUC is a *representation diagnostic*, not evidence of useful intervention decisions. Existing native episodes do not represent persistent cross-generation plateau dynamics; the next genuine test must log **GA-wide stalled checkpoints** and include new high-quality score values, or deliberately create longer native stateful search episodes. A dual encoder is not currently warranted.

## Validation provenance and mistakes

The initial run [41988458715](https://github.com/teddyli18000/web-ingest/actions/runs/41988458715) failed because it incorrectly demanded all six lengths have eligible S64/H64 snapshots. The follow-up [41988668712](https://github.com/teddyli18000/web-ingest/actions/runs/41988668712) computed all four datasets but failed on a two-character CSV delimiter in the final verification, which was a workflow bug. Final [41988782417](https://github.com/teddyli18000/web-ingest/actions/runs/41988782417) correctly validated and committed **all four** horizon datasets, including the zero-label/scarce-event regimes. All source code, exact seeds, manifest, and raw source native trace are topic-local. This is observational; sequential snapshots within the same native run are not independent scientific trials, and intervals are resampled over only **six** heldout runs.
