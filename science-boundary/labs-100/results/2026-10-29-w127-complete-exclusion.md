# Complete exclusion of odd-perfect `(20,0), W=127` (`E=558`)

Date: 2026-10-29

## Claim

There is no length-100 binary sequence in the normalized odd-perfect half-sum class

```text
(sum A, sum B) = (20,0)
```

with

```text
W = E_even/4 = 127,
E = 50 + 4W = 558.
```

This closes the entire sharp W127 corner. It does **not** by itself exclude W129/W131, other odd-perfect half-sum classes, or higher odd-energy layers.

## Exact full model

The retained base implementation

```text
code/oddperfect_e558_xor_cpsat.py
```

uses 100 Boolean negative-sign variables for the original sequence. For every LABS lag `k`, it introduces the XOR disagreement count

```text
q_k = # { i : s_i != s_(i+k) }
```

and therefore the exact correlation

```text
C_k = (100-k) - 2 q_k.
```

At W127 in `(20,0)` the arithmetic classification forces

```text
odd k:   C_k in {+1,-1},
even k:  C_k in {2,4},
          exactly 26 of the 49 even correlations are 4.
```

Odd-perfectness with `ab=0` forces opposite odd correlations to have opposite signs. W127 equality plus the universal opposite-even congruence forces

```text
C_(2r) = C_(100-2r), r=1,...,24,
C_50 = 2.
```

The model imposes all of these as exact XOR-cardinality equations, plus the half sums `20,0`. A feasible solution is independently rescored against the original LABS definition.

The support shard

```text
ka = # { i=0,...,24 : A_i=A_(i+25) }
```

can take only

```text
10,12,14,16,18,20,22,24.
```

Earlier exact searches had already removed `ka=10,16,18,20,22,24`; only `ka=12,14` remained.

## Strong redundant order-10 partition

The exact order-10 programs

```text
code/oddperfect_h20_w127_h10_profiles.cpp
code/oddperfect_h20_w127_ngp10.cpp
```

regenerate 4,220 residue-sum profile pairs that satisfy the necessary order-10 periodic-cross and projected NGP conditions.

The wrapper

```text
code/oddperfect_e558_xor_order10_cpsat.py
```

adds 20 exact residue-sum variables

```text
sum_{i == r mod 10} A_i,  r=0,...,9,
sum_{i == r mod 10} B_i,  r=0,...,9.
```

Two complementary modes are available:

```text
--mode allowed    require the 20-tuple to be one of the 4,220 rows;
--mode forbidden  require the 20-tuple not to be one of the 4,220 rows.
```

For any fixed `ka`, these two cases partition **every assignment of the exact full E558 model**, regardless of whether one trusts the profile generator as complete. Thus proving both modes infeasible is an independent partition audit of the base model.

## Allowed-half exact run

One four-core GitHub runner regenerated the 4,220 rows and ran `ka=12` and `ka=14` concurrently with two CP-SAT workers each.

Workflow run:

```text
41001837939
```

Exact results:

```text
ka=12 mode=allowed status=INFEASIBLE wall_time=3.412787982
ka=14 mode=allowed status=INFEASIBLE wall_time=3.419349924
```

The run also independently regenerated

```text
SUMMARY input_pairs=63660 projected_NGP_survivors=4220
```

before solving.

## Forbidden-half audit

A second four-core runner regenerated the same 4,220 rows, but then required the residue-sum tuple to lie **outside** that set.

Workflow run:

```text
41002160549
```

Exact results:

```text
ka=12 mode=forbidden status=INFEASIBLE wall_time=1.543292969
ka=14 mode=forbidden status=INFEASIBLE wall_time=1.57223563
```

Hence for each last shard

```text
(full E558 assignments)
 = (profile in table) union (profile outside table)
 = empty union empty
 = empty.
```

This removes dependence on the completeness of the 4,220-row generator from the final exclusion.

## Base-model arithmetic audit

The XOR cardinality encoding was also checked independently at the formula level:

- for odd `k=2r+1`, the two permitted disagreement counts `49-r` and `50-r` rescore exactly to `C_k=+1,-1`;
- for even `k=2r`, the two permitted disagreement counts `49-r` and `48-r` rescore exactly to `C_k=2,4`;
- `23*2^2 + 26*4^2 = 508`, so total energy is `50+508=558`.

No timeout, `UNKNOWN`, or killed process is used as evidence in this conclusion.

## Relation to the order-10 generator

Although the partition audit makes generator completeness unnecessary for the final proof, the 4,220 rows are also mathematically necessary for a true W127 candidate:

1. the periodic odd-perfect cross condition projects to the order-10 quotient;
2. the order-10 convex energy bound partitions the 49 even correlations. The global `(20,0)` convex lower bound is already `E_even>=508`, while a W127 candidate has `E_even=508`, so its projected lower bound must equal 508;
3. W127 opposite-even equality makes `(A,B)` an NGP50, whose alternating order-10 fold satisfies the projected negaperiodic Golay equation tested by the second generator.

Thus the fast allowed-half infeasibility is consistent with the structural derivation; the forbidden-half run serves as a stronger audit rather than a necessary assumption.

## Consequence

The complete W127 support split

```text
ka=10,12,14,16,18,20,22,24
```

is now closed.

Therefore the next `(20,0)` odd-perfect targets are exactly the already-classified sparse near-NGP branches

```text
W129 -> E566, with at most one opposite-lag NGP defect,
W131 -> E574, with at most two opposite-lag NGP defects.
```

The next search should exploit those one/two-defect structures rather than return to W127 support enumeration or generic LABS local search.
