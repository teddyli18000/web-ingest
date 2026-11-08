# Record-level constructive rewiring and core-coupled search — 2026-11-08

## Target and authoritative sources

Goal: independent set of **at least 134,754** in `C7^⊠10`, versus the public Few Shots p004 threshold **134,753**. No such improved candidate has yet been validated here.

- Public construction: Itty–Rosin–Carstensen–Reichman (2026), [paper](https://arxiv.org/abs/2607.21517), [pinned code and R367](https://github.com/nathanielitty/lower-bounds-for-shannon-capacity/tree/fe8966079013abaac21d1c08441500100f8e3b86/c7).
- Upstream problem/verifier: [Few Shots p004](https://github.com/few-shots/few-shots/tree/main/problems/p004-shannon-capacity-c7).
- The Itty 134,753 certificate is rebuilt *without relying on a downloaded oversized word list*, directly from `R367.txt` and `construct_cc_10_7_134753.py`. Official Few Shots p004 replay: [run 42500797468](https://github.com/teddyli18000/web-ingest/actions/runs/42500797468), success, valid 134753.

## New constructive mechanism: global ten-dimensional neutral replacement

Unlike the fixed-parent nine-/ten-port search that peaked at the officially verified **134,705** (see [prior research](constructive-fiber-repair-2026-11-07.md)), this model starts at the **full 134,753-point public record**.

For a candidate new point `p=(u,v)`, let `N_old(p)` be its exact set of confusable old ten-dimensional points. Introduce variables `x_p` for addition and `y_q` for deletion. Solve:

`max Σ_p x_p - Σ_q y_q`

subject to `x_p≤y_q` whenever `q∈N_old(p)`, and `x_p+x_r≤1` for all confusable new-new pairs. The solver uses a lexicographic secondary preference for as many newly added points as possible **without losing one point of true cardinality**.

The candidate universe is all `(u,v)` with both factors outside the retained 359-point five-dimensional core, old-core footprint `|N_B(u)|·|N_B(v)|≤2`, and at most two actual ten-dimensional old blockers. This still includes all 5D factors of arbitrarily large core support when the *other* factor has support zero. Candidate generation is exhaustive **for this stated family**, not for all `C7^10`.

### Independently reproduced exact outcome

- **9,177** ten-dimensional addition candidates.
- **5,527** distinct old blockers.
- **25,987** new-new conflict edges.
- HiGHS MILP returns **OPTIMAL** and a zero maximum gain in the stated family.
- With seed **1**, a **3,034-added / 3,034-removed** legal ten-dimensional record-level alternative is constructed; other deterministic objective tiebreaks yield 3,033-sized exchanges.
- All three generated 134,753-point codes passed the *official Few Shots p004 verifier*, with distinct canonical hashes in [run 42502891420](https://github.com/teddyli18000/web-ingest/actions/runs/42502891420), success:
  - seed 1: `9cb1312bedf4e49df987a2f8eed0efbb6d6199ba01860ddcd3cd1a8f816736b6`;
  - seed 17: `d3664c3ed7b26f4c50fef1f96cd644f928eff400b7e7dd228494aa79871a3256`;
  - seed 101: `5127054dce1c46c5f99796b50cc01cba079bf69118fb874bd01a34cf1e852c59`.

Reusable deterministic producer: [`code/c7p004_record_coordinated_repair.py`](../code/c7p004_record_coordinated_repair.py). The one-shot workflow [`temp-science-boundary-p004-coordinated-repair.yml`](https://github.com/teddyli18000/web-ingest/blob/main/.github/workflows/temp-science-boundary-p004-coordinated-repair.yml) pins the public parent, replays it, creates three new 10D certificates and independently judges them.

Locally, an independently implemented second round from one such neutral code effected a further **4,686-for-4,686** legal rearrangement, verified by a distinct 10D prefix-neighborhood bitset checker. This continuation is **not** yet an official independently reproduced artifact. Do not count it as a new record or use it as a substitute for the hosted result.

## First-principles analysis: why the giant neutral search is not yet a gain mechanism

A wider local scan with at most three actual old blockers finds **49,390** outside×outside candidates. However, **49,341** of these candidates have **zero** blockers in the 359×359 core: they only interact with terminal fibers/periphery. Only **49** candidate points in this entire low-blocker pool actually touch the core.

Thus the 3,034-for-3,034 replacement can drastically change the **periphery** while holding the entire giant core fixed. This strongly explains why candidate turnover increases without improving quality. Repeating its lexicographic/neutral objective with more seeds does **not** introduce the missing mechanism.

The next search needs candidates with larger immediate blocker counts but a **shared rectangular core-deletion footprint**; individually expensive two-sided additions can become profitable only when many of them reuse the same released core cells and their row/column auxiliary additions are optimized simultaneously.

## Constructive rectangular core-periphery model

A distinct solver [`code/c7p004_core_rectangle_construct.py`](../code/c7p004_core_rectangle_construct.py) now chooses two dense six-owner subsets `A,C⊂B` generated from overlapping five-dimensional support-three hyperedges. At each chosen pair, it forms the complete allowed factor pools:

`F_A=A ∪ {u∉B: N_B(u)⊆A}`, and analogously `F_C`.

For **every** point of `F_A×F_C` not already in the record (which includes old-core, row, column, outside×outside, and periphery regions), the MILP computes its exact blockers in the current full ten-dimensional record, introduces all required deletion variables, enforces **every** selected new-new conflict, and optimizes the *actual* score. A positive candidate is directly materialized for Few Shots verification.

This representation differs qualitatively from the previous 9,177 candidate universe: it can delete old core cells while coupling all three addition types in one solve. Its finite owner sets are still **restricted slices** of the global problem; a failed slice is never described as global impossibility.

Local pilots from the original public parent tested rank-1, rank-3 and rank-4 support rectangles and several dozen rank-6 mixed owner rectangles. These found no positive gain; all observed best objectives were zero. Their limited samples do not exhaust the six-owner family. A further exploratory rank-six batch on the independently verified 3,034-change record was launched locally without an improved witness before stopping that interactive pilot.

A hosted **constructive** experiment now runs the model from both the **published 134,753-point code** and its **independently verified 3,034-point alternative**, with four search shards each, in [GitHub Actions run 42503523088](https://github.com/teddyli18000/web-ingest/actions/runs/42503523088). If any candidate exceeds 134,753, the job automatically executes the upstream Few Shots official verifier. At the time of initial recording this run was in progress; its final status must be checked before declaring any result.

## Decision after the search

If positive gains emerge, freeze the full certificate, independent verdict and exact parameters, and submit through Few Shots. If these dense fixed-size rectangles only produce zero-gain alternatives, **do not merely scale the same family to millions of samples**. The next formulation should change the *factor support owner sets and retained core jointly in one dynamic search* (or develop a distinct ten-dimensional decomposition) rather than separately fixing A,C then optimizing endpoint selectors.

**Current verified best:** 134,753, unchanged. The main new result is an **officially reproducible multi-thousand-point constructive record-to-record move**, plus a new core-coupled search representation.
