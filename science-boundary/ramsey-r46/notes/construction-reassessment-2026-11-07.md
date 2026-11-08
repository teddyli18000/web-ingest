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


### 2026-11-08 final audit of four workflows

Read GitHub Actions' actual final run/job states and successful-job logs (not merely green job badges). All four campaigns are **finished**:

| run | conclusion | completed useful outcomes |
|---|---|---|
| [42456135866](https://github.com/teddyli18000/web-ingest/actions/runs/42456135866) | cancelled (2 shards cancelled) | 35-point controls seeds 1,2: SAT and independent K4=I6=0 (247 and 248 edges); 36-point fusion seeds 11–14: UNSAT for each *specified frozen pair* |
| [42456264481](https://github.com/teddyli18000/web-ingest/actions/runs/42456264481) | cancelled (2 shards cancelled) | 36-point overlap seeds 21,22,24,25,26,27: UNSAT for each *specified frozen pair* |
| [42456461164](https://github.com/teddyli18000/web-ingest/actions/runs/42456461164) | cancelled (6 shards cancelled) | 35-point cross-parent fusion seeds 102,104,105,106,108,112: UNSAT for each *specified frozen pair* |
| [42457396915](https://github.com/teddyli18000/web-ingest/actions/runs/42457396915) | success (all 5 shards) | Glucose4 interface self-test passed; control35 seed31: 209 defects at timeout; 36-point fusion seeds41,42 and overlap seeds45,46: timeout UNKNOWN, no improved candidate |

**Important correction to the proposed algorithm:** The four completed 36-point Glucose4 runs generated 10,526–11,069 lazy Ramsey clauses, examined 28–31 SAT models each, and timed out at ~240 seconds. In all four, \`fixed_edges_remaining=306\` equals \`original_fixed_edges=306\`; **zero UNSAT assumption cores were reached and zero parent-internal edges were released**. Thus the *intended* core-guided mutation was not exercised at all. The method behaved as frozen-half synthesis during these runs. The 35-point control in the same engine also failed to reconstruct a valid graph (209 defects after 150 seconds), unlike the separate CaDiCaL fixed-half controls. This is evidence of insufficient convergence for this formulation, not of a Ramsey obstruction.

The 36-point Glucose4 summaries all print \`best_defects=14\`, but this is an **initialized incumbent threshold** (\`best=14 if n==36\`), **not a discovered 14-defect graph**. No \`IMPROVED\` line, \`best-nearmiss.json\`, or \`certificate.json\` was produced in any of those four 36-point shards. Their artifacts contain only the summary. The 35-point Glucose4 artifact does contain a near-miss; its 209-defect result was independently recounted by the workflow. No new 36-point candidate exists in these runs to independently recount; the retained old 14-defect candidate is the unchanged incumbent.

**Research decision:** Do not present this as successful adaptive core relaxation, and do not repeat it at higher seeds or longer timeout. A next experiment would need an *explicit* relaxation mechanism that can activate before the full frozen-core SAT search proves UNSAT, e.g. an optimization over selected intra-core edges with a calibrated 35-point positive control. The present four-workflow campaign is closed with **no verified sub-14 result and no 36-point certificate**. Existing baseline and prior 35-point positive controls remain intact.


### 2026-11-08: proactive witness-driven repair

The first corrected Glucose4 campaign [42457396915](https://github.com/teddyli18000/web-ingest/actions/runs/42457396915) is complete. Five of five jobs exited successfully without a 36-point witness. The four n=36 cases ended UNKNOWN after ~240 seconds with all **306** interior-edge assumptions still fixed, around 28–31 SAT models each and ~10,500–11,000 learned Ramsey clauses. The n=35 positive-control case returned best 209 defects (69 K4, 140 I6), also timed out. This experiment therefore *never actually exercised the proposed edge-unfreezing mechanism*; the solver did not prove UNSAT within the budget and hence never produced a conflict core. A green workflow was not a success at the construction goal.

Reformulation committed: after every fourth incomplete SAT model, proactively release up to five of the remaining parent-internal edges most involved in newly observed K4/I6 violations, regardless of whether the solver has reached UNSAT. This turns the frozen parent halves into progressively mutable templates and directly addresses the failure mode above. Source: \`adaptive_halves_cadical.py\`, commit \`822c073\`. Fresh five-shard controlled experiment: [42499813332](https://github.com/teddyli18000/web-ingest/actions/runs/42499813332), workflow \`temp-ramsey-r46-proactive-repair.yml\`. It includes two kinds of 36-point parents and a 35-point hidden-answer control. The actual result must be read from its final logs; at the time of writing this note the new run is queued. A 36-point candidate must still be independently recounted and passed through the authoritative Few Shots verifier before any record claim.
