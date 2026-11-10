# Conditional exterior value as a search signal — 2026-11-10

## Objective and result
Few Shots p006 requires an unrestricted **length-100** ±1 sequence with aperiodic LABS energy **E<=574**; the live [FEWSHOT record](https://github.com/few-shots/few-shots/blob/main/problems/p006-labs-100/FEWSHOT.md) on 2026-11-10 remains **578**. This study does **not** produce a new record.

A new *conditional-value* ranking signal was measured against raw outer-spin gradient and two cost-matched classical full-tabu baselines. It is useful for **planted repair where the damaged core window is supplied**; it is **not** yet a superior unrestricted N100 generator. Separate source E578 and E606 anchors were used; results must not be generalized to independently discovered source orbits.

## Mechanism
Let s=(u,v) denote arbitrary *outer* and *inner* spins, with known inner index set I (50 indices on N100) and exterior J. Define the computational approximation

    F_L(u) = min_{0<=t<=L} E(u, Tabu_I^t(v | u)).

Instead of ranking a proposed exterior flip j by its immediate full-sequence energy E(s^j), rank it by **the best complete LABS energy attained after 300 subsequent 50-site tabu moves while j remains flipped**. This is a finite computational value function, not an exact mathematical minimum. The algorithm receives only the corrupted initial sequence and the core index set, **not** the original teacher bits or the identity of the wrong outer position.

A precise comparison: for each teacher, hide the teacher after flipping exactly 20 spins inside a 50-bit circular window and 1 additional spin outside it. At each trial score all 50 possible outside-site corrections, with 300 inner-only steps (15,000 candidate evaluations per correction, plus its raw-score call). The correct outer site is revealed **only after** all 50 conditional scores are produced, to compute offline rank and recovery counts.

[Reproducible benchmark](../code/conditional_exterior_rank.cpp), with existing tested [incremental full-energy core solver](../code/conditional_core_bridge.cpp):

    cd science-boundary/labs-100
    g++ -O3 -std=c++20 code/conditional_exterior_rank.cpp -o /tmp/labs-cond-rank
    /tmp/labs-cond-rank 1 20 300 50 11
    /tmp/labs-cond-rank 1 30 300 50 12
    /tmp/labs-cond-rank 1 30 300 50 13
    /tmp/labs-cond-rank 2 20 300 50 11
    /tmp/labs-cond-rank 2 30 300 50 12

For each identical corrupted input, cost-matched controls receive the same **750,000** total neighbor proposals: (a) one unrestricted 7,500-step full tabu, (b) ten 750-step full-tabu restarts from the original X with independent seeds. The conditional bank is charged **750,050**, including each candidate's raw-score evaluation. All methods' accepted search energies are original 99-lag integer LABS energies; the core solver's best is fully recomputed independently of its incremental flip updates in C++.

### Primary reproducible completed runs (same code, fully finished)

| N100 hidden anchor | seed | cases | mean outer rank from raw E | mean conditional rank | true outer site in conditional top-5 (raw top-5) | hidden E recovered: conditional / full / 10-restart |
|---|---:|---:|---:|---:|---:|---:|
| E578 | 11 | 20 | 18.1 | 8.95 | 9 (6) | **2 / 0 / 0** |
| E578 | 12 | 30 | 25.13 | 8.17 | 16 (6) | **3 / 0 / 0** |
| E578 | 13 | 30 | 19.87 | 7.50 | 15 (5) | **3 / 0 / 0** |
| E606 | 11 | 20 | 23.0 | 2.70 | 18 (3) | **2 / 0 / 0** |
| E606 | 12 | 30 | 21.27 | 3.13 | 25 (4) | **4 / 0 / 0** |

Combined **E578: 8/80** teacher-energy recoveries and conditional top-5 **40/80**, versus raw-gradient top-5 **17/80**. Combined **E606: 6/50** recoveries and conditional top-5 **43/50**, versus raw **7/50**. Independent random windows and corruption seeds are *not* independent source orbit lineages.

A separate original-kernel pilot over seeds 7–10 (different implementation and tabu random number streams) had E578 **12/130** recoveries, conditional true-site top-5 **86/130** versus immediate-energy **22/130**; E606 **18/130**, conditional top-5 **96/130** versus immediate-energy **18/130**. The 300-step kernels and planted trial generators differ; these counts are **not combined** with the primary table. The earlier pilot log and native source are preserved in the downloadable session bundle.

A completed N60 E218 planted-anchor probe had noticeably weaker short-horizon ranking (20 outside positions; conditional mean rank ~7.9 versus raw 10.95 over 60 cases) and **zero** teacher recoveries with 300 inner steps, while 1,200-step N60 conditional ranking could recover **3/30** on a separate seed. Thus this is not a source-independent theorem, even as a conditional recovery heuristic.

## Reality check: no candidate-quality gain on intact N100 anchors

The exact same source-level conditional idea was applied from *intact*, publicly known E578 and E606 anchors without planted errors. Eight core-window offsets for each W in {40,50,60,70}, all exterior single-bit flips in each offset, 500 inner tabu steps per candidate:

| Source | Candidate masks | Charged full-E candidate evaluations | Lowest postrepair E | Candidate with E<=650 |
|---|---:|---:|---:|---:|
| N100 E578 | 1,440 | 37,601,440 | **686** | 0 |
| N100 E606 | 1,440 | 37,601,440 | **698** | 0 |

All best full strings were independently rescored by separate literal Python O(N²) integer correlations. Zero new N100 elite candidate, zero record.

A finite *conditional outer-mask beam* (12 non-reverting exterior changes, six state beam width, 12 children each, 300 inner tabu steps per child; two seeded runs each from E578/E606) also degraded sharply: smallest encountered among its postrepair children E774 from E578, E722 from E606. Thus the method cannot simply be scaled by adding one more outer site or more beam stages.

### Why the planted success is real but narrow
The conditional score includes the capacity to cancel poor exterior correlations by a highly nonlocal *interior relaxation*, unavailable to a raw two-spin or single-spin gradient. On planted inputs, fixing the *one* wrong outer bit restores the teacher-compatible boundary and makes inner repair far more effective. But from an already excellent complete source, **every** one-bit boundary deviation destroys so much cancellation that even repaired cores remain far above that source. The outer correction is easier to *identify* than a new improved exterior is to *construct*.

The next generator must change the **outer action support**, not merely score a larger number of single-site departures. Test a proposal that **jointly chooses several outer signs and a corresponding interior compensation**, retaining the signed multi-lag correlation cut term exactly; make its target distinct high-quality new-orbit yield per end-to-end compute, rather than return to the known teacher. Positive controls without privileged correct core windows, plus true native classical multi-start baselines, are required before expanding N100 computation.

## Correctness audit: isolated n=4 ambiguity

On 2026-11-10 a sibling AI4S agent opened [issue #23](https://github.com/teddyli18000/web-ingest/issues/23) suggesting the older [isolated n4 probe](../code/isosubsys.cpp) had an erroneous even-distance two-body term and needed the shared midpoint inside the chosen four sites. The claim depends on the *order* of polynomial expansion versus edge deletion:

- For **projection of the already-expanded full Bernasconi Hamiltonian**, every even-gap pair contributes `2s_i s_j` because `(s_i s_m)(s_m s_j)=s_i s_j` even if midpoint `m` is outside the selected subsystem. The old even-gap rule is algebraically correct.
- For the **different construction** that deletes all boundary-crossing correlation edges before squaring individual correlations, the midpoint must be selected. Do not conflate them.

At selected positions (0,1,2,4), all + spins, the two-body projected value is **6**, not 4. Directly averaging full LABS E over every exterior sign verifies the original even-gap formula at all **2,000** selected-assignment cases for lengths 5–8; see [exact independent standard-library regression](../code/check_isolated_n4_projection.py). The tentative midpoint-only edit was reverted after this check; the distinction was documented in issue #23. [Lau & Gangat v3, Sec. III.1](https://arxiv.org/html/2610.14361v3) says to delete *Hamiltonian terms* containing nonsubsystem spins and describes a two/four-body Ising Hamiltonian, which aligns with post-expansion projection, but source-level authors' implementation equivalence remains unverified. Previous N100 n4 performance claims remain *research-probe claims*, not claimed exact reproduction of authors' code.

## Verification, literature and limits

- Current public target verified directly via [Few Shots p006](https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100) and FEWSHOT main; no merged record beats E578 as of 2026-11-10.
- Contemporary methods inspected: [Lau & Gangat, arXiv:2610.14361v3](https://arxiv.org/html/2610.14361v3); [Pšeničnik et al., arXiv:2607.09688](https://arxiv.org/abs/2607.09688); [Zhang et al., arXiv:2504.00987](https://arxiv.org/abs/2504.00987). Neither this pilot nor the former one claims to beat modern native GPU memetic tabu or partition SAW.
- All declared completed ranking results are from fully finished logged trials; a later seed-13 E606 full-control run reached the execution timeout and was **not counted**.
- The primary comparison matches **neighbor proposals**, *not CPU wall time*. Converting proposed full sequence energies into costs is comparable within this C++ code, but selection and memory overhead differs.
- No E<=574 candidate was produced; no Few Shots certificate or shot was submitted.
