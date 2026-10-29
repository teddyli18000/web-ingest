# AI4S search-method discovery for low-autocorrelation binary sequences

## Question

Can learning or program discovery produce a **reproducible, transferable improvement in low-autocorrelation binary sequence (LABS) search**, especially at escaping difficult local minima or selecting promising search basins? A verified improvement at length 100 is an ambitious secondary outcome, not a claimed result.

This is an independent **methodological research direction**, distinct from the existing `science-boundary/labs-100/` record-construction effort. Preserve distinct evidence and do not modify the other topic's files.

## Current state

**Opened 2026-10-29. No new experiments or verified breakthrough in this workspace yet.**

Prior exploratory work, published separately in [CreoEnMi-p/few-shots — AI4S Boundary](https://github.com/CreoEnMi-p/few-shots/tree/main/research/ai4s-boundary), contains an early neural-perturbation pilot, classical reference code, reproducibility checks, and a conditional research charter. These materials are **prior evidence to inspect**, not instructions to obey and not a claim of state-of-the-art performance.

According to the published pilot, a small online neural policy did **not** consistently outperform simple alternatives at lengths 40, 60, and 100; a separate record-seeded test did **not** improve the verified length-100 value of 578. The pilot had weak baselines, few seeds, and unmatched wall-clock/model overhead, so it neither establishes nor refutes the value of learned search.

## Research aim

Investigate whether a genuinely different search representation, learned decision mechanism, or discovered optimization program can outperform strong non-learned methods on **unseen LABS instances**, under fair matched-compute evaluation. Assess current literature and the actual source code before treating a method as novel.

The original working hypothesis is that evaluating **post-relaxation basin outcomes** for coordinated moves may contain more useful information than rewarding an immediate bit flip. Treat this as a hypothesis to test or replace, not a prescribed solution.

## Evidence and reproducibility

- [Previous AI4S pilot and reproducibility instructions](https://github.com/CreoEnMi-p/few-shots/tree/main/research/ai4s-boundary)
- [Previous formal research charter and prospective success criteria](https://github.com/CreoEnMi-p/few-shots/blob/main/research/ai4s-boundary/notes/research-charter.md)
- [Previous results and limitations](https://github.com/CreoEnMi-p/few-shots/blob/main/research/ai4s-boundary/notes/interpretation.md)
- [Few Shots p006 problem, exact verifier, and baseline](https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100)
- [Existing independent LABS-100 record-oriented research](../labs-100/)

## Next steps

The incoming research agent should review the prior pilot and the latest public literature, decide what evidence is still missing, then design and execute independently justified experiments. Keep code, datasets, negative results, reproducibility details, and the next handoff in this directory. Use `main` and the repository's scientific-workspace instructions. GitHub Actions are available for useful compute; minor work does not require them.

Distinguish improvements to search methodology from verified record-breaking certificates. Do not claim a new LABS record without exact independent verification and current-prior-art review.

## Work log

- **2026-10-29:** Opened this distinct AI4S methodology topic with links to the previous exploratory study. No new computational claim.
