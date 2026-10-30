# Exact order-25 fibre-signature MITM oracle

Date: 2026-10-30

## Purpose

The order-25 periodic compression is useful only if its binary fibre lifts can be checked cheaply.  A previous W127 homometric survivor required a direct Cartesian-product scan of `2^11 * 2^13 = 16,777,216` binary `(A,B)` lifts.  The W129/W131 target classes make the missing fibre condition especially sparse, so the Cartesian product is unnecessary.

This note records an exact meet-in-the-middle interface for a **fixed** compressed candidate.  It is a lift oracle, not an enumeration of all order-25 compressed candidates and not a LABS record claim.

Implementation:

```text
code/oddperfect_order25_fibre_mitm.cpp
```

## Exact fibre key

Write a length-50 binary half in its order-25 periodic and fibre channels.  For `A`,

```text
A_i      = p_i + alpha_i,
A_(i+25) = p_i - alpha_i,
```

where `p_i in {-1,0,+1}` and a binary fibre sign is free exactly when `p_i=0`.  For the B channel use the unshifted compression `q`; in the standard order-25 convention used by the homometric search,

```text
c = x^13 q,
q_j = c_(j+13 mod 25).
```

For a binary half `X`, define

```text
NAF_X(r) = C_X(r) - C_X(50-r),   r=1,...,24.
```

For the original length-100 even correlations,

```text
C_(2r)       = C_A(r)       + C_B(r),
C_(100-2r)   = C_A(50-r)    + C_B(50-r),
```

hence exactly

```text
C_(2r) - C_(100-2r) = NAF_A(r) + NAF_B(r).      (1)
```

Every `NAF_X(r)` is even and lies in `[-50,50]`.  Therefore each coordinate can be encoded injectively by

```text
NAF_X(r)/2 + 25 in {0,...,50},
```

using six bits.  All 24 coordinates occupy 144 bits, stored exactly in three `uint64_t` words.  No probabilistic fingerprint is used.

## Sparse target neighbourhoods

The exact W129/W131 near-NGP classification says the antisymmetric even-correlation difference is supported on at most two coordinates, with each nonzero value equal to `+/-4`.

For a fixed compressed `(p,c)` candidate, enumerate the lift family with more fibre bits once, form all exact 144-bit `NAF` keys, sort and deduplicate them.  Enumerate the smaller lift family and query:

```text
defect 0:  NAF_A + NAF_B = 0,
defect 1:  exactly one coordinate is +/-4,
defect 2:  exactly two coordinates are independently +/-4.
```

Thus the query neighbourhood sizes are respectively

```text
1,
24 * 2 = 48,
C(24,2) * 4 = 1104.
```

This replaces the fibre Cartesian product by one table construction plus exact nearest-key lookups.

For the current hard structural cases the exact defect counts are:

```text
W129-A   : 1
W131-A0  : 0
W131-A2  : 2
W131-B1  : 2
W131-B3  : 1
```

The earlier easy W129/W131 branches were already excluded by the full-sequence XOR model.

## Independent regression on the historical W127 survivor

The W127 homometric survivor recorded in `2026-10-29-order25-homometric-fibre-interface.md` has

```text
zeros(p)=11,
zeros(q)=13,
```

so the old direct checker inspected exactly `2^24=16,777,216` lift pairs and proved that none has zero NGP defect.

A local four-thread build of the new exact key method on the same fixed survivor gave

```text
hash_unique=8192
probe_lifts=2048
compatible zero-defect probe lifts=0
```

and therefore independently reproduces the same exclusion without forming the Cartesian product.  On this local environment the zero-defect query took about `0.003 s`; a two-defect neighbourhood query over the same survivor took about `0.055 s`.  These timings are calibration only; the exact result is the zero compatible-key count.

The built-in command

```text
oddperfect_order25_fibre_mitm --regress-w127 --defect 0
```

reproduces the historical survivor check.

## Computational consequence

For norm-26 W129/W131 compressed candidates, the total number of fibre bits is always

```text
(25-k_p) + (25-k_c) = 50 - 26 = 24.
```

For norm-28 candidates it is 22.  The MITM oracle therefore turns a fixed candidate's worst lift stage from `2^24` or `2^22` pair evaluations into two one-sided enumerations plus at most 1104 exact lookups per lift on the smaller side.

This does not solve the remaining problem by itself.  The scientifically useful interface is now clear: exact order-25 compressed enumeration should emit `(p,c)` candidates directly into this fibre oracle, and only fibre-compatible survivors need reconstruction as full length-100 sequences.

## Next use

If the current order-10 full-sequence search does not close the five hard W129/W131 classes, the preferred next exact route is:

1. enumerate the 24 target order-25 homometric spectral types exactly;
2. preserve the finite support/sign symmetries used successfully in the W127 order-25 searches;
3. run this exact fibre-key oracle immediately on each compressed survivor;
4. reconstruct and independently rescore a full binary sequence only after a fibre key matches.

This targets the channel that killed the known W127 periodic survivor instead of spending more time in generic CP-SAT search.
