# 2026-10-28 congruence structure for the exact E=574 level

## Scope correction

This note concerns the **exact first improvement level `E=574`**, not every Few Shots certificate with `E<=574`.

For N=100 all energies are `2 (mod 4)`, so the levels below the public `578` record are

```text
574, 570, 566, 562, ...
```

The mod-8 class alternates between these levels. In particular, the global-product constraint derived below proves that an **exact `E=574`** sequence has product `+1`, but a hypothetical `E=570` sequence would have product `-1` and could lie in the same product class as the incumbent. Therefore the searches in this note are a target-specific attack on the first improvement level; they are not a global exclusion of all `E<=574` sequences.

## 1. Total energy mod 8 is determined by the global sign product

Let `s` have length `N=100` and flip one position `p`. For lag `k`, let `T_k` be the sum of the one or two products in `C_k` that contain `s_p`. The flip changes

```text
C_k' = C_k - 2 T_k,
```

so

```text
(E'-E)/4 = sum_k (T_k^2 - C_k T_k).
```

Modulo two, `C_k` has the parity of `N-k`, hence the parity of `k`. For odd `k`, the summand is zero modulo two. For even `k`, it is congruent to `T_k` modulo two.

`T_k` is odd exactly when only one of `p-k` and `p+k` lies in the sequence. If `a=p`, `b=N-1-p`, and without loss `a<=b`, the number of positive even `k` with exactly one incident term is

```text
floor(b/2) - floor(a/2).
```

For `N=4m`, using `a+b=4m-1`, this number is always odd. Therefore every single-bit flip changes the energy by

```text
E' - E = 4 (mod 8).
```

The all-plus N=100 sequence has

```text
sum_{j=1}^{99} j^2 = 6 (mod 8).
```

Starting from all-plus, an even number of flips gives global product `+1` and an odd number gives global product `-1`. Hence for every N=100 sequence,

```text
global product +1  =>  E = 6 (mod 8),
global product -1  =>  E = 2 (mod 8).
```

Consequences for the first two improvement levels:

```text
E=574 -> global product +1,
E=570 -> global product -1.
```

The public E=578 incumbent has global product `-1`. Thus an exact E=574 candidate is at odd Hamming distance from every standard symmetry image of the incumbent, while this statement does **not** apply to a hypothetical E=570 candidate.

## 2. Odd-lag energy mod 16 is determined by the parity-half products

Split the sequence into the 50 even-position and 50 odd-position signs,

```text
A_i=s_{2i}, B_i=s_{2i+1},
a=sum A_i, b=sum B_i.
```

Let `O` be the sum of `C_k^2` over odd lags. Pair odd lags `k` and `100-k`. Write their correlations as odd integers `C,D`. The exact LABS congruence gives

```text
C + D = 0 (mod 4).
```

Write `C+D=4q`. Since `C` is odd,

```text
C^2 + D^2 = 2 + 8q (mod 16).
```

There are 25 such pairs. Also

```text
sum_{k odd} C_k = ab.
```

Therefore

```text
O = 50 + 8 * (ab/4 mod 2)  (mod 16).
```

For a half of length 50, its sign product is `+1` exactly when its sign sum is `2 (mod 4)`, and `-1` exactly when its sign sum is `0 (mod 4)`. Hence

```text
O = 10 (mod 16)  iff both half-products are +1,
O =  2 (mod 16)  otherwise.
```

## 3. Exact E=574 classes inside the odd-perfect layer

An odd-perfect sequence has every odd `|C_k|=1`, so `O=50`. The pair congruence then forces every opposite odd pair to be `(1,-1)` or `(-1,1)`, hence

```text
ab = 0.
```

For **exact E=574**, the global product must be `+1`, so the two half-products are equal. Since `O=50 = 2 (mod 16)`, they cannot both be `+1`. Therefore an odd-perfect exact-574 sequence must satisfy

```text
half-product(A) = half-product(B) = -1,
a = b = 0 (mod 4),
ab = 0.
```

