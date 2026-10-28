# 2026-10-28 Golay-52 double-deletion / interleaving probe

## Motivation

Split an N=100 sequence into its even and odd positions, `A,B` of length 50.  Then

```text
C_{2r}(s) = C_r(A) + C_r(B).
```

Thus the even-lag contribution is exactly the complementary-pair residual energy of `A,B`.  This suggests starting from a binary Golay complementary pair near length 50 rather than perturbing the N=100 incumbent.

Binary Golay pairs exist at length 52 but not length 50.  A public primitive length-26 pair is

```text
A26 = ++++ -++--+-+ -+--+-+++--+++
B26 = ++++ -++--+-+ ++++ -+---++---
```

(spaces only for readability; the code contains the exact 26 signs).  The standard doubling construction

```text
A52 = [A26, B26]
B52 = [A26, -B26]
```

was independently checked to satisfy `C_k(A52)+C_k(B52)=0` for every nonzero lag.

Primary public sources for the length-26 pair and length-52 construction:

- <https://patents.justia.com/patent/20260012305>
- <https://patents.google.com/patent/US20260012305A1/en>

Golay-pair background / length construction: Jedwab & Parker, *A construction of binary Golay sequence pairs from odd-length Barker sequences* (2009), <https://doi.org/10.1002/jcd.20222>.

## Exact finite family

`code/golay52_delete.cpp` enumerates every choice of two deletions from `A52` and every choice of two deletions from `B52`, giving

```text
C(52,2)^2 = 1,758,276
```

length-50 pairs.

Any LABS-100 sequence has odd-lag energy at least 50.  Therefore a sequence with total energy at most 574 must have even-lag energy at most 524.  The scanner computes the exact 49-component autocorrelation vector for every deletion variant, screens every pair by this necessary condition, and only then interleaves the pair.

For each screened pair it exhausts 32 post-deletion relative operations that leave the screened even-lag energy unchanged:

- reverse either length-50 half independently;
- negate one half relative to the other;
- jointly alternate both length-50 halves;
- swap the two halves.

A joint alternation of the original length-52 Golay pair before deletion is not generally equivalent to post-deletion alternation because deleting symbols changes parity after the deletion points.  The complete scan is therefore run twice: once on the canonical pair and once after this pre-deletion joint alternation.  Reversal/sign/swap equivalences before deletion are already absorbed by deletion-index reversal and the post-deletion operations above.

## Results

Canonical length-52 pair:

```text
screened = 38,924 deletion pairs with even energy <= 524
transformed = 1,245,568 complete N=100 candidates
best E = 1478
odd energy = 1266
even energy = 212
deletions A = (23,24)
deletions B = (26,27)
```

Jointly alternated length-52 pair before deletion:

```text
screened = 16,414 deletion pairs with even energy <= 524
transformed = 525,248 complete N=100 candidates
best E = 1478
odd energy = 1266
even energy = 212
```

Best sequence (same energy in both scans):

```text
++++++++--++++----++--++--++----++--++++++----+++++++-+--++-+--+-++--++-+-+-+-+--++--+-+-++-+--+-+-+
```

A separate pre-screen calculation found deletion pairs with even-lag energy as low as `164`, so the construction does create very strong near-complementarity in the parity halves.  The failure is instead the odd cross-correlation contribution, which remains enormous under the exhausted relative operations.

## Interpretation

This rules out a concrete and natural finite construction family as a source of an `E<=574` record: double-deleting the canonical length-52 Golay pair (including its nontrivial pre-deletion joint alternation) and applying all listed relative symmetries cannot work.

It does **not** rule out arbitrary near-complementary length-50 pairs, nor nonlinear re-orderings/cyclic operations that change the even-lag residual itself.  The low-even-energy states may still be useful as homotopy seeds, but existing lag-weight homotopy calibration from related complementary/periodic seeds has only reached the high-700s, so this direction should not receive large compute unchanged.
