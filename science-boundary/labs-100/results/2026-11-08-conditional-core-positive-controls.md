# Two-ended construction, hidden-solution core repair, and unknown-boundary test (2026-11-08)

## Question and current status

Can we construct an unrestricted 100-spin binary sequence with strictly lower aperiodic LABS energy than the public **578**? The first possible improvement is **574**. The official Few Shots p006 rule/record and QOBLIB reference were rechecked on 2026-11-08.

**Result: no E<=574 witness.** The key positive observation is conditional: if the correct outer 20–50 bits of a known high-quality sequence are supplied, a 40/50-bit center tabu repair routinely recovers the hidden center and its verified energy. This has **not** transferred to constructing a new low-energy outer boundary; do not inflate a positive control into a new record or a generally better search algorithm.

All result strings in this round were independently rescored with a separate literal Python O(N²) 99-lag integer scorer, in addition to the C++ incremental self-checks. Full source, raw terminal states, and a second verifier are available in the session artifact bundle. Reusable primary C++ source is now committed under [code/conditional_core_bridge.cpp](../code/conditional_core_bridge.cpp), [code/boundary_core_proposals.cpp](../code/boundary_core_proposals.cpp), and [code/two_end_beam.cpp](../code/two_end_beam.cpp).

## 1. Why prefix-first construction is structurally misleading

Exact integer scoring of the publicly certified N100 E578 sequence, truncated to its first 60 bits, gives **E(prefix60)=1226**. Independently, the actual complete N60 known optimum has energy **218**. Thus a heuristic that keeps only exceptionally low-energy *partial prefixes* need not keep the prefix of a good N100 completion: the suffix can cancel large prefix correlations.

Try two-ended construction instead. At depth t the assigned positions are {0,...,t-1} union {N-t,...,N-1}. For lag k let p_k be the sum of products with **both** endpoints assigned and r_k the count of currently unassigned lag-k pairs. Then for any completion,

    C_k(final) = p_k + integer in [-r_k,+r_k] with step 2.

The admissible per-lag bound (independent of joint realizability) is the smallest squared integer with the final parity of N-k reachable in that interval; sum across lags to get a correct but weak lower bound. Partial energy Q=sum p_k² is **not** a lower bound, since future terms can cancel p_k.

[code/two_end_beam.cpp](../code/two_end_beam.cpp) grows both endpoints (four sign assignments per step, global-negation normalizes first sign to +), keeps width K by Q / Q-plus-lower-bound or a variance-style score sum p_k²/(r_k+alpha), then independently checks full final E.

| N | known best | two-end width 10k raw Q | width 100k raw Q | width 100k best tested alternative |
|---|---:|---:|---:|---:|
| 40 | 108 | 144 | 120 | 116 (Q+4LB) |
| 60 | 218 | 354 | 350 | 322 (sum p²/(r+1) or (r+5)) |
| 100 | 578 | 1186 | 1130 | 1130 (Q+LB) |

No hidden teacher bits were provided to beam search. This method also fails its positive control. We must infer *jointly achievable cancellation*, not just penalize current correlations or rank by per-lag independent bounds. Do not scale width unchanged.

## 2. Why simple continuous correlation-cut relaxation fails

For a current sequence s and binary flip mask m_i in {0,1}, define the complete integer lag-correlation change:

    C_k(s⊙(-1)^m) - C_k(s)
      = sum_i m_i [-2s_i(s_(i-k)+s_(i+k))]
        + 4 sum_(i=0)^(N-k-1) s_i s_(i+k) m_i m_(i+k),

where missing neighbor terms in the first sum are zero. This identity was checked independently for all lags in 100 random test cases at each N40/N60/N100.

The second, quadratic mask term is the *necessary jointly flipped edge correction*. Dropping it and solving a capped-simplex linear least squares suggests wildly infeasible correlation cancellations. Example N100 E606, K flipped positions, 3000 rounded masks per arm:

