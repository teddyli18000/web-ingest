# Neutral2 nine-center MaxSAT results

Date: 2026-10-27

## Setup

A neutral 2-for-2 perturbation of the 367-point `C7^⊠5` parent was exhaustively enumerated. Only one legal neutral2 state had enough private centers to support a nine-center port construction. It had 10 private centers, hence 10 choices of nine centers.

For each of those ten choices, an exact weighted MaxSAT instance maximized the number of retained port vertices subject to the modeled same-fiber and cross-orientation conflicts.

For nine deleted centers, the square block contributes

```text
(367 - 9)^2 = 358^2 = 128,164.
```

The current record is 134,753, so a breakthrough requires at least 6,590 retained port vertices.

## Exact optimum by rank

| Rank | Retained port vertices | Total score | Gap to 134,754 |
| ---: | ---: | ---: | ---: |
| 0 | 6,574 | 134,738 | 16 |
| 1 | 6,574 | 134,738 | 16 |
| 2 | 6,574 | 134,738 | 16 |
| **3** | **6,589** | **134,753** | **1** |
| 4 | 6,574 | 134,738 | 16 |
| 5 | 6,574 | 134,738 | 16 |
| **6** | **6,588** | **134,752** | **2** |
| 7 | 6,574 | 134,738 | 16 |
| 8 | 6,574 | 134,738 | 16 |
| 9 | 6,574 | 134,738 | 16 |

These are exact optima for the encoded MaxSAT family, not heuristic lower bounds.

## Interpretation

Rank 3 exactly ties the 134,753 baseline. This is the most important structural near miss found in the initial campaign: the family can reach the existing record and needs exactly one more retained 10D vertex to improve it.

Rank 6 is one step behind at 134,752. The other eight ranks form a common lower plateau at 134,738.

This strongly suggests that follow-up work should inspect the specific conflict structure of ranks 3 and 6 rather than broaden uniformly over all nine-center subsets.

## Reproduction provenance

The values above were read from the ten GitHub Actions artifacts produced by workflow run `40539450408` in `teddyli18000/web-ingest` (`Temp Few Shots p004 neutral2 MaxSAT`). Each artifact contained the `status.json` emitted after RC2 completed exact optimization.

The durable implementation is in `../code/neutral2_maxsat.py`; its dependencies are `generalized9.py` and `neutral2_sweep.py`.

## Missing artifact to freeze next

The initial workflow only saved a certificate when the score exceeded 134,753, so the exact rank-3 selected-variable model was not persisted. The next experiment should rerun rank 3 and save the maximizing assignment even though it only ties the record. That concrete model is needed for local structural surgery and independent replay.
