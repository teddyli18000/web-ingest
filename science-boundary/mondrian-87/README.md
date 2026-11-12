# Mondrian dissection of the 87×87 square (p016)

## Question
Find a complete tiling of the 87×87 square by pairwise noncongruent integer-sided axis-aligned rectangles with area defect strictly below 18.

## Current state (2026-11-12)
- Few Shots current merged record: **18**; shot `zyaoii/mondrian87-single-bridge-18`, PR #62, 19 rectangles, area range [390,408]. Goal ≤17.
- The older OEIS/Muessig certificate has defect 22 and 13 rectangles.
- An independent cell-occupancy recomputation of the PR #62 certificate found exact cover, distinct unordered shapes, area sum 7569, area multiset `[390,390,390,391,392,392,396,396,396,396,400,400,403,405,405,405,406,408,408]` and defect 18. The official Few Shots CI also verified the merged shot at 18.
- **Best verified current score remains 18; no ≤17 certificate yet.** We now prioritize constructive complete-tiling generation and topology-changing repair, not local exclusions.
- **Constructive search actively running in GitHub Actions:** [19/20/21-rectangle run](https://github.com/teddyli18000/web-ingest/actions/runs/43242994182), [16/17/18/22/23/25-rectangle run](https://github.com/teddyli18000/web-ingest/actions/runs/43243760984). Search changes shape selections, orientations and placements jointly, with official Few Shots verification for any solution.
- Tested all **58,008** moves altering one/two independent edge-coordinate classes by ±1 or ±2, three classes by ±1, or four classes by ±1. Of these, **22,248** produced valid tilings; best defect remained **18**. See [topology_probe.py](topology_probe.py). This excludes only that precise neighborhood around the 19-piece incumbent.

## Current constructive campaigns (2026-11-12)
- **Record-topology connected repair:** [patch_repair.py](patch_repair.py) releases both 408-area tiles (for target [390,407]) or all three 390-area tiles (for [391,408]), connects those pieces through contact-graph neighborhoods, and retiles each released patch using simultaneous CP-SAT shape and placement variables. [Four jobs](https://github.com/teddyli18000/web-ingest/actions/runs/43249965520) started; results pending.
- **Global joint coordinate re-embedding:** [joint_coords.py](joint_coords.py) globally reoptimizes all 19 rectangle widths/heights together using integer coordinate variables, pairwise noncongruence, and allowed-area tables. Unlike earlier local move tests, this is not limited to small displacements. [Four jobs](https://github.com/teddyli18000/web-ingest/actions/runs/43251403522) started; results pending.
- **85→87 border surgery:** a valid public 85×85 21-piece defect-16 tiling from [HoustonWeHaveABug/MondrianPuzzle](https://github.com/HoustonWeHaveABug/MondrianPuzzle/blob/master/mondrian_achievements.txt) has exact area 7225 and unordered shapes all distinct. The added 87²−85²=344 area equals one new near-equal tile. [frame_repair.py](frame_repair.py) keeps interior tiles and reconstructs 6–19 pieces from released connected neighborhoods; [four jobs](https://github.com/teddyli18000/web-ingest/actions/runs/43248082953) completed without a ≤17 certificate. Minimal 5-border-tile surgery has a geometric bottom-row obstruction, motivating extended repair. Source is used as an algorithmic reference, not represented as a newly authored 85 result.
- **84→87 migration hypothesis:** independent published 84×84 18-piece defect-16 tiling has areas 384–400; 87²−84²=513, so a 19-piece 87 target (average 398.368) requires one new near-398 tile plus modest redistribution. Exact local boundary surgeries with mandatory release of out-of-window pieces have not yet produced a witness. Structural quality remains unproven.

## Record mechanism
The successful construction has a vertical line x=34 crossing only one rectangle, (8,0,66,6); independently fill notched left/right regions, deduplicate complete region fillings by shape set, then match complementary halves. This structural restriction is a search heuristic, not a mathematical requirement.

## Candidate research directions
1. **Topology-coordinate optimization**: represent a dissection by equivalence classes of coincident edge coordinates and optimize them jointly as integers, holding topology fixed initially. Area is bilinear in coordinate differences; distinguish distinct shapes.
2. **Joint topology moves**: search local multi-rectangle retessellations without keeping the bridge, rather than moving single edges.
3. **Unrestricted exact cover / CP-SAT**: enumerate near-equal-area rectangles for each admissible area window and solve nonoverlap, shape uniqueness and complete coverage together; use candidate recipes/area-sum pruning.
4. **Multiple-separator constructions** and alternate rectangle counts, not only the 19-rectangle incumbent.

## Constructive solver (2026-11-12)
- [cpsat_search.py](cpsat_search.py): each eligible unordered shape has at most one selected orientation; OR-Tools optional 2D intervals enforce nonoverlap, and exact total area 7569 ensures full coverage. This is a genuinely different family from the single-bridge record.
- Two one-shot CP-SAT Actions workflows evaluated 12 independent parameter shards (four CP-SAT workers per shard); LNS cases release random subsets of incumbent rectangles while simultaneously choosing replacement shapes and placements. Both six-shard CP-SAT campaigns completed with no witness. Eleven feasible parameter cases exhausted their 840-second search budget and returned UNKNOWN; the deliberately broader A=395,k=19 case was shown infeasible by model presolve. These are constructive feasibility searches, not optimality claims.\n- [frontier.cpp](frontier.cpp) is an independent unrestricted corner-first C++ exact-cover constructor with shape-unique area-sum pruning and row-gap reachability. [Seven additional constructive shards](https://github.com/teddyli18000/web-ingest/actions/runs/43245340216) cover 19–25 rectangles without fixing a separator.\n- [area_windows.py](area_windows.py) regenerates target window filters.
- A cardinality/area-sum bitset DP (local experiment) identifies feasible windows for k=19: **388–392**; k=20: **368–372**; k=21: **351–352**; k=22: **334–336**; k=23: **319–322**; k=25: **293–295**. Those ranges are necessary arithmetic conditions, not constructive solutions.
- A separate guillotine-recursion prototype produced no witness within area windows 250–650; switch to unrestricted non-guillotine topology instead of scaling this direction.

## Important arithmetic
For k rectangles, area average is 7569/k; for k=19 it is 398.368421…. All rectangles in any defect ≤17 19-piece candidate must lie in an interval of length ≤17 containing this average. Shape selection alone does not guarantee placement.

## Sources
- [Few Shots problem and verifier](https://github.com/few-shots/few-shots/tree/main/problems/p016-mondrian-87)
- [Merged PR #62](https://github.com/few-shots/few-shots/pull/62)
- [Bassen (2016), Further Insight into the Mondrian Art Problem](https://mathpickle.com/wp-content/uploads/2016/12/Bassen-Further-Insight-into-the-Mondrian-Art-Problem.pdf)
- [García-Colín et al., New results for the Mondrian art problem (2021)](https://doi.org/10.1016/j.dam.2021.01.016)
- [Garrison, Seiler, Semchankau (2026), New Upper bounds on the Mondrian Art Problem](https://arxiv.org/abs/2609.01998)

## Work log
- 2026-11-12: Independently verified public 85×85 (21 pieces, D16, areas336–352) and 84×84 (18 pieces, D16, areas384–400) complete dissections. Tested 85→87 border-patch surgery on 4 CP-SAT jobs (no candidate); switched to coordinated 19-piece patch reconstruction and global integer coordinate solving. Captured source/provenance above. The independent C++ complete-construction job batch also finished with no ≤17 candidate.

- 2026-11-12: Both CP-SAT campaigns finished; 11 valid-window runs did not construct a candidate within 840 seconds each; A=395,k19 was arithmetically infeasible. Logs are attached to the two Actions runs. Seven distinct C++ construction jobs, across k19,20,21,22,23,25, were still running as of 15:19 UTC; two had completed without a candidate. One C++ shard searches 20-30 million states per 91-second area-window budget. No lower bound on M(87) is claimed.\n- 2026-11-12: Switched from local edge exclusions to unrestricted constructive CP-SAT and 12 Actions search shards. Verified solver setup works on GitHub runner; one k=19, A=395 case exits infeasible rapidly, consistent with area-sum DP. The remaining shards were confirmed started, not yet verified successful.

- 2026-11-12: Read workspace instructions, Few Shots rules, problem, verifier and record chain. Synced PR #62 and reconstructed the independently verified certificate statistics. Research directions documented above.

- 2026-11-12: Executed exhaustive small edge-coordinate move enumeration around the record construction: 18 independent movable classes (9 horizontal-coordinate and 9 vertical-coordinate), 58,008 enumerated moves, 22,248 valid coverings with unique shapes, best 18. Coordinates and all 7,569 cells independently rechecked for each candidate.

## Next steps
- Check connected patch and joint coordinate constructive runs; preserve any exact candidate immediately. The job runs the official Few Shots verifier on candidates; independently verify locally before making a claim.
- Prefer graph/topology-changing constructive models if CP-SAT stalls; in particular, release connected patch neighborhoods and reassemble across previous rectangle contacts rather than continually varying the same coordinates.
- If a certificate scores ≤17, resync Few Shots main, prepare a compliant shot with the verifier's exact score and submit it.
