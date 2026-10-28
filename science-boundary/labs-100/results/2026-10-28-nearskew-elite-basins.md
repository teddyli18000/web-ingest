# 2026-10-28 exact structure of low-energy near-skew basins

## Purpose

The calibrated odd-perfect search repeatedly enters the canonical N=100 near-skew manifold `s=(+1,skew99)`, but it does not only find the public `E=578` record. Historical Actions traces also contain inequivalent near-skew states at energies `622, 650, 674, 678, 682, 686, ...`.

This note asks whether the strongest non-record basin, `E=622`, is locally repairable, whether it can be improved by optimizing one parity block at a time, and whether exact recombination between strong near-skew parents exposes an unseen low-energy child.

No `E<=574` sequence has been found so far.

## E=622 seed

Verified sequence:

```text
++--+--+++++++++++++++-------++++--+--+--+--+++--+---++-++---+++---++-+--+-+-+--+-+-+-+-+-+-+--+++--
```

Exact decomposition:

```text
E = 622
odd energy = 50
even energy = 572
```

It is canonical near-skew:

```text
s_p s_{100-p} = (-1)^p,  p=1,...,49.
```

Its ordinary Hamming distance to the public incumbent symmetry orbit is large, but in the corrected 50 near-skew free coordinates it is radius 24 from the incumbent.

## Exact ordinary Hamming shells around E=622

Small shells were exhausted with `code/sphere_shell.cpp`; radius 6 was independently reproduced in GitHub Actions run `40734030950`.

| exact Hamming radius | candidates | shell minimum |
| ---: | ---: | ---: |
| 2 | 4,950 | 822 |
| 4 | 3,921,225 | 902 |
| 6 | 1,192,052,400 | **966** |

Radius-6 evidence:

```text
BASE energy=622
RADIUS radius=6 tested=1192052400 best=966 seconds=220.678
BESTSEQ -+--+--+++++++++++++++----+++++++--+--+--+--+++--+--+++-++---+++---++-+--+-+++--+-+-+-+-+-+-+--+++--
```

The tested count equals `C(100,6)`. The radius-2 and radius-4 scans also found no `O=58` state. Thus this basin is not repairable by any ordinary edit of 2, 4, or 6 bits that lowers total energy.

## Exact near-skew free-coordinate shells around E=622

A more natural neighborhood stays inside the odd-perfect near-skew manifold. One free-coordinate flip changes one skew pair, or the center bit, while preserving odd energy `50` exactly. GitHub Actions run `40734086504` exhausted radii 1 through 8 using the corrected coordinate map.

| free-coordinate radius | candidates | shell minimum |
| ---: | ---: | ---: |
| 1 | 50 | 934 |
| 2 | 1,225 | 990 |
| 3 | 19,600 | 1182 |
| 4 | 230,300 | 1070 |
| 5 | 2,118,760 | 1054 |
| 6 | 15,890,700 | **862** |
| 7 | 99,884,400 | 958 |
| 8 | 536,878,650 | 974 |

Every tested count equals `C(50,r)`. None approaches 622. In particular, the basin remains isolated even after allowing paired structural moves that would be distance two in the ordinary bit representation.

## Parity-block decomposition and blockwise global minima

Write the full sequence as parity halves

```text
A_j = s_{2j},
B_j = s_{2j+1},
j=0,...,49.
```

For a canonical near-skew state, after global-sign and alternating-sign normalization `s0=s1=+1`:

- the `A` half has 25 independent near-skew coordinates;
- the `B` half has 24 independent coordinates modulo the alternating symmetry;
- every odd correlation remains `+/-1`;
- the objective is the even-lag energy
  `sum_r (C_A(r)+C_B(r))^2`, plus the constant odd energy 50.

`code/nearskew_block.cpp` exhausts one full block while freezing the other, with periodic independent full rescoring.

For the E=622 seed:

```text
fixed B, exhaust all 2^25 = 33,554,432 A assignments: minimum E = 622
fixed A, exhaust all 2^24 = 16,777,216 B assignments: minimum E = 622
```

