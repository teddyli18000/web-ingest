# Exact exclusion of the odd-perfect endpoint-defect-3 layer

Date: 2026-10-29

## Statement

For a length-100 odd-perfect binary sequence (`O=50`), let `d=min(d_L,d_R)` be the minimum number of nonzero odd autocorrelations in the two length-99 endpoint deletions. After reversal, orient an endpoint with minimum defect to the right.

The exhaustive computation recorded here proves:

> There is no odd-perfect length-100 sequence with invariant endpoint defect `d=3` and total LABS energy `E<=574`.

This is a structural exclusion only. It does not exclude `d>=4` or odd-energy layers `O>50`.

## Complete target half-sum reduction

Write

```text
A = sum_i s_{2i},
B = sum_i s_{2i+1}.
```

For the right endpoint deletion `R=s[0..98]`,

```text
sum_{k odd} C_k(R) = A(B-s_99).
```

With exactly three nonzero right-deletion odd correlations, each is `+/-2`. Under odd-perfectness `AB=0`. The right-oriented defect-3 target classes are therefore exactly

```text
(|A|,|B|) = (2,0) or (6,0).
```

Both have the same even-energy cap `520` for `E<=574`.

A useful simplification is that these four signed classes do not need four separate solves. Add only the single linear equation `B=0`. The support-sum identity then forces

```text
A = +/-2 or +/-6
```

automatically, because a sum of three values in `{+2,-2}` is `+/-2` or `+/-6`.

## Exact modular-nullspace method

For each of the

```text
C(49,3) = 18,424
```

three-lag supports, reflection inversion determines the bad mirror coordinates. Fix one bad coordinate by global negation, enumerate the remaining bad-coordinate ratios and endpoint sign, and linearize all 49 odd-perfect conditions.

As in the defect-2 search, the alternating-sign LABS symmetry

```text
t_i=(-1)^i s_i
```

is quotiented by imposing `s_0 s_1=+1`, equivalently `u_0=u_1` in reflection coordinates.

The resulting integer linear system is reduced modulo 257. Every generated equation is checked to satisfy

```text
abs(rhs) + sum(abs(coefficients)) < 257,
```

so any `+/-1` solution modulo 257 lifts to the same exact integer equation. Only the free variables of the modular RREF are enumerated. Each modular `+/-1` solution is reconstructed as a full sequence; candidates within the even-energy cap are rescored from the original autocorrelation definition and their right support is independently checked.

## Full profile

A complete RREF-only profile over all 18,424 supports gave:

```text
anchor/endpoint systems       1,038,682
inconsistent systems            777,734
consistent systems              260,948
free assignments              683,093,673
maximum reduced nullity                 22
```

Thus about 74.9% of the linearized systems are inconsistent before any free-variable enumeration.

## Exhaustion

The full exact search was split into five disjoint support-index ranges:

```text
[0,4000)
[4000,8000)
[8000,12000)
[12000,16000)
[16000,18424)
```

Every range returned

```text
complete=1 found=0 stopped=0
```

Aggregate exact workload:

```text
systems                1,038,682
inconsistent              777,734
prepared consistent        260,948
free assignments        683,093,673
+/-1 modular solutions  204,187,502
target candidates       204,187,502
maximum nullity                  22
```

Here `pm_candidates == target_checked` is expected: because the search includes `B=0`, the exact support-sum identity automatically forces `|A| in {2,6}` for every exact `+/-1` linear solution.

The per-range transcript is preserved in `2026-10-29-endpoint-defect3-modular-exhaustion.log`.

## Independent implementation check

A separate Python implementation reconstructed the reflection equations, modular Gaussian elimination, `B=0` constraint and `u_0=u_1` quotient, then enumerated all free assignments for representative supports. It matched the C++ solver exactly:

```text
support    systems inconsistent enum   +/-1 solutions maxnull best exact E
1,3,5      64      60           4      4              0       102138
9,19,25    64      56           48     6              3       12890
49,61,73   32      10           67584  654            13      4946
37,59,73   64      0            4096   6              6       10938
1,3,97     4       2            2      2              0       57154
```

All representative exact energies are far above 574. This check is independent code, not a second full 18,424-support exhaustion.

## Consequence and search-space reassessment

Endpoint defects 1, 2 and 3 are now excluded for the odd-perfect `E<=574` target. Defect 4 is qualitatively larger: `C(49,4)=211,876` supports, and separated four-edge supports can have eight bad reflection coordinates, producing up to 128 bad-ratio anchors before endpoint/half-sum branching.

A preliminary defect-4 profile over the first 1,000 supports already required 455,344 linear systems; although 449,527 were inconsistent and only 1,057,832 free assignments survived, RREF construction dominated runtime. Therefore the next step should not simply scale the defect-3 loop unchanged. Reuse common eliminations between the `A=0` and `B=0` branches, exploit support-run structure, or return to a global odd-perfect formulation before spending a large compute campaign on defect 4.
