# 2026-10-28 exact near-skew global-move experiments

## Question

The strongest known N=100 LABS states repeatedly lie in the canonical near-skew manifold `s=(+1,skew99)`, where all odd-lag correlations have magnitude one. Small local moves around the public `E=578` record and the independently found `E=622` basin are strongly negative. This note tests two much larger move classes exactly:

1. complete coordinate-wise crossover cubes between distinct low-energy near-skew parents;
2. alternating exact global best responses of the two parity blocks.

These are intended to test whether the failure of local search is merely a neighborhood-size issue.

No `E<=574` certificate was found.

## Exact elite crossover campaign

`code/nearskew_cube.cpp` takes two canonical near-skew parents that differ in `d` free coordinates and enumerates every one of their `2^d` coordinate-wise recombinations by Gray code. It periodically recomputes the full N=100 LABS energy and verifies that odd energy remains 50 and the near-skew relation remains exact.

GitHub Actions run `40735211408` exhausted all 15 parent pairs of dimension at most 25 among eight inequivalent canonical elites with energies

```text
578, 622, 650, 674, 678a, 678b, 682, 686.
```

The complete evidence table is:

| parents | dimension | states | exact cube minimum | minimum count |
| --- | ---: | ---: | ---: | ---: |
| 578–622 | 24 | 16,777,216 | 578 | 1 |
| 578–678a | 25 | 33,554,432 | 578 | 1 |
| 578–686 | 20 | 1,048,576 | 578 | 1 |
| 622–650 | 25 | 33,554,432 | 622 | 1 |
| 622–674 | 24 | 16,777,216 | 622 | 1 |
| 622–678a | 21 | 2,097,152 | 622 | 1 |
| 622–678b | 19 | 524,288 | 622 | 1 |
| 622–682 | 24 | 16,777,216 | 622 | 1 |
| 650–678b | 24 | 16,777,216 | 650 | 1 |
| 650–682 | 25 | 33,554,432 | 650 | 1 |
| 674–678a | 25 | 33,554,432 | 674 | 1 |
| 674–678b | 21 | 2,097,152 | 674 | 1 |
| 678a–678b | 24 | 16,777,216 | 678 | 2 |
| 678a–686 | 25 | 33,554,432 | 678 | 1 |
| 678b–682 | 23 | 8,388,608 | 678 | 1 |

Total explicitly enumerated states:

```text
265,814,016
```

Every job independently passed the full-energy check on its reported winner. In all 15 cubes, the minimum is exactly the better endpoint energy. The only count greater than one is the equal-energy `678a–678b` cube, where both endpoint basins attain 678.

Thus, for this collection of the strongest currently available inequivalent near-skew parents, **pairwise coordinate crossover has been exactly exhausted rather than merely sampled**. It gives no synergistic child at all, not just no record child.

## Exact parity-block decomposition

Write the N=100 sequence as its even and odd positions

```text
A_j = s_{2j},
B_j = s_{2j+1},
j=0,...,49.
```

After global-sign and alternating-sign normalization `s0=s1=+1`, canonical near-skew gives:

- 25 independent `A` coordinates;
- 24 independent `B` coordinates modulo the alternating symmetry;
- odd energy identically 50;
- for `r=1,...,49`,

```text
C_{2r}(s) = C_A(r) + C_B(r).
```

Define

```text
D_r = (C_A(r)+C_B(r))/2.
```

Then exactly

```text
E(s) = 50 + 4 * sum_r D_r^2.
```

The public record `E=578` has `sum D_r^2=132`; a near-skew Few Shots certificate requires `sum D_r^2<=131`.

This turns the near-skew target into a structured closest-pair problem between `2^25` possible `A` autocorrelation vectors and `2^24` possible `B` autocorrelation vectors.

## Exact one-block optimization

`code/nearskew_block.cpp` freezes one parity block and exhausts every assignment of the other. Periodic full rescoring protects the Gray-code incremental path.

For the independently verified `E=622` basin:

```text
fixed B, enumerate all 2^25 A assignments: minimum 622, count 1
fixed A, enumerate all 2^24 B assignments: minimum 622, count 1
```

The tested `E=678` exact-574-congruence-sector basin has the same property: the complete A block and complete B block both return the seed itself as the unique best response.

Therefore these states are **blockwise global minima**. Escaping them inside near-skew requires a genuinely joint A/B move.

## Exact-block coordinate descent from random starts

`code/nearskew_block_descent.cpp` starts from a random canonical near-skew state. Each A step enumerates all `2^25` A assignments and installs the exact best response to the current B. Each B step enumerates all `2^24` B assignments and installs the exact best response to the current A. It stops at a blockwise fixed point.

GitHub Actions run `40736172380` used eight independent seeds. Every final sequence was independently rescored by `code/verify.py`.

| seed | initial E | final E | exact block states tested |
| ---: | ---: | ---: | ---: |
| 101 | 5110 | **818** | 150,994,944 |
| 211 | 4950 | 862 | 150,994,944 |
| 307 | 5738 | 954 | 150,994,944 |
| 401 | 5010 | 850 | 201,326,592 |
| 503 | 5478 | 922 | 201,326,592 |
| 601 | 4106 | 966 | 100,663,296 |
| 701 | 3990 | 974 | 150,994,944 |
| 809 | 5982 | 866 | 150,994,944 |

Total exact block states enumerated across the calibration:

```text
1,258,291,200
```

Best final energy is only `818`. The runs converge rapidly to blockwise fixed points, but those fixed points are far above the known 622 and 578 basins. This method is therefore not calibrated well enough to justify more random starts unchanged.

## Interpretation

These experiments reject two natural explanations for the difficulty of the N=100 record basin.

First, the obstacle is not that genetic crossover sampled too few children: 265.8 million complete pairwise recombinations among eight strong, inequivalent parents contain no synergy at all. Second, the obstacle is not merely that one-bit or paired-bit neighborhoods are too small: exact global optimization of an entire 24/25-variable parity block still converges from random starts to high-energy fixed points.

The useful representation is now the scaled complementary-pair objective

```text
minimize  sum_r D_r^2,
D_r=(C_A(r)+C_B(r))/2,
```

under the palindrome/anti-palindrome constraints inherited from near-skew. The threshold is only `131` versus the incumbent value `132`, but the closest-pair sets have sizes `2^25` and `2^24`.

The next near-skew work should therefore target the **joint closest-pair problem** directly (exact feasibility, branch-and-bound, projection/hash search, or stronger algebraic bounds), rather than more pairwise crossover or block-coordinate descent. If those approaches also saturate, the higher-value move is to leave the near-skew/odd-perfect manifold and search controlled higher odd-energy layers.
