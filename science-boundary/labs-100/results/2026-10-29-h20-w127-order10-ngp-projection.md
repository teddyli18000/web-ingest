# Odd-perfect `(20,0)`, `W=127`: exact order-10 cross + NGP projection

Date: 2026-10-29

## Scope

This note continues the exact `W=127` branch from `2026-10-29-h20-ngp50-paley-exclusion.md`.

An odd-perfect `(20,0)` candidate at `W=127` would have total LABS energy

```text
E = 50 + 4*127 = 558.
```

The equality arithmetic forces every even correlation `C_(2r)` to be `2` or `4`, with opposite even lags equal. Equivalently, the parity halves `(A,B)` must form a length-50 negaperiodic Golay pair (NGP50). Independently, odd-perfectness requires the periodic cross equation

```text
A B* + x B A* = 0  in Z[x]/(x^50-1).
```

The purpose here is to combine these two necessary conditions in the order-10 quotient exactly.

No E=558 sequence is claimed.

## Stage 1: exact order-10 odd-perfect cross profiles

Implementation:

```text
code/oddperfect_h20_w127_h10_profiles.cpp
```

For order 5, let `alpha,beta` be the residue sums of `A,B` modulo 5. The cross equation gives three exact integer equations. We retain only profiles whose convex lower bound on the even energy reaches the exact `W=127` floor (`E_even=508`).

Each order-5 profile is then lifted to order 10 by splitting every residue class into its two classes modulo 10. The negacyclic part of the cross equation in `Z[x]/(x^5+1)` has only two independent linear equations; fixing one side allows exact elimination of two coordinates on the other side.

A 5-thread local reproduction gives

```text
unique_A=13540 unique_B=9282 pairs=63660 seconds=4.59726
```

Thus the exact order-10 cross condition plus the exact order-10 convex energy floor leaves **63,660 distinct mod-10 profile pairs**.

These are necessary profiles only; they need not lift to binary length-50 sequences.

## Stage 2: exact order-10 NGP projection

For an ordinary order-10 residue sum `s_r`, define the alternating five-block fold

```text
gamma_r = A_r - A_(r+10) + A_(r+20) - A_(r+30) + A_(r+40),
eta_r   = B_r - B_(r+10) + B_(r+20) - B_(r+30) + B_(r+40).
```

For five signs in one residue class, each fold coordinate is odd and lies in

```text
{-5,-3,-1,1,3,5}.
```

For a fixed ordinary residue sum, the compatible alternating-fold values are finite and can be enumerated exactly.

Since an E558 candidate is an NGP50, reduction modulo `x^10+1` gives the exact necessary identity

```text
gamma gamma* + eta eta* = 100  in Z[x]/(x^10+1).       (1)
```

For a length-10 vector, its negacyclic autocorrelation is determined by its norm and four independent off-zero components. The implementation hashes those signatures for the `A` profiles and looks up the complementary signature required from `B`.

Implementation:

```text
code/oddperfect_h20_w127_ngp10.cpp
```

The exact 5-thread reproduction gives

```text
A_signatures=16764246 generation_seconds=1.31369
B_signatures_checked=44287724 total_seconds=11.8139
SUMMARY input_pairs=63660 projected_NGP_survivors=4220
```

Therefore the simultaneous order-10 projections of

1. the odd-perfect periodic cross condition,
2. the exact W127 energy floor, and
3. the NGP50 condition

reduce the branch from `63,660` profile pairs to exactly **4,220 profile pairs**.

This is a rigorous projection result. It is **not** an exclusion of E558: the 4,220 survivors have not yet been lifted through the full 50 coordinates and the original aperiodic odd correlations.

## Interpretation

The low-order quotient is already highly selective, but it does not collapse the branch. Scaling the same filter to more random search is not attractive. The next exact steps are:

1. lift the 4,220 survivors to the order-25/full-50 constraints, where support and half-sum information is much sharper;
2. in parallel, solve the complete E558 branch as a 0-1 feasibility model: every pair product is an XOR bit, so every autocorrelation becomes a linear cardinality equation;
3. treat any solver timeout as `UNKNOWN`, never as an exclusion.

The 4,220 surviving profile pairs are regenerated deterministically by the committed programs and are not stored as a durable data dump.
