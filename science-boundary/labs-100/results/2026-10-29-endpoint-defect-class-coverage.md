# Endpoint-defect class coverage

For an odd-perfect N=100 sequence split into parity halves with sums `a,b`, we have `ab=0`. Delete the last sign and call the length-99 sequence `R=s[0..98]`. Every odd `C_k(R)` is `0` or `±2`; let the nonzero support size be `d_R`.

The parity sums of `R` are `a` and `b-s_99`, hence the exact correlation-sum identity gives

```text
sum_(k odd) C_k(R) = a (b-s_99).
```

Because the left side is the sum of exactly `d_R` values in `{+2,-2}`:

```text
|a(b-s_99)| <= 2 d_R,
a(b-s_99) == 2 d_R (mod 4).
```

If `b=0` and `a>=0`, this becomes

```text
a <= 2 d_R,
a/2 == d_R (mod 2).
```

If `a=0`, the defect sum is zero, so `d_R` must be even.

Reversal swaps endpoint deletions and parity halves. Therefore every invariant layer `d=min(d_L,d_R)` can be oriented so the minimum is the right deletion. For the full odd-perfect target `E<=574`, the nonzero half-sum magnitude is in `h=0,2,...,20`, and the complete right-oriented class coverage is:

- odd `d`: `(Aabs,Babs)=(h,0)` with `h<=2d` and `h/2 == d (mod 2)`;
- even `d`: every `(0,h)`, `h=0,2,...,20`, plus `(h,0)` with `h<=2d` and `h/2 == d (mod 2)`.

Examples:

```text
d=1: (2,0)
d=2: (0,h) for all h=0,2,...,20, plus (4,0)
d=3: (2,0),(6,0)
d=4: (0,h) for all h=0,2,...,20, plus (4,0),(8,0)
```

For `d=2`, there are `C(49,2)=1176` two-lag supports and 12 distinct target classes, hence 14,112 support/class cases before pruning. For `d=3`, `C(49,3)=18,424` supports times only two classes gives 36,848 cases.

For odd-perfect `O=50`, use even-energy cap `524` when the nonzero half sum is `0 mod 4`, and `520` when it is `2 mod 4`; the latter follows from the global-product energy congruence.

The same identity fixes support-sign balance: if the zero half is `A`, an even support has equal numbers of `+2` and `-2`; in the extra defect-2 class `(4,0)`, both support correlations have the same sign. This is optional exact pruning for the support-linearized solver.

A six-case defect-2 Actions pilot was launched after this derivation to calibrate representative supports before scaling the full sweep.
