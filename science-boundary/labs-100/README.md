# LABS length 100

## Question

Can we find a binary sequence of length 100 with LABS energy below the public best-known value 578? The Few Shots target is `E <= 574` because length-100 energies satisfy `E ≡ 2 (mod 4)`.

Few Shots problem: `few-shots/few-shots`, `problems/p006-labs-100`.

## Current state

**Active; no breakthrough yet. Current best verified energy remains 578.**

Public incumbent:

`++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-`

Few Shots main was rechecked on 2026-10-28 and still contains only the preset `578` record for p006. The 2025 massively parallel unrestricted memetic-tabu work also matched rather than improved N=100, so 578 remains best-known, not proved optimal.

### Strongest current facts

- Ordinary Hamming radii **1 through 7** around the incumbent are fully exhausted: `17,278,988,695` non-center sequences, no improvement. Shell minima at radii 5, 6, 7 are `950`, `978`, `974`.
- The incumbent is exactly `(+1, skew99)`. All 50 odd-lag correlations have parity-minimal magnitude 1, so odd-lag energy is exactly `50` and even-lag energy is `528`.
- This gives a natural **50-free-variable near-skew manifold**. An audit found an off-by-one bug in the first shell scanner; the old reported minima `1266,1398,1382,1338,1314` are invalid and withdrawn. Corrected exact minima at free-coordinate radii 1..8 are `806, 994, 1046, 962, 882, 958, 950, 850`. No improvement occurs through radius 8.
- The full corrected `2^25 = 33,554,432` recombination cube between the two near-skew symmetry representatives of the incumbent has exact minimum `578`, attained only at its two endpoints.
- A calibrated **odd-perfect** search (all odd `|C_k|=1`) is the first home-grown method here that repeatedly rediscovers 578 from random starts. A scaled Actions campaign with 2,048 random starts reached 578 independently in all 8 shards, but found no `<=574`; checked final 578 states are incumbent symmetries.
- The previously highlighted `E=622` odd-perfect state is far in ordinary Hamming distance but was later reclassified as another point of the same near-skew structural manifold. Several other low-energy odd-perfect states likewise have a near-skew representative after applying the standard 8 LABS symmetries.
- A dedicated search now measures the best odd-perfect state **outside every near-skew symmetry orientation**. The first completed shard reached 578 overall but only `1162` outside the near-skew orbit; the remaining shards are still running (Actions `40634532205`).
- The first non-odd-perfect energy layer is odd-lag energy `58`. Exact targeted scans show there is no O=58 state at incumbent Hamming distance 5 or 7; even distances are impossible from the necessary parity-half sums. An exact split radius-9 scan is running as Actions `40633483470`; completed patterns so far have zero O=58 states.
- A 50-variable exact near-skew CP-SAT search for even energy `<=524` (equivalently total `<=574`) is running across parity-half sign-sum classes as Actions `40634783271`. Its incumbent smoke test reproduced `578` exactly.
- An independent outer-in branch-and-bound for the same near-skew target has been implemented (`code/nearskew_bnb.cpp`) and is under short calibration in Actions `40635231041`.
- Direct neighboring-length editing remains weak: the 2025 unrestricted `N=99,E=553` record inserts to N=100 only at best `606`; historical N=101 E578 deletes to an incumbent symmetry, while N=102/N=103 transfers are much worse.
- A finite Golay/near-complementary construction was exhausted: all target-relevant double deletions of a canonical length-52 Golay pair and 32 relative post-deletion symmetries (plus the nontrivial pre-deletion joint alternation case) have best N=100 energy `1478`, despite even-lag energy as low as 164 in the family. Complementarity alone does not control the odd cross-correlations.

## What is known / structural identities

For signs `s_i ∈ {−1,+1}`,

```text
C_k = Σ_i s_i s_{i+k},
E = Σ_{k=1}^{99} C_k².
```

Exact general LABS optima are proved only through N=66. Reversal, global sign flip, and alternating sign flip generate up to eight energy-equivalent copies.

Split the sequence into its even and odd positions,

```text
A_i = s_{2i},   B_i = s_{2i+1},  i=0..49,
a = Σ A_i,      b = Σ B_i.
```

Then

```text
C_{2r} = C_A(r) + C_B(r),
sum_{k odd} C_k = ab,
sum_{r=1}^{49} C_{2r} = (a²+b²-100)/2.
```

Every odd-lag correlation has odd parity, so the minimum odd-lag energy is 50. Call a sequence **odd-perfect** when every odd `|C_k|=1`. The general congruence

```text
C_k + C_{100-k} ≡ 0 (mod 4)
```

then forces opposite odd correlations to cancel, hence every odd-perfect sequence has `ab=0`. A `574` target inside this manifold requires even energy at most `524`.

For the canonical near-skew orientation, positions `1..99` form a length-99 skew-symmetric tail and satisfy, in zero-based full-sequence coordinates,

```text
s_p s_{100-p} = (-1)^p,  p=1,...,49.
```

This leaves 50 free signs and makes odd energy identically 50. One parity-half sum is zero. If the other half has sum `a`, then