The seed is the unique minimum in both scans. Therefore E=622 is a **blockwise global minimum**, not merely a 1- or 2-coordinate local minimum. Any improving path within the near-skew manifold must change variables in both parity blocks jointly.

The independently found E=678 exact-574-congruence-sector seed has the same property: exhausting either complete parity block while freezing the other leaves its minimum at 678.

## Exact crossover cubes

`code/nearskew_cube.cpp` turns recombination between two canonical near-skew parents into a complete finite search. If the parents differ in `d` free coordinates, every one of their `2^d` coordinate-wise recombinations is enumerated by Gray code; the implementation periodically recomputes the full energy and near-skew constraints from scratch.

Completed exact examples before the broader elite campaign:

| parents | differing coordinates | states | cube minimum |
| --- | ---: | ---: | ---: |
| 578 incumbent ↔ 622 | 24 | 16,777,216 | 578 |
| 622 ↔ exact-sector 678 | 21 | 2,097,152 | 622 |
| 578 incumbent ↔ exact-sector 678 | 19 | 524,288 | 578 |
| alternating-incumbent ↔ 622 | 25 | 33,554,432 | 578 |
| alternating-incumbent ↔ exact-sector 678 | 24 | 16,777,216 | 578 |

None contains 574.

A broader exact campaign, Actions run `40735211408`, enumerates all 15 parent pairs of dimension at most 25 among eight inequivalent near-skew elites at energies `578, 622, 650, 674, 678, 678, 682, 686`. The union contains roughly 266 million explicitly enumerated recombination states. Its final table should be appended here after the run completes and is independently checked.

## Elite parents mined from historical odd-perfect traces

The parents for the broader campaign were recovered from preserved Actions evidence of the calibrated odd-perfect search, then canonicalized and rescored independently. Representative canonical energies include:

```text
578, 622, 650, 674, 678, 678, 682, 686
```

All eight satisfy odd energy 50 and the canonical near-skew reflection. The two E=678 states are inequivalent in the 50 free coordinates.

This is useful because crossover is only scientifically interesting once parents represent distinct low-energy basins rather than standard LABS symmetry copies of the same state.

## Exact BnB calibration with the forced center bit

The exact-energy-574 congruence analysis implies that, inside canonical near-skew, the center sign is fixed once the even-half sign-sum class is fixed. A temporary calibration patched `code/nearskew_bnb.cpp` to assign that center coordinate at the root instead of branching on it last.

The propagation is sound and materially reduces visited nodes, but it does not make the present BnB formulation competitive enough for a blind full proof. Representative 120-second, four-thread runs:

```text
a = 0:   117,440,514 nodes, 4/1024 prefix tasks completed, timeout
a = -16: 140,509,186 nodes, 47/1024 prefix tasks completed, timeout
a = 16:  108,789,762 nodes, 9/1024 prefix tasks completed, timeout
```

No certificate was found. These are `UNKNOWN` partial traversals, not infeasibility proofs. Future exact work needs a stronger decomposition or bound, not simply more time on this implementation.

## Interpretation

The low-energy near-skew landscape is not a smooth basin around the public record. At least E=622 and E=678 are deeply isolated and are exact global minima under either one-block optimization. Small ordinary edits, small structure-preserving edits, and several complete two-parent recombination cubes all fail to interpolate to a better sequence.

This points toward a qualitatively different next search space:

1. **joint A/B large neighborhoods** — escape must change both parity blocks together;
2. **multi-parent or algebraically defined subspaces** rather than pairwise crossover alone;
3. **controlled exit from odd-perfect / near-skew** into higher odd-energy layers when the structural manifold becomes saturated;
4. stronger exact decompositions that exploit the `A/B` autocorrelation-sum form directly.

These negative results do not prove 578 optimal and do not exclude lower non-near-skew states. They do substantially reduce the value of continuing local polishing of the known low-energy near-skew basins.