| K | linearized projected target E | best actually reconstructed E, guided | best random-mask E |
|---:|---:|---:|---:|
| 6 | 109.69 | 1118 | 1438 |
| 8 | 63.19 | 1526 | 1590 |
| 12 | 18.05 | 1894 | 1942 |
| 16 | 3.34 | 2046 | 2166 |
| 20 | 0.25 | 2182 | 2326 |

The guided proposals are frequently better than random masks but remain nowhere near the E606 parent. This is **candidate generation quality** only and not an improved solver. Fixed-cardinality full-energy mask-swap optimization and signed odd/even spectral interpolation were also tried from verified N100 E606/E578; neither returned an E<606 state. In particular, splicing the incumbent's 50 odd-lag squared energy and the non-skew E606 parent's 316 even-lag squared energy yields a formal target sum of 366, but the spectral splice is not independently binary-realizable.

Also ran 16×50,000-step exhaustive 4,950-pair-neighborhood tabu trajectories from the N100 E606 basin (exactly 3,960,000,000 scored pair candidates). No E<606 appeared. These are negatives only for the specific search interfaces.

## 3. Positive control: hidden high-quality center with known correct boundary

Source [code/conditional_core_bridge.cpp](../code/conditional_core_bridge.cpp). For each of 40 trials at each seedtag 0,1,2:

1. Select a known certified complete teacher: N60 E218 (QOBLIB), N100 E578 (Few Shots/QOBLIB), or N100 E606 (independently verified source derived by inserting one sign into 2025 non-skew N99 E553).
2. Choose a contiguous window of width W=40 for N60 or W=50 for N100 (alternating centered and randomly wrapped).
3. Flip **exactly 20 random positions inside this window**, producing the initial sequence.
4. **Hide the teacher from the repair algorithm.** Its only inputs are the corrupted initial sequence, the allowed site list, and original LABS energy. No target sequence or target energies enter its move choice. The test oracle knows only how to judge recovery afterwards.
5. Compare fixed-window tabu (W proposals per step, 30k steps) with otherwise identical unrestricted tabu (N proposals per step, 20k N60 / 15k N100 steps). Same initial corrupted state, PRNG seed formula and **exactly equal energy-evaluation budgets**: 1.2m per N60 arm, 1.5m per N100 arm. The algorithms consume different RNG streams after site selection because the allowed site sets differ, as expected. Same tabu tenure 9 plus uniform 0..6 random tenure and 300-step stagnation kicks.
6. Record each terminal best complete sequence, verify exact energy independently, report only if it reaches the hidden teacher's energy or better.

| Teacher | seedtag 0 core/full hits | seedtag 1 core/full | seedtag 2 core/full | total |
|---|---:|---:|---:|---:|
| N60 E218 | 13/0 | 20/0 | 21/0 | **54/120 vs 0/120** |
| N100 E578 | 39/0 | 40/0 | 39/0 | **118/120 vs 0/120** |
| N100 E606 | 40/0 | 38/0 | 37/0 | **115/120 vs 0/120** |

These are genuine positive controls for **conditional reconstruction with an oracle-supplied correct boundary/window**, not blind search performance. They also do **not** establish a general statistical advantage over more sophisticated methods aware of mutation support: the full tabu control is intentionally not given the 20-bit damage localization or a correct-boundary hint. The same source orbit is reused across trials, so do not treat 120 outcomes as 120 independent solver instances for generalization.

Exact reproducibility:

    g++ -O3 -std=c++20 -fopenmp code/conditional_core_bridge.cpp -o /tmp/core
    # N60: mode 0. N100: mode 1 (E606), mode 2 (E578).
    for seedtag in 0 1 2; do
      /tmp/core 0 40 30000 40 9 0 "$seedtag"  # core
      /tmp/core 0 40 20000 40 9 1 "$seedtag"  # matched unrestricted
      /tmp/core 1 40 30000 50 9 0 "$seedtag"
      /tmp/core 1 40 15000 50 9 1 "$seedtag"
      /tmp/core 2 40 30000 50 9 0 "$seedtag"
      /tmp/core 2 40 15000 50 9 1 "$seedtag"
    done

