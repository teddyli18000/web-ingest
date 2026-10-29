# Exact exclusion of the odd-perfect endpoint-defect-4 layer

Date: 2026-10-29

## Statement

For a length-100 odd-perfect binary sequence (`O=50`), let `d=min(d_L,d_R)` be the minimum number of nonzero odd autocorrelations in the two length-99 endpoint deletions. By reversal, orient an endpoint of minimum defect to the right.

The exhaustive computation recorded here proves:

> There is no odd-perfect length-100 sequence with invariant endpoint defect `d=4` and total LABS energy `E<=574`.

Combined with the exact near-skew result (`d=0`) and the completed defect-1, defect-2 and defect-3 searches, any surviving odd-perfect `E<=574` sequence must therefore have invariant endpoint defect at least 5.

This result says nothing directly about odd-energy layers `O>50`.

## Target coverage without half-sum branching

Write

```text
A = sum_i s_{2i},
B = sum_i s_{2i+1}.
```

Odd-perfectness itself implies `AB=0`. For the `E<=574` target, the nonzero half-sum magnitude is even and at most 20. Its admissible even-energy cap is

```text
524,  h == 0 (mod 4),
520,  h == 2 (mod 4),
```

where `h=max(|A|,|B|)`.

Earlier endpoint searches solved separate half-sum classes. For defect 4 this is unnecessary: first solve the full odd-perfect reflection-linear system with no `A=0` or `B=0` equation, then reconstruct each exact `+/-1` solution and apply the complete target filter

```text
A*B == 0,
h <= 20,
h even,
even energy <= cap(h).
```

The exact endpoint-support sum identity provides additional restrictions automatically. In particular, for four nonzero deletion correlations the `B=0` branch can only realize `|A| in {0,4,8}`, while the `A=0` branch has balanced deletion-support signs; the solver does not need to hard-code these consequences.

## Reflection linearization

Fix one of the

```text
C(49,4) = 211,876
```

possible four-lag right-deletion supports. Reflection inversion determines the bad mirror coordinates. Once one bad coordinate is normalized and the other bad-coordinate ratios plus the remaining symmetry gauge are fixed, all 49 odd-perfect conditions are integer linear equations in the remaining `+/-1` reflection variables.

The equations are reduced modulo 257. Before accepting this as an exact filter, every generated row is checked to satisfy

```text
abs(rhs) + sum(abs(coefficients)) < 257.
```

Therefore a `+/-1` assignment that satisfies a row modulo 257 satisfies the original integer row exactly: a nonzero residual cannot wrap by 257. The implementation also reconstructs full candidates and independently recomputes all original autocorrelations before any hit can be reported.

## Direct quotient of the alternating-sign symmetry

The LABS transformation

```text
t_i = (-1)^i s_i
```

preserves energy, the right endpoint support, and `|A|,|B|`.

The older solver represented this quotient by adding another linear equation. Defect 4 instead incorporates it directly into the coordinate gauge together with global negation:

- Global negation fixes one bad reflection coordinate `x_ref=+1`.
- If an even bad coordinate is available, choose it as the reference. Alternating sign leaves that reference fixed and flips the endpoint sign, so set the endpoint sign to `+1`.
- If all bad coordinates are odd, choose an odd bad reference. The composition of alternating sign and global negation restores that reference while flipping an even good coordinate; fix `u_0=+1` and retain both endpoint signs.

Thus exactly one representative of each relevant symmetry orbit is retained without introducing an extra equation or duplicate endpoint branch.

## Two-stage exact elimination

A preliminary defect-4 profile showed that most anchor systems are inconsistent. Full Gauss-Jordan reduction on every system was therefore wasteful.

The final solver uses:

1. an immediate pure-constant-row contradiction test;
2. forward Gaussian elimination modulo 257, eliminating only below pivots and aborting on inconsistency;
3. full RREF only for forward-consistent systems;
4. Gray-code enumeration of only the RREF free variables;
5. bit-parallel even-energy screening using the two 50-bit parity halves;
6. full original-autocorrelation verification for any candidate reaching the target cap.

This changes only the computation order, not the solution set.

## Complete exhaustion

All 211,876 supports were covered by 13 disjoint contiguous ranges. Every retained range finished with

```text
complete=1
found=0
stopped=0
```

The aggregate exact workload was

```text
supports                         211,876
anchor/gauge systems          21,415,652
inconsistent systems          17,409,272
consistent prepared systems    4,006,380
free assignments enumerated   6,505,945,690
+/-1 modular solutions         3,235,101,931
target-half-sum candidates     2,057,004,339
maximum reduced nullity                   24
```

No target candidate had `E<=574`.

The exact per-range transcript is in [`2026-10-29-endpoint-defect4-modular-exhaustion.log`](2026-10-29-endpoint-defect4-modular-exhaustion.log).

### Handling one failed process correctly

During an initial five-process campaign, the process assigned `[150000,172000)` was terminated by `SIGKILL` under memory pressure. That run is **not** used as evidence and is not present in the proof transcript.

The entire missing interval was rerun as four smaller complete ranges:

```text
[150000,155500)
[155500,161000)
[161000,166500)
[166500,172000)
```

All four completed with `found=0`, so the final support coverage is continuous and has no gap.

## Independent implementation checks

A separate Python reconstruction of reflection inversion, the direct symmetry gauge, modular RREF, exact integer-row verification, sequence reconstruction and full LABS scoring matched the C++ system counts and candidate counts on representative supports:

```text
support        systems  inconsistent  enum  +/-1 solns  target  maxnull  best exact E
1,3,5,7        128      116           12    12          8       0        88066
1,3,5,97       8        2             8     4           1       1        108486
1,49,51,97     4        2             2     2           1       0        117214
9,19,25,31     128      122           48    10          10      3        6118
23,33,41,69    128      40            7872  6           6       9        4942
25,35,53,69    128      0             5632  2           2       6        17086
```

A separately sampled high-nullity support was intentionally not fully enumerated by the Python checker, so it is not cited as independent evidence. The full exclusion rests on the complete C++ ranges; the Python cases are implementation cross-checks.

## Reproducibility

The retained unified implementation is

```text
code/oddperfect_endpoint_modular.cpp
```

It supports endpoint defects through 4 and contains the direct symmetry gauge, modulo-257 lifting guard, forward-consistency filter, exact RREF/nullspace enumeration, target filtering and independent full candidate verification.

## Consequence and next search-space decision

The odd-perfect target layer now has the following exact endpoint picture:

```text
d=0   near-skew manifold, exact minimum E=578
d=1   no E<=574
d=2   no E<=574
d=3   no E<=574
d=4   no E<=574
```

Hence any odd-perfect breakthrough must satisfy

```text
d >= 5.
```

A naive defect-5 extension is not justified. There are

```text
C(49,5) = 1,906,884
```

supports, almost nine times the defect-4 count, and up to ten bad reflection coordinates. Since candidate quality has not improved while the excluded region has grown, the next step is to reassess the representation rather than simply multiply the same search. Promising directions are to reuse elimination across related supports/anchors, exploit the banded/path structure of the linearized equations, or return to a global odd-perfect formulation with endpoint defect used as a derived constraint rather than the primary enumeration axis.
