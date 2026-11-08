# p003 constructive breakthrough: 36-point 12-defect candidate (2026-11-08)

## Verified outcome, not a new Ramsey lower bound

The best retained n=36 near miss has **12 forbidden subsets**: exactly **12 K4s and zero independent 6-sets**, with **260 edges**. This is a real construction improvement from the prior 14-defect graph (10 K4, 4 independent sixes, 263 edges). The edge-labelled Hamming distance is **29 undirected edges**. **This graph is not a valid (4,6)-graph** because twelve K4s remain. Do not submit it as a Few Shots proof.

Complete adjacency witness: \`results/compound-repair-36-12-defects.json\` (GitHub commit \`940ff8da\`).

### Independently recounted and deterministic reproduction

Source: \`compound_repair_search.py\` (commit \`03f1ab06\`). The decisive experiment uses a conflict **cascade with delayed acceptance**: choose a current forbidden K4/I6, flip an edge to destroy it, follow the dynamically generated next forbidden witness for up to six coupled repair flips, and only then decide whether to accept the whole macro move. An elite pool diversifies restarts, and exact K4/I6 deltas are cross-checked with full independent bitset recount on improvements.

Deterministic reproduction:

\`\`\`bash
python3 science-boundary/ramsey-r46/compound_repair_search.py \
  --initial science-boundary/ramsey-r46/results/algorithm22-calibration-best-14.json \
  --out /tmp/p003-repro12.json --seed 42 --depth 6 --steps 220 --seconds 15
\`\`\`

Expected progress: 14→13 at macro iteration 135, 13→12 at iteration 136. The exact 36-row adjacency is reproduced. Independently verified using direct enumeration of all \`C(36,4)=58,905\` 4-sets and \`C(36,6)=1,947,792\` 6-sets, not the search engine's incremental delta. The verification confirms 12 K4, 0 I6, 260 edges and 29 differing edges relative to the previous graph. The dedicated deterministic GitHub Action is [temp-ramsey-r46-repro12.yml](https://github.com/teddyli18000/web-ingest/actions/workflows/temp-ramsey-r46-repro12.yml). Examine the Action outcome before claiming a second-platform reproduction.

### Rooted/MaxSAT campaigns and plateau

The previous near14 root-aware fixed/partially mutable static SAT experiments [42501283478](https://github.com/teddyli18000/web-ingest/actions/runs/42501283478) and [42501739284](https://github.com/teddyli18000/web-ingest/actions/runs/42501739284) did not produce a valid n=36 graph: ten root=3 cases were UNKNOWN after about 300s, and six distinct-root cases were four UNKNOWN and two fixed-set UNSAT. The results only characterize their respective restricted search and timeout budgets. Earlier root-aware CNF formulation was validated by injecting the original exact 35-point answer ([42501506877](https://github.com/teddyli18000/web-ingest/actions/runs/42501506877)).

Locally, multiple runs of the same six-step compound repair starting from the new twelve-defect witness plateau at 12. A first-principles search-space reassessment found:

- The 12 K4 subgraphs can be hit by a coordinated seven-edge deletion, but the resulting K4-free graph gains **92 independent 6-sets**, so naive monotone K4 removal is counterproductive.
- A prototype enumerated 211 diversified eight-edge K4 covers and greedily/beam-repaired induced I6s; every run returned to 12 or worse. Freezing part of the deleted cover to prevent trivial undoing still showed no improvement in 183 attempts.
- Independent C++ edge-delta enumeration over **all 396,270 ordered two-edge flips** from the new candidate found no score below 12; adding a third flip to each of 48 lowest-score two-flip states also did not improve the score. This only excludes these *immediate move spaces*.
- Randomized eight- to ten-edge ascending-set beam searches (about 90 fully completed runs) did not find <12. This is no global exclusion. All of these methods are constrained by the current candidate's coordinate basin, and simply repeating them is not justified by evidence.

### Next constructive mechanism

\`elite12_lns_sat.py\` (commit \`22ef193\`) makes 1–6 selected vertices' incident edges jointly variable (35–195 edges), leaves the remaining graph fixed, and encodes the exact **total forbidden set count <=11** using one penalty Boolean for each possible K4 or independent six. A single cardinality budget is enforced over penalties; degree bounds 11–17 remain hard. The model allows a small number of I6s again if this reduces K4 enough, so it is not trapped on the zero-I6 manifold.

A twelve-neighborhood 11-defect construction experiment was launched as [42504776739](https://github.com/teddyli18000/web-ingest/actions/runs/42504776739). This is a direct constructive target, not an exclusion-oriented campaign. If a SAT candidate appears, the workflow independently recounts all forbidden subsets and preserves the 36×36 adjacency in an artifact. A zero-defect candidate is sent to the Few Shots official verifier.

## Research priority

The full target remains a **zero-defect 36-vertex Ramsey witness**. In the interim, improve verified candidate quality below 12. Any plateau requires broader coordinated changes (jointly varying vertex neighborhoods, grafted structures, or other representations) rather than saturating the same greedy local moves.

## Reference context

- Exoo (2012), *On the Ramsey Number R(4,6)*.
- Current public baseline: https://github.com/few-shots/few-shots/tree/main/problems/p003-ramsey-r46
- New related constructive heuristic experience: https://github.com/ypwang61/ScaleAutoResearch-Ramsey (compound drop/repair studies on other Ramsey parameters).
