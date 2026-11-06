# p003 takeover: low-interface reformulation (2026-11-06)

## Confirmed handoff state

- Few Shots `p003` still scores 35 (no merged shots); a score-36 graph is required.
- The current workspace has post-audit exclusions of all 36-vertex graphs with at most 219 edges; these do not prove a new bound.
- At 220 edges, within the `n11=6` layer, only `seq2 = 11^6 12^17 13^12 14` remains open. All other degree-11-count layers at 220 edges are not globally eliminated.
- The existing `m220_n11_6_seq2_structural_verify.py` leaves eight class matrices (six with low boundary R=22, two with R=24). Do not treat this as a full exclusion.
- Earlier row-CSP claims relying on withdrawn `tf()` logic are not valid evidence.

## New independently checkable small-interface observation

The two certified six-low subgraphs are `Ep~o` (R=22) and `EznW` (R=24). Decode graph6 in upper-triangle *column-major* order.

For every choice of two low neighbors of a degree-12 middle vertex, its remaining four lows have independence number exactly two (15/15 choices, for both low graphs). For choices of three low neighbors, the other three lows have independence number two in 14/20 cases (R=22) or 12/20 cases (R=24), and one in 6/20 or 8/20 cases respectively. These are small combinatorial facts and do not exclude a graph.

Proof: exhaustive inspection of at most 20 subsets of the explicit six-vertex graphs. The low graphs have independence number two; every induced four-vertex subgraph has a nonedge because neither has a 4-clique.

Use this to build **one joint interface model**, not independently optimized vertex neighborhoods: for each of 17 degree-12 middle vertices, select a low-neighbor subset L, a degree-13 neighbor count a, and a degree-14 flag b. The necessary constraints are

- `2 <= |L| <= 6`, `0 <= a <= 12`, `b in {0,1}`, and `|L|+a+b <= 12`;
- `S(m) = 144+a+2b-|L| <= 147` (independently certified no-lucky-d12 bound);
- If the low nonneighbors contain an independent pair, `a+b >= 5`, since nine nonneighbors among the 13 high vertices would contain an independent triple by `R(4,3)=9`, giving an independent six-set with the pair and m;
- For `|L|=2`, the existing stronger result is `a=5,b=0,S=147`.

Jointly enforce all six low-column degrees, total middle-to-high class edge counts and the specific surviving class matrices. Next, rather than a complete general 36-vertex SAT, synthesize the high 13-vertex subgraph, its middle interface, and middle-middle edges **together**. Evaluate constructive candidates by independently recounting K4 and I6 defects and by exact verifier if zero defects.

The observation does **not** prove new impossibility; this direction seeks a construction, while keeping the narrowing results as search priors rather than equating exclusion with success.

## Verification and sources

- Local six-vertex subset enumeration independently recomputed on 2026-11-06.
- Repository's authoritative structural script: `m220_n11_6_seq2_structural_verify.py` and result `results/m220-n11-6-seq2-structural-post-audit.json`.
- Few Shots: https://github.com/few-shots/few-shots/tree/main/problems/p003-ramsey-r46
- Radziszowski, *Small Ramsey Numbers*, revision 18 (2026-04-24), https://www.cs.rit.edu/~spr/ElJC/sur.pdf

## Next executable step

Implement a tiny deterministic enumerator of low-middle incidence row types and solve the eight exact-class aggregate problems first; retain only if it creates a useful reduction or a genuinely different constructive candidate family. Compare candidate quality by verified defect counts, not only by number of excluded class matrices.
