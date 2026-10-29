# 2026-10-29 exact reflection reduction for odd-perfect endpoint defect 1

## Result

The first non-near-skew endpoint-defect class of odd-perfect N=100 sequences admits a much smaller exact representation than the original 100-bit outer-in search.

After the safe normalization already used by `oddperfect_outer_bnb.cpp`, endpoint defect `d=1` forces

```text
(a,b) = (2,0),
d_R = 1,
```

where `R=s[0..98]` is the length-99 right-end deletion. Its 49 odd autocorrelations are therefore all zero except one lag `h`, where the value is `+2` or `-2`.

The new observation is that this sparse odd-autocorrelation pattern uniquely fixes the **reflection-defect pattern** of `R`. Relative to a true skew-symmetric length-99 sequence, only one or two specific mirror pairs can violate the skew relation. Thus each fixed defect lag has only 50 free normalized signs rather than an unrestricted 100-bit representation.

## Reflection variables

Let a binary sequence `R=(r_0,...,r_98)` have length `n=99=2m+1`, `m=49`. Define

```text
rho_j = (-1)^(m-j) r_j r_{98-j},
z_j   = (1-rho_j)/2 in {0,1}.
```

Then

```text
rho_j = rho_{98-j},
z_j   = z_{98-j},
z_49  = 0.
```

True skew symmetry is exactly `z_j=0` for all `j`.

For `q=1,...,49`, put

```text
k = 99-2q.
```

Pair the `2q` terms of `C_k(R)` by `i <-> 2q-1-i`. For one such pair the two products sum to

```text
(-1)^(49-i) r_i r_(2q-1-i) * (rho_i-rho_(2q-1-i)).
```

Hence a paired contribution is zero when the two reflection bits agree and is `+/-2` when they disagree. Modulo two after dividing by two,

```text
C_(99-2q)(R)/2 == sum_(j=0)^(2q-1) z_j  (mod 2).
```

This congruence is independent of the unknown sign values of `R`.

## Consequence for one odd-correlation defect

If every odd correlation of `R` is zero except `C_h(R)=+/-2`, define

```text
q0 = (99-h)/2.
```

The prefix parities above are zero for every `q != q0` and one for `q=q0`. Combining those prefix equations with `z_j=z_(98-j)` and `z_49=0` has a unique solution.

In the left half `j=0,...,48`, the violated skew mirror pairs are exactly

```text
h < 49:  {h-1, h}
h = 49:  {48}
h > 49:  {98-h, 99-h}.
```

All other `z_j` are zero. Therefore a defect-1 length-99 deletion differs from a skew-symmetric length-99 sequence in only one or two prescribed mirror relations.

This pattern was also exhaustively checked for every binary sequence at odd lengths through 19 before being used computationally; the proof above is the reason it holds and does not rely on those checks.

## Sign of the unique defect

For the normalized N=100 sequence, `R=s[0..98]` has parity-half sums

```text
A_R = a = 2,
B_R = b-s_99 = -s_99.
```

The identity `sum_(k odd) C_k(R)=A_R B_R` therefore gives

```text
C_h(R) = -2 s_99.
```

Since the full N=100 odd correlation is

```text
C_h(s) = C_h(R) + s_(99-h) s_99,
```

odd-perfectness further forces

```text
s_(99-h) = +1.
```

So for each lag `h` both the reflection pattern and the sign of the unique length-99 defect are fixed once `s_99` is chosen.

## Reduced exact search

A prototype exact branch-and-bound uses these relations directly:

- `s_99` is one free endpoint sign;
- each of the 49 mirror pairs of `R` is represented by one sign with the fixed `rho_j` relation;
- the center `s_49` is free;
- the safe symmetry `s_1=+1` removes one variable.

This leaves **50 binary variables**.

The 49 target equations for the odd correlations of `R` become especially sparse after substituting the reflection relations. Each equation contains at most four signed pair-products. The search also enforces `(a,b)=(2,0)`, the exact even-correlation sum `-48`, and the standard rigorous even-energy lower bound against `E_even<=524`.

Local calibration shows a large reduction over the generic endpoint-count BnB. For example, target classes at defect lags 1, 3, and 97 are completely ruled out in milliseconds to a few milliseconds on the local prototype; central lags remain materially harder but are small enough for independent per-lag Actions jobs rather than hundreds of coarse 100-bit shards.

As a regression against accidental over-pruning, the same representation with a loose energy cap exactly finds a valid high-energy defect-1 sequence at lag 1:

```text
++++--++--++--++--++--++--++--++--++--++--++--++--++--++--++--++--++--++--++--++--++--++--++--++--+-
```

Independent rescoring gives

```text
E = 134098
odd energy = 50
(a,b) = (2,0)
(d_L,d_R) = (0,1)
unique R defect: C_1(R)=2
```

This validates that the reduced coordinates contain genuine defect-1 states; the target search is not empty by construction.

## Implication

The previously launched coarse 256-shard defect-1 rescue is superseded by this representation. The scientifically useful next computation is to exhaust the 49 possible defect lags directly in the reduced coordinates. A completed no-certificate result would be an exact exclusion of the entire normalized odd-perfect endpoint-defect-1 target layer, not a heuristic failure.
