# 2026-10-28 exact-E=570 low-odd structure

## Why 570 matters

Few Shots accepts any energy below 578. Length-100 energies are 2 modulo 4, so after the first candidate layer 574 the next possible score is 570. Exact 570 is in the opposite mod-8 product class from exact 574:

```text
E = 570 = 2 (mod 8)  =>  global sign product = -1.
```

This follows from the exact N=100 congruence recorded in `2026-10-28-target-congruence.md`.

## Odd-perfect layer O=50

If all 50 odd correlations have magnitude one, then every opposite odd-lag pair is `(1,-1)` or `(-1,1)`, and therefore the product of the parity-half sums satisfies

```text
ab = 0.
```

For a length-50 sign half, product `+1` is equivalent to half sum `2 mod 4`, while product `-1` is equivalent to half sum `0 mod 4`. Since exact E=570 has global product `-1`, the two parity-half products must be opposite. Up to swapping/reversal normalization, the zero half has sum 0 and the nonzero half has sum

```text
b = 2 (mod 4), b >= 0.
```

The even-lag energy budget is

```text
570 - 50 = 520.
```

Using

```text
sum_even C = (b^2 - 100)/2
```

and Cauchy on the 49 even correlations,

```text
(sum_even C)^2 <= 49 * 520,
```

leaves exactly five canonical half-sum classes:

```text
(2,0), (6,0), (10,0), (14,0), (18,0).
```

The public E=578 incumbent is O=50 with half sums `(10,0)`, so its structural class survives at exact 570 even though the incumbent itself is eight energy units too high.

## O=58 is impossible at exact 570

For N=100,

```text
O = 10 (mod 16)
```

holds exactly when both parity-half products are `+1`. But O=58 is `10 mod 16`, which would force global product `+1`, contradicting the exact-E=570 requirement global product `-1`.

Hence the entire O=58 layer can be omitted from an exact-570 search.

More generally, exact 570 can only occupy even odd-defect indices `t` in `O=50+8t`; the first layers are O=50,66,82,... .

## Interaction with the incumbent neighborhood exclusion

The incumbent's ordinary Hamming shells through radius 7 are exhaustively known to contain no sequence below 578. Therefore an exact E=570 sequence in the `(10,0)` class, if it exists, must be at Hamming distance at least 8 from the incumbent (and likewise from every standard symmetry image by Hamming-isometric symmetry).

This makes exact-570/O=50 a useful targeted exact problem: it shares the incumbent's strongest odd-lag structure, but the known local ball can be excluded immediately.

No E<=574 sequence is claimed here; these are necessary structural reductions for subsequent exact search.
