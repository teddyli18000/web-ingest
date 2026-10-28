# LABS length 100

## Question

Can we find a binary sequence of length 100 with LABS energy below the public best-known value `578`?

For signs `s_i in {−1,+1}`,

```text
C_k = sum_i s_i s_{i+k},
E = sum_{k=1}^{99} C_k^2.
```

Length-100 energies are `2 (mod 4)`, so the first possible improvement is `574`, followed by `570, 566, ...`.

Few Shots problem: `few-shots/few-shots`, `problems/p006-labs-100`.

## Current state

**Active; no unrestricted breakthrough yet. Current best verified energy remains 578.**

Public incumbent:

```text
++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-
```

The most important new result is a rigorous structural exclusion:

> **The entire N=100 near-skew manifold has exact minimum energy 578.**

For any canonical near-skew `s=(s_0,...,s_99)`, delete `s_0` to get a skew-symmetric length-99 sequence `t`, and append `s_0` to get a skew-symmetric length-101 sequence `u`. Exact correlation algebra gives

```text
E(t) + E(u) = 2 E(s) - 1.
```

Packebusch–Mertens exhaustively proved the skew-symmetric optima through N=119; their table gives `E_skew(99)=577` and `E_skew(101)=578`. Hence

```text
2 E(s)-1 >= 577+578 = 1155,
E(s) >= 578.
```

The incumbent attains equality. Therefore **any unrestricted sequence with E<578 must lie outside every standard symmetry image of the near-skew manifold**.

Full proof: [`results/2026-10-29-nearskew-optimum-proof.md`](results/2026-10-29-nearskew-optimum-proof.md).

### Strongest current facts

- Ordinary Hamming radii **1 through 7** around the incumbent are completely exhausted: `17,278,988,695` non-center sequences, no improvement. Radius-6 minimum `978`; radius-7 minimum `974`.
- The incumbent is exactly `(+1, skew99)`, so all 50 odd-lag correlations have magnitude one; odd energy is `50`, even energy `528`.
- The whole near-skew manifold is now **proved** to have optimum `578`; previous CP-SAT/BnB/local-shell work inside that manifold is superseded as a target route, though preserved as evidence.
- A calibrated unrestricted **odd-perfect** search (`odd energy = 50`) repeatedly rediscovers the E578 near-skew basin from random starts. In 2,048 scaled starts all eight Actions shards reached 578, none reached <=574.
- Searching odd-perfect states outside every near-skew symmetry orientation found the same reproducible `E=1162` orbit in all eight shards. That orbit has a `3-bit boundary + skew97 core`; it is not low enough to be competitive but exposes a structural hierarchy.
- Exact boundary+skew-core searches exclude large structured classes: odd-perfect target feasibility is ruled out for full boundary classes `d=5,7,9,11,13`; the first odd-defect layer `O=58` is target-infeasible for `d=3`, and exact minima for `d=5..25` are all far above 574.
- Exact pairwise crossover among eight inequivalent near-skew elites (`578,622,650,674,678,678,682,686`) exhausted **265,814,016** recombination states. Every one of 15 cubes has minimum exactly equal to its better parent; pairwise coordinate crossover gives no synergy.
- Exact A/B block descent over the near-skew parity decomposition enumerated **1,258,291,200** full block states across eight random starts; best final energy was only `818`. This route is not worth scaling.
- Direct neighboring-length editing remains weak: the 2025 unrestricted N=99 E553 record inserts to N=100 only at best `606`; historical N101 E578 deletes to an incumbent symmetry; N102/N103 transfers are much worse.
- A finite Golay-52 deletion/relative-symmetry family was exhausted; best N100 energy `1478`.

## Structural identities for the remaining unrestricted search

Split the sequence by parity,

```text
A_i = s_{2i},
B_i = s_{2i+1},
i=0,...,49,
a = sum A_i,
b = sum B_i.
```

Then

```text
C_{2r} = C_A(r) + C_B(r),
sum_{k odd} C_k = ab,
sum_{r=1}^{49} C_{2r} = (a^2+b^2-100)/2.
```

Every odd-lag correlation is odd, so the minimum odd-lag energy is `50`. Call a sequence **odd-perfect** when every odd `|C_k|=1`. The opposite-lag congruence

```text
C_k + C_{100-k} == 0 (mod 4)
```

forces opposite odd correlations to cancel in an odd-perfect sequence, hence `ab=0`.

The interleaving form is useful outside near-skew too:

```text
C_s(2r)   = C_A(r)+C_B(r),
C_s(2r+1) = C_{A,B}(r)+C_{B,A}(r+1).
```

Thus the next frontier is not another near-skew solver. It is to understand whether the simultaneous conditions

```text
all odd correlations = +/-1,
even energy <= 524,
not near-skew under any LABS symmetry
```

are feasible at all.

## Exact target-layer arithmetic

The energy/product congruence is target-specific:

```text
global product +1 => E == 6 (mod 8),
global product -1 => E == 2 (mod 8).
```

Therefore exact `E=574` has global product `+1`, while exact `E=570` has product `-1`. Do not incorrectly use the 574 product class to exclude lower levels.

Write odd energy as

```text
O = 50 + 8t.
```

For exact E574, `code/target_arithmetic.py` combines odd opposite-pair defects, even-correlation square budgets, parity-half sums and the `z=i` Fourier identity. Surviving low-defect half-sum classes are recorded in [`results/2026-10-28-exact574-arithmetic.md`](results/2026-10-28-exact574-arithmetic.md).

For exact E570, `O=58` is impossible by the mod-16/product congruence; the odd-perfect layer survives only in canonical half-sum classes `(2,0),(6,0),(10,0),(14,0),(18,0)`. See [`results/2026-10-28-exact570-structure.md`](results/2026-10-28-exact570-structure.md).

## Evidence and experiments

### Incumbent exact neighborhood

- radii 1–5: 79,375,495 candidates, no improvement;
- radius 6: 1,192,052,400 candidates, minimum `978`;
- radius 7: Actions `40561186271`, 16,007,560,800 candidates, minimum `974`.

Full record: [`results/2026-10-27-incumbent-shells.md`](results/2026-10-27-incumbent-shells.md).

### Near-skew: now solved exactly

Historical experiments included corrected free-coordinate shells, symmetry cubes, E622/E678 basin shells, complete parity-block best responses, 15 elite crossover cubes, CP-SAT and BnB calibration. These all remain reproducible negative evidence, but the exact skew99/skew101 sandwich proof now dominates them.

Key records:

- [`results/2026-10-28-near-skew.md`](results/2026-10-28-near-skew.md)
- [`results/2026-10-28-nearskew-arithmetic.md`](results/2026-10-28-nearskew-arithmetic.md)
- [`results/2026-10-28-nearskew-elite-basins.md`](results/2026-10-28-nearskew-elite-basins.md)
- [`results/2026-10-28-nearskew-global-moves.md`](results/2026-10-28-nearskew-global-moves.md)
- [`results/2026-10-29-nearskew-optimum-proof.md`](results/2026-10-29-nearskew-optimum-proof.md)

### Odd-perfect outside near-skew

`code/oddperfect_walk.cpp` is the first home-grown heuristic here calibrated into the record regime. `code/oddperfect_outside_nss.cpp` separately records the best state whose entire eight-element LABS symmetry orbit avoids near-skew.

Actions `40634532205`: 1,024 random odd-perfect starts, 100,000 phase-2 steps each. Every shard's best outside-near-skew state had exact energy `1162`, and all are symmetry images of one orbit. That state is exactly `3-bit boundary + skew97` and is a strict weight-1/2 odd-perfect local minimum.

Full records:

- [`results/2026-10-28-odd-perfect.md`](results/2026-10-28-odd-perfect.md)
- [`results/2026-10-28-odd-perfect-components.md`](results/2026-10-28-odd-perfect-components.md)
- [`results/2026-10-28-oddperfect-outside-nearskew.md`](results/2026-10-28-oddperfect-outside-nearskew.md)

### Boundary + skew-core hierarchy

A finite-state decomposition keeps an odd boundary of length `d` and a skew-symmetric suffix. Exact target searches exclude all normalized odd-perfect classes for `d=5,7,9,11,13`. For `O=58`, `d=3` is target-infeasible and every odd `d=5..25` was fully enumerated; exact minima range from 2022 upward.

Full record: [`results/2026-10-28-skewcore-hierarchy.md`](results/2026-10-28-skewcore-hierarchy.md).

### Neighboring-length / complementary constructions

See:

- [`results/2026-10-27-cross-length.md`](results/2026-10-27-cross-length.md)
- [`results/2026-10-28-golay52-deletion.md`](results/2026-10-28-golay52-deletion.md)

## Dead ends / constraints learned

