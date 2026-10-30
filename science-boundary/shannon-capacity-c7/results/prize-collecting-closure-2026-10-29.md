# Prize-collecting closures around the pinned BPZ/Tan C7 record

Status: **no verifier-valid score above 134,753**.  This note records exact exclusions obtained after the core-release search was reformulated to pay directly for peripheral losses and baseline blockers.

Pinned five-dimensional source: `tandonravi/C7-Shannon-Capacity-Heterogeneous-Recursion` commit `c753408492dde92a239708986d16c15dbf6c3235`.  The public ten-dimensional target remains the Few Shots p004 baseline 134,753.

## Killer colors of the raw k=5/k=6 +1 support defects

`code/bpz_support_defect_killer_audit.py` independently replayed supports against the pinned `B=I0\R` and the eight private pairs.

- The unique k=5 defect has six additions: five kill five **distinct** private-pair colors `{0,4,5,6,7}` and one is killer-free.
- k6 defect 0 has four distinct killer colors `{0,4,5,6}` and three killer-free additions.
- k6 defects 1,2,3 each have five distinct killer colors `{0,4,5,6,7}` and two killer-free additions.

Thus there is no same-color loss compression *inside* any one raw +1 defect.  Any compression has to come from repeating a killer color across a nontrivial projection in the other coordinate.

Reproduction: GitHub Actions run `40988154181`, job `123843919517`; workflow completed successfully.

## Exact arbitrary-row amplification closure

`code/bpz_amplify_row_defects.py` tested all five known raw +1 defects against all 18 terminal optima and both row/column orientations: 180 scenarios.

For a fixed scenario and arbitrary row set `A subset B`, it replaces `A x C` by `A x Y`.  The exact net increment is

`|A| - | union_{a in A} L_a |`,

where `L_a` is the set of existing terminal-periphery points lost by row `a`.  Maximization over all `2^359` row subsets is a maximum-weight closure problem and was solved exactly by one s-t min cut per scenario.

Result: **maximum delta = 0 in all 180 scenarios**.  The best solution selects no rows.  Hence repeatedly applying one of the known raw +1 defects cannot amortize its peripheral losses into a ten-dimensional improvement for any pinned terminal optimum.

Reproduction: run `40988459478`, job `123844875581`; workflow success, Few Shots verifier skipped because no positive candidate.  Runtime about 22.4 s, peak RSS about 354 MB.

## Nonperfect four-owner x raw-defect rectangle prize bound

`code/bpz_nonperfect4_rawdefect_prize.py` rebuilt all 16,166 connected four-owner support sets and independently re-identified exactly 68 nonperfect sets.  It crossed each of those 68 sets with the unique k=5 and four k=6 raw +1 defects, for 340 rectangles.

For each rectangle it solved an exact weighted MaxSAT upper-bound problem:

`weak prize = selected unlocked vertices - activated oriented killer colors - deleted core cells`.

Charging only one unit per activated oriented killer color is deliberately optimistic: the true projection-independence peripheral penalty can only be at least this large.  Therefore a nonpositive weak prize rigorously excludes that rectangle (conditional on the pinned `alpha(C7^5)<=367` argument used by the core-release analysis).

Exact result:

- 272 rectangles have weak gain `-1`;
- 68 rectangles have weak gain `0`;
- **no rectangle has positive weak gain**;
- maximum strong penalty evaluated on the weak-optimum witnesses gives strong witness gain `-12`.

Thus all 340 `nonperfect-4 x raw-(k5/k6)` rectangles are closed before a full periphery solve is even necessary.

Reproduction: run `40988481099`, job `123844941480`; workflow success.  The script's self-checks reproduced 16,166 connected four-owner sets and exactly 68 nonperfect sets.  Runtime about 184 s on the acquired runner.

## Exact prize MaxSAT for cross-incompatible omitted terminal blocks

Earlier Hall searches exactly handled omitted product blocks whose complete candidate union is cross-independent.  `code/bpz_two_block_prize_maxsat.py` removes that restriction.

For a pair of omitted terminal blocks with candidate union `C`, it solves exactly

`max_{S independent subset C} |S| - |N_I(S)|`,

where `I` is the 134,753-point record and `N_I(S)` is the set of record points that must be deleted.  Candidate-conflict edges are hard clauses; candidate selections have unit reward; each touched baseline blocker has unit cost.  This includes arbitrary exchange radius, cross-block conflicts, and blocker sharing.

The first packed sweep covered every genuinely cross-incompatible block pair whose union had at most 6,000 candidates:

- 168 block pairs tested;
- exact maximum gain **0**;
- one reported zero-gain optimum was the empty selection for blocks `HO` and `HV` (88 candidates, 24 cross-conflicts, 480 possible blockers).

No verifier step was triggered.

Reproduction: run `40988719150`, job `123845693259`; workflow success.  Four RC2 workers used about 340% aggregate CPU; elapsed time about 72 s; peak RSS about 435 MB.

A follow-up packed sweep raises the candidate-union cap to 30,000 so the same exact formulation covers nearly all medium-sized omitted-block pairs while retaining one long multi-core runner instead of many queued shards.

## Consequence for the next search

The following mechanisms are now poor places to spend more compute unchanged:

1. replicate one known five-dimensional +1 defect across arbitrary rows/columns;
2. pair one of those defects with any of the 68 known nonperfect four-owner support graphs in a rectangle;
3. combine small cross-incompatible terminal blocks while hoping shared blockers overcome cross-conflicts.

The active directions are instead:

- extend exact two-block prize optimization to the medium block regime (30k candidate cap, then decompose the three 100k-scale blocks rather than feed them monolithically to MaxSAT);
- enumerate higher-order support-graph types, especially nonperfect/high-alpha five-owner graphs not represented by the five raw +1 defects;
- optimize genuinely nonrectangular unions of support rectangles with owner/core cost and projection-dependent killer cost in the objective.
