# 2026-10-28 target congruence class for E=574

## Purpose

The public N=100 record has energy 578, while the first possible breakthrough is 574. Because the gap is only four, modular information about the energy can separate the target from the known record basin before doing any search.

This note derives two exact congruence constraints and records a first search restricted to the resulting target class.

## 1. Total energy mod 8 is determined by the global sign product

Let `s` have length `N=100` and flip one position `p`. For lag `k`, let `T_k` be the sum of the one or two products in `C_k` that contain `s_p`. The flip changes

```text
C_k' = C_k - 2 T_k,
```

so

```text
(E'-E)/4 = sum_k (T_k^2 - C_k T_k).
```

Modulo two, `C_k` has the parity of `N-k`, hence the parity of `k`. For odd `k`, the summand is zero modulo two. For even `k`, it is congruent to `T_k` modulo two.

`T_k` is odd exactly when only one of `p-k` and `p+k` lies in the sequence. If `a=p`, `b=N-1-p`, and without loss `a<=b`, the number of positive even `k` with exactly one incident term is

```text
floor(b/2) - floor(a/2).
```

For `N=4m`, using `a+b=4m-1`, this number is always odd (whether `a` is even or odd). Therefore every single-bit flip changes the energy by

```text
E' - E = 4 (mod 8).
```

The all-plus N=100 sequence has

```text
sum_{j=1}^{99} j^2 = 6 (mod 8).
```

Starting from all-plus, an even number of flips gives global product `+1` and an odd number gives global product `-1`. Hence for every N=100 sequence,

```text
global product +1  =>  E = 6 (mod 8),
global product -1  =>  E = 2 (mod 8).
```

Consequences:

- `574 = 6 (mod 8)`, so **every E=574 sequence has global product +1**.
- The public E=578 incumbent has global product `-1`.
- Thus every 574 candidate is at odd Hamming distance from every standard symmetry image of the incumbent (the N=100 LABS symmetries preserve the global product).

This is stronger than the generic `E = 2 (mod 4)` fact used in the problem statement.

## 2. Odd-lag energy mod 16 is determined by the parity-half products

Split the sequence into the 50 even-position and 50 odd-position signs,

```text
A_i=s_{2i}, B_i=s_{2i+1},
a=sum A_i, b=sum B_i.
```

Let `O` be the sum of `C_k^2` over odd lags. Pair odd lags `k` and `100-k`. Write their correlations as odd integers `C,D`. The exact LABS congruence gives

```text
C + D = 0 (mod 4).
```

Write `C+D=4q`. Since `C` is odd,

```text
C^2 + D^2 = 2 + 8q (mod 16).
```

There are 25 such pairs. Also

```text
sum_{k odd} C_k = ab.
```

Therefore

```text
O = 50 + 8 * (ab/4 mod 2)  (mod 16).
```

For a half of length 50, its sign product is `+1` exactly when its sign sum is `2 (mod 4)`, and `-1` exactly when its sign sum is `0 (mod 4)`. Hence

```text
O = 10 (mod 16)  iff both half-products are +1,
O =  2 (mod 16)  otherwise.
```

## 3. Exact target classes inside the odd-perfect layer

An odd-perfect sequence has every odd `|C_k|=1`, so `O=50`. The pair congruence then forces every opposite odd pair to be `(1,-1)` or `(-1,1)`, hence

```text
ab = 0.
```

A 574 target has global product `+1`, so its two half-products are equal. But `O=50 = 2 (mod 16)`, so they cannot both be `+1`. Therefore an odd-perfect 574 target must satisfy

```text
half-product(A) = half-product(B) = -1,
a = b = 0 (mod 4),
ab = 0.
```

After reversal/sign normalization one half sum is zero and the other is nonnegative. Cauchy applied to the 49 even correlations and the exact identity

```text
sum even C = (a^2+b^2-100)/2
```

shows the nonzero half sum is at most 20 for even energy `<=524`. Thus the entire odd-perfect target is contained in only six canonical half-sum classes:

```text
(0,0), (4,0), (8,0), (12,0), (16,0), (20,0).
```

The older generic CP-SAT split included eleven classes `(0,0),(2,0),...,(20,0)`; the odd classes modulo four are now rigorously irrelevant to E=574.

The incumbent has half sums `(10,0)` and half products `(+1,-1)`, so it lies in the wrong congruence class for a breakthrough.

## 4. A natural barrier state and target-class search

Flipping position 0 of the incumbent gives

```text
E = 774
odd energy = 50
half products = (-1,-1)
```

so this is a simple entry point into the correct O=50 target class. Flipping position 50 similarly gives E=806.

`code/oddperfect_targetclass.cpp` performs a strict tabu walk in this class:

- random phase-1 starts are driven to odd energy 50 and retained only when both half products are `-1`;
- phase 2 considers same-parity double flips only, so each half product stays fixed;
- a move is legal only if every odd correlation remains `+/-1`;
- correlations and energies are updated exactly; debug builds independently rescore every 1024 steps.

Small local calibration from the E=774 barrier:

- 16 runs x 30,000 steps: best `E=702`;
- a later 16-run x 100,000-step batch reached **E=678** before the local execution cap.

The E=678 sequence is

```text
---------+--+-+--+--+-++-++++---+----++---++-+++-++---+---++-++--+-+++-++-+---++++---+++++---+-+-+-+
```

Independent exact rescoring gives

```text
E = 678
odd energy = 50
even energy = 628
half sums = (-8,0)
half products = (-1,-1)
```

Random target-class starts were weaker in the first small batch (best 822), so the E=774 boundary transition is currently the better seed.

Direct opposite-parity two-bit flips from the E=774 state and from an independently found E=702 target-class state produced no O=58 state. That is only a local observation, but it agrees with the broader evidence that the first defect layer is separated by a substantial move barrier.

## Interpretation

This does not improve the public record. The useful result is a representation change:

- the known E=578 basin is in a congruence class that **cannot contain E=574**;
- odd-perfect target search should therefore avoid spending most of its effort rediscovering 578;
- the correct O=50 target class is sharply reduced to six half-sum classes and supports a distinct low-energy basin (currently E=678 in the local strict walk).

The strict same-parity double-flip walk is not yet calibrated close enough to 574 to justify a large blind Actions campaign. The next useful algorithmic step is a controlled macro/repair move that remains in global product `+1` but can cross between the O=50,58,66,... target-compatible layers without falling back into the 578 product class.

No E<=574 certificate was found in this experiment.
