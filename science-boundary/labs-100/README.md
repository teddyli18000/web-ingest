# LABS length 100

## Question

Can we find a binary sequence of length 100 with LABS energy below the public best-known value 578? The Few Shots target is `E <= 574` because length-100 energies satisfy `E ≡ 2 (mod 4)`.

Few Shots problem: `few-shots/few-shots`, `problems/p006-labs-100`.

## Current state

**Active; no breakthrough yet. Current best verified energy remains 578.**

Public incumbent:

`++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-`

This remains a genuine frontier: the 2025 massively parallel unrestricted memetic-tabu campaign improved many nearby lengths but matched, rather than improved, `N=100, E=578`. The value is best-known, not proved optimal.

### Strongest current facts

- Ordinary Hamming radii **1 through 7** around the incumbent are fully exhausted: `17,278,988,695` non-center sequences, no improvement. Shell minima at radii 5, 6, 7 are `950`, `978`, `974` respectively.
- The incumbent is exactly obtained by prepending `+1` to the historical skew-symmetric `N=99, E=577` sequence. Consequently all 50 odd-lag autocorrelations of the N=100 incumbent have the parity-minimal magnitude `1`; they contribute only `50` of the total energy `578`.
- This gives a natural **50-free-variable near-skew subspace** `s=(+1, skew99)` where all odd lags are automatically optimal. Exact free-variable shells 4 through 8 around the incumbent are complete; their minima are `1266, 1398, 1382, 1338, 1314`. Thus the incumbent is also extremely isolated under structure-preserving paired moves.
- The second standard symmetry image that lies in the same near-skew representation differs in exactly 25 free variables. The entire `2^25 = 33,554,432` crossover subcube between these two `E=578` endpoints was enumerated exactly; its minimum is still `578`.
- The new 2025 unrestricted `N=99,E=553` record transfers to N=100 only at best `E=606`, and that transferred candidate has no better sequence within ordinary Hamming radius 5.
- Historical `N=101,E=578` deletes to a symmetry copy of the incumbent; `N=102,E=567` and `N=103,E=555` transfer poorly (`710` and `714`).
- Current simple unrestricted long-tabu, CPU memetic, fixed-distance swap, direct isolated-subsystem, and near-skew SAW/tabu probes are all poorly calibrated compared with 578 and should not receive large blind compute budgets.
- Diverse skew-99 candidates found by short tabu search transfer to N=100 at best `650` outside the known skew optimum. Priority-queue unrestricted refinement of several `650-686` seeds did not enter the record basin (best `646`).

## What is known

- Objective: `C_k = Σ_i s_i s_{i+k}`, `E = Σ_{k=1}^{99} C_k²`, `s_i ∈ {−1,+1}`.
- The first possible improvement is 574.
- Exact LABS optima are proved only through N=66, not N=100.
- Reversal, global sign flip, and alternating sign flip generate up to eight energy-equivalent copies.
- Modern relevant methods include unrestricted memetic/tabu search, skew/partitioned proposal generation followed by unrestricted refinement, priority-queue/rotation basin crossing, and isolated small-subsystem optimization.

## Structural derivation

Let the N=100 sequence be split into even and odd positions `A_i=s_{2i}` and `B_i=s_{2i+1}`, `i=0..49`. For odd lag `k=2r+1`,

```text
C_{2r+1} = Σ_{t=0}^{49-r} A_t B_{t+r}
          + Σ_{t=0}^{48-r} B_t A_{t+r+1}.
```

Thus all odd correlations are linear in either half when the other half is fixed. The incumbent has `|C_{2r+1}|=1` for every odd lag. Direct half-repair can restore this property after small perturbations, but the resulting full energies remain far above 578; odd-lag perfection is useful structure but not sufficient.

A stronger sufficient construction comes from skew symmetry. If `t` is a skew-symmetric sequence of length 99, every odd `C_k(t)=0`. For `s=(+1,t)`,

```text
C_k(s) = t_{k-1} + C_k(t),
```

so every odd `C_k(s)=±1`. `code/nss_shell.cpp` exploits this 50-variable representation exactly.

## Evidence and experiments

### Exact ordinary Hamming neighborhood

- Radii 1-5: 79,375,495 candidates, no improvement.
- Radius 6: 1,192,052,400 candidates, shell minimum `978`.
- Radius 7: GitHub Actions run `40561186271`, 16,007,560,800 candidates, shell minimum `974`, 3433.59 s.
- Total non-center candidates through radius 7: `17,278,988,695`.
- The disposable radius-7 workflow was removed after validation.

Full record: [`results/2026-10-27-incumbent-shells.md`](results/2026-10-27-incumbent-shells.md).

### Near-skew exact search

Free-variable shell results:

| radius | candidates | minimum |
| ---: | ---: | ---: |
| 4 | 230,300 | 1266 |
| 5 | 2,118,760 | 1398 |
| 6 | 15,890,700 | 1382 |
| 7 | 99,884,400 | 1338 |
| 8 | 536,878,650 | 1314 |

Radius 8 was completed by GitHub Actions run `40608557906` in 120.881 s; artifact id `12781094278`. The temporary workflow was removed after validation.

The complete 25-variable symmetry-to-symmetry recombination cube (`33,554,432` points) also has minimum `578`.

Full record: [`results/2026-10-28-near-skew.md`](results/2026-10-28-near-skew.md).

### Neighboring-length transfers

The strongest direct transfer is the 2025 unrestricted `N=99,E=553` record with one inserted sign, giving `N=100,E=606`; its Hamming radii 1-5 contain no improvement. Other tested N=98 and N=101-104 sources are worse.

