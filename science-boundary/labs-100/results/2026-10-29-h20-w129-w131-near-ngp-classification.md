# Odd-perfect `(20,0)`: exact W129/W131 sparse near-NGP classification

Date: 2026-10-29

## Scope

This note classifies the two odd-perfect `(20,0)` breakthrough budgets immediately above the W127 corner.

Write

```text
A_i=s_(2i), B_i=s_(2i+1),
a=sum A_i=20, b=sum B_i=0,
c_r=C_(2r),
d_r=c_r/2, r=1,...,49,
W=sum d_r^2=E_even/4.
```

For this half-sum class

```text
sum d_r = 75.
```

The global product is `+1`, so the relevant odd-perfect breakthrough budgets are

```text
W=127 -> E=558,
W=129 -> E=566,
W=131 -> E=574.
```

The W127 equality case is recorded separately in
`2026-10-29-h20-ngp50-paley-exclusion.md`.

No LABS improvement is claimed here.

## Correlation multisets

Put `d_r=1+y_r`. Then

```text
sum y_r = 26,
W = 101 + sum y_r^2,
W-127 = sum y_r(y_r-1).
```

For integer `y`, the nonzero values of `y(y-1)` begin with `2` (at `y=-1,2`) and `6`.
Therefore the complete W129 and W131 multisets are forced.

### W129

Exactly one coordinate has contribution 2:

```text
A: d=0 x1, d=1 x21, d=2 x27,
or
B: d=1 x24, d=2 x24, d=3 x1.
```

### W131

Exactly two coordinates have contribution 2:

```text
A: d=0 x2, d=1 x19, d=2 x28,
B: d=0 x1, d=1 x22, d=2 x25, d=3 x1,
C: d=1 x25, d=2 x22, d=3 x2.
```

These are exact consequences of the sum and norm alone.

## Opposite-lag parity

For every binary length-100 sequence the opposite even-lag congruence gives

```text
d_r == d_(50-r) (mod 2),  r=1,...,24.
```

In the `(20,0)` global-product `+1` class, `C_50 == 2 (mod 4)`, so

```text
d_25 is odd.
```

Define the antisymmetric even-correlation defect

```text
v_r = (c_r-c_(50-r))/4
    = (d_r-d_(50-r))/2,  r=1,...,24.
```

A nonzero `v_r` can therefore occur only when an opposite-lag pair is `(0,2)` or `(1,3)` in either order. In all target multisets below every nonzero defect has `|v_r|=1`.

## Exact W129 cases

### W129-A: `0^1 1^21 2^27`

The middle coordinate must be `d_25=1`. After removing it, one `0` and 27 `2`s remain in the even-parity sector. Hence the unique `0` must pair with a `2`.

Therefore

```text
#supp(v) = 1,
sum v_r^2 = 1.
```

The unique defect is a `(0,2)` opposite pair.

### W129-B: `1^24 2^24 3^1`

There are two possibilities.

If `d_25=3`, all 24 off-centre `1`s pair among themselves and all 24 `2`s pair among themselves:

```text
#supp(v) = 0.
```

This branch is an exact NGP50 branch.

If `d_25=1`, the off-centre odd sector contains 23 `1`s and one `3`, forcing exactly one `(1,3)` pair:

```text
#supp(v) = 1,
sum v_r^2 = 1.
```

Thus every W129 candidate is either an NGP50 or differs from NGP by exactly one opposite-lag defect.

## Exact W131 cases

### W131-A: `0^2 1^19 2^28`

Here `d_25=1`. Off centre there are two `0`s, 18 `1`s and 28 `2`s.

The two zeros either pair together, giving no defect, or each pairs with a `2`, giving two `(0,2)` defects. Therefore

```text
#supp(v) in {0,2}.
```

### W131-B: `0^1 1^22 2^25 3^1`

If `d_25=3`, the unique `0` must pair with a `2`, while the 22 `1`s pair normally:

```text
#supp(v) = 1.
```

If `d_25=1`, the unique `0` pairs with a `2` and the unique `3` pairs with a `1`:

```text
#supp(v) = 2.
```

### W131-C: `1^25 2^22 3^2`

If `d_25=1`, the two `3`s either pair together or each pairs with a `1`:

```text
#supp(v) in {0,2}.
```

If `d_25=3`, one off-centre `3` remains and must pair with a `1`:

```text
#supp(v) = 1.
```

## Consequence

Across the entire `(20,0)` odd-perfect target range through E574,

```text
W127: sum v_r^2 = 0,
W129: sum v_r^2 <= 1,
W131: sum v_r^2 <= 2.
```

So the target is not a generic departure from negaperiodic complementarity. It is a sparse near-NGP problem with at most two defective opposite-lag pairs.

This changes the appropriate next search space:

1. use the exact W127 NGP equations for the zero-defect branches;
2. introduce one or two explicitly located `(0,2)` / `(1,3)` defects for W129/W131;
3. combine those tiny defect supports with the periodic odd-perfect cross equation and order-25 / cyclotomic compression keys;
4. avoid generic endpoint-defect or unrestricted LABS search for these branches.

The classification is target-specific and does not exclude any branch by itself.
