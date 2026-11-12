# Mondrian dissection of the 87×87 square (p016)

## Question
Find a complete tiling of the 87×87 square by pairwise noncongruent integer-sided axis-aligned rectangles with area defect strictly below 18.

## Current state (2026-11-12)
- Few Shots current merged record: **18**; shot `zyaoii/mondrian87-single-bridge-18`, PR #62, 19 rectangles, area range [390,408]. Goal ≤17.
- The older OEIS/Muessig certificate has defect 22 and 13 rectangles.
- An independent cell-occupancy recomputation of the PR #62 certificate found exact cover, distinct unordered shapes, area sum 7569, area multiset `[390,390,390,391,392,392,396,396,396,396,400,400,403,405,405,405,406,408,408]` and defect 18. The official Few Shots CI also verified the merged shot at 18.
- No improved candidate has yet been established.
- Tested all **58,008** moves altering one/two independent edge-coordinate classes by ±1 or ±2, three classes by ±1, or four classes by ±1. Of these, **22,248** produced valid tilings; best defect remained **18**. See [topology_probe.py](topology_probe.py). This excludes only that precise neighborhood around the 19-piece incumbent.

## Record mechanism
The successful construction has a vertical line x=34 crossing only one rectangle, (8,0,66,6); independently fill notched left/right regions, deduplicate complete region fillings by shape set, then match complementary halves. This structural restriction is a search heuristic, not a mathematical requirement.

## Candidate research directions
1. **Topology-coordinate optimization**: represent a dissection by equivalence classes of coincident edge coordinates and optimize them jointly as integers, holding topology fixed initially. Area is bilinear in coordinate differences; distinguish distinct shapes.
2. **Joint topology moves**: search local multi-rectangle retessellations without keeping the bridge, rather than moving single edges.
3. **Unrestricted exact cover / CP-SAT**: enumerate near-equal-area rectangles for each admissible area window and solve nonoverlap, shape uniqueness and complete coverage together; use candidate recipes/area-sum pruning.
4. **Multiple-separator constructions** and alternate rectangle counts, not only the 19-rectangle incumbent.

## Important arithmetic
For k rectangles, area average is 7569/k; for k=19 it is 398.368421…. All rectangles in any defect ≤17 19-piece candidate must lie in an interval of length ≤17 containing this average. Shape selection alone does not guarantee placement.

## Sources
- [Few Shots problem and verifier](https://github.com/few-shots/few-shots/tree/main/problems/p016-mondrian-87)
- [Merged PR #62](https://github.com/few-shots/few-shots/pull/62)
- [Bassen (2016), Further Insight into the Mondrian Art Problem](https://mathpickle.com/wp-content/uploads/2016/12/Bassen-Further-Insight-into-the-Mondrian-Art-Problem.pdf)
- [García-Colín et al., New results for the Mondrian art problem (2021)](https://doi.org/10.1016/j.dam.2021.01.016)
- [Garrison, Seiler, Semchankau (2026), New Upper bounds on the Mondrian Art Problem](https://arxiv.org/abs/2609.01998)

## Work log
- 2026-11-12: Read workspace instructions, Few Shots rules, problem, verifier and record chain. Synced PR #62 and reconstructed the independently verified certificate statistics. Research directions documented above.

- 2026-11-12: Executed exhaustive small edge-coordinate move enumeration around the record construction: 18 independent movable classes (9 horizontal-coordinate and 9 vertical-coordinate), 58,008 enumerated moves, 22,248 valid coverings with unique shapes, best 18. Coordinates and all 7,569 cells independently rechecked for each candidate.

## Next steps
Implement topology-coordinate model and test neighborhood improvements on the 18-defect seed; independently confirm every generated certificate using Few Shots verifier. If candidate quality plateaus, switch to topology-changing search and exact-cover representations.
