# p004 constructive cross-partition anchor repair (2026-11-12)

## Objective

Construct a verifier-valid independent set of at least **134,754** in C7^⊠10. Do not confuse high-cardinality exchange or an UNSAT subfamily with a record improvement. The live Few Shots board checked 2026-11-12 still lists **134,753**.

Primary public source: Itty–Rosin–Carstensen–Reichman (2026), arXiv 2607.21517, independently reconstructed and verified 134,753 certificate; three neutral alternatives of 134,753 officially verified in Actions run 42502891420.

## New constructive representation

Unlike the prior rigid 359×359 five-dimensional square and fixed core-owner rectangles, **permute the ten coordinate positions into arbitrary 5+5 partitions**, then expose a prefix row (a five-dimensional word) and its entire five-dimensional suffix set.

Choose a **new ten-dimensional anchor point** (u,v), either from the parts of another officially valid 134,753-point solution missing in the current one or from an independent random mutation of a ten-dimensional word. Collect every incumbent prefix row containing an old point confusable with the anchor. Release all those rows jointly, together with a few neighboring rows; keep all other prefix rows fixed.

For each released prefix u, the exact permitted suffix universe consists of all 7^5 suffixes not confusable with suffixes in any *frozen* prefix row adjacent to u. A single joint binary-MILP selects new suffixes from **every permitted suffix** of every released row, enforcing all same-row and cross-row strong-product conflicts. The anchor variable is fixed to one. The objective prioritizes actual ten-dimensional point cardinality, with diverse equal-score tie-breaks. A one-point-deficit state is occasionally permitted as an intermediate, while keeping the verified 134,753 record as fallback. A new score >134,753 is independently checked and automatically passed to the Few Shots p004 verifier.

This changes the factorization interface and does not fix the original core, former end-point owners, or the old 5+5 split. The active candidate universe is still the released finite row block and is not asserted to cover the whole graph.

Reusable producer: [code/c7p004_cross_partition_anchor_repair.py](../code/c7p004_cross_partition_anchor_repair.py).

## Local proof-of-mechanism

Four published/hosted officially verified 134,753 certificates were parsed and compared. For a mixed 5+5 coordinate partition, the three alternate record-level codes contribute **4,266** currently missing high-quality ten-dimensional anchors (rather than resampling 140k mostly already-selected points). In a local pilot, anchor-constrained row MILPs on four or five prefixes produced legal equal-score transitions affecting up to **98 ten-dimensional points in a single move**. Some forced candidates require an intermediate 134,752 state, motivating the valley-crossing rule. These observations are *constructive mobility*, not a positive record.

## Hosted pilot and defect corrected

Initial [Actions run 43251407252](https://github.com/teddyli18000/web-ingest/actions/runs/43251407252): four source basins, 180 nominal iterations each; all jobs completed successfully and independently replayed 134,753 final codes. Maximum accepted single-block symmetric differences: 78, 70, 14 and 2. No candidate >134,753.

**Important diagnosis:** The first generator erroneously sampled random anchors from the entire union of ~140k mother-code words, more than 96% of which already existed in the current solution. Consequently, only 19–33 actual MILP solves were made per 180 attempted steps. This is a *candidate-discovery inefficiency*, not evidence that dynamic cross-partition search was exhausted.

The second [Actions run 43251915668](https://github.com/teddyli18000/web-ingest/actions/runs/43251915668) fixes selection to favor the 4,266 genuinely missing parent-code words, with a 35% independent speculative mutation stream, and expands to 420 steps per source across four runners. **This run was still executing when this note was first written.** Read final job statuses, numerical scores, independent checker and official Few Shots verdict (if positive) before making any claim.

## Next formulation if scores remain flat

The next qualitative extension is **coupled multi-anchor repair**: jointly force two or more fresh points from distinct parent-code basins that share old blockers across multiple prefix rows; rank blocks by prospective *new* core-point support, not by how many old points are replaced. Require at least one candidate absent from *all* four mother certificates, and adapt released prefix rows based on the replacement conflicts. This changes the topology of the search, rather than enlarging the same random neighborhood indefinitely.

No new Few Shots shot is ready without a fully validated score of at least 134,754.