- **Do not spend further compute inside near-skew to beat 578. It is now rigorously impossible.**
- Do not repeat small ordinary edits around the incumbent; radius 7 is exact and strongly negative.
- Do not use the withdrawn first near-skew shell numbers; the old scanner had an off-by-one mirror bug. The corrected data are preserved in the result note.
- Do not scale simple CPU tabu/memetic/direct isolated-subsystem probes unchanged; their calibration is poor.
- Do not scale strict odd-perfect walking merely with more starts; it repeatedly collapses into the now-proved-optimal near-skew basin.
- Do not scale pairwise near-skew crossover or exact one-block descent; both have been tested at hundreds of millions to >1 billion exact states without synergy.
- Raw neighboring-length insertion/deletion and the tested Golay-52 family are dead ends by themselves.
- CP-SAT `UNKNOWN` is never an exclusion. Preserve only proved `INFEASIBLE` classes or independently verified certificates as exact claims.

## Next steps

1. **Odd-perfect outside near-skew:** attack the proposition “every odd-perfect N100 sequence with `E<=574` is near-skew (up to LABS symmetry).” A proof would eliminate the entire `O=50` layer because near-skew is now exactly bounded by 578.
2. Build the odd-perfect exact model directly in the `A/B` interleaving coordinates, explicitly excluding all eight near-skew orientations. Use cross-correlation constraints rather than a generic 100-bit full-correlation model.
3. Search for an analytic lower bound coupling complementary-pair energy `sum_r(C_A+C_B)^2` to the odd cross-correlation constraints `C_{A,B}(r)+C_{B,A}(r+1)=+/-1`; equality/near-equality theory from Golay/near-complementary sequences may be relevant.
4. Continue target-specific exact layers outside near-skew: `O=58` for exact 574, and `O=66`/higher layers according to the arithmetic decomposition. Keep exact 570 separate because its allowed defect parity differs.
5. Re-check Few Shots/public record immediately before any claim. If `E<=574` is found, freeze the sequence, independently rescore with `code/verify.py`, verify with the Few Shots verifier, create only `certificate.json` and `SHOT.md`, run `tools/check.py`, then publish under `teddyli18000` as authorized.

## Durable artifacts

- [`code/`](code/) — independent scorer; exact shell scanners; odd-perfect search kernels; target arithmetic/CP-SAT models; skew-core enumerators; neighboring-length and complementary-family tools.
- [`results/`](results/) — all meaningful exact exclusions, calibrations, negative searches and structural derivations.
- [`notes/literature-and-methods.md`](notes/literature-and-methods.md) — literature and method decisions.

## Sources

- Few Shots p006 problem/verifier: <https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100>
- Few Shots procedure: <https://github.com/few-shots/few-shots/blob/main/skills/take-a-shot/SKILL.md>
- QOBLIB LABS benchmark/solutions: <https://github.com/ZIB-AOPT/QOBLIB/tree/main/02-labs>
- Knauer record table / historical solver mirror: <https://github.com/borkob/git_labs>
- Packebusch & Mertens, exact LABS and skew-symmetric enumeration: <https://arxiv.org/abs/1512.02475>
- Prestwich, improved LABS branch-and-bound: <https://arxiv.org/abs/1305.6187>
- Bošković, Brglez & Brest, heuristic LABS search: <https://arxiv.org/abs/1406.5301>
- Zhang et al., massively parallel memetic tabu (2025): <https://arxiv.org/abs/2504.00987>
- Pšeničnik et al., dual-step optimization: <https://arxiv.org/abs/2409.07222>
- Pšeničnik et al., search-space region prioritization (2026): <https://arxiv.org/abs/2607.09688>
- Lau & Gangat, isolated-subsystem optimization (2026): <https://arxiv.org/abs/2610.14361>

## Work log

- **2026-10-27:** Reproduced the baseline; added independent scoring/search kernels; exhausted incumbent Hamming radii through 6; surveyed current solver literature and neighboring-length records.
- **2026-10-28:** Exhausted incumbent radius 7. Derived/corrected the near-skew representation. Calibrated odd-perfect search; found the reproducible outside-near-skew E1162 boundary+skew97 basin. Built exact skew-core and target-arithmetic decompositions. Exhausted large near-skew local, crossover and block neighborhoods. Established target-specific mod-8/mod-16 constraints for E574/E570.
- **2026-10-29:** Proved the exact N100 near-skew optimum is 578 using `E99(t)+E101(u)=2E100(s)-1` plus Packebusch–Mertens' exact skew optima `577` and `578`. Refocused the frontier on non-near-skew odd-perfect and higher odd-defect layers.
