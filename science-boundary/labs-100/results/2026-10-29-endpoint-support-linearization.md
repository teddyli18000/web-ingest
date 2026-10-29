# 2026-10-29 linearization of sparse endpoint-defect layers

## Result

The reflection inversion does more than reduce the number of free signs. Once the reflection-defect support is fixed, the entire odd-correlation subsystem of the length-99 endpoint deletion becomes **linear in binary signs** after enumerating only a few anchor ratios.

For endpoint defect `d`, the reflection pattern has at most `2d` bad mirror coordinates. Choosing one bad coordinate as a reference leaves at most `2d-1` bad-coordinate ratios plus one endpoint ratio to enumerate. Conditional on those few bits, all 49 odd-perfect constraints are linear equations in the remaining `+/-1` variables.

This removes the main nonlinearity from the low-defect exact search.

## Why every odd-correlation monomial crosses the defect boundary

Use the notation of `2026-10-29-endpoint-support-reflection-inversion.md` for a length-99 deletion `R`:

```text
rho_j = (-1)^(49-j) R_j R_(98-j),
rho_j in {+1,-1}.
```

Let `B` be the set of left-half coordinates with `rho_j=-1`. After pairing the terms of an odd autocorrelation, every surviving term has coefficient proportional to

```text
rho_i-rho_j.
```

Therefore a term survives iff exactly one of the two reflection coordinates is in `B`. After mapping any right-half index back to its left reflection coordinate, every monomial has the form

```text
x_b x_g,  b in B, g not in B.
```

There are no bad-bad or good-good monomials in these equations.

## Anchor transform

Choose one `b0 in B` and use global sign negation to normalize

```text
x_b0 = +1.
```

For each other bad coordinate define the small enumerated ratio

```text
gamma_b = x_b x_b0 in {+1,-1}.
```

For every good coordinate define

```text
u_g = x_g x_b0 in {+1,-1}.
```

Then every surviving quadratic monomial becomes

```text
x_b x_g = gamma_b u_g,
```

which is linear in the `u` variables once the `gamma` values are fixed.

If `|B|=r`, only `r-1` anchor ratios are needed. Reflection inversion gives `r<=2d`, so endpoint defect `d` needs at most `2d-1` such ratio bits.

## The full odd-perfect endpoint condition is also linear

Let `s_99` be the endpoint omitted from `R` and define the endpoint ratio

```text
e = s_99 x_b0 in {+1,-1}.
```

At a supported odd lag `k`, write the deletion correlation as

```text
D_k = C_k(R)/2.
```

Since the full length-100 sequence is odd-perfect,

```text
C_k(s) = C_k(R) + s_(99-k) s_99 = +/-1.
```

At a deletion defect, `C_k(R)=+/-2`, so necessarily

```text
D_k = -s_(99-k)s_99.
```

Map `s_(99-k)` to its left reflection coordinate `j` with fixed reflection multiplier `m`. Then

```text
D_k = -m e u_j,
```

which is again linear after enumerating `e`.

At nonsupport lags the target is simply `D_k=0`.

Thus **all odd-perfect constraints are linear signed-sum equations** in the `u` variables after at most

```text
2^(|B|-1) * 2 <= 2^(2d)
```

small anchor/endpoint cases.

## Even energy and half sums

The global reference sign cancels from every pair product, so all autocorrelation energies depend only on the transformed variables and the enumerated ratios. The two parity-half sums may change sign under the normalization, so target classes are imposed by absolute half sums; the standard LABS global/alternating symmetries recover the canonical signs.

The exact even-correlation sum remains

```text
sum C_even = (a^2+b^2-100)/2,
```

and the usual fixed-product/unknown-product lower bound remains valid during branch-and-bound.

## Defect-1 impact

For endpoint defect 1, `|B|` is one or two. The dedicated reflection-coordinate solver initially made the central defect lags look difficult because it still treated the odd equations as quadratic reachability conditions. The anchor transform removes that artificial difficulty.

A local complete sweep of all 49 possible right-deletion defect lags for the only normalized defect-1 target class

```text
(|a|,|b|)=(2,0), E_even<=524
```

finished in about `7.3 s` total on one local process invocation per lag. Every lag completed with no `E<=574` certificate. Representative exact-search costs were:

```text
h=1   : 132 nodes
h=25  : 385,148 nodes
h=31  : 1,375,712 nodes
h=47  : 18,748 nodes
h=49  : 426 nodes
h=51  : 16,776 nodes
h=67  : 1,103,264 nodes
h=97  : 156 nodes
```

The largest individual local wall time was below one second.

As a regression against accidental emptiness, the same linearized representation with a loose energy cap found a genuine defect-1 sequence. Independent direct rescoring gave

```text
E = 134474
odd energy = 50
(|a|,|b|) = (2,0)
right endpoint-defect support = {1}
```

so the transformed search space contains valid defect-1 states.

## Implementation

`code/oddperfect_support_linear_bnb.cpp` implements the general support-based transform. It accepts an explicit right-deletion defect support, absolute parity-half sums, and an even-energy cap. Every reported leaf is independently rescored from the full 100 signs before it can be accepted.

The immediate independent verification task is a GitHub Actions sweep of all 49 defect-1 supports. If that reproduces the local no-certificate result, the entire normalized odd-perfect endpoint-defect-1 `E<=574` layer is exactly excluded.