## 4. Actual unknown-boundary constructive experiment

The central question is whether the conditional solver generates good **new boundaries**, rather than merely repairing errors within an already correct boundary. Source [code/boundary_core_proposals.cpp](../code/boundary_core_proposals.cpp) actually changes the outer positions and then releases only W core positions for full-energy tabu:

- source E578 and randomly flip r=1..20 outer positions;
- source E606 and randomly flip r=1..20 outer positions;
- source E578 center with partially inherited E606 outer signs;
- source E606 center with partially inherited E578 outer signs.

Outer positions are frozen during each repair. The genuine improvement target (E<=574) is not present and no oracle window is known to be correct. Original energy and the eightfold symmetry-orbit distance from both sources are checked for all terminal strings.

| Released core W | trials per arm | repair steps per arm | evaluations all four arms | best E across arms |
|---:|---:|---:|---:|---:|
| 50 | 100 | 8,000 | 160,000,000 | **686** |
| 60 | 120 | 12,000 | 345,600,000 | **786** |
| 70 | 120 | 12,000 | 403,200,000 | **746** |
| 80 | 120 | 12,000 | 460,800,000 | **774** |
| total | 1,840 runs | — | **1,369,600,000** | 686 |

Zero terminal states reached E<=650. The best E686 is still near the original E578 orbit, not a novel competitive basin. Running longer per arbitrary mutated boundary or widening the core without a coherent *joint* boundary-and-interior proposal is unsupported.

Reproduce:

    g++ -O3 -std=c++20 -fopenmp code/boundary_core_proposals.cpp -o /tmp/outer
    for mode in 0 1 2 3; do
      /tmp/outer "$mode" 100 8000 50 0
      /tmp/outer "$mode" 120 12000 60 1
      /tmp/outer "$mode" 120 12000 70 1
      /tmp/outer "$mode" 120 12000 80 1
    done

## 5. Research reassessment: what must change next

The productive insight is **conditional landscape structure**, not an unconditional record. The same core solver strongly reconstructs an already known good sequence when the correct exterior is fixed, but the success vanishes when the exterior is selected by naive random flips or a two-parent site splice. This separates the source of difficulty into a *latent boundary/coarse state selection problem* plus an easier conditional inner repair problem.

Stop treating “search a bigger fixed Hamming radius / core width / random boundary” as the main objective. A qualitatively different candidate generator would **jointly search a compact boundary representation and internal compensation**, ideally with a low-cost *predicted conditional-optimum* signal that is empirically calibrated on independent hidden-answer sources before N100 scaling. In particular, the boundary operator must learn or derive the signed cross-lag cancellation of the two parts, instead of optimizing them separately. Compare against the strong native memetic-tabu, epistasis, true-parent crossover and GOMEA-style ablations already documented by [the separate AI4S LABS research topic](../../labs-ai4s-search/README.md); do not duplicate it blindly.

### Reproducibility and limits

- The C++ searches were executed locally with four OpenMP threads; run times are local, not a reproducible CPU-speed claim.
- Every terminal witness used in the cited result tables was rescored independently with integer O(N²) arithmetic (including all 360 positive-control pairs and 1,840 boundary cases). No independent GitHub Actions runner execution was claimed for this round.
- Evaluation budgets count complete neighbor energy computations and exclude the site-selection/housekeeping overhead. They are matched within the paired control comparison, not equivalent to matching real CPU cost across unrelated algorithms.
- No E<=574 candidate exists in these outputs and no Few Shots shot was prepared or submitted.

## Primary references

- Official Few Shots p006: https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100
- QOBLIB LABS solutions: https://github.com/ZIB-AOPT/QOBLIB/tree/main/02-labs/solutions
- Zhang et al. 2025 / revised 2026 GPU memetic tabu: https://arxiv.org/abs/2504.00987
- Pšeničnik et al. 2026 SAW/partition prioritization: https://arxiv.org/abs/2607.09688
- Lau & Gangat 2026 small-subsystem search: https://arxiv.org/abs/2610.14361
