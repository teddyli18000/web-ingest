# 2026-10-28 odd-perfect search outside the near-skew orbit

## Purpose

The calibrated odd-perfect walk repeatedly reaches low energies and often ends at the public `E=578` record or another sequence symmetry-equivalent to the canonical `(+1, skew99)` near-skew manifold. Ordinary Hamming distance is therefore a poor measure of structural diversity.

`code/oddperfect_outside_nss.cpp` instruments the same phase-2 exact odd-perfect walk but separately records the best state whose entire standard 8-element LABS symmetry orbit avoids the canonical near-skew relation

```text
s_p s_{100-p} = (-1)^p,  p=1,...,49.
```

Every reported `BESTSEQ` and `OUTSEQ` was independently rescored with `code/verify.py` inside the Action job.

## Campaign

GitHub Actions run `40634532205` used 8 independent shards. Each shard used 128 random phase-1 odd-perfect starts and 100,000 exact odd-perfect phase-2 steps, for 1,024 starts total. Four tabu-tenure ranges were used twice.

| shard | tenure | best overall | best outside near-skew orbit |
| ---: | ---: | ---: | ---: |
| 0 | 3..10 | 622 | **1162** |
| 1 | 5..15 | 578 | **1162** |
| 2 | 7..21 | 578 | **1162** |
| 3 | 10..30 | 678 | **1162** |
| 4 | 3..10 | 578 | **1162** |
| 5 | 5..15 | 578 | **1162** |
| 6 | 7..21 | 622 | **1162** |
| 7 | 10..30 | 702 | **1162** |

The eight independently obtained `E=1162` outputs are all standard LABS symmetry images of the **same** sequence orbit.

One representative is

```text
+--+-+-+-+-++-+---+-+--++-+---+--++--++-+-+--+-++-+----++++------++--++---+----++-----+----+++++++++
```

Its exact decomposition is

```text
E = 1162
odd energy = 50
even energy = 1112
parity-half sums = (0,-10)
```

This is empirical search evidence, not a proof that 1162 is the optimum outside the near-skew orbit. What is striking is the reproducibility: all eight shards converge to exactly the same outside structural basin.

## New structural classification: 3-bit boundary + skew97 core

The `E=1162` orbit is not unstructured. In the representative above, positions `3..99` (zero-based) form a length-97 skew-symmetric sequence exactly.

The center of this suffix is global position `51`. For every `p=3,...,50`,

```text
s_p s_{102-p} = (-1)^(51-p).
```

All 48 equalities hold exactly. Equivalently, if

```text
t_j = s_{3+j},  j=0,...,96,
```

then

```text
t_{48+r} = (-1)^r t_{48-r},  r=1,...,48.
```

So the strongest odd-perfect state found outside the `1 + skew99` family is naturally a

```text
3-bit prefix + skew97 tail
```

state.

This changes the useful representation of the search space. Rather than a binary distinction between “near-skew” and “everything else”, the observed low-energy odd-perfect basins suggest a hierarchy of odd boundary lengths:

```text
d = 1:  1-bit boundary + skew99 core   -> public E=578 record basin
d = 3:  3-bit boundary + skew97 core   -> reproducible E=1162 outside basin
d = 5:  5-bit boundary + skew95 core   -> to investigate
d = 7:  7-bit boundary + skew93 core   -> to investigate
...
```

The standard LABS reversal/negation/alternation symmetries can move the boundary to the opposite side or change orientation, so classification must be performed over the full symmetry orbit.

## Exact local move structure at E=1162

Exhaustive one-/two-bit odd-perfect neighborhoods of the representative give:

```text
legal 1-bit moves: 0
legal 2-bit moves: 27
```

All 27 legal double flips are reflection pairs with

```text
p + q = 102,
```

the mirror axis of the skew97 suffix. Every such legal neighbor has energy strictly above 1162; the lowest is 1346. Thus this state is a strict local minimum of the exact weight-1/2 odd-perfect move graph used by the calibrated walk.

This explains why independent shards repeatedly identify the same `E=1162` outside state: it is a real structured attractor of the search graph, not merely the best random sample observed once.

## Consequence

The next search should not spend more compute merely asking the same strict odd-perfect walk to avoid near-skew. A more informative decomposition is to search fixed **skew-core boundary length** classes directly and ask how the best achievable LABS energy changes with `d=1,3,5,...`.

The immediate tests are:

1. build a classifier for the longest skew-symmetric contiguous core over all LABS symmetry images;
2. optimize the `d=3` family directly and reproduce / improve 1162;
3. search `d=5,7,...` families for substantially lower basins;
4. determine whether transitions between adjacent `d` classes give controlled routes across the large odd-energy barriers seen around the incumbent.

No `E<=574` sequence was found in this campaign.
