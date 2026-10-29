# AI4S search-method discovery for low-autocorrelation binary sequences

## Question

Can learning or program discovery produce a **reproducible, transferable improvement in low-autocorrelation binary sequence (LABS) search**, especially at escaping difficult local minima or selecting promising search basins? A verified improvement at length 100 is an ambitious secondary outcome, not a claimed result.

This is an independent **methodological research direction**, distinct from the existing `science-boundary/labs-100/` record-construction effort. Preserve distinct evidence and do not modify the other topic's files.

## Current state

**2026-10-29: expanded basin-transition experiments, independent held-out lengths, and a decisive descent-operator counterexample. No demonstrated transferable policy improvement or verified new LABS record.** [Read the full current research report](notes/basin-geometry-2026-10-29.md). Core observations: for one steepest-descent protocol the 50%-escape radius approximately grows as sqrt(N) at ordinary minima (N24–100, plus independent N48/72/96); at official N100 energy 578 its threshold increases to about 9.58; switching to first-improvement descent moves the ordinary N100 threshold from about 6.10 to 2.39. Action rankings across the two relaxations have near-zero correlation. Accordingly, deterministic basin labels are solver-dependent and a learned policy cannot safely assume basin geometry is invariant. The source [geometry_repro.py](geometry_repro.py) reproduces all radius/record measurements; [operator_agreement.py](operator_agreement.py) reproduces matched-action comparisons. The early pilot below is now background, not the leading result.

**Earlier pilot:** See [pilot 01](notes/pilot-01.md) and [runnable Python source](pilot_basin.py). On 12 initial seeds and lengths 24/32, selecting two-bit disturbances by post-relaxation basin energy improved median best energy versus selecting by immediate perturbed energy (64 vs 70; 122 vs 128). The full lookahead oracle is expensive and not deployable as-is: this is evidence for a predictive target, **not** a superior end-to-end search method.

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

A first held-out **two-descent value** model has now been tested with [ensemble_probe.py](ensemble_probe.py): train on N40/64 and rank N100 actions by average positive gain across steepest and first-improvement relaxation. On 150 independent N100 basins per radius, candidate-level learned improvements over a cheap single-spin-delta-sum heuristic had paired bootstrap intervals spanning zero, despite a large hindsight-oracle gap. **Do not claim demonstrated learning-driven search gains.** Next test truly different action representations (explicit autocorrelation-lag/spin coupling, trajectory history) and learn **conditional perturbation radius accounting for near-record stiffness**; all comparisons must include wall-time and strong classical tabu/self-avoiding baselines. Exploratory held-out-length gradient boosting did **not** show robust gains at N64/100 deep minima over cheap stability rules, so do not scale model size without new evidence. Compare with hand-crafted immediate-energy ranking and strong classical tabu/self-avoiding search; use at least 20 seeds and wall-clock matched evaluation before any method-level claim. Keep code, datasets, negative results, reproducibility details, and the next handoff in this directory. Use `main` and the repository's scientific-workspace instructions. GitHub Actions are available for useful compute; minor work does not require them.

Distinguish improvements to search methodology from verified record-breaking certificates. Do not claim a new LABS record without exact independent verification and current-prior-art review.

## Work log

- **2026-10-29:** [Held-out ensemble-value test](ensemble_probe.py): 27,000 matched steepest/first-descent candidate outcomes, train N40/64 and evaluate N100 on 150 independent stage-40 minima per radius. Cheap features and gradient boosting did not consistently outperform sum-of-single-flip-delta ranking on *positive improvement per action*; paired 95% bootstrap intervals include zero. Retain as a fully reproducible negative result. See [report](notes/basin-geometry-2026-10-29.md).

- **2026-10-29:** [Full basin geometry and transfer report](notes/basin-geometry-2026-10-29.md): 136,800 steepest-descent perturbations at lengths 24/32/40/64/100; independent held-out 48/72/96; 9,900 official record-basin stress perturbations with no improvement; steepest versus first-descent radius experiment; 27,000 matched-action cross-descent outcomes. Verified exact incremental energy and an algebraic formula for the sum of all one-bit energy barriers. **Negative critical test:** basin escape and action value depend sharply on the descent operator. Generated source and reproducibility commands live in this topic, no other workspace was edited.

- **2026-10-29:** [Pilot 01](notes/pilot-01.md) evaluated random, immediate-energy and post-relaxation selection with a common fixed eight-candidate 2-flip pool per round at N=24/32. Full candidate relaxation charged to all policies, 12 seeds, 3 rounds. The post-relaxation oracle selects better basins; generalization and net benefit after prediction costs remain unknown. Sources and reproducible code committed under this topic.

- **2026-10-29:** Opened this distinct AI4S methodology topic with links to the previous exploratory study. No new computational claim.
