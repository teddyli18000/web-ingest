# A new action space: optimize the 12-spin mask as an object — 2026-11-04

## Mathematically exact representation

Let s∈{−1,+1}^N be a frozen LABS state and x_i∈{0,1} be a **joint multi-spin proposal** (flip spin i iff x_i=1). For every lag k,

[
C_k(sodot(-1)^x)=C_k(s)-2sum_{i=0}^{N-k-1} s_i s_{i+k},[x_i
e x_{i+k}].
]

Thus changing a large set of bits corresponds to a cut in the collection of lag-indexed signed interaction graphs. Its value is **not** the sum of one-bit gradients: the cut boundary depends on all selected positions jointly. One can search directly in a fixed-weight Johnson graph of masks with (sum_i x_i=12), using two-bit mask swaps (remove one selected bit; add one unselected bit). The physical s→s' can change 12 bits in one action even when the optimizing trajectory in **mask space** consists of small swaps.

This representation is distinct from repeated physical one-bit tabu moves, but is still a classical local combinatorial search. There is no learned generator yet.

## Exact candidate-only experiment

[Source C++](mask_space.cpp); [first analysis](analyze_mask_space.py), [controlled analysis](analyze_mask_space_v2.py). Run [GitHub Actions experiment](https://github.com/teddyli18000/web-ingest/actions/runs/41990375154). Six published symmetry-distinct near-boundary anchors selected before analysis: N64 E208, N80 E352, N92 E490, N99 non-skew E553, N99 skew E577, N100 near-skew E578. Each arm gets **50 ms** on one source candidate, 20 seeded repetitions per source, m=12 exactly.

Arms:
- **A fresh uniform:** each candidate chooses 12 independent uniformly drawn distinct positions, exact score after flipping all 12;
- **B optimized mask:** begin with uniform 12-mask, propose replacement of one selected and one unselected position; accept strict exact LABS E decreases, restart mask after 300 rejected swaps;
- **C stationary uniform mask random walk:** same two-flip incremental evaluation (and similar scores-per-ms) as B, but unconditionally accepts every swap. A uniform initial mask and symmetric swap kernel imply uniform stationary mask distribution, though successive samples are correlated.

The independent direct O(N²) LABS evaluator checks every retained output and the exact post-descent output. Every reported best candidate differs from its anchor by **exactly 12** spins. Post-descent is a retrospective **diagnostic excluded from generator clock**, so post-descent figures must not be called costed end-to-end solver performance.

### Complete paired results

Each entry is the mean best instantaneous LABS E found under the 50 ms candidate generation budget, 20 independent mask-generator seeds. **Lower is better.**

| Original anchor | E_anchor | fresh random | uniform mask walk | optimized mask | optimized minus walk E |
| --- | ---: | ---: | ---: | ---: | ---: |
| N64 |208|719.2|666.8|**445.6**|−221.2 |
| N80 |352|1167.2|1120.0|**717.6**|−402.4 |
| N92 |490|1556.4|1461.6|**949.2**|−512.4 |
| N99 non-skew |553|1783.2|1724.6|**1099.2**|−625.4 |
| N99 skew |577|1820.6|1704.8|**1094.0**|−610.8 |
| N100 near-skew |578|1852.0|1734.0|**1149.6**|−584.4 |

For N100, the source-fixed seed bootstrap 95% CI for **walk E minus optimized E** is **[+540.79,+628.8]**; all 20 paired comparisons favor the optimizer. Per 50 ms N100: uniform walk evaluates mean **73,554** masks, optimized mask **79,265**, fresh random only **16,018**. Thus the large performance difference cannot be attributed solely to the faster two-flip evaluation of proposed masks. However, this does **not** isolate every mechanism (walk correlation/restarts/search selection differ) and these seeds are replicates of *one source certificate*, not independent near-record N100 basins.

After retrospective steepest direct-energy descent from each optimized N100 candidate, mean E remains **1096.2**, compared with anchor E578; none is a frontier-quality new result. Neither the best mask E1149.6 nor post-descent E1096.2 is an improved solver. This is **evidence for learnable/mineable coordination within a new action representation**, but a powerful *cheap classical optimizer* already exploits it. Training a neural generator would have to exceed this classical frontier under the same full solver budget.

Raw [v1 TSV](results/mask_geometry_v1.tsv), [v1 per-anchor analysis](results/mask_geometry_v1.json), [v2 exact TSV](results/mask_geometry_v2.tsv) and [v2 three-arm analysis](results/mask_geometry_v2.json). The initial v1 workflow failed compilation due to missing `<climits>`; fixed and independently verified in successful v1 runs 41990054557/41990296289. v2 run 41990375154 completed and persisted exact output; do not mix those failures into scientific negative evidence.

## Consequence for next model representation

**Do not simply train to imitate the optimizer's Hamming-12 low-immediate-energy masks.** Even after large gains relative to random proposals, the produced macro is ~500 energy above the source and remains bad after original-objective descent. The next action family must be a **variable-cardinality, correlation-preserving conditional cut generator**:

- retain a *corridor* of low-stress correlation modes while reorganizing selected lag clusters, explicitly coupling odd/even lag compensation;
- permit temporary off-target bit changes and multi-block correlated repair, unlike the monotone Hamming path to the oracle-known N99 E553;
- sample from native elite *source-distinct checkpoint histories* rather than relabeling the lone N100 E578 certificate as many basins;
- evaluate full candidate construction, local repair, acceptance and future long-horizon gain against original crossover+MTS and strong published newer MTS/SAW using equal total computation.

Falsification gates: (a) at comparable CPU budget can the new representation generate near-source, symmetry-distinct endpoints from true elites? (b) Does it beat cheap **mask swap** and stronger non-neural repair/recombination? (c) Does deployed source-native solver reach good states faster on independent held-out lengths? If not, architecture complexity has not been earned.

**No new N100 record, no shot and no change to the distinct `labs-100/` topic.**
