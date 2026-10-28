# 2026-10-28 odd-perfect small-neighborhood structure

## Question

The calibrated `oddperfect_walk.cpp` search repeatedly returns to the public `E=578` basin from random starts. This note asks whether that behavior can be explained by the move graph used in phase 2: exact Hamming-weight 1 or 2 flips that keep every odd autocorrelation at magnitude 1.

The conclusions below are exact enumerations for the named states. They are **not** a proof that the full odd-perfect manifold has only these components or generators.

## Reproducible scanner

`code/oddperfect_neighborhood.py` enumerates every bit subset of a requested weight (through 4), applies the flip exactly at the correlation-vector level, and retains the move iff every odd `|C_k|` is still 1. It reports the exact full LABS energy of each legal neighbor.

Example:

```bash
python3 science-boundary/labs-100/code/oddperfect_neighborhood.py \
  '++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-' \
  --max-weight 2
```

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

The weight-3 and weight-4 legal subsets found by exhaustive enumeration introduce no new obvious low-weight direction beyond combinations of these same singleton/mirror-pair generators. In particular the weight-4 count `1,225 = C(50,2)` is consistent with choosing two of the 50 legal pair generators.

This is a structural explanation for why a phase-2 walk restricted to weight-1/2 odd-perfect moves can spend enormous compute while repeatedly returning to the same low-energy basin: around the incumbent its legal move graph is extremely sparse and highly organized.

## Far `E=622` basin

The independently verified odd-perfect `E=622` sequence from Actions run `40612938897` is

```text
++--+--+++++++++++++++-------++++--+--+--+--+++--+---++-++---+++---++-+--+-+-+--+-+-+-+-+-+-+--+++--
```

It has odd energy `50`, even energy `572`, and minimum Hamming distance `47` from the incumbent symmetry orbit.

Its exact small-neighborhood counts are the same as for the incumbent:

| exact flip weight | number of odd-perfect moves |
| ---: | ---: |
| 1 | 2 |
| 2 | 50 |
| 3 | 98 |
| 4 | 1,225 |

Again the legal weight-1/2 moves have the same mirror-pair form. Thus this sparsity is not merely a consequence of being one or two flips from the record sequence: it appears in at least one inequivalent low-energy basin almost half the Boolean cube away.

## The pattern is not universal

A representative higher-energy odd-perfect state found during phase-1 search is

```text
-----++-+--++--++--++----++-+++-+++-+--+-++++-+--++++-+----++++-+++-+++--+-++--++--++--++++--+-+---+
```

Its exact energy is `5098`; its parity-half sums are `(a,b)=(6,0)`. It is odd-perfect but does not have the same low-weight neighborhood: it has only one legal single flip and 27 legal double flips. Therefore the 2-single/50-pair mirror structure should be treated as a property of specific structured components, not a theorem for all odd-perfect sequences.

Likewise, examples with the *other* parity half carrying the zero sum show an analogous but shifted mirror pattern. This supports a component-oriented view of the manifold rather than one universal move basis.

## Implication for search design

The current calibrated kernel is still valuable: its random phase-1 construction plus strict phase-2 walk has repeatedly rediscovered `E=578`, which earlier unrestricted CPU probes did not. But merely extending the same strict 1/2-bit phase-2 walk is unlikely to explore qualitatively new low-energy components efficiently.

The next search mechanisms should therefore permit controlled excursions outside odd-perfect and then repair back, or use an exact conditional solver/recombination step to move between distinct low-energy components. This is a change of search representation, not a claim that `E=578` is locally or globally optimal within the whole odd-perfect manifold.

## Verification status

- All neighborhood counts above are exact exhaustive subset counts for the named sequence and weight.
- `E=622` was independently rescored by `code/verify.py` in Actions run `40612938897`.
- No `E<=574` sequence was found in these neighborhood scans.