```text
sum even-lag C = (a²-100)/2.
```

Together with even energy `<=524`, Cauchy already forces `|a|<=20`, which is used to split the exact near-skew search into small sign-sum classes.

## Evidence and experiments

### Exact ordinary Hamming neighborhood

- Radii 1-5: 79,375,495 candidates, no improvement.
- Radius 6: 1,192,052,400 candidates, minimum `978`.
- Radius 7: Actions `40561186271`, 16,007,560,800 candidates, minimum `974`, 3433.59 s.

Full record: [`results/2026-10-27-incumbent-shells.md`](results/2026-10-27-incumbent-shells.md).

### Corrected near-skew exact search

| free radius | candidates | corrected minimum |
| ---: | ---: | ---: |
| 1 | 50 | 806 |
| 2 | 1,225 | 994 |
| 3 | 19,600 | 1046 |
| 4 | 230,300 | 962 |
| 5 | 2,118,760 | 882 |
| 6 | 15,890,700 | 958 |
| 7 | 99,884,400 | 950 |
| 8 | 536,878,650 | 850 |

Corrected radius 8: Actions `40613535569`, 155.142 s. The tested count equals `C(50,8)`. The old radius-8 run `40608557906` and old shell minima are invalid because the first scanner used the wrong mirror index; the result note carries the correction notice.

The corrected 25-coordinate symmetry crossover cube contains `33,554,432` states and has minimum `578`, count 2.

Full record: [`results/2026-10-28-near-skew.md`](results/2026-10-28-near-skew.md).

### Odd-perfect manifold

`code/oddperfect_walk.cpp` first drives a random sequence to odd energy 50, then uses exact one-/two-bit moves that preserve all odd `|C_k|=1` while minimizing full energy.

- calibration run `40612938897`: 1,024 random starts; rediscovered 578 and produced strong intermediate basins;
- scaled run `40627045447`: 2,048 random starts; all 8 shards reached 578; none reached 574;
- `E=622` state was independently verified but is itself direct near-skew, at corrected free-coordinate radius 24 from the incumbent;
- exact local move enumeration around incumbent and E622 gives the same sparse 2-single / 50-double mirror-pair structure, explained by their common near-skew geometry;
- `code/oddperfect_outside_nss.cpp` now records the best state outside the entire 8-orientation near-skew orbit. First finished shard: best overall 578, best outside `1162`, both independently rescored. Campaign `40634532205` is still running.

Full records: [`results/2026-10-28-odd-perfect.md`](results/2026-10-28-odd-perfect.md) and [`results/2026-10-28-odd-perfect-components.md`](results/2026-10-28-odd-perfect-components.md).

### First defect layer: odd energy 58

For O=58, exactly one opposite odd-correlation pair has magnitude pattern `1/3` instead of `1/1`; the parity-half sums must be `(±2,±2)`. The incumbent has `(10,0)`.

Exact target-compatible scans:

- Hamming radius 5: 1,370,250 candidates, `O=58` count 0;
- Hamming radius 7: 583,269,750 candidates, `O=58` count 0;
- even Hamming radii cannot satisfy the required half-sum parity;
- therefore the first possible O=58 bridge is radius 9 or farther.

The radius-9 necessary-half-sum space has `97,153,987,500` candidates split over ten independent patterns in Actions `40633483470`. Completed patterns `p7` (2,820,431,250 states) and `p9` (1,017,900,000 states) both contain zero O=58 states; more patterns are running.

### Exact near-skew target searches

`code/cpsat_nearskew.py` directly enforces the 50-variable skew reflection, models only the 49 even correlations, imposes even energy `<=524`, and states the exact correlation-sum identity. Its smoke test fixes the incumbent and reproduces `578`. Actions `40634783271` searches all even sign sums `a=-20,-18,...,20` for a `574` certificate or strict infeasibility.

`code/nearskew_bnb.cpp` is an independent exact branch-and-bound inspired by outer-in LABS enumeration. At a partial assignment it decomposes each even correlation into fixed terms plus unknown ±1 products and obtains a rigorous lower bound before branching. Actions `40635231041` is a short four-class calibration; scale only if pruning/throughput justify it.

### Neighboring-length / complementary constructions

The strongest simple neighboring-length transfer is `N=99,E=553 -> N=100,E=606`; its ordinary Hamming radii 1-5 contain no improvement.

`code/golay52_delete.cpp` exhausts the target-relevant part of a natural length-52 Golay-pair double-deletion family. Canonical pair: 38,924 deletion pairs satisfy the necessary even-energy `<=524` screen, giving 1,245,568 transformed full candidates; best total energy is `1478 = 1266+212`. The pre-deletion joint-alternation case gives the same best. This finite family is excluded as a direct source of 574.

Full records: [`results/2026-10-27-cross-length.md`](results/2026-10-27-cross-length.md) and [`results/2026-10-28-golay52-deletion.md`](results/2026-10-28-golay52-deletion.md).

## Dead ends / constraints learned

