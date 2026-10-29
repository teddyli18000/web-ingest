# 2026-10-29 exact shell around the E=678 target-class basin

## Purpose

The target-congruence search found an odd-perfect N=100 sequence in the E=574-compatible global-product class:

```text
---------+--+-+--+--+-++-++++---+----++---++-+++-++---+---++-++--+-+++-++-+---++++---+++++---+-+-+-+
```

Independent scoring gives

```text
E = 678
odd energy = 50
even energy = 628
half sums = (-8,0)
half products = (-1,-1)
```

Because E=574 has global product +1, this basin was more relevant than the public E=578 basin for a direct target-class search. A two-bit tabu probe that preserves global product +1 failed to improve 678, so the next question was whether the basin merely required a slightly larger local move.

## Exact shells

Local exact enumeration found no improvement at small even radii. The decisive completed shell is radius 6, which preserves the global sign product.

GitHub Actions run `40795115127` compiled the durable `code/sphere_shell.cpp` scanner and exhaustively checked

```text
C(100,6) = 1,192,052,400
```

sequences at exact Hamming distance 6.

Runner output:

```text
BASE energy=678
RADIUS radius=6 tested=1192052400 best=974 seconds=250.702
BESTSEQ -+----------+-+--+--+-++-++++--++----++---++-+++-++---++--+++++--+-+++-++-+---++-+---+++++---+-+-+-+
```

The tested count equals `C(100,6)`, so the shell is complete. The reported best sequence was independently rescored by `code/verify.py` inside the job and returned exactly `974`.

Earlier local exact scans gave minima `830` at radius 2 and `902` at radius 4. Thus no same-product sequence within Hamming distance 6 improves the E=678 center.

## Interpretation

The E=678 target-class state is not a shallow local minimum that can be repaired with a 2-, 4-, or 6-bit macro move. Its radius-6 shell is substantially worse than the center.

This is a negative local result, not a lower bound on the unrestricted problem. It argues against spending more compute on concentric Hamming shells around this basin. The higher-value exact direction is structural: odd-perfect sequences outside the now-solved near-skew manifold, especially the low endpoint-defect layers.
