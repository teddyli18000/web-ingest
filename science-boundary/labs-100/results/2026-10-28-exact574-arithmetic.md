# 2026-10-28 exact-E=574 arithmetic decomposition

## Scope

This note is about the **exact energy layer E=574**, the first energy below the public record 578. It is not by itself an exhaustive search for every Few Shots breakthrough `E <= 574`: energies 570, 566, ... alternate between the two global-product mod-8 classes and must remain in a complete breakthrough search.

The goal is to replace generic search with exact necessary arithmetic conditions on the 99 autocorrelations before invoking SAT/CP-SAT or sequence enumeration.

## Inputs

Write the odd-lag energy as

```text
O = 50 + 8t
```

because each of the 50 odd correlations is odd. For exact total energy 574, the even-lag energy is

```text
V = 524 - 8t = 4(131 - 2t).
```

For even lags write

```text
d_r = C_{2r}/2, r=1,...,49.
```

Then

```text
sum_r d_r^2 = 131 - 2t.
```

The exact-E=574 product congruence proved in `2026-10-28-target-congruence.md` gives global sign product `+1`.

## Odd opposite-pair DP

Pair each odd lag `k=1,3,...,49` with `100-k`. Let

```text
x = C_k, y = C_{100-k}.
```

Both are odd and the exact LABS congruence gives

```text
x + y = 0 (mod 4).
```

Define the pair defect

```text
w = (x^2 + y^2 - 2)/8 >= 0,
q = (x+y)/4.
```

Across the 25 pairs,

```text
sum w = t,
sum q = ab/4,
```

where `a,b` are the sums of the 50 even-position and 50 odd-position signs. `code/target_arithmetic.py` enumerates the exact bounded `(w,q)` choices for every lag pair and performs a finite DP over `(t,ab/4)`.

## Even opposite-pair DP

For `r=1,...,24`, pair `d_r` with `d_{50-r}`. The opposite-lag mod-4 congruence implies the two integers have the same parity. The middle value `d_25=C_50/2` is odd because exact E=574 has global product `+1`.

The DP tracks

```text
Q = sum d_r^2,
S = sum d_r,
T = sum (-1)^r d_r.
```

The first two are tied to the target and parity-half sums by

```text
Q = 131 - 2t,
S = (a^2+b^2-100)/4.
```

For the third, split the sequence into residue classes modulo 4. Let `q_j` be the sum of the 25 signs in positions `j mod 4`, so every `q_j` is odd. Put

```text
u = q_0-q_2,
v = q_1-q_3.
```

Evaluating the sequence polynomial at `z=i` gives

```text
u^2+v^2 = 100 + 4T,
```

while

```text
q_0+q_2=a,
q_1+q_3=b.
```

The script enumerates these residue-class possibilities exactly and intersects them with the even-correlation DP.

## Exact-E=574 half-sum classes

The resulting low-odd-defect layers are:

| t | odd energy O | canonical `(|a|,|b|)` classes that survive the arithmetic DP |
| ---: | ---: | --- |
| 0 | 50 | `(0,0),(4,0),(8,0),(12,0),(16,0),(20,0)` |
| 1 | 58 | `(2,2)` |
| 2 | 66 | `(0,0),(4,0),(8,0),(12,0),(16,0),(20,0)` |
| 3 | 74 | `(2,2),(6,2)` |
| 4 | 82 | `(0,0),(4,0),(4,4),(8,0),(12,0),(16,0)` |
| 5 | 90 | `(2,2),(6,2),(10,2)` |

The `t=0` and `t=1` rows independently reproduce the previously derived O=50 and O=58 structures. This is a useful regression check that the independent arithmetic formulation is consistent.

For `t=2` (O=66), this has a concrete consequence for **exact E=574**: the `double-same` odd-defect pattern has `ab=+/-8`, normalized half sums `(2,4)`, and is therefore in the wrong global-product class. It cannot realize energy exactly 574. It must nevertheless remain in the broader `E<=574` search because it could in principle realize 570, 562, ... .

At the opposite end of the odd-energy budget, `t=64` and `t=65` have no arithmetic profile at all for exact E=574. The complete output for all `t=0..65` is reproducible with `code/target_arithmetic.py`.

## Classical branch-and-bound benchmark

Before building this arithmetic decomposition, a local implementation reproduced the Packebusch-Mertens combined bound and their tighter chain relaxation for an outside-in branch-and-bound tree, specialized to the exact-E=574 threshold.

The result explains why a generic N=100 proof is not the right immediate route:

- through outer shell `m=10` (20 fixed border signs), both bounds prune **zero** nodes;
- on 3,000 random border assignments per depth, the tight/combined bound rejected only `1/3000` at `m=16`, `12/3000` at `m=20`, `116/3000` at `m=24`, `666/3000` at `m=28`, and `1193/3000` at `m=30`;
- the tight bound was materially more expensive per node while essentially identical to the combined bound until very deep in this N=100, threshold-574 setting.

This is consistent with the published role of the Wiggenbrock/Prestwich combined bound: it is powerful for exact optimization through the mid-60s, but N=100 remains far beyond that regime without additional target-specific structure.

## Search implication

The promising exact decomposition is therefore:

1. choose a small odd-energy layer `t` and its finite odd-pair defect pattern;
2. restrict to the arithmetic-surviving half-sum classes above;
3. enforce the even square budget and Fourier identities directly in the exact model;
4. report `INFEASIBLE` only when the solver proves it; timeouts remain `UNKNOWN`.

The currently running O=66 CP-SAT campaign was launched before this exact-E=574 arithmetic refinement. Its `double-same` case is still scientifically relevant to the broader `E<=574` target, while its `single18` and `double-mixed` cases can later be split by the six exact-574 half-sum classes if needed.

No E<=574 certificate was found in this work.

## Sources

- Packebusch & Mertens, *Low Autocorrelation Binary Sequences*, J. Phys. A 49 (2016), arXiv:1512.02475.
- Prestwich, *Improved Branch-and-Bound for Low Autocorrelation Binary Sequences*, arXiv:1305.6187.
