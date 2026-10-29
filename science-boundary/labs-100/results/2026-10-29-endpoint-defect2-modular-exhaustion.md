# Exact exclusion of the odd-perfect endpoint-defect-2 layer

Date: 2026-10-29

## Statement

For length-100 binary sequences with odd energy `O=50`, let `R=s[0..98]` and define the right endpoint-deletion defect support as the odd lags `k in {1,3,...,97}` for which `C_k(R) != 0`. After using reversal to orient an endpoint of minimum defect to the right, the complete invariant-defect-2 target layer has exactly two nonzero right-deletion odd correlations.

The exhaustive search recorded here proves:

> There is no odd-perfect length-100 sequence with invariant endpoint defect `d=min(d_L,d_R)=2` and total LABS energy `E<=574`.

This is a structural exclusion only. It does not exclude defect `d>=3`, nor odd-energy layers `O>50`.

## Why the half-sum coverage is complete

Write the parity-half sums as

```text
A = sum_i s_{2i},
B = sum_i s_{2i+1}.
```

For the right deletion `R`, the exact identity

```text
sum_{k odd} C_k(R) = A(B-s_99)
```

combined with two nonzero deletion correlations, each equal to `+/-2`, gives the complete target coverage after reversal:

- `A=0` and `|B| in {0,2,...,20}`; or
- `B=0` and `|A|=4`.

For the first branch, the admissible even-energy cap is `524` when `|B| == 0 (mod 4)` and `520` when `|B| == 2 (mod 4)`. For `|A|=4,B=0`, the cap is `524`.

This merges the previous 12 per-support half-sum classes into three signed linear branches: `A=0`, `(A,B)=(+4,0)`, and `(-4,0)`.

## Reflection linearization

Fix a two-lag right support. Reflection inversion determines the set of bad mirror coordinates. After normalizing one bad coordinate and enumerating the remaining bad-coordinate ratios plus the endpoint sign, all 49 odd-perfect conditions become integer linear equations in the remaining `+/-1` variables.

The previous solver searched those variables directly. The new solver first performs Gaussian elimination modulo 257 and enumerates only the free variables of the reduced system.

This modular step is safe as an exact filter. For every defect-2 system generated here, each original integer equation satisfies

```text
abs(rhs) + sum(abs(coefficients)) < 257.
```

Therefore a `+/-1` assignment satisfying the equation modulo 257 satisfies the original integer equation exactly; a nonzero residual cannot wrap by 257.

## Alternating-sign symmetry quotient

The LABS symmetry

```text
t_i = (-1)^i s_i
```

preserves total energy, the right deletion support, and `|A|,|B|`, while changing the sign of `s_0 s_1`. Global negation does not change `s_0 s_1`. Hence every target orbit has exactly one representative with

```text
s_0 s_1 = +1.
```

In the reflection coordinates this is the additional linear condition `u_0=u_1`. Adding it reduced the full defect-2 free-variable enumeration from about 3.88 billion assignments to 2.20 billion without removing any target orbit.

## Exhaustion

There are

```text
C(49,2) = 1176
```

possible two-lag supports. The final solver was compiled with

```text
g++ -O3 -march=native -fopenmp -std=c++20
```

and run on all support indices `[0,1176)` in 12 disjoint contiguous ranges with five threads. Every range returned

```text
complete=1 found=0 stopped=0
```

The aggregate final workload was:

```text
systems=53,586
inconsistent linear systems=39,687
prepared consistent systems=13,899
free assignments enumerated=2,195,571,814
+/-1 modular candidates=639,865,078
target-half-sum candidates checked=432,096,948
maximum reduced nullity=24
```

The exact per-range transcript is preserved in `2026-10-29-endpoint-defect2-modular-exhaustion.log`.

## Independent implementation check

A separate Python reconstruction of the reflection equations, modular RREF, `u_0=u_1` symmetry condition, and half-sum branches matched the C++ solver exactly on four representative supports:

```text
support   systems  inconsistent  enum    pm_candidates  target_checked  maxnull
1,3       48       42            6       6              4               0
95,97     48       44            4       4              4               0
1,49      24       20            12288   8192           7326            12
25,49     24       20            262144  11194          10756           16
```

The C++ solver reports the same counts for all four cases. Any candidate reaching the energy cap is also rescored by a separate full autocorrelation calculation before it can be reported as a hit.

## Implementation notes

The final implementation uses two levels of compute compression:

1. algebraic reduction to the modular nullspace;
2. a flattened OpenMP queue of assignment chunks, not one job per support/class.

This keeps a single runner busy even for a high-nullity support. The hot modular update uses bounded conditional reduction instead of integer division, and even energy is screened with 64-bit parity-half bitsets and popcount before the independent full scorer is invoked.

## Consequence / next target

Defect 2 is now closed exactly for `O=50,E<=574`. Together with the already completed defect-1 local sweep, the next structurally distinct endpoint layer is defect 3. Its right-oriented half-sum coverage is much smaller than defect 2: only `(2,0)` and `(6,0)` up to signs, while the support count is `C(49,3)=18,424`. The modular-nullspace method should be tested there before returning to the generic global odd-perfect BnB.
