# p006 constructive mechanism reset and independent-parent campaign — 2026-11-12

## Objective / current verified score

Construct an unrestricted length-100 ±1 LABS sequence with **original integer aperiodic energy E<=574**. The official [Few Shots p006 record chain](https://github.com/few-shots/few-shots/blob/main/problems/p006-labs-100/FEWSHOT.md) was checked again on 2026-11-12 and remains **578**. A best score of 578 is *not* proof of global optimality.

This round explicitly stopped treating larger exclusion regions or more Hamming-shell scans as progress. All search arms generated and scored complete binary candidates; candidate quality, cost, and symmetry distance are the decision metrics. No E<=574 candidate emerged.

## Why the previous candidate search did not transfer

The two trusted, unlike, fully scored N100 parents have energy decomposition

| parent | Odd-lag squared energy O | Even-lag squared energy V | total E |
|---|---:|---:|---:|
| QOBLIB historical near-skew | 50 | 528 | 578 |
| 2025 published non-skew N99 E553 lifted by 1 sign | 290 | 316 | 606 |

The non-skew source has drastically better even-lag cancellation, but its odd-lag contribution is larger. Neither separately minimizing O or V, nor linear correlation interpolation between the sources, constructs a feasible better N100 signal.

Instead of asking which particular local move is excluded, the constructive question becomes: **Where can we obtain independent high-quality N100 parents with genuinely different signed lag-cancellation patterns, so that cross-basin compensation is possible?** Most prior runs stayed anchored to the same two orbits, and all multi-spin operators returned worse states.

## Finite constructive probes executed locally

All C++ candidates use exact packed 128-bit XOR/popcount original LABS energy; selected complete witnesses independently rescored with separate Python literal 99-lag integer summation. Counts below are proposed complete states, not independent symmetry orbits.

- **Skew-mirror defect skeleton + full coupled base repair.** Parametrize the 99-spin skew-symmetric core by 49 pair-anchor variables, a center sign and 49 independently switchable mirror defects. Change several defects at once; perform a full 50-variable compensated tabu repair. From N100 E578 and E606 parents, 100 runs × 1800 inner steps scored **9,180,799** candidates. Lowest *new result among generated children* was **E874**, but only one changed spin relative to E606; the lowest generated orbit at distance >=8 from *both* sources was **E1014**. On a hidden N59 E205 → N60 target-E218 construction test, 400 × 2000 steps scored **24,803,606** candidates, best **E322** (the source transfer before repair was E246). Fail: weak new-basin generation.
- **Full odd/even Pareto corridor.** Two-sided caps on O and V, optimizing complete LABS energy plus paired excess penalties. Four 2000-step runs, **1,832,020** complete scored proposals. Best parent remained 578; best independent orbit-distance >=8 state was **E990**. Not an improvement.
- **100-bit Golay-product construction from length-10 binary complementary pairs.** Independently verified the length-10 Golay pair, generated its full 64-pair elementary equivalence orbit, composed all 64² Turyn length-100 products, rescored both members (**8,192** full N100 candidates) and checked the zero-sum autocorrelation identity at all 99 lags. Best complete N100 E **1426**. A mathematical family, not a competitive p006 source.
- **Continuous unimodular complex-phase homotopy.** Alternating phase minimization and gradually increased binary attraction from N100 E578, two independent perturbed phase starts. Both finally projected back to the original E578 string; not a new family.
- **Domain-wall coordinates.** Let t_i=s_i s_(i+1). A t-coordinate flip negates an entire suffix; two flips negate an arbitrary interval while keeping in-segment products. N100 best one-step interval-from-E578 was E686 and from E606 was E698. On the hidden N59→N60 transfer at eight 3500-step seeds per arm (1.68m evaluations per arm), physical, wall and hybrid operators all returned E246. On N100, twelve 5000-step seeds and ~6m scored states per arm, full-spin/wall/hybrid best was the existing E606. No new low-energy orbit.
- **Atomic mirror-defect/base compensation.** Directly score whole sequences where a mirror-defect indicator changes in the *same move* as one or two base paired spins. This avoids accepting an incomplete exterior repair. Four × 1200-step guided runs, **16,843,222** complete candidates, best orbit distance >=8 from both parents **E898**. Crucially, an equal-work simple-coordinate tabu arm (4 × 42,000 steps, **16,632,760** scored candidates) found a **better E886** distant candidate. The apparent short-budget advantage of joint moves does not survive a cost-matched baseline. Independently rescored E886 witness:

```
+++++--++----++--++++--++++++++++++--+----++-++----++--+---+---+++++---+-++-+--+-++-+-+-+-+-+--+-+-+
```

  This string has E886 and symmetry-orbit Hamming distance 35 from historical E578 and 8 from published-lift E606. It is **not** a p006 record or a demonstrated globally unpublished orbit.
- **Exact 20-variable repair.** Eight adaptively selected 20-site support cubes around N100 strong source sequences, **8,388,608** complete binary assignments rescored; best remains the published E578 parent. Earlier 14-site scans in this topic were also negative. Expanding the same fixed-dimensional blocks further is unjustified without a new proposal distribution.

Local sources and transcripts were retained in this session's downloadable artifact bundle, while the decision, validated sequences, and upcoming independent-source harvester are committed here. None of the negative checks imply E574 is impossible; they only evaluate their specified generators.

## New construction plan — source independence before crossover

The [independent native N100 harvest tool](../code/native_new_orbit_harvest.py) uses the public historical unrestricted **2009-era lMAts** solver from the pinned source commit `borkob/git_labs@1aa123407636e48630174e0bf122037e369c1d68` (same source pin as the separately verified sibling AI4S research). It will run **16 independent seeds** on N100, at 900 real CPU seconds each, with four single-threaded processes per Linux runner and at most two runners concurrently. Every produced sequence is fully rescored by independent Python integer arithmetic and canonicalized across all eight LABS symmetries. No incumbent perturbation is passed to the solver, and no teacher-target bits enter the generator.

The temporary push-triggered workflow `.github/workflows/temp-labs100-independent-orbits-20261112.yml` uploads each shard as a machine-readable artifact. It never claims a record or auto-submits a Few Shots shot. The 2025 GPU MTS and 2026 GPU SAW are *stronger external references*, not equivalent to the historical CPU native source.

**Go/no-go criterion:** A new source-independent N100 orbit within a competitive quality band (preferably E<=700, still short of E578) enables a new cross-correlation-conditioned two-parent constructor. If the harvest only produces much worse states or duplicate orbits, do not scale the same source-generation regime without reformulating again. In the construction step, optimize exact signed cross-boundary lag contributions jointly with donor selection and full-sequence repair, and compare with known native MTS, classic crossover and the sibling AI4S source/virtual-parent controls. Any E<=574 certificate must pass exact independent scoring and the official Few Shots verifier before a shot claim.

## Primary sources

- Few Shots p006 official problem and record: https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100
- Native 2009-era solver/source: https://github.com/borkob/git_labs/tree/1aa123407636e48630174e0bf122037e369c1d68/solvers/lMAts-lRRts/src
- Packebusch & Mertens, proven optimality N<=66 / skew N<=119: https://arxiv.org/abs/1512.02475
- Zhang et al. 2025/2026 massively parallel GPU MTS: https://arxiv.org/abs/2504.00987
- Pšeničnik et al. 2026 region prioritization / GPU self-avoiding walks: https://arxiv.org/abs/2607.09688
- Lau & Gangat 2026 subsystem search: https://arxiv.org/abs/2610.14361
- Jedwab & Parker 2009 binary Golay complementary pair taxonomy: https://doi.org/10.1002/jcd.20222
