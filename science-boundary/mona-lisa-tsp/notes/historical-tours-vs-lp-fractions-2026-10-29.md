# Historical tour disagreement × genuine Concorde fractional LP — 2026-10-29

## Question

Does the intersection between strong-algorithm tour disagreement and fractional LP support locate better *connected* tours than either signal alone? Distinguish descriptive overlap from verified predictive value. The target is a strict score improvement below Nagata 5,757,191 under exact TSPLIB EUC_2D scoring.

## Primary data and validation

- Original Waterloo Mona Lisa Challenge: https://www.math.uwaterloo.ca/tsp/data/ml/monalisa.html
- Seven public historical tours at scores 5757199, 5757200, 5757203, 5757204, 5757205, 5757241, 5757245 plus Nagata baseline 5757191. Every downloaded tour is an independently verified 100,000-city Hamiltonian cycle at its advertised integer length.
- **Not seven independent solver replicates**. Five are Helsgaun LKH lineage; 5757204 and 5757241 originate from Dong et al., but both borrowed Helsgaun starting tours. Source correlation must temper statistical generalization.
- Three original Concorde LP primal snapshots: 2011-07-15 (`mona.4zsub.x`), 2012-01-21 (`mona.5zsub.x`), 2012-04-18 (`mona.6nsub.x`). Inputs have original 0-based endpoint IDs. Per-city degree sums are within at most 0.000255 of 2, consistent with six-decimal primal rounding. These are genuine LP solutions, **not** fabricated fractional candidate weights.
- Exact reproducible data, source hashes and spatial permutation test: [data/historical-lp-overlap.json](../data/historical-lp-overlap.json), [historical_lp_disagreement.py](../historical_lp_disagreement.py), [run 40847695759](https://github.com/teddyli18000/web-ingest/actions/runs/40847695759).
- Neighborhood-based spatial permutation control preserves each of 24×24 location-bin marginals; 300 randomizations (so p-value resolution 1/301) and seed are saved. This controls coarse geography, **not** spatial autocorrelation, city-graph dependencies, algorithm lineage or hidden confounding.

## Confirmed structural findings

1. **94,228 Nagata edges** appear in all seven older tours (94.228%); only **5,772 incumbent edges** are changed by at least one. **11,085 cities** participate in some local difference. All historical alternate edges together comprise **103,857** unique edges; including Nagata raises the union to **105,835**.
2. The LP snapshot of 2012-04-18 contains 125,776 positive-support edges, 50,886 fractional (x∈(0,1) after a strict 1e−5 tolerance) and 43,915 cities incident to fractional edges. The prior snapshots have 52,320 and 49,952 fractional edges, with 32,745 **cities** incident to fractional edges in all three snapshots. Persistent *cities* are not proof that the same fractional edges persist.
3. Of 9,815 cities where at least two historical tours differ from Nagata, **8,426 (85.85%)** are incident to 2012 fractional edges, vs **39.35%** of remaining cities. Within 24×24 spatial bins, the empirical null intersection mean is ≈4,507 vs observed 8,426 (1.87×). No randomization reached the observed value (p ≤0.00332 at 300 permutations).
4. The stable incumbent edge set is not purely integral in the LP: **73,691** stable Nagata edges have x≈1, **20,372** are fractional and **165** zero/absent from 2012 LP support. Hence do not freeze 94,228 edges as if LP certified all of them.
5. Taking graph components of ALL variable edges (union of eight tours minus intersection) yields **517 connected disputed wiring regions**, with **47** admitting ≥3 distinct local patterns and **13** admitting ≥4. Each local pattern is a projection of a *valid full tour*, **not an independently legal substitution**; outside fixed-port interfaces can interact globally.
6. Top-ranked actual components (ID, vertices, different wirings, 2012 fractional vertices, persistently fractional vertices in all three LPs): (0, 1,523, 7, 1,411, 1,287), (1, 894, 6, 748, 660), (3, 526, 5, 487, 457), (5, 482, 6, 398, 364), (6, 424, 6, 400, 333). Region 0 has 1,404 cities satisfying both historical disagreement≥2 and fractional LP. Sources: [historical_wiring_components.py](../historical_wiring_components.py), [data/historical-wiring-components-summary.json](../data/historical-wiring-components-summary.json), [run 40848746212](https://github.com/teddyli18000/web-ingest/actions/runs/40848746212).

## Matched-benchmark result: does joint selection already beat single-signal baselines?

[Run 40848215262](https://github.com/teddyli18000/web-ingest/actions/runs/40848215262), [compare_disagreement_lp_selectors.py](../compare_disagreement_lp_selectors.py):
- Five selectors: historical edge votes, LP fractional ambiguity x(1−x), their edge intersection, node-level joint, random. Budgets 192 and 512 novel candidate edges, same official exact cost metric, same Nagata baseline, same CP-SAT AddCircuit formulation; all **10** connected 1-unit-improvement subproblems proved **INFEASIBLE**.
- Degree-2 relaxations on exactly the same edge pools revealed hidden savings, without connectivity: at budget 512, historical votes reached 5,757,167 (gain 24), LP fractional 5,757,168 (gain 23), intersection/joint 5,757,169 (gain 22), random 5,757,191 (gain 0).
- At budget 192, historical/intersection/joint degree-2 minimum 5,757,182 (gain 9), LP fractional 5,757,186 (gain 5), random 5,757,191.
- **Crucial evidence against an overly optimistic interaction claim:** the history and intersection selectors chose the **same 192 edges** (and 512/512 of history's top 512 edges are also LP-fractional), while joint was very similar. With these rankings, historical route popularity is largely redundant with 2012 fractional LP support. Intersection does *not* show additional predictive signal at these budgets. All tests are conditional on small edge pools, not proof of optimality.

## Next: topology-aware region exact comparison

[lp_wiring_region_exact.py](../lp_wiring_region_exact.py) admits *all* historical parent alternative edges inside the top 1, 3, or 8 contested regions, then adds a fixed count of true 2011/2012 LP fractional edges never used by any parent. Tests persistent-across-three LP selection vs single-snapshot ambiguity vs matched random selection.

**Important observation from candidate pool preflight:** only **76** novel LP-fractional chords lie entirely inside the single highest-disagreement component, **135** inside the top three, and **219** inside the top eight. The original 128/256-edge budgets caused preflight assertion failures; these were *configuration errors*, not optimization exclusions. Corrected budgets: 64/128/192, respectively. This shows simple LP overlap tends to *confirm already seen connections* rather than supply many new within-component chords; crossing-region LP edges may be the necessary qualitatively different interface, so their omission must be recorded as an intentional scope limitation.

## Research interpretation and falsifiers

- Historical-vs-LP agreement robustly identifies **ambiguity**, which is different from identifying a **strict improvement**.
- The genuinely high-value question may be *where competing wiring blocks interact through LP-fractional **cross-block** edges* rather than where both measurements simply flag the same city.
- A next falsifiable reformulation is a **quotient/interface graph**: contract jointly agreed tour paths, represent competing region boundary ports and LP-fractional cross-region edges, then optimize a connected global tour with exact integer weights. This can coordinate topology without simply enlarging local geographic k-opt regions.
- Compare against spatial and size-matched random region selections and with held-out historical tours, not only LP-positive hot spots. The seven historical tours are temporally and genealogically correlated, which may inflate apparent confidence.
- If region-local LP augmentation is again infeasible, prioritize **cross-region LP edges** and independent diverse solver populations, not more interior LP chords.

No new p010 record has been obtained; do not submit without upstream verification and a score ≤5,757,190.