- Do not spend more compute on ordinary small edits around the incumbent: radius 7 is exact and strongly negative.
- Do not use the superseded near-skew shell numbers from the buggy scanner; only the corrected radii above are valid.
- Do not scale the first simple unrestricted CPU tabu/memetic/isolated-subsystem implementations unchanged; their calibration is poor.
- Strict odd-perfect 1/2-bit walking is calibrated enough to find 578, but simply adding more starts repeatedly falls into the same near-skew symmetry family and has not found 574.
- Coarse penalty/basin-cycling and lag-homotopy excursions were poorly calibrated (best far states in the high 700s); do not scale unchanged.
- Raw insertion/deletion from neighboring lengths and the tested Golay-52 deletion family are dead ends by themselves.
- CP-SAT `UNKNOWN` is not an exclusion. Only a valid certificate or proved `INFEASIBLE` class is decisive.

## Next steps

1. Finish and record the exact radius-9 O=58 scan. If every pattern is empty, the first odd-energy defect layer is at incumbent distance at least 11, a strong constraint on repair-based search.
2. Finish the outside-near-skew odd-perfect audit. Use its best score as the calibration target for genuinely different structural components, rather than ordinary Hamming distance.
3. Finish the 21-class near-skew CP-SAT campaign. Preserve every `INFEASIBLE` class as an exact exclusion; independently verify any feasible `<=574` sequence immediately.
4. Calibrate the independent near-skew branch-and-bound. If its partial-correlation lower bound is promising, strengthen it with the fixed correlation-sum constraint and scale it as an independent exact route.
5. If the near-skew target can be ruled out, return to first principles: search controlled higher odd-energy layers (58, 66, ...) or a representation that can cross between odd-perfect structural components rather than extending the same local move graph.
6. Re-check the current public record before any claim. If `E<=574` is found, freeze the sequence, rescore with `code/verify.py`, verify with Few Shots' verifier, create only `certificate.json` and `SHOT.md`, run `tools/check.py`, then publish under `teddyli18000` as authorized.

## Durable artifacts

- [`code/`](code/) — independent scorer; ordinary/near-skew/O58 exact scanners; odd-perfect search kernels; CP-SAT formulations; branch-and-bound probe; neighboring-length and complementary-family enumerators.
- [`results/2026-10-27-incumbent-shells.md`](results/2026-10-27-incumbent-shells.md) — exact ordinary Hamming exclusions.
- [`results/2026-10-28-near-skew.md`](results/2026-10-28-near-skew.md) — corrected near-skew derivation, exact shells, and crossover cube.
- [`results/2026-10-28-odd-perfect.md`](results/2026-10-28-odd-perfect.md) — calibrated/scaled odd-perfect search and structural reclassification.
- [`results/2026-10-28-odd-perfect-components.md`](results/2026-10-28-odd-perfect-components.md) — exact local move graph evidence.
- [`results/2026-10-28-golay52-deletion.md`](results/2026-10-28-golay52-deletion.md) — finite complementary-family exclusion.
- [`results/2026-10-27-cross-length.md`](results/2026-10-27-cross-length.md) — neighboring-length transfers.
- [`notes/literature-and-methods.md`](notes/literature-and-methods.md) — literature and method decisions.

## Sources

- Few Shots p006 problem/verifier: <https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100>
- Few Shots procedure: <https://github.com/few-shots/few-shots/blob/main/skills/take-a-shot/SKILL.md>
- QOBLIB LABS benchmark/solutions: <https://github.com/ZIB-AOPT/QOBLIB/tree/main/02-labs>
- Knauer record table / historical solver mirror: <https://github.com/borkob/git_labs>
- Packebusch & Mertens, exact LABS and skew-symmetric enumeration: <https://arxiv.org/abs/1512.02475>
- Bošković, Brglez & Brest, heuristic LABS search: <https://arxiv.org/abs/1406.5301>
- Zhang et al., massively parallel memetic tabu (2025): <https://arxiv.org/abs/2504.00987>
- Pšeničnik et al., dual-step / restricted-proposal refinement: <https://arxiv.org/abs/2409.07222>
- Pšeničnik et al., search-space region prioritization (2026): <https://arxiv.org/abs/2607.09688>
- Lau & Gangat, isolated-subsystem optimization (2026): <https://arxiv.org/abs/2610.14361>

## Work log

- **2026-10-27:** Opened durable topic; reproduced 578; surveyed literature and public solvers; exhausted ordinary incumbent radii through 7; tested neighboring-length and initial heuristic routes.
- **2026-10-28:** Derived near-skew representation. Audited and fixed an off-by-one in its first exact shell scanner; reran corrected radii 1-8 and the symmetry crossover cube.
- **2026-10-28:** Built and scaled odd-perfect search. 2,048 random starts across 8 shards all rediscovered 578 but no 574. Reclassified E622 as near-skew and launched an explicit outside-near-skew audit.
- **2026-10-28:** Derived the O=58 defect layer and exact half-sum constraints; excluded radii 5 and 7 and launched split radius-9 enumeration.
- **2026-10-28:** Exhausted the target-relevant Golay-52 double-deletion family with no competitive candidate.
- **2026-10-28:** Launched two independent exact near-skew target routes: 21-class CP-SAT and an outer-in branch-and-bound calibration.