After reversal/sign normalization one half sum is zero and the other is nonnegative. Cauchy applied to the 49 even correlations and

```text
sum even C = (a^2+b^2-100)/2
```

bounds the nonzero half sum by 20 when total energy is 574. Thus the exact-574 odd-perfect level is contained in six canonical half-sum classes:

```text
(0,0), (4,0), (8,0), (12,0), (16,0), (20,0).
```

This reduction must **not** be used to discard a possible E=570 odd-perfect sequence, whose global product class is different.

## 4. Natural E=574-class barrier and strict walk

Flipping position 0 of the incumbent gives

```text
E = 774
odd energy = 50
half products = (-1,-1)
```

and therefore enters the exact-574 odd-perfect congruence class. `code/oddperfect_targetclass.cpp` performs a strict tabu walk there using same-parity double flips that preserve both half-products and require all odd correlations to remain `+/-1`.

Small calibration from this barrier reached first `E=702` and then

```text
E = 678
odd energy = 50
even energy = 628
half sums = (-8,0)
half products = (-1,-1)
```

with sequence

```text
---------+--+-+--+--+-++-++++---+----++---++-+++-++---+---++-++--+-+++-++-+---++++---+++++---+-+-+-+
```

Independent exact rescoring confirmed these values.

A structural audit then showed that this E=678 sequence is itself in the canonical `1 + skew99` near-skew manifold. The strict walk therefore found a different congruence sector **inside the same 50-variable near-skew geometry**, not a genuinely unrelated basin.

## 5. Exact ordinary shells around E=678

The local isolation of the E=678 state was checked without assuming near-skew structure.

- exact distance 2: all `C(100,2)=4,950` candidates; shell minimum `830`; no odd-energy-58 state;
- exact distance 4: all `C(100,4)=3,921,225` candidates; shell minimum `902`; `1,225` odd-perfect states and no odd-energy-58 state;
- exact distance 6: GitHub Actions run `40731781096`; all `C(100,6)=1,192,052,400` candidates; shell minimum **974** in `184.854 s`.

Radius-6 evidence:

```text
BASE energy=678
RADIUS radius=6 tested=1192052400 best=974 seconds=184.854
BESTSEQ -+----------+-+--+--+-++-++++--++----++---++-+++-++---++--+++++--+-+++-++-+---++-+---+++++---+-+-+-+
```

Because E=678 has global product `+1`, even Hamming distances remain in that product class while odd distances switch to product `-1`. The completed even shells 2,4,6 therefore show that this particular exact-574-class basin has no improving sequence through distance 6. They do not exclude more distant exact-574 states and do not say anything decisive about the E=570 product class.

## 6. Additional exact near-skew consequence

In the canonical near-skew representation `s=(+1,skew99)`, the 25 odd-position reflection pairs each have product `-1`, so the product of the odd-position half is always `-1`. The 24 noncentral even-position pairs have product `+1`, leaving

```text
product(even-position half) = s_50.
```

Therefore an exact E=574 near-skew candidate, whose global product is `+1`, must have

```text
s_50 = -1.
```

Equivalently, in a fixed even-half sign-sum class `a`, the near-skew center sign is already determined by the parity of `(50-a)/2`. Existing exact BnB code had been branching on this center coordinate late; fixing it at the root is a sound propagation improvement for fixed-class searches.

## Interpretation

The useful result is a target-level decomposition, not a record improvement:

- exact E=574 lies in a global-product class different from the E=578 incumbent;
- within odd-perfect sequences, exact E=574 is further restricted to half-product `(-1,-1)` and six canonical half-sum classes;
- the best strict walk found E=678, but that state is still near-skew and is exactly isolated from improvement through ordinary Hamming distance 6;
- exact searches for E=574 can safely exploit the forced near-skew center bit when working inside that manifold.

A complete Few Shots search must still retain the alternating lower energy levels `570,566,...`; the congruence restrictions for E=574 are not a proof about those levels.

No `E<=574` certificate was found in this experiment.
