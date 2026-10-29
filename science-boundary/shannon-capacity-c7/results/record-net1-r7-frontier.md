# C7^10 record-seed net+1 radius-7 frontier

Status: active. No Few Shots-verified score above 134,753 has been found.

This file tracks the exact unrestricted ten-dimensional search starting from the public Few Shots 134,753-point baseline. Statements below are local/exchange results around that seed, not a proof of the global value of `alpha(C7^10)`.

## Preconditions: exact net+1 closure through radius 6

The public baseline has been replayed with the Few Shots verifier; canonical hash:

`650b05567deb26a339a788674dce5a36cba3beaeafe2c6daae631bed481b0df8`.

Arbitrary ten-dimensional remove-`r` / add-`r+1` improvements are exactly negative for every `r <= 6`. Radius 6 was partitioned by the maximum blocker-support size of a selected addition (`2,3,4,5,6`); every stratum completed with no candidate and therefore no breakthrough verifier invocation.

The direct maximum-support-6 result is:

```json
{"kind":"none","method":"exact-unrestricted-net1-r6-direct-support","baseline_size":134753,"coverage0":0,"lower_candidates":5831591,"coverage6_candidates":3197204,"lower_support_groups":5663965,"coverage6_groups":3003919,"eligible_owner6":262690,"tested_owner6":262690,"max_supported_pool":26}
```

The max-support-5, -4, -3, and -2 connected-support stages were independently sharded and completed with no witness. See `results/record-net1-frontier.md` and the reusable `search_net2_r6_*` / net1-retarget code for the lower strata.

### Consequence for radius 7

Any hypothetical remove-7/add-8 witness must have a connected selected blocker-support hypergraph on its seven removed owners. If the selected support hypergraph were disconnected, distributing eight additions over seven owners would force one connected component to contain more additions than owners, yielding a smaller-radius net+1 witness, contradicting exact closure through radius 6.

This connectivity fact is the basis of all radius-7 support-extension enumerations below.

## Maximum support 7: exact negative

The direct support-7 stratum has completed exactly with no witness.

- workflow head: `f6f6bb196d846d2f45fd4f21263d00106cfe1b79`
- run: `40733405252`
- result: success; breakthrough verifier skipped because no candidate was produced.

## Maximum support 6: active exact search

Reusable solver: `code/search_net1_r7_c6_anchor.cpp`.

For an observed six-owner support anchor `A`, connectedness forces the seventh owner to be joined to `A` by an actual observed support. The solver enumerates those real co-owner neighbors, canonicalizes each seven-owner union by its least contained observed c6 support, reconstructs the complete outside pool `P_6(U)`, and exactly decides whether it contains eight pairwise nonconfusable vertices.

Workflow:

- head: `a2162a4fd7d0e36b438610b37e48739a13a0a992`
- run: `40795963628`
- 32 shards.

The first completed shard, shard 13, was exactly negative:

```json
{"kind":"none","method":"exact-net1-r7-maxsupport6","baseline_size":134753,"shard":13,"shards":32,"lower_candidates":9028795,"support_groups":8667884,"coverage6_groups":3003919,"generated_owner7":63338379,"canonical_owner7":63300157,"eligible_owner7":5755843,"tested_owner7":5755843,"max_supported_pool":35,"max_anchor_neighbor_owners":1573}
```

It took about 7m07s wall time and peaked at about 8.57 GiB RSS on a hosted runner. The Few Shots breakthrough verifier was skipped because no candidate was produced. Remaining shards were queued at the time of this note.

## Maximum support 5: active support-extension exact search

Reusable solver: `code/search_net1_r7_c5_extensions.cpp`.

An initial mathematically complete two-section expansion (`A -> x -> y`) was rejected as an engineering formulation after the radius-6 c5 census showed up to 876 co-owner neighbors and about 119.6 million generated paths in only one eighth of the anchor set.

The durable solver was therefore replaced by a stricter but still complete real-support crossing formulation. From a c5 anchor, the two remaining owners can be introduced only as:

- one real `E2` crossing introducing both owners; or
- two consecutive real `E1` crossings.

Every final seven-owner set is canonicalized by its least contained observed c5 support, the complete `P_5(U)` is reconstructed, and an independent 8-set is decided exactly.

Current workflow:

- solver commit: `9bf3474edb832bbc28b5b0a609b289ddbdf2afbe`
- workflow head: `31d9a14473bf8eae61920dd91b3c5aeaade74378`
- run: `40796274142`
- 8 shards; queued at the time of this note.

The older broad 32-shard run `40795866852` is superseded scientifically by the real-support-extension implementation and should not be used as the preferred formulation.

## Maximum support 4: solver ready

Reusable solver: `code/search_net1_r7_c4_extensions.cpp`.

Starting from a c4 anchor, three owners remain. Real support crossings can introduce one, two, or three new owners. Up to ordering, all connected introduction patterns are covered by:

- `E3`;
- `E2 -> E1`;
- `E1 -> E2`;
- `E1 -> E1 -> E1`.

The solver canonicalizes the final owner set, reconstructs complete `P_4(U)`, and exactly tests for eight compatible additions. Code exists but had not yet been put on a hosted runner when this note was written.

## Maximum support 3: solver ready

Reusable solver: `code/search_net1_r7_c3_connected.cpp`.

Rather than manually enumerate all compositions of four new owners by one- and two-owner crossings, this solver performs an owner-set BFS from an exact c3 anchor using only real observed `E1` and `E2` crossings. Partial owner sets are deduplicated. At size seven the solver canonicalizes on the least contained c3 anchor, reconstructs complete `P_3(U)`, and exactly tests for an independent 8-set.

Code exists but had not yet been put on a hosted runner when this note was written.

## Maximum support 2: solver ready

Reusable solver: `code/search_net1_r7_c2_connected.cpp`.

With support sizes only one and two, selected size-2 supports must contain a connected graph spanning all seven removed owners. The solver enumerates all connected seven-owner sets in the sparse observed support-2 owner graph, canonicalizes by the least support-2 edge, reconstructs complete `P_2(U)`, and exactly tests for eight compatible additions.

Code exists but had not yet been put on a hosted runner when this note was written.

## Equal-score alternative basins

Two independently verified 134,753-point seeds have also been exactly screened through radius 5 for arbitrary net+1 exchanges:

- BPZ/Tan `J+`, verifier hash `ac593f1040cef29621bfe705305359360ca58cb47fa1482ae810a51ca9b16b95`;
- neutral2 rank-3 exact MaxSAT tie, verifier hash `3b3a3a6c08418d604c530e3dccd188e8b4beabf986016af08040e19b6fd59e81`.

Both are negative through unrestricted radius 5. They remain useful alternative basins if the public baseline radius-7 closure becomes saturated.

## Next actions

1. Finish all 32 max-support-6 shards and all 8 real-support max-support-5 shards; promote them to exact negative evidence only when every completion guard succeeds.
2. Run/compile-test max-support 4, then 3, then 2 using the prepared durable solvers.
3. If all six radius-7 strata (`7,6,5,4,3,2`) are negative, record a complete exact net+1 radius-7 closure around the public baseline and change formulation rather than blindly extending the same local radius search.
4. Any candidate must be materialized to 134,754 points and accepted by the upstream Few Shots verifier before it is called a breakthrough.
