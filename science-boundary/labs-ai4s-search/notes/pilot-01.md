# Pilot 01 — Counterfactual basin lookahead (2026-10-29)

## Status
**Preliminary mechanism diagnostic, not a learned method, record, or fair end-to-end solver comparison.**

Command: `python3 science-boundary/labs-ai4s-search/pilot_basin.py --seeds 12 --rounds 3 --probes 8 --lengths 24 32`

Python 3 standard library, deterministic initial seeds 0–11. Exact integer objective. For every starting local minimum, draw eight distinct 2-flip perturbations per round; fully relax every candidate by steepest single-bit descent. Compare selection by random candidate, immediate perturbed energy, and post-relaxation candidate energy. All methods pay for the same candidate lookahead; exact objective-call counts are reported, including the immediate-score evaluation. Tie-breaks are deterministic.

| N | policy | median best energy | mean best energy | approximate mean energy calls |
|---|---|---:|---:|---:|
| 24 | random | 76 | 78.00 | 2097 |
| 24 | immediate | 70 | 70.00 | 2087 |
| 24 | post-relax | 64 | 64.67 | 2011 |
| 32 | random | 134 | 135.67 | 2788 |
| 32 | immediate | 128 | 127.33 | 2764 |
| 32 | post-relax | 122 | 115.33 | 2724 |

Measured execution for these 72 runs: 3.81 seconds in a local Python environment (environment not standardized). Re-run to obtain per-seed JSON and exact counts.

**Interpretation:** post-relaxation outcomes contain selection information absent from immediate energies, on this small diagnostic. However the full post-relax oracle evaluates all candidates, and comparing to random/immediate does not establish a competitive novel solver or learned generalization. Costs may differ across trajectories because descent steps differ. Moreover all policies paid for all candidate relaxations—this does *not* show that predicting outcomes is feasible. Pilot 00's online neural policy failed to show consistent gains at N=40,60,100.

## Next test
Construct *out-of-sample* predictor of post-relaxation energy from pre-relaxation cheap features, avoiding outcome leakage; train on N=24,28,32 and test on unseen N=36,40 with >=20 seeds. Charge feature extraction, model inference, actual relaxations, and data generation costs. Compare to cheap hand-crafted ranking, learned logits shuffled, and blind-feature policy, plus stronger tabu/self-avoiding search. Measure time-to-target under wall-clock and exact energy-call budgets. If oracle-prediction gap is not economically recoverable, reformulate rather than scale a network.

## Sources
- Previous pilot: https://github.com/CreoEnMi-p/few-shots/tree/main/research/ai4s-boundary
- Żurek et al. 2024, DDQN + SDLS: https://doi.org/10.14428/esann/2024.ES2024-36
- Zhang et al. 2025, GPU memetic tabu: https://arxiv.org/abs/2504.00987
- Pšeničnik et al. 2026, Thompson sampling + parallel self-avoiding walks: https://arxiv.org/abs/2607.09688
- Pšeničnik et al. 2025, two-stage restriction/unrestricted search: https://doi.org/10.1016/j.dsp.2025.105316
- Clausen et al. 2024, limited-reach polynomial DP: https://doi.org/10.1016/j.cor.2024.106586
