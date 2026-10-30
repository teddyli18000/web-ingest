# Low11 symmetric-difference exact search: overlap `t=2` and `t=12`

Date: 2026-10-30

## Scope

This note concerns the remaining odd-perfect `(20,0)` low11 order-25 compressed branches that occur in the W129/W131 target range.  The unresolved order-25 norm splits have

```text
(kp,kc) = (12,14) or (14,12),
kp = ||p||^2,
kc = ||c||^2,
sum p = 10,
sum c = 0.
```

Let `P,C` be the binary support masks of the ternary length-25 sequences `p,c`, and let

```text
t = |P intersect C|.
```

The exact lag-zero cross equation gives `sum_i p_i c_i=0`, so `t` is even.  Since `kp+kc=26` on 25 coordinates, the possible overlap layers are

```text
t = 2,4,6,8,10,12.
```

This note exactly excludes the two extreme layers `t=2` and `t=12` for both norm splits.

## Symmetric-difference reformulation

Put

```text
D = P xor C.
```

Then

```text
|D| = kp+kc-2t = 26-2t.
```

Modulo 2, the cyclic cross equation

```text
P C* + C P* = 0
```

becomes, after substituting `C=P+D`,

```text
P D* + D P* = 0.                         (1)
```

For fixed `D`, equation (1) is linear over GF(2) in the 25 support bits of `P`.

When `|D|>12`, replace `D` by its complement `E=D+J`, where

```text
J = 1+x+...+x^24.
```

Because `kp` is even,

```text
P J* + J P* = 0,
```

so equation (1) is unchanged.  Therefore the six overlap layers can be represented by difference supports of weights

```text
t:                   2  4  6  8 10 12
reduced difference:  3  7 11 10  6  2
```

instead of fixing one full support and searching for the other.

## Exact enumeration

Implementation:

```text
code/oddperfect_low11_symdiff_exact.cpp
```

For a selected `(t,kp)` the program:

1. enumerates affine orbits of the reduced difference support in `Z_25`;
2. solves (1) exactly over GF(2);
3. keeps exactly the kernel vectors having `|P|=kp` and `|C|=26-kp`;
4. quotients `P` by the stabilizer of the fixed difference support;
5. enumerates every `p` sign assignment with `sum p=10`;
6. solves `sum c=0` and all 13 independent integer cyclic cross equations `H_r=0`, `r=0,...,12`, by exact meet-in-the-middle, using `c -> -c` symmetry only;
7. checks every integer-cross-compatible pair against the full low11 order-25 target

```text
G_r = PAF_p(r)+PAF_c(r) in {2,3,4}, r=1,...,12,
sum_r G_r = 37.
```

No SAT/CP solver or timeout is used in this computation.

## Results

The complete counts are

```text
overlap  kp  difference orbits  support-pair orbits  p-sign tests  H matches  target hits
12       12  2                  788                  9,456         266        0
12       14  2                  788                  71,708        125,127    0
 2       12  6                  4,374                52,488        1,007      0
 2       14  6                  4,374                398,034       126,214    0
```

Thus no low11 compressed target exists in the `t=2` or `t=12` support-overlap layers for either remaining norm split.

## Independent reproduction

A separate hosted GitHub Actions run compiled the durable source from a clean checkout and executed all four exact cases concurrently on one four-CPU runner.  The workflow asserted every count above and completed successfully:

```text
run 41047897161
artifact labs100-low11-symdiff-extremes
```

The Action transcript exactly reproduced all four local count vectors.

## Consequence

The remaining low11 order-25 search is reduced from six overlap layers to

```text
t = 4,6,8,10,
kp = 12 or 14.
```

The same representation is especially promising for `t=10`, whose reduced difference weight is only 6 and has only 366 affine difference-support orbits.  The middle layers `t=6,8` have many more support-pair orbits and should not be attacked by mechanically scaling the same signed enumeration without additional order-10 / near-NGP filtering.
