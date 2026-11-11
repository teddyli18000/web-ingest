# p003 construction-first status — 2026-11-11

## Goal and exact incumbent

Build a valid 36-vertex graph with K4=0 and I6=0. Public bound checked 2026-11-11: 36 ≤ R(4,6) ≤ 40. No zero-defect witness has been constructed or submitted.

Three committed 36-vertex **near misses**, each independently fully recounted, have the **same current best score of 12**:
- \`results/compound-repair-36-12-defects.json\`: 260 edges, 12 K4, 0 I6.
- \`results/neutral-network-36-12-defects-259edges.json\`: 259 edges, 12 K4, 0 I6.
- \`results/neutral-network-36-12-defects-257edges.json\`: 257 edges, 12 K4, 0 I6.

Distinct edge counts prove these three graphs nonisomorphic. They are still near misses, not valid Ramsey witnesses.

## Audit of previous directed construction attempts

- [42857315597](https://github.com/teddyli18000/web-ingest/actions/runs/42857315597) **failed before SAT**: all twelve linkage jobs raised \`NameError\` in \`linked_conflict_sat.py\`, referencing undefined variable \`e\` in the K4-cover ranking lambda. They supplied **no negative evidence about the selected SAT neighborhoods**.
- Fixed the name bug. Added an explicit pinned-parent score-12 control test. All three controls passed in [43027098984](https://github.com/teddyli18000/web-ingest/actions/runs/43027098984), each establishing exact SAT score consistency on its source 257/259/260-edge near miss.
- The repaired linked-edge campaign [43027504479](https://github.com/teddyli18000/web-ingest/actions/runs/43027504479) successfully tested 12 targeted edge pools (44, 63, 83, 105 variables). All returned UNSAT for **that frozen non-variable edge set** with exact target K4+I6≤11 and hard 11–17 degree restrictions. No candidate improvement.
- **Modeling reassessment:** Degree 11–17 is a necessary constraint for a *perfect* 36-vertex Ramsey graph, but **not** for a 36-vertex graph that still contains 11 forbidden subsets. Enforcing it as hard for the intermediate best-near-miss target restricts the construction search unnecessarily. A second run [43028094813](https://github.com/teddyli18000/web-ingest/actions/runs/43028094813) removed the hard near-miss degree bounds. All 12 frozen linked-edge pools still returned UNSAT (0.5–15 seconds). This does *not* prove that any unrestricted 11-defect graph is impossible.
- Four independent locally compiled C++ bitboard cascade runs from the retained 260-edge near miss each performed roughly 234–236k macro iterations in 75 seconds, enforcing exact K4/I6 delta arithmetic and verifying improvements by complete recount. They did not beat 12. This is additional evidence of a fixed graph-coordinate plateau, not a global exclusion. Local scratch code and logs are under \`/mnt/data/ramsey003/fast_cascade.cpp\` and \`fast_trials/\`; the durable constructively distinct approaches are described here and in previous notes.

## New constructive mechanism: counterexample-guided SAT with active edge release

\`core_guided_defect_cascade.py\` implements a qualitatively different search interface.

1. Begin with all 630 edges as Boolean SAT variables, initially frozen to one of the three verified 12-defect parents using **assumptions**, not permanent clauses.
2. Encode a global **exact bound K4 + I6 ≤ 11** over known forbidden 4/6-vertex sets via penalty literals and a cardinality network. Do **not** enforce degree restrictions for approximate candidates.
3. If UNSAT under the frozen-edge assumptions, obtain a SAT **unsatisfiable core** and actively unfreeze selected original edges. This selects the repair interface from actual solver conflicts instead of prescribing a fixed 44–105-edge neighborhood.
4. If SAT finds a complete candidate but its independent full-graph K4/I6 count exceeds 11, add those new forbidden sets as counterexamples and reconstruct the SAT model. Repeat; keep structurally relevant search assumptions.
5. If a complete graph has ≤11 forbidden sets, independently recount and freeze its exact adjacency. A zero-defect witness would then be verified through Few Shots' authoritative verifier.

The approach is falsifiable on a known-answer control: frozen 257-edge near miss, target=12, 12 starting witnessed K4 constraints. [43028884433](https://github.com/teddyli18000/web-ingest/actions/runs/43028884433) **passed this control**: first SAT solve found a complete score-12 model with zero released edges. Six 11-target searches from independent parents/seeds were then launched in the same workflow. **Inspect the final run summary/artifacts before claiming a search result.**

The critical constructive signal is an observed sequence of UNSAT assumption cores, released edges, SAT candidate graphs, and new K4/I6 witnesses—not merely repeated UNSAT in fixed subspaces.

## Next

Check [43028884433](https://github.com/teddyli18000/web-ingest/actions/runs/43028884433). If the new mechanism remains unable to produce good complete candidates after releasing many edges, reformulate its branching/constraint interface and use actual witnessed search states as evidence. Preserve improvements only when independent complete recount verifies them; submit to Few Shots if and only if score becomes zero.

## Primary sources

- Exoo (2012), https://doi.org/10.37236/2102
- Radziszowski, *Small Ramsey Numbers* (2026 revision), https://www.cs.rit.edu/~spr/ElJC/sur.pdf
- Few Shots p003, https://github.com/few-shots/few-shots/tree/main/problems/p003-ramsey-r46
