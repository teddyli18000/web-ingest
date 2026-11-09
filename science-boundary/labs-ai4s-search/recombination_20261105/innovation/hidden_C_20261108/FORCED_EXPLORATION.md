# Exploratory amendment after sealed N50 outcome (2026-11-09)

## Why the first protocol is not final evidence

The [first N50 sealed experiment](results/test50/verdict.json) is exact-verified (144 states, 6 arms ×150ms; 670,888 full event rows preserved losslessly). Every arm failed to recover C on 72 AB-blind states. On 72 C-shell privileged positives, all six arms recovered C in the same 17 cases **on the shared first direct repair(X)**. No arm gained an additional C hit after that repair.

**Discovered after looking at the sealed outcome:** ordinary A, true B and fake B rank a proposal bank which included the exact current state at j=0 by raw E. The no-op often defeats every actual modification before Tabu repair. This is a real and consequential **baseline configuration defect**, not evidence that better learning is impossible, and renders the first comparison inadequate for the user's question.

## Amended, exploratory experiment — NOT a second sealed N50 test

**N50 is no longer truly unseen at the design/decision level.** Its parent/target orbits and the first test outcomes are known; reusing N50 with fresh seeds does *not* restore scientific holdout status. Explicitly classify this experiment as posthoc exploration under fresh **state/rng seeds 8–15**. It may repair the baseline defect and estimate failure modes, not establish genuinely unbiased cross-length transfer.

Same original N46/N47 model data, but train a separately named model on only the **five nonzero proposed masks j=1..5**, never overwrite previously frozen first-test model. N46 model coefficients, N47 choose regularization, no N50 in fitting. Publish and SHA-freeze this new model in a separate main commit **before running new N50 states**.

At deployment set `LABS_FORCE_NONZERO=1`, for all matching arms 0..4 (A-only exact E, true B exact E, fake B exact E, full learned true-B + exact epistasis/history, cheap energy/history model). Each arm samples the same five cardinalities (2/4/6/8/10) and identical total wall-time, with only the donor's available/virtual support varying. Original arm5 independently seeded 2/4/6/8/10-spin ILS is retained as a strong single-source baseline. All arms share their one initial native steepest→64 Tabu7→steepest repair(X). The learned model pays for online feature extraction and candidate ranking; offline training time and generated source seeds are reported.

No C bits, orbit identifiers, or source-length-specific fingerprints are passed to the solver or trained model. C vault is read only by a separate posthoc exact scorer. The C-shell states are privileged and **not** primary blind-search evidence.

**Primary:** post-initial *incremental* source-distinct other-optimum/C hit from AB-blind states. **Positive-control:** recovery of hidden C from C-shell only when first direct repair(X) has failed. The event trace is losslessly gzipped and independently checks all pre/post integer LABS E and symmetry class. Report repaired-orbit diversity, full-repair calls, wall time, and per-orbit/per-damage stratification. Crucially, AB-blind or hidden-C rare positives might be structurally absent from a 150–200ms budget. If no extra hits, add a *retrospective shared proposal-bank reachability oracle* (never available to the search policies) before concluding there is no learnable signal.

This amendment is not a justification for deep models. It is a controlled attempt to rescue fair classical and learning comparisons after a discovered no-op mistake.