Full record: [`results/2026-10-27-cross-length.md`](results/2026-10-27-cross-length.md).

### Heuristic calibration

- Long one-bit tabu: typical bests around 800-900+.
- First CPU memetic prototype: noncompetitive.
- Direct N=100 implementation of the 2026 `n=4` isolated-subsystem kicked-descent idea: about 970+ from random starts after millions of proposals; incumbent starts keep 578 as best seen.
- Near-skew random tabu/SAW: about 1160+ best in representative calibrated batches, although incumbent perturbations can fall back to 578.
- Elite crossover of the eight incumbent symmetry images found only the same eight `E=578` images, no inequivalent 578.

Full records: [`results/2026-10-27-search-benchmarks.md`](results/2026-10-27-search-benchmarks.md) and [`results/2026-10-28-near-skew.md`](results/2026-10-28-near-skew.md).

## Dead ends / constraints learned

- Do not spend more compute on ordinary small edits around the incumbent: radius 7 is exact and strongly negative.
- Ordinary radius 8 would be about eleven hosted-runner hours at measured throughput while radii 5-7 have minima near 1000; this is low-value compared with structured searches.
- Do not scale the current simple CPU tabu/memetic/isolated-subsystem implementations unchanged.
- Raw insertion/deletion from neighboring records is a dead end by itself.
- The natural near-skew manifold explains the incumbent, but local shells and symmetry crossover inside it are also strongly negative.
- A random fixed-distance shell search is not sufficiently calibrated; a useful long-distance method must first demonstrate it can rediscover a 578 basin from genuinely different starts.

## Next steps

1. **Broader odd-perfect / near-complementary manifold:** exploit the linear odd-lag constraints without requiring endpoint skew symmetry. Develop macro moves or constrained solving that preserve/restore all `|C_odd|=1` while directly minimizing the even-lag contribution (incumbent: 528; a 574 target with odd energy 50 needs even energy 524).
2. **Distinct record basins:** continue searching public archives and strong proposal generators for an inequivalent N=100 `E=578` (or a diverse 580-650 family). Recombination is only interesting once parents are not symmetry copies.
3. **2026 partition-prioritization idea:** generate diverse restricted/skew/partitioned candidates, but only scale if their unrestricted refinements enter a substantially better quality regime than the current 646+ diverse-seed probes.
4. **Algorithm calibration before Actions:** reserve long Actions for exact searches or heuristics that can first reproduce known low-energy basins at meaningful rates.
5. Re-check the current public record immediately before any record claim.
6. If `E <= 574` is found, freeze the sequence, independently rescore with `code/verify.py`, verify with the Few Shots verifier, create only `certificate.json` and `SHOT.md`, run `tools/check.py`, and publish under `teddyli18000` as authorized.

## Durable artifacts

- [`code/`](code/) — exact scorer, unrestricted probes, ordinary Hamming scanners, near-skew shell scanner, neighboring-length transfer code, isolated-subsystem probe.
- [`notes/literature-and-methods.md`](notes/literature-and-methods.md) — literature/method decisions and derivations.
- [`results/2026-10-27-smoke.md`](results/2026-10-27-smoke.md) — initial incremental-score validation.
- [`results/2026-10-27-search-benchmarks.md`](results/2026-10-27-search-benchmarks.md) — heuristic calibration and negative results.
- [`results/2026-10-27-cross-length.md`](results/2026-10-27-cross-length.md) — neighboring-length transfer results.
- [`results/2026-10-27-incumbent-shells.md`](results/2026-10-27-incumbent-shells.md) — exact ordinary local-shell exclusions.
- [`results/2026-10-28-near-skew.md`](results/2026-10-28-near-skew.md) — near-skew derivation, exact shells, and symmetry-cube exclusion.

## Sources

- Few Shots p006 problem statement and verifier: <https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100>
- Few Shots procedure: <https://github.com/few-shots/few-shots/blob/main/skills/take-a-shot/SKILL.md>
- QOBLIB LABS benchmark/solutions: <https://github.com/ZIB-AOPT/QOBLIB/tree/main/02-labs>
- Knauer record table mirror / historical solver archive: <https://github.com/borkob/git_labs>
- Packebusch & Mertens, exact optimization through length 66: <https://arxiv.org/abs/1512.02475>
- Bošković, Brglez & Brest, skew/self-avoiding and LABS heuristic search: <https://arxiv.org/abs/1406.5301>
- Zhang et al., massively parallel unrestricted memetic tabu (2025): <https://arxiv.org/abs/2504.00987>
- Pšeničnik et al., search-space region prioritization / two-stage refinement (2026): <https://arxiv.org/abs/2607.09688>
- Lau & Gangat, small isolated-subsystem optimization (2026): <https://arxiv.org/abs/2610.14361>

## Work log

- **2026-10-27:** Opened durable topic; reproduced baseline and surveyed current literature/solver archives.
- **2026-10-27:** Added exact scorer and search kernels; calibrated unrestricted tabu/memetic and isolated-subsystem probes; reproduced neighboring-length transfers.
- **2026-10-27:** Extended ordinary incumbent exclusion through radius 6 and launched radius 7.
- **2026-10-28:** Validated exact ordinary radius 7 (16.0 billion candidates; minimum 974) and removed its temporary workflow.
- **2026-10-28:** Derived the near-skew 50-variable representation from the historical skew-99 optimum; added `code/nss_shell.cpp` and exhausted free-variable radii 4-8, including radius 8 via one-shot Action.
- **2026-10-28:** Exhausted the full `2^25` crossover cube between the two near-skew symmetry representatives; minimum remained 578. Tested diverse skew-99 proposal transfers and priority-queue refinement; no competitive new basin found.
