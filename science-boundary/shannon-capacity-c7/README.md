# Shannon capacity of the 7-cycle: computational lower-bound search

## Question

Can we construct an independent set in the strong graph power `C7^⊠10` with more than **134,753** vertices, improving the public Few Shots p004 baseline?

Equivalently, we seek a verifier-valid certificate of size at least **134,754**. The immediate research target is a new lower bound for `α(C7^⊠10)`; any claim about Shannon capacity itself must be stated only at the strength justified by that finite-power improvement.

## Why this may be a frontier

The 134,753-point construction is a highly structured record-scale object built from a 367-point independent set in `C7^⊠5`, a companion 367-point family, an `8×367 + 8×367` port construction, and a `(367-8)^2` square block. A one-point improvement would improve the known finite-power lower bound used by Few Shots p004. This workspace treats the upstream verifier and public construction code as the authoritative computational checks; novelty beyond that benchmark must be re-checked against current literature before being claimed.

## Current state

**No verified improvement yet. Current public target: 134,754.**

The strongest near-boundary result so far comes from an exact MaxSAT optimization of a neutral 2-for-2 perturbation of the 367-point parent together with a nine-port generalization. Of the ten eligible nine-center subsets in the only useful neutral2 parent state:

- **rank 3 has exact optimum 134,753**, tying the current record and missing a breakthrough by exactly **1**;
- **rank 6 has exact optimum 134,752**;
- rank 0 has exact optimum 134,738.

This is the present frontier. The next work should modify the rank-3 structural model rather than repeat strict SAT or shallow local replacement searches.

## What is known from our computation

1. The 134,753 baseline is locally rigid under several exact replacement neighborhoods. Direct add-1, remove-1/add-2, remove-2/add-3, remove-3/add-4, and remove-4/add-5 searches found no improvement.
2. The original ninth-port construction would have theoretical score 134,770, but strict SAT formulations requiring all intended port vertices are UNSAT.
3. Neutral 2-for-2 parent perturbations produce only **27** legal states; only one state has enough private centers to support a nine-center construction. That state has 10 private centers, giving 10 nine-center subsets.
4. Exact MaxSAT over those ten subsets shows at least one construction can recover the full current record of 134,753. Therefore the structural family reaches the boundary exactly and is not merely a loose near miss.
5. Extensive automorphism / translation / signed-permutation / companion-repair probes did not produce a verified improvement.

These are computational statements about the searched families, not general impossibility results for `C7^⊠10`.

## Current hypothesis / route

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

### Structural ninth-port search

The public construction can be viewed as a large square block plus two families of port fibers. Replacing the eight-center deletion set by nine centers has a nominal gain of +17 if all 18 endpoint choices per companion fiber can be retained. Strict SAT and several rewirings were UNSAT.

### Neutral2 parent search

Exact enumeration found 27 legal neutral 2-for-2 parent states. One state (historically labeled state 18) has 10 private centers and thus 10 possible nine-center subsets. Strict generalized SAT over these subsets was UNSAT.

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

Public inputs are intentionally not copied here:

- Few Shots p004 baseline certificate and verifier: `few-shots/few-shots`, `problems/p004-shannon-capacity-c7/`.
- 367-point `C7^⊠5` source set `R367.txt`: `nathanielitty/lower-bounds-for-shannon-capacity`, `c7/R367.txt`.

The original exploratory implementations remain historically available in `temp-work/few-shots-p004/` and in the `web-ingest` Git history, but this directory is the durable handoff.

## Next steps

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
