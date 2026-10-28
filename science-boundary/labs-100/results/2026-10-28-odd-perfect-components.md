# 2026-10-28 odd-perfect small-neighborhood structure

## Question

The calibrated `oddperfect_walk.cpp` search repeatedly returns to the public `E=578` basin from random starts. This note asks whether that behavior can be explained by the move graph used in phase 2: exact Hamming-weight 1 or 2 flips that keep every odd autocorrelation at magnitude 1.

The conclusions below are exact enumerations for the named states. They are **not** a proof that the full odd-perfect manifold has only these components or generators.

## Reproducible scanner

`code/oddperfect_neighborhood.py` enumerates every bit subset of a requested weight (through 4), applies the flip exactly at the correlation-vector level, and retains the move iff every odd `|C_k|` is still 1. It reports the exact full LABS energy of each legal neighbor.

## Incumbent component

For the public `N=100, E=578` incumbent, exhaustive small-neighborhood enumeration gives:

| exact flip weight | number of odd-perfect moves |
| ---: | ---: |
| 1 | 2 |
| 2 | 50 |
| 3 | 98 |
| 4 | 1,225 |

The two legal single flips are positions `0` and `50` (zero-based indexing).

The weight-2 legal set is exactly

```text
(0,50)
and
(p,100-p) for p=1,...,49.
```

The weight-3 and weight-4 legal subsets introduce no new obvious low-weight direction beyond combinations of these singleton/mirror-pair generators. In particular `1,225 = C(50,2)` at weight 4 is consistent with choosing two of the 50 pair generators.

This explains why a phase-2 walk restricted to weight-1/2 odd-perfect moves can spend enormous compute while repeatedly returning to the same low-energy structural family: around the incumbent its legal move graph is extremely sparse and organized.

## E=622 state: far in ordinary Hamming distance, but still near-skew

The independently verified odd-perfect `E=622` sequence from Actions run `40612938897` is

```text
++--+--+++++++++++++++-------++++--+--+--+--+++--+---++-++---+++---++-+--+-+-+--+-+-+-+-+-+-+--+++--
```

It has odd energy `50`, even energy `572`, and minimum ordinary Hamming distance `47` from the incumbent symmetry orbit.

Its exact small-neighborhood counts are the same as for the incumbent:

| exact flip weight | number of odd-perfect moves |
| ---: | ---: |
| 1 | 2 |
| 2 | 50 |
| 3 | 98 |
| 4 | 1,225 |

A later structural audit explains why this match is less surprising than it initially appeared. The `E=622` state itself satisfies

```text
s_p s_{100-p} = (-1)^p,  p=1,...,49,
```

so positions `1..99` are a length-99 skew-symmetric tail exactly as for the incumbent. In the corrected 50 near-skew free coordinates, `E=622` is radius `24` from the incumbent; that paired-coordinate distance corresponds to ordinary Hamming distance `47` because one center coordinate flips a single bit and the others flip mirror pairs.

Therefore this state is **not** evidence that the 2-single/50-pair generator structure occurs in a distinct non-near-skew component. It is another distant point of the same near-skew structural manifold.

## The pattern is not universal

A representative higher-energy odd-perfect state found during phase-1 search is

```text
-----++-+--++--++--++----++-+++-+++-+--+-++++-+--++++-+----++++-+++-+++--+-++--++--++--++++--+-+---+
```

Its exact energy is `5098`; its parity-half sums are `(a,b)=(6,0)`. It is odd-perfect but does not have the same low-weight neighborhood: it has only one legal single flip and 27 legal double flips. Therefore the mirror-pair basis is a property of structured regions, not a theorem for all odd-perfect sequences.

Examples with the other parity half carrying the zero sum show an analogous shifted mirror pattern. This supports a component-/orientation-based view of the manifold rather than one universal move basis.

## Implication for search design

The current calibrated kernel is valuable because random phase-1 construction plus strict phase-2 walking repeatedly rediscovers `E=578`. But simply extending the same strict walk is unlikely to map qualitatively different low-energy regions efficiently.

Two follow-ups are now more informative:

1. explicitly track the best odd-perfect state whose entire 8-element LABS symmetry orbit is outside the near-skew manifold (`code/oddperfect_outside_nss.cpp`);
2. search the near-skew manifold globally using its own 50-variable representation instead of interpreting ordinary Hamming distance as structural diversity.

Controlled excursions through higher odd-energy layers remain another route, but existing coarse penalty/homotopy probes were poorly calibrated and should not simply be scaled unchanged.

## Verification status

- All neighborhood counts above are exact exhaustive subset counts for the named sequence and weight.
- `E=622` was independently rescored by `code/verify.py` in Actions run `40612938897`.
- The near-skew reclassification was independently checked from the explicit reflection relation above.
- No `E<=574` sequence was found in these neighborhood scans.
