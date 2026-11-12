# Shannon capacity of the 7-cycle: computational lower-bound search

## Question

Can we construct an independent set in the strong graph power `C7^⊠10` with more than **134,753** vertices, improving the public Few Shots p004 baseline?

Equivalently, we seek a verifier-valid certificate of size at least **134,754**. The immediate research target is a new lower bound for `α(C7^⊠10)`; any claim about Shannon capacity itself must be stated only at the strength justified by that finite-power improvement.

## Why this may be a frontier

The 134,753-point construction is a highly structured record-scale object built from a 367-point independent set in `C7^⊠5`, a companion 367-point family, an `8×367 + 8×367` port construction, and a `(367-8)^2` square block. A one-point improvement would improve the known finite-power lower bound used by Few Shots p004. This workspace treats the upstream verifier and public construction code as the authoritative computational checks; novelty beyond that benchmark must be re-checked against current literature before being claimed.

## Current state

**2026-11-12 — constructive search pivot:** Four officially verified 134,753-point ten-dimensional mother codes were factored through several *new* 5+5 coordinate partitions. A new [forced-anchor exact row-repair solver](code/c7p004_cross_partition_anchor_repair.py) jointly regenerates all legal suffixes in selected prefix rows, preserving or temporarily lowering score by one to enter different basins. [Initial pilot](https://github.com/teddyli18000/web-ingest/actions/runs/43251407252) showed up to 78-point single-block equal-score changes; after correcting candidate sampling to focus on **4,266 truly missing mother-code words**, [four hosted trajectories](https://github.com/teddyli18000/web-ingest/actions/runs/43251915668) completed **1,232 exact MILPs** and many nontrivial neutral moves, but no 134,754-point code. A [second construction](code/c7p004_pair_anchor_construct.py) forces **two compatible new points sharing old blockers**, one absent from all four mother codes. Its [123 solved two-anchor cases](https://github.com/teddyli18000/web-ingest/actions/runs/43252967377) still yielded no gain. These runs establish *real constructive mobility* beyond the original factor interface, not a proof about all of C7^10. Full [reproducible research note](results/cross-partition-anchor-repair-2026-11-12.md).

**Next distinct constructive target:** Find a five-dimensional **11-port orientable** private-neighbor configuration, then a size-≥365 auxiliary avoiding its two-sided obstruction. This would produce **at least 134,766** ten-dimensional points, clearing the p004 record. Two independently verified 367-point neutral parents already have 14 distinct private-neighbor owners, but not an 11-pair valid orientation; a new [11-port constructor](code/c7p004_orientable_t11_construct.py) directly optimizes simultaneous orientability rather than the raw owner count, and scans translated public auxiliaries immediately on success. [Four-worker Actions search 43254623906](https://github.com/teddyli18000/web-ingest/actions/runs/43254623906) is executing as of this update. **No improved certified score yet.**


**2026-11-08 — verified record-level constructive mobility:** Rebuilt the 134,753-point Itty–Rosin–Carstensen–Reichman ten-dimensional code from a pinned public source, then used an exact score-first MILP to replace **3,034 old points with 3,034 new points in one coordinated move**. Two other independent tie-break seeds replaced **3,033** each; **all three complete 134,753-point certificates passed the official Few Shots p004 verifier**, each with a distinct canonical hash. Reproducer: [large coordinated repair](code/c7p004_record_coordinated_repair.py), [official verification run](https://github.com/teddyli18000/web-ingest/actions/runs/42502891420). Full [2026-11-08 research and next constructive representation](results/record-level-3034-neutral-and-core-coupling-2026-11-08.md). **The public record is not improved.**

**Reformulation from first principles:** Of the 49,390 outside×outside candidates with at most three old blockers in a wider scan, **49,341 do not touch the giant 359×359 core at all**. This explains why very large neutral periphery rearrangements fail to raise score. A separate model now jointly optimizes rectangular core releases, row/column fibers, and outside×outside points; [GitHub Actions run 42503523088](https://github.com/teddyli18000/web-ingest/actions/runs/42503523088) completed all **800** six-owner constructive cases across the published and 3,034-neutral record substrates with **no positive gain**. All eight jobs completed successfully. Do not scale unchanged fixed rectangles; change owner sets and retained-core structure jointly. Don't interpret this bounded family as a global exclusion; if its quality stays flat, stop scaling fixed rectangles and **change the core owner sets and factor endpoints jointly**.


**2026-11-06 active frontier — frozen 12-private-owner circular basins, verified port search:** Two new 367-point five-dimensional witnesses have **12 distinct private owners** each and admit respectively **48** and **576** valid ten-port orientations; they are preserved as [port12a](data/circular-port12-port12a-2026-11-05.json) and [port12b](data/circular-port12-port12b-2026-11-05.json). Exhaustive cyclic-FFT scans of every t=9/t=10 orientation against **41** pinned public auxiliary codes and all **16,807** translations each found no disjoint auxiliary: best t=10 defects are **8** and **9**, best t=9 defects **5** and **7**. [Full experiment record and hosted verification](results/circular-port12-t9-t10-campaign-2026-11-06.md). **No improved p004 score.**

**Constructive threshold and next distinct mechanism:** For a valid t=10 port set, a *D-free 366-point auxiliary* already yields **134,769** ten-dimensional points through `(367-10)^2+2×10×366`, beating 134,753. The best pinned t=10 near miss has 8 auxiliary words in its forbidden 1,229-word region. Instead of another translation sweep of the same 41 codes or a larger fixed-core exchange radius, jointly reconstruct the auxiliary's internal structure to retain **at least 366** allowed words. A valid t=11 orientation would lower the required auxiliary size to **365**, but neither frozen parent admits t=11 under its current private pairs.


**2026-11-04 exact computational closure:** The entire free-label/full-phase reconstruction family based on 38 pinned public 367-word `C7^5` codes has verified optimum **367** on every coordinate axis. It allows complete 4D slice templates from any original symbol label to be placed at any destination label and translated independently by any of the 2,401 four-dimensional shifts. Across **6,882** ordered template pairs, **6,174** have no compatible relative phase; **708** admit only the zero phase; no nonzero relative phase is compatible. The resulting 7-cycle DP optimum is exactly **367** on all five axes, independently replayed by 4D integer convolution. See [full theorem and two reproductions](results/c7p5-free-label-full-phase-closure-2026-11-04.md). **This is not a bound on all of `C7^5`; no p004 record improvement.**

**New search-space decision:** Stop extending translations/relabelings of unchanged public slices. Search must introduce genuinely new **internal 4D slice shapes** or genuinely independent 5D parent basins, and jointly optimize them with neighboring layers. The exact two-layer MILP pilot found only 367, and the 3,000-variable full three-layer CP-SAT probes timed out as `UNKNOWN`; see [whole-layer block frontier](results/c7p5-whole-layer-blocks-2026-11-04.md).


**2026-11-04 new exact result:** A nine-factor support-3 kernel has a rigorously checked fractional owner-clique dual contradiction of **1/2**, yet its full `9×9` tensor candidate set has exact **zero** raw-core prize (MILP). All **38** nearest one-factor and **15** strongest two-factor expansions also have optimal gain zero, replayed on the pinned public BPZ/Tandon data in [Actions run 41849969593](https://github.com/teddyli18000/web-ingest/actions/runs/41849969593). See [fractional-nine-charge-2026-11-04.md](results/fractional-nine-charge-2026-11-04.md) and [reproducer](code/bpz_fractional_nine_charge.py). This rules out these restricted product families, not the global problem. **No improved p004 score.** Next formulation should alter the core jointly or attack the independent five-dimensional 368-point problem, not extend the same kernel by more one/two-factor cases.


**2026-11-04 takeover update:** The rank-3 134,753 MaxSAT tie described below is historical rather than the latest research frontier. Later work has exact net+1 radius-six closure, a global product-injection exclusion for support≤2, and the first support-three assignment obstruction whose minimal 63-factor product still has zero prize. See [`results/takeover-2026-11-04.md`](results/takeover-2026-11-04.md) for the audited current evidence, unresolved statuses, and the next distinct support-three expansion experiment.


**No verified improvement yet. Current public target: 134,754.**

The strongest near-boundary result so far comes from an exact MaxSAT optimization of a neutral 2-for-2 perturbation of the 367-point parent together with a nine-port generalization. Of the ten eligible nine-center subsets in the only useful neutral2 parent state:

- **rank 3 has exact optimum 134,753**, tying the current record and missing a breakthrough by exactly **1**;
- **rank 6 has exact optimum 134,752**;
- rank 0 has exact optimum 134,738.

This was the 2026-10-27 frontier; it is preserved for historical context and has been superseded by later direct 5D and structural product investigations.

## What is known from our computation

1. The 134,753 baseline is locally rigid under several exact replacement neighborhoods. Direct add-1, remove-1/add-2, remove-2/add-3, remove-3/add-4, and remove-4/add-5 searches found no improvement.
2. The original ninth-port construction would have theoretical score 134,770, but strict SAT formulations requiring all intended port vertices are UNSAT.
3. Neutral 2-for-2 parent perturbations produce only **27** legal states; only one state has enough private centers to support a nine-center construction. That state has 10 private centers, giving 10 nine-center subsets.
4. Exact MaxSAT over those ten subsets shows at least one construction can recover the full current record of 134,753. Therefore the structural family reaches the boundary exactly and is not merely a loose near miss.
5. Extensive automorphism / translation / signed-permutation / companion-repair probes did not produce a verified improvement.

These are computational statements about the searched families, not general impossibility results for `C7^⊠10`.

## Historical 2026-10-27 hypothesis / route (superseded)

The best route is to start from the **rank-3 MaxSAT optimum at 134,753** and enlarge the model by one controlled structural degree of freedom. Candidate extensions, in priority order:

1. **Release one square-block constraint.** Permit one additional deletion or replacement inside the `(358)^2` square block if it unlocks at least two extra port vertices. Optimize net score directly.
2. **Jointly optimize parent and port choices.** The current neutral2 state is fixed before MaxSAT. Move one additional parent point while keeping the port selection variables live in the same optimization.
3. **Mixed 9/10-center construction.** A tenth center may cost square-block vertices but could unlock enough endpoint capacity to yield positive net gain.
4. **Use the exact rank-3 model as a seed for local structural search**, measuring objective delta rather than asking for an all-or-nothing strict ninth port.

The key principle is to optimize **net 10D score directly**. Requiring an idealized complete port gadget has already been shown to be too rigid.

## Evidence and experiments

### Exact shallow local replacement search

An exact full-space coverage convolution over all `7^10 = 282,475,249` vertices established no direct add-1, no remove-1/add-2, and no remove-2/add-3 breakthrough. Later exact searches extended this negative result through remove-4/add-5.

The full-space method uses separable cyclic `[1,1,1]` transforms in each coordinate to count how many baseline vertices conflict with every ambient vertex, then groups low-coverage candidates by their exact conflicting owners.

Detailed counts, memory/runtime data, and the CI-status caveat for the 4→5 run are preserved in [`results/exact-local-search.md`](results/exact-local-search.md).

### Structural ninth-port search

The public construction can be viewed as a large square block plus two families of port fibers. Replacing the eight-center deletion set by nine centers has a nominal gain of +17 if all 18 endpoint choices per companion fiber can be retained. Strict SAT and several rewirings were UNSAT.

### Neutral2 parent search

Exact enumeration found 27 legal neutral 2-for-2 parent states. One state (historically labeled state 18) has 10 private centers and thus 10 possible nine-center subsets. Strict generalized SAT over these subsets was UNSAT. A compact, exactly reconstructible description of the strongest strict near miss is frozen in [`results/neutral2-near-miss.json`](results/neutral2-near-miss.json).

### MaxSAT relaxation

`code/neutral2_maxsat.py` replaces the strict “keep every intended port vertex” requirement with an exact maximum-cardinality optimization. For each eligible nine-center subset it maximizes retained port vertices subject to all modeled conflicts.

The square-block contribution for nine deleted centers is fixed at `358^2 = 128,164`. To break the record requires at least `6,590` port vertices. Rank 3 reaches exactly the current record, so its optimized port contribution is `6,589`.

See `results/neutral2-maxsat-summary.md`.

## Dead ends

See [`notes/failed-routes.md`](notes/failed-routes.md). Important negative routes are preserved there so future Agents do not repeat them.

## Reproduction

Core reusable research logic is under `code/`:

- `generalized9.py` — 5D parent/companion model, safe-endpoint SAT machinery, and candidate construction.
- `neutral2_sweep.py` — exact neutral 2-for-2 parent enumeration and nine-center sweep.
- `neutral2_maxsat.py` — exact maximum-cardinality relaxation used for the present frontier.
- `search_exact.cpp` — exact full-space 0→1 / 1→2 / 2→3 neighborhood search.
- `search3.cpp` — exact remove-3/add-4 search.
- `search4.cpp` — exact remove-4/add-5 search.
- `neutral2.cpp` and `neutral2_autosym.cpp` — strict neutral2 near-miss and full signed-permutation/translation follow-up.
- `neutral2_generalized9.py` — generalized SAT repair probe on the best strict neutral2 state.

Public inputs are intentionally not copied here:

- Few Shots p004 baseline certificate and verifier: `few-shots/few-shots`, `problems/p004-shannon-capacity-c7/`.
- 367-point `C7^⊠5` source set `R367.txt`: `nathanielitty/lower-bounds-for-shannon-capacity`, `c7/R367.txt`.

Exact source provenance and input conventions are recorded in [`data/README.md`](data/README.md).

The original exploratory implementations remain historically available in `temp-work/few-shots-p004/` and in the `web-ingest` Git history, but this directory is the durable handoff.

## Next steps

1. Construct an independent **366-point** `C7^5` auxiliary disjoint from the explicit eight-hit ten-port obstruction `D` of size 1,229; then build and run the upstream verifier on the resulting **134,769-point** ten-dimensional certificate.
2. Re-parameterize neutral 367-word parent changes to change the *conflict graph between private neighbors*. Two disjoint odd triangles explain the current t<=10 limit in port12b; a genuine t=11 oriented parent together with a D-free 365-word auxiliary would instead yield **134,766**.
3. If joint source/auxiliary reconstruction fails to improve constructive candidate quality, reassess the gadget interface itself rather than merely increasing time limits on the same restricted MILP.
4. The original independent 368-word `C7^5` target would still square to 135,424. Verify every purported improvement with Few Shots p004 before a new-record claim.

## Historical 2026-11-04 next steps (superseded)

1. Build a **new 4D slice-template generation mechanism** that changes the internal selected words, not merely their translation or original symbol labels. Couple candidate validity across the 7-cycle.
2. Seek structurally distinct 5D source basins outside the pinned I0/X/Family-F corpus.
3. Any `C7^5` witness of 368 would square to 135,424 points.

## Historical next steps (2026-10-27)

1. Freeze and materialize the exact **rank-3 134,753 MaxSAT model**, not just its score, so later extensions can diff against a concrete boundary state.
2. Build a net-score MaxSAT/ILP that allows one extra square-block deletion/replacement and asks whether it can recover at least two additional port vertices.
3. If that fails, couple one additional neutral parent swap into the optimization instead of enumerating the parent first.
4. Any candidate ≥134,754 must be checked by the upstream p004 verifier before being described as a breakthrough.
5. Before any external novelty claim, re-check current literature and the Few Shots board.

## Sources

- Few Shots p004 problem, verifier, baseline certificate, and board: `https://github.com/few-shots/few-shots/tree/main/problems/p004-shannon-capacity-c7`
- Public C7 construction source and `R367.txt`: `https://github.com/nathanielitty/lower-bounds-for-shannon-capacity/tree/master/c7`

## Work log

### 2026-10-27 — migration from temporary exploration

Migrated the durable C7 research state from `temp-work/few-shots-p004/` into `science-boundary/shannon-capacity-c7/`. Preserved the exact frontier model, summarized exact negative routes, and intentionally left transient GitHub Actions workflows/logs out of the durable workspace.

The most important new boundary result at migration time is the neutral2 MaxSAT family: one exact optimum ties the 134,753 record and misses improvement by one point.
