# p003 construction-first reassessment — 2026-11-07

## Scientific objective and status

Build one *valid* 36-vertex graph with no K4 and no independent 6-set, proving R(4,6)>=37. No such graph was obtained in this session. The verified incumbent near-miss remains 14 forbidden subsets (10 K4, 4 I6), with 263 edges, in \`results/algorithm22-calibration-best-14.json\`.

Public status rechecked 2026-11-07: R(4,6) remains listed between 36 and 40 in the 2026 Radziszowski survey and McKay's collection; Few Shots p003 still has no merged winning shot.

## Construction experiments, independently checked

### Cross-core six-tail regeneration

A 36-vertex near-miss can be split into 30-core plus six tails with a *valid core and six individually legal single-vertex extensions* precisely when every existing K4/I6 witness intersects the chosen six tails in at least two vertices.

- Exhaustive six-vertex hitting-set enumeration yields **46** eligible partitions for the 14-defect incumbent.
- Independently generated single-tail legal-neighborhood catalogue sizes range **21..1303** over these 46 cores; the largest domain is for tails \`(5,6,13,25,34,35)\`.
- Candidate generator \`cross_core_six_tail_repair.py\` optimizes all \`2^15\` tail-tail adjacency patterns *jointly* for each six-mask proposal using the exact 2-, 3-, 4-, 5-, 6-tail defect decomposition, not a surrogate cost. It cross-samples 1–6 tail masks with restarts.
- GitHub Actions run [42455217975](https://github.com/teddyli18000/web-ingest/actions/runs/42455217975) finished all six matrix shards, each confirming **best defects = 14** after 6000 proposals/core = **276000** proposals total. All 46 cores were processed. No novel 36-vertex witness or sub-14 candidate.
- A putatively distant 14-defect near-miss was 81 labelled edge flips from the original but only *one* flip after optimizing the permutation of the six tail vertices. Do not count unaligned Hamming distance as genuine diversity.

**Interpretation:** This is negative evidence only for this *sampling mechanism*, not impossibility of a valid 36-vertex graph or saturation of the six-core space. The search remains in the known basin; do not simply increase the same 276000 trials without reformulation.

### Degree-preserving multi-edge full-graph moves

A local C++ prototype tested pairwise K4/I6-conflict repair, 2-switch rewiring, partial neighborhood swaps involving 2–6 vertices, and random multi-edge kicks while respecting the necessary 11..17 degree range. From the 14-defect incumbent, roughly a million proposals yielded no score below 14. A guided weighted-conflict variant also failed to improve. Neither source is retained in the repository since neither changed the candidate quality; working scratch files are local to the session.

### K4-hard local repair

Exactly destroying the incumbent's K4s using 3–5 deletions increases the independent-6 count sharply; among enumerated covers, best 0-K4 construction had 60 independent six-sets. This is not competitive with the 14-defect incumbent. These deletion-only repairs have a qualitatively different objective and should not be scaled absent a mechanism to repair the resulting independent six-sets jointly.

### Positive-control cross-cut synthesis on 35 vertices

Instead of preserving a big 30-core and adding one vertex, freeze two independently valid halves and synthesize their connecting edge set. The *hidden known answer* is a published 35-vertex graph: the solver sees only two induced halves and is not given the cross edges.

A local Z3 prototype reconstructed verified legal 35-vertex graphs with:

| split | cross-edge variables | generated edges | K4 | I6 |
|---|---:|---:|---:|---:|
| 30+5 | 150 | 248 | 0 | 0 |
| 27+8 | 216 | 247 | 0 | 0 |
| 24+11 | 264 | 246 | 0 | 0 |

A separate 24+11 run generated seven verified legal 35-vertex solutions (248/247/246 edges). Their \`(number of triangles, number of independent-five sets)\` fingerprints all match entries in \`results/extension-all-37.json\`, suggesting the same known Exoo basin. This fingerprint does **not** prove isomorphism; use a graph isomorphism checker before claiming novelty.

An exact one-vertex extension SAT on the above three example graphs returned UNSAT in each case; no 36-vertex graph resulted. A 17+18 hidden-answer split did not solve within the local time budget; this does *not* mean the model is invalid. Further Z3 21+14 experiments exceeded the local budget, motivating a stronger CDCL engine.

### New genuinely different constructive representation (active)

\`independent_halves_cadical.py\` uses CaDiCaL195 and no fixed 30-core. Its 36-vertex mode samples *two independently chosen 18-vertex induced graphs from distinct Exoo 35-point parents*, treating the copies as disjoint, then solves for **all 324 cross edges**. A found SAT model is independently recounted and submitted to the Few Shots verifier. Its 35-vertex positive control fixes 17+18 valid induced halves from an existing 35-vertex solution and hides all 306 cross edges.

Launched in [GitHub Actions 42456135866](https://github.com/teddyli18000/web-ingest/actions/runs/42456135866): two 35-point positive controls and six 36-point independent-parent fusions. Inspect official verdicts/artifacts before treating a green job as a mathematical success.

## Decision

The best candidate quality is still 14; do **not** scale repeated near14 local searches without a new positive signal. Prioritize genuinely independent parent structure and positive-control-calibrated regeneration, then verify any n=36 SAT witness with both the standalone exact bitset recount and the authoritative Few Shots verifier.

## Sources

- Few Shots p003: https://github.com/few-shots/few-shots/tree/main/problems/p003-ramsey-r46
- Exoo (2012), *On the Ramsey Number R(4,6)*: https://www.combinatorics.org/ojs/index.php/eljc/article/view/v19i1p66
- McKay public 37 graph6: https://users.cecs.anu.edu.au/~bdm/data/r46_35some.g6
- Radziszowski, *Small Ramsey Numbers*, 2026 revision: https://www.combinatorics.org/ojs/index.php/eljc/article/view/DS1


### Overlapping-parent and genuinely cross-parent synthesis (follow-up)

- \`independent_halves_cadical.py\` now also has \`overlap36\`: take two 18-vertex induced graphs of one published valid 35-vertex graph that overlap in exactly one original vertex, duplicate that original vertex into two vertices, and resynthesize every one of the 324 cross edges without retaining the original cross-edge assignment. The experiment is [42456264481](https://github.com/teddyli18000/web-ingest/actions/runs/42456264481), eight seeded pairs.
- \`fusion35\` instead takes 17 and 18 vertices from **two distinct published Exoo graphs** and synthesizes all 306 cross edges. Its key objective is to produce genuinely new *valid* 35-point parents, not just to regenerate the same 37 graph types. \`screen_fused35_extension.py\` checks K4/I6 and attempts exact one-vertex extension using two independent algorithms, and records whether each graph's triangle/I5 fingerprint is new relative to all 37 published examples. Distinct fingerprints certify nonisomorphism; matching fingerprints are inconclusive without an isomorphism test.
- The constructed 35-vertex hidden-answer controls in [42456135866](https://github.com/teddyli18000/web-ingest/actions/runs/42456135866) both returned SAT, independently recounted as valid: 247 edges in 17.748 seconds, 248 edges in 70.672 seconds. This establishes **construction ability** for the balanced split and is the relevant calibration benchmark.
- Cross-parent 35 synthesis and immediate extension are running in [42456461164](https://github.com/teddyli18000/web-ingest/actions/runs/42456461164), twelve seeded fusions. The necessary test for progress is a previously unseen 35-point structure or, decisively, a verified 36-vertex graph. An UNSAT fixed-half pair is not a global nonexistence claim.
- When a valid 36-point candidate is output, rerun the independent full-matrix K4/I6 test and the live Few Shots verifier, then commit and submit the exact certificate per Few Shots rules. These workflows retain candidates as GitHub Action artifacts for 14 days.


### 2026-11-07 late follow-up — solver timeout audit and mutable halves

A reproducibility issue was detected by reading the live GitHub Actions logs for [42456461164](https://github.com/teddyli18000/web-ingest/actions/runs/42456461164): \`pysat.solvers.Cadical195.interrupt()\` raises \`NotImplementedError: Limited solve is currently unsupported by CaDiCaL.\` The \`threading.Timer\` in \`independent_halves_cadical.py\` therefore did **not** enforce the advertised 240-second per-instance bound; one pair ran ~665 seconds and returned UNSAT. The finished UNSAT status applies only to that fixed pair, but elapsed times are not bounded by the script parameter. Treat still-running jobs as unknown; do not infer they are UNSAT. PySAT docs: https://pysathq.github.io/docs/api/solvers.html

**New constructive representation:** \`adaptive_halves_cadical.py\` (despite the retained historical file name) now uses **Glucose4**, which supports assumption cores, \`solve_limited\`, and \`interrupt\`. It does not freeze the two 18-vertex parent cores as immutable. Every one of the 630 graph edges is a variable; parent-internal edges are initially protected only by SAT assumptions. When the Ramsey constraints plus these assumptions become UNSAT, extract a core of incompatible fixed edges, relax a small batch of these assumptions, and continue solving. Ramsey clauses are generated lazily from actual violating K4 and I6 sets. The mathematical degree restrictions \`n-25 <= deg <= 17\` are encoded exactly (35: 10..17; 36: 11..17). This permits *both* parent interiors to change, without specifying a Hamming radius around either graph.

- Initial (superseded, incorrect timeout engine) Action: https://github.com/teddyli18000/web-ingest/actions/runs/42457230557
- Corrected Glucose4 job with solver self-test, independent defect recount, and official Few Shots verification if a 36-point witness is found: https://github.com/teddyli18000/web-ingest/actions/runs/42457396915
- The source was checked against the PySAT solver API and the stand-alone bitset recount on the 35-point baseline and 36-point retained 14-defect graph. **No construction result is claimed until the new Action actually completes.**

Do not report a solved 35-point positive-control instance as a new Ramsey bound. The scoring target remains a verified 36-point zero-defect certificate; a genuine sub-14 defect candidate is a lesser but directly measurable improvement.
