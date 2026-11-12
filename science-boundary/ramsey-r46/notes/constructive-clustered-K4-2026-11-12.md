# p003 constructive pivot: clustered forbidden motifs (2026-11-12)

## Aim and current score

Construct a 36-vertex graph with **zero K4 and zero independent six-sets**, to prove \(R(4,6)\ge37\). No such graph has been produced, and **12 total forbidden subsets** remains the best verified *near-miss* count.

The public bound was checked against the October 2026 Ramsey record page and the April 2026 revision of Radziszowski's survey: **36 ≤ R(4,6) ≤ 40**. A valid 36-point certificate would improve that lower bound. Sources: https://cairn-commons.com/problems/ramsey-r46 and https://www.cs.rit.edu/~spr/ElJC/sur.pdf.

## Strong evidence about the 12-defect attraction basin

Run [43239920115](https://github.com/teddyli18000/web-ingest/actions/runs/43239920115) took **all 37 distinct published Exoo 35-vertex graph6 parents** and independently optimized their 36-point one-vertex soft extension, followed by unrestricted six-step-to-fifteen-step conflict-cascade repairs. The positive control passed, and all 37 post-repair graphs were independently recounted. **27 of 37** outputs had exactly **12 K4 and zero I6**; the others ranged from 14 to 17 defects. An independent NetworkX VF2 graph-isomorphism comparison of the 37 retained output matrices gave **33 distinct isomorphism classes**. Thus the 12-valued plateau does not consist solely of relabelled copies.

Every one of those 27 zero-I6, 12-K4 graphs shared two striking properties:
- Exactly **four degree-16 vertices**.
- Every edge belongs to at most **two K4**, and the smallest collection of red edges meeting all 12 K4 has size **seven**. The 7-edge hitting set value was checked by independent subset-cover dynamic programming over the exact K4 witness lists for all 27.

A separate independent C++ annealer starting from twelve **fully random 36-point graphs, with no inherited Exoo parent structure**, reached the same 12-K4/0-I6 level in approximately 12 seconds and its output was independently identified as isomorphic to output 2 from the Exoo-parent campaign. A separate Pareto-weighted local search from all published-parent-derived outputs reached the same score12; no score11.

These are evidence of a structurally persistent optimization attractor, **not** a global lower bound on the forbidden subset count.

## New constructive representation: concentrate K4 conflicts before surgery

Instead of making K4s individually disappear, search for a *different structure of their intersections*. If many K4s share an edge, a small number of coordinated edge deletions can attack them together. This is a change in search objective and interface, not another fixed-core exclusion.

The C++ constructor uses incremental exact K4/I6 move deltas and an auxiliary edge-overlap reward:
\[
 \operatorname{overlap}(G)=\sum_{uv \in E(G)}\max\{0,\,\#K_4(uv)-1\},
 \qquad E_{\lambda}(G)=\#K_4+\#I_6-\lambda\operatorname{overlap}(G).
\]
The overlap term is used for exploration only. Full graph defect count remains the true result metric.

**First independently validated clustered parent**:
- File: \`results/clustered-36-14-defects-mincover5.g6\`
- 36 vertices, **264 edges, 12 K4, 2 I6**, total 14 defects. It is **not** a new Ramsey record or even a better near miss.
- **Maximum K4s sharing one edge = 6** (vs. at most 2 in the old 12-defect family).
- **Minimum number of red edges meeting all 12 K4 = 5** (vs. 7). There are exactly **456** distinct five-edge covers.
- Deleting such a five-edge cover eliminates all red K4, and the best of those 456 deletions creates **67 independent six-sets**.
- Independent verifier: \`verify_clustered_parent.py\`. Its entire result was rerun and confirmed in [43252059540](https://github.com/teddyli18000/web-ingest/actions/runs/43252059540).

This establishes **constructive structural diversification** across the old 12-valued plateau, but not a defect-score breakthrough.

### What failed within the new representation

A local direct test from this clustered graph after all 456 five-edge K4 covers used a randomized greedy *joint I6-hitting red addition* strategy. In 34,581 cover-and-repair attempts (34,574 completed to I6=0), **none produced total defects ≤14**. This is evidence about that greedy repair policy, not proof that no successful collective repair exists. A 17-second full Pareto anneal from this clustered parent also failed to improve its score14. Another path-relinking/crossover probe among 249 aligned pairs of the 37 candidate graphs evaluated roughly 144,240 path/crossover moves and did not beat score12. Further repetition without a qualitative change is not justified.

## Active construction, verification and next step

New reusable C++ code: \`clustered_k4_construct.cpp\`, exact edge-flip delta with overlap, multiple high-quality parents, and an archive of low-defect *structurally distinct* graphs. Eight independent campaigns with different overlap reward weights: [43252453863](https://github.com/teddyli18000/web-ingest/actions/runs/43252453863). Inputs: the verified 257/259/260/264-edge 12-defect parents **and** the new clustered score14 parent. All emitted candidates receive an independent full K4/I6 recount; a zero-defect candidate is passed through the Few Shots verifier.

**Decision rule:** Retain a score ≤11 only after full independent recount; retain a clustered intermediate if it materially lowers the simultaneous K4 edge cover (from five to four or less) or yields a new composition of near-optimal conflicts. Do not optimize purely for enlarged overlap indefinitely: if the candidate score or minimum cover ceases to improve, return to jointly synthesizing a new structural family.

## Exact reproducibility

Run:

\`\`\`bash
python3 science-boundary/ramsey-r46/verify_clustered_parent.py \
 --g6 science-boundary/ramsey-r46/results/clustered-36-14-defects-mincover5.g6
\`\`\`

The verifier reconstructs the complete graph from graph6, independently enumerates all K4 and I6, checks all edge-set covers of sizes 1–5, and tests every 5-edge cover by physically removing the selected edges and recounting forbidden sets. It makes no solver assumptions and is separate from the constructor.
