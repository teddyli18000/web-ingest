# 2026-10-28 exact arithmetic constraints in the N=100 near-skew manifold

## Setup

Use the canonical near-skew orientation

```text
s = (+1, t)
```

where `t` is a length-99 skew-symmetric sequence. In zero-based full-sequence coordinates this is equivalent to

```text
s_p s_{100-p} = (-1)^p,  p=1,...,49.
```

All odd-lag correlations of `s` have magnitude one, so their total energy is exactly `50`. A Few Shots breakthrough `E<=574` inside this manifold therefore requires even-lag energy at most `524`.

The identities below are exact necessary conditions. They are used only as redundant propagation / lower bounds; they do not assume that a target solution exists.

## 1. Even correlations of a length-99 skew tail are 3 mod 4

Write the tail indices as `0,...,98`, with center 49. Skew symmetry gives

```text
t_{49+r} = (-1)^r t_{49-r}.
```

For even shift `k=2r`, pair the terms of

```text
C_{2r}(t) = sum_{i=0}^{98-2r} t_i t_{i+2r}
```

under `i <-> 98-2r-i`. The two products in every noncentral pair are equal. The single central product, at `i=49-r`, is `(-1)^r`. There are `49-r` paired products. Modulo four,

```text
C_{2r}(t)
  = (-1)^r + 2 * (sum of 49-r signs)
  ≡ (-1)^r + 2(49-r)
  ≡ 3 (mod 4).
```

Thus, for every `r=1,...,49`,

```text
C_{2r}(t) ≡ 3 (mod 4).
```

## 2. The full N=100 even-correlation residue encodes one sequence bit

Because `s=(+1,t)`,

```text
C_k(s) = t_{k-1} + C_k(t).
```

For even `k=2r`, `t_{k-1}=s_k`, so the previous result yields

```text
C_k(s) ≡ 3 + s_k ≡ 1 - s_k (mod 4).
```

Equivalently, writing

```text
d_r = C_{2r}(s)/2,
```

we have

```text
d_r even  <=> s_{2r}=+1,
d_r odd   <=> s_{2r}=-1.
```

This is now stated explicitly in `code/cpsat_nearskew.py` as

```text
C_k = 4 h_k + 2 x_k,
```

where `x_k=1` represents sign `-1`.

## 3. Sign-sum class fixes the number of odd scaled correlations

Let the 50 even-position signs of the length-100 sequence have sum

```text
a = s_0 + s_2 + ... + s_98.
```

The normalization fixes `s_0=+1`. If `m` of the remaining 49 even-position signs are negative, then

```text
a = 50 - 2m,
m = (50-a)/2.
```

By the residue result above, **exactly `m` of the 49 integers `d_r` are odd**.

The parity-half identity gives

```text
sum_{r=1}^{49} C_{2r} = (a^2-100)/2,
```

hence

```text
sum_{r=1}^{49} d_r = (a^2-100)/4.
```

Finally,

```text
E_even = 4 * sum d_r^2.
```

So every near-skew sign-sum class has the following purely arithmetic relaxation:

- 49 integer variables `d_r`;
- exactly `(50-a)/2` are odd;
- their sum is `(a^2-100)/4`;
- target requires `4 sum d_r^2 <= 524`.

## 4. Consequences: energy mod 8 and two classes excluded without search

Because `d^2 mod 2` equals the parity of `d`,

```text
E_even ≡ 4m (mod 8).
```

Therefore, when `m` is even, a nominal cap `524` tightens to `520`; when `m` is odd, `524` is attainable modulo eight.

The minimum possible square sum under only the count/parity/sum conditions above can be computed exactly by splitting the required total between the odd and even `d_r` groups and equalizing the integers inside each group. The resulting arithmetic lower bounds are:

| `a` | odd `d_r` count `m` | `sum d_r` | arithmetic min `E_even` | effective target cap |
| ---: | ---: | ---: | ---: | ---: |
| -20 | 35 | 75 | **556** | 524 |
| -18 | 34 | 56 | 312 | 520 |
| -16 | 33 | 39 | 180 | 524 |
| -14 | 32 | 24 | 128 | 520 |
| -12 | 31 | 11 | 124 | 524 |
| -10 | 30 | 0 | 120 | 520 |
| -8 | 29 | -9 | 116 | 524 |
| -6 | 28 | -16 | 112 | 520 |
| -4 | 27 | -21 | 108 | 524 |
| -2 | 26 | -24 | 104 | 520 |
| 0 | 25 | -25 | 100 | 524 |
| 2 | 24 | -24 | 96 | 520 |
| 4 | 23 | -21 | 92 | 524 |
| 6 | 22 | -16 | 88 | 520 |
| 8 | 21 | -9 | 84 | 524 |
| 10 | 20 | 0 | 80 | 520 |
| 12 | 19 | 11 | 76 | 524 |
| 14 | 18 | 24 | 120 | 520 |
| 16 | 17 | 39 | 244 | 524 |
| 18 | 16 | 56 | 384 | 520 |
| 20 | 15 | 75 | **540** | 524 |

Therefore `a=-20` and `a=20` are **strictly impossible** for an `E<=574` near-skew solution, before considering any binary-sequence realizability constraints. The remaining 19 sign-sum classes require exact search.

For the incumbent, `a=10`, so `m=20`, `sum d_r=0`, and its even energy `528` has the required residue `0 mod 8`. A breakthrough in the same `a=10` class must therefore have even energy at most `520`, not merely 524.

## Use in exact solvers

- `code/cpsat_nearskew.py` states the mod-4 correlation/bit relation explicitly and tightens each fixed sign-sum class to its attainable mod-8 cap. The two impossible `±20` classes collapse to immediate contradictions.
- `code/nearskew_bnb.cpp` uses the same residue at partial nodes, the class arithmetic lower bound, the fixed correlation-sum convex relaxation, and the standard fixed-product interval bound.

These constraints are independent of solver heuristics. A solver timeout remains `UNKNOWN`; only a complete branch-and-bound traversal, CP-SAT `INFEASIBLE`, or a verified certificate is decisive.

## Related literature

The fixed-product correlation lower bound and outer-in branching used by the independent branch-and-bound are standard exact LABS ideas reviewed by Packebusch & Mertens and Prestwich. The mod-4 / sign-sum reductions above are specialized here to the N=100 extension of a length-99 skew tail.

- Packebusch & Mertens, *Low Autocorrelation Binary Sequences*, J. Phys. A 49 (2016), arXiv:1512.02475: <https://arxiv.org/abs/1512.02475>
- Prestwich, *Improved Branch-and-Bound for Low Autocorrelation Binary Sequences*, arXiv:1305.6187: <https://arxiv.org/abs/1305.6187>
