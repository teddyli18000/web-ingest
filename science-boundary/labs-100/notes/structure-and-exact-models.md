# Structural observations and exact-model probes

## Incumbent correlation decomposition

For the public `E=578` sequence, every odd-lag autocorrelation is already as small as parity permits:

```text
|C_k| = 1 for all 50 odd k in {1,3,...,99}.
```

Therefore the odd-lag energy is exactly `50`, the absolute minimum possible for any length-100 binary sequence. The remaining `528` units of energy come from the 49 even lags.

This gives a useful conditional target:

- if a candidate also has `|C_k|=1` at every odd lag, then a new record `E<=574` is equivalent to even-lag energy `<=524`;
- if one odd lag grows from magnitude 1 to 3, the odd-lag energy increases by 8, so the even-lag part would need to fall to at most 516 to compensate.

The incumbent's even-lag absolute-value distribution is:

```text
|C|=0 : 12 lags
|C|=2 : 16 lags
|C|=4 : 16 lags
|C|=6 : 4 lags
|C|=8 : 1 lag
```

which gives `16*4 + 16*16 + 4*36 + 1*64 = 528`.

The largest even-lag values include `C_20=6`, `C_40=6`, `C_50=-8`, `C_58=-6`, and `C_76=-6`.

## Even/odd subsequence view

Write the length-100 sequence as an interleaving of two length-50 sequences

```text
A_j = s_{2j},   B_j = s_{2j+1}.
```

Then for `r=1,...,49`,

```text
C_{2r}(s) = C_r(A) + C_r(B).
```

Thus the incumbent's even-lag energy is exactly the combined complementary-defect energy of the pair `(A,B)`. This makes near-complementary-pair constructions a natural structural proposal source.

For odd lags,

```text
C_{2r+1}(s)
 = sum_j A_j B_{j+r}
 + sum_j B_j A_{j+r+1},
```

with the sums truncated to their valid aperiodic ranges. The incumbent satisfies the unusually strong condition that every one of these 50 cross terms sums to `+1` or `-1`.

## Sum identities

Let

```text
S = sum_i s_i,
T = sum_i (-1)^i s_i,
O = sum_{k odd} C_k,
V = sum_{k even, k>0} C_k.
```

The standard polynomial identities at `z=1` and `z=-1` give

```text
O + V = (S^2 - 100)/2,
V - O = (T^2 - 100)/2,
```

hence

```text
V = (S^2 + T^2 - 200)/4,
O = (S^2 - T^2)/4.
```

For the incumbent, `S=T=10`, so both `O` and `V` are zero. These are necessary aggregate constraints, not strong enough by themselves to prove an energy lower bound.

## Exact XOR-cardinality MILP formulation

A full LABS instance can be written as a 0-1 MILP with only the 100 sequence bits integral.

Let `x_i in {0,1}` encode the sign and introduce `y_ij = x_i XOR x_j`. The XOR relation is the convex hull

```text
y >= x_i - x_j
y >= x_j - x_i
y <= x_i + x_j
y <= 2 - x_i - x_j
```

so `y` may remain continuous because binary `x` forces it to 0 or 1.

For lag `k`, define

```text
d_k = sum_i y_{i,i+k},
m_k = 100-k,
C_k = m_k - 2 d_k.
```

The square `C_k^2 = (m_k-2d_k)^2` is a convex integer function. An exact epigraph over integer `d_k` is obtained with one tangent for every integer `r=0,...,m_k`:

```text
z_k >= (8r - 4m_k) d_k + (m_k^2 - 4r^2).
```

At an integer feasible `d_k`, the tangent with `r=d_k` is exact, so minimizing `sum z_k` is exactly the LABS objective rather than an approximation.

### Odd-minimal restricted model

The incumbent structure can be imposed linearly. For odd `k`, `m_k` is odd and `|C_k|=1` is equivalent to

```text
(m_k-1)/2 <= d_k <= (m_k+1)/2.
```

Since `d_k` is integral, this allows exactly the two required values.

Under these odd-minimal constraints, only the 49 even-lag square epigraphs are needed, with target

```text
sum_{k even} z_k <= 524.
```

A prototype has approximately 5,100 variables (100 binary sequence bits, pair-XOR variables, and even-lag epigraph variables) and about 22,000 linear constraints. Symmetry `x_0=x_1=0` is valid using global negation plus alternation.

### Solver probe

A SciPy/HiGHS implementation was tested locally with a 30-second limit. The formulation is exact, but branch-and-bound did not find even a primal feasible solution within that time on the odd-minimal restricted problem. The earlier full-space `E<=574` MILP was similarly weak.

Conclusion: the formulation is mathematically clean and may be useful with a stronger CP-SAT/MIP solver or specialized cuts, but the current HiGHS relaxation/search is too weak to justify a large GitHub Actions campaign.

## Odd-minimal manifold probe

A separate one-bit tabu search minimizing only odd-lag energy can reach the theoretical minimum `50` very quickly from random starts. Typical such sequences have very large even-lag energy (thousands), demonstrating that the condition `|C_k|=1` for every odd lag is not itself rare enough to explain the incumbent's quality.

Experiments that gradually reweight from even-only energy toward the full objective, starting either from random sequences or from the incumbent, did not produce a candidate below 578. The best random-start totals remained in the mid-800s or worse; incumbent-start runs retained the incumbent as their best seen state.

This suggests that the hard part is the intersection of the odd-minimal manifold with exceptionally low complementary defect in the even/odd subsequences, not merely satisfying the odd-lag constraints.

## Golay-pair check

Binary Golay complementary pairs exist at length 100 by Turyn composition. An explicit length-10 Golay pair from the classical construction was verified, all 128 ordered length-10 Golay pairs were enumerated, and all 128^2 direct Turyn products of two length-10 pairs were checked. The best constituent length-100 sequence energy among these direct compositions was `1426`, far above 578.

Therefore ordinary length-100 Golay construction is not directly competitive for the single-sequence LABS objective, despite the useful complementary-pair viewpoint.

## Sources

- Jürgen Willms, *A note on Barker sequences of even length*, arXiv:2104.00502: <https://arxiv.org/abs/2104.00502>
- P. B. Borwein and R. A. Ferguson, *A complete description of Golay pairs for lengths up to 100*, Math. Comp. 73 (2004), 967-985.
- Jonathan Jedwab's Golay complementary sequence overview: <https://www.sfu.ca/~jed/Research/golay.html>
