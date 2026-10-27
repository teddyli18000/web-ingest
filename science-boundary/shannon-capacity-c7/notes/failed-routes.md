# Failed and constrained routes

This file records scientifically useful negative results from the initial `temp-work/few-shots-p004/` campaign. It is intentionally a compressed memory of failure, not a transcript of every experiment.

## Exact local replacement neighborhoods

The 134,753-point baseline was checked against increasingly deep exact local replacements. No verifier-valid improvement was found for:

- direct add 1;
- remove 1 / add 2;
- remove 2 / add 3;
- remove 3 / add 4;
- remove 4 / add 5.

The first stages were implemented by an exact full-space conflict-coverage transform over all `7^10` vertices. Later stages used the resulting low-coverage owner structure to keep the search finite. These failures only rule out the searched replacement neighborhoods around this particular baseline.

## Strict ninth-port construction

The original 8-port structure suggests deleting a ninth 5D center and replacing the lost square-block mass with two new 367-fiber families. The nominal score would be 134,770 (+17).

Multiple exact formulations failed:

- fixed ninth pair;
- rewired ninth pair;
- generalized safe-endpoint SAT;
- family-port variants;
- joint R/X repair attempts.

Conclusion: requiring every intended ninth-port endpoint is too rigid. Future work should optimize net retained vertices rather than demand a complete gadget.

## Companion transforms

No breakthrough was found after probing transformations of the companion construction, including:

- translations;
- one-swap translations;
- signed coordinate permutations;
- larger automorphism families;
- automorphisms of the best neutral2 near-miss state.

These experiments make simple symmetry-equivalent companion replacements a low-priority direction.

## Alternative archived 5D parents

Archived/public alternative `C7^⊠5` parent sets and nearby swap variants were tested as inputs to the port construction. None produced a verified improvement in the explored families.

## Neutral 2-for-2 parent perturbations

Exact enumeration found 27 legal neutral 2-for-2 parent states. Only one state has enough private centers (10) to support a nine-center construction, yielding exactly 10 nine-center subsets.

Strict SAT on all ten subsets is UNSAT.

However, this route is **not dead**: its MaxSAT relaxation reaches 134,753 exactly for rank 3. Therefore only the strict all-port requirement is closed; the underlying parent state remains the current best frontier.

## Rank-3 one-swap parent neighborhood

Starting from the rank-3 neutral2 state, every legal private one-for-one parent replacement was enumerated and the port MaxSAT problem was re-solved exactly with the rank-3 nine deleted indices fixed.

There are exactly 10 such one-swap moves. Nine of them leave the exact optimum unchanged at **134,753** with 6,589 selected port vertices. The only move at the one undeleted private center (owner index 294, replacing 16388 by 16046) is worse: it reduces the safe endpoint set from 18 to 17 and the exact score to **134,703**.

So the complete legal one-swap parent neighborhood around this state does not improve the record. This closes the simplest version of “move one parent point, then re-optimize all ports”; future parent changes must either involve multiple coupled swaps, change the deleted-center set simultaneously, or be combined with square-block relaxation.

## Neutral 3-for-3 and neutral walks

An exact neutral 3-for-3 parent search and deeper sequential neutral-swap walks were implemented to look for 5D parents with at least nine useful private centers and lower H/V obstruction. They did not yield a verified 10D improvement in the completed campaign.

These searches should not simply be rerun unchanged. If revisited, they should be coupled to the final 10D objective (e.g. MaxSAT net score), because the earlier proxy objective—private-center count / overlap—can miss states that are globally better after endpoint optimization.

## Why the current next step is different

The best exact MaxSAT state ties the record at 134,753. That means the remaining gap is one 10D vertex, not a broad structural failure. Repeating transformations, strict SAT, or shallow replacement search is unlikely to be the best use of compute.

The next models should allow a small cost in the square block or parent structure and optimize the net gain in port vertices directly. A move costing one square-block vertex is worthwhile if it unlocks two or more additional compatible port vertices.
