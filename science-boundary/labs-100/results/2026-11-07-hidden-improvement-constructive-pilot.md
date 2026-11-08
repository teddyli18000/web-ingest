# Hidden-improvement constructive pilot — 2026-11-07

## Purpose
Continue p006 with a **constructive positive-control benchmark**, not additional exclusion of E<=574. The public Few Shots board and FEWSHOT record still show N=100 energy 578 (checked 2026-11-07 PST). Target is E<=574, and no new N=100 candidate was found in this pilot.

## Experiment
- Length N=40, 48 independent seeded cases, `random.Random(20261107)`.
- Score each generated sequence by full exact aperiodic LABS energy `sum_{k=1}^{N-1} (sum_i s_i s_{i+k})**2`.
- Build a hidden reference via deterministic exhaustive single-bit best-improvement descent of a random sequence.
- Generate an initial solution by flipping 10 random bits of the hidden reference and independently descending again. Keep target sequence hidden from both repair algorithms. **Only cases with initial E strictly greater than reference E count as nontrivial positive controls.**
- For each case compare 16 rounds of three-bit perturbation followed by identical full 40-bit steepest descent; accept a move only when E decreases.
- Random arm chooses perturbation sites inside a random 10-site subset. Pressure arm chooses a 10-site circular window near the site with maximal simple lag-correlation pressure (sum of |C_k| over lags touching that site). Each gets the same 16 exact-descent calls after perturbation.
- Every case is deterministic under Python's built-in PRNG, and the original objective is scored exactly, without compressed proxy.

## Results
Among 48 generated cases, 24 had initial E strictly greater than hidden reference E.
Of these 24 genuinely nontrivial positive controls:
- random-window perturbation recovered E <= hidden reference in **19/24**;
- correlation-pressure-window perturbation recovered E <= hidden reference in **21/24**.

Across all 48 cases (including trivial already-good initial states):
- random recovery 43/48; pressure recovery 45/48;
- mean final E random **180.4166666667**; pressure **179.8333333333**.

These outcomes do **not** establish a statistically meaningful advantage; the positive control is easy and many cases were already at least as good as the reference. The original baseline attempt with restricted single-bit descent and no perturbation made *zero moves* from already 1-flip-local-optimal parents: an important negative design finding. The pilot therefore revised the operator to cross a barrier with a three-bit perturbation and then run complete single-bit descent.

## Interpretation and next experiment
This is **not** an N100 record and not evidence that pressure-guided repair beats strong contemporary methods. The next benchmark must (a) reject trivial parents when constructing cases, (b) use independently good and diverse hidden reference states rather than random 40-bit local minima, (c) compare with tabu/ILS and a shuffled-pressure ablation, (d) compare equal objective-evaluation cost instead of equal repair rounds, and (e) test 60<=N<=100 where quality floors are meaningful. If a mechanism gains a clear repeatable recovery advantage, move it to the N100 unrestricted search while scoring every completed candidate with original integer autocorrelations.

## Related literature
- Packebusch & Mertens (2016), https://arxiv.org/abs/1512.02475
- Pšeničnik et al. (2026), https://arxiv.org/abs/2607.09688 (partition priorities and parallel self-avoiding walks on significantly longer lengths; not an N100 claim)
- Few Shots p006, https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100

## Verification status
Local script and deterministic result JSON were executed in the session that produced this note. This is a pilot not yet independently replicated on Actions; do not cite as a proof or record.
