# Order-25 homometry and the missing fibre channel

Date: 2026-10-29

## Purpose

This note isolates a compression/lifting interface that is not visible in the existing order-25 periodic projection.  It gives one exact nontrivial W127 projection survivor, proves that all of its binary lifts fail, and derives the corresponding W131/E574 compressed spectral targets.

No LABS improvement or global exclusion is claimed.

## Symmetric homometric coordinates

In the order-25 compression of the normalized odd-perfect `(20,0)` class, let `p,c` be the ternary length-25 sequences after the standard half-shift of the B channel.  The periodic odd-perfect condition is

```text
p c* + c p* = 0  in Z[x]/(x^25-1).
```

Define

```text
u = p + c,
v = p - c.
```

Then coefficientwise cyclic autocorrelation gives

```text
PAF_u - PAF_v = 2 (p c* + c p*).
```

Hence the periodic cross equation is exactly equivalent to

```text
boxed: PAF_u = PAF_v.                       (1)
```

Moreover, the zero coefficient of the cross equation gives `p dot c=0`, so

```text
sum u = sum v = 10,
||u||^2 = ||v||^2 = ||p||^2 + ||c||^2.
```

The coordinate coupling is finite and exact:

```text
u_i =  2  => v_i = 0,
u_i = -2  => v_i = 0,
u_i =  1  => v_i in {-1,+1},
u_i = -1  => v_i in {-1,+1},
u_i =  0  => v_i in {-2,0,+2}.
```

Thus the compressed periodic problem is a small-alphabet cyclic homometry problem with a strong coordinatewise compatibility constraint, not a generic pair of ternary sequences.

## A genuine W127 order-25 survivor

For W127, `||p||^2+||c||^2=26`, and the 12 independent common PAF values must lie in `{2,3,4}` and sum to 37.

A local homometric search found the following exact pair:

```text
u = [ 1,-1, 0, 0, 1, 0, 0, 0, 0, 1, 2, 2, 1, 1, 0, 0, 0, 0, 0, 0, 2, 0,-2, 2, 0]
v = [ 1, 1, 2, 2, 1, 0, 0, 0, 0, 1, 0, 0,-1, 1, 0, 2,-2, 0, 2, 0, 0, 0, 0, 0, 0]
```

The induced ternary compression is

```text
p = [ 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1,-1, 0, 1, 0, 1, 0,-1, 1, 0]
c = [ 0,-1,-1,-1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0,-1, 1, 0,-1, 0, 1, 0,-1, 1, 0]
```

with

```text
(ka,kc) = (14,12),
sum p = 10,
sum c = 0,
K_1..K_12 = [4,4,2,4,3,2,2,2,4,4,3,3].
```

All 25 coefficients of the original integer cross equation vanish.  Therefore the W127 order-25 projection is genuinely nonempty in a support class not covered by the exact `ka>=18` exclusions.

## Exact binary lift exclusion for this survivor

Recover the unshifted B compression `q` from

```text
c = x^13 q,
q_j = c_(j+13 mod 25).
```

A binary length-50 half `A` lifting `p` has two choices exactly where `p_i=0`; similarly `B` lifts `q`.  This survivor has

```text
zeros(p)=11,
zeros(q)=13,
```

so there are exactly

```text
2^11 * 2^13 = 16,777,216
```

binary `(A,B)` lifts.

The committed checker

```text
code/oddperfect_w127_homometric_liftcheck.cpp
```

reconstructs all of them and evaluates the original aperiodic even correlations.  Exact 5-thread reproduction:

```text
W127_HOMOMETRIC_SURVIVOR ka=14 kc=12 K=4,4,2,4,3,2,2,2,4,4,3,3,
EXACT_LIFT_SUMMARY A_lifts=2048 B_lifts=8192 pairs=16777216 even_compatible=0 threads=5
EXACT_RESULT SURVIVOR_HAS_NO_W127_BINARY_LIFT
```

Thus this compressed survivor has **no W127 binary lift**.  This is an exact exclusion of this survivor only, not of the `ka=14` shard.

## Interpretation: the missing character channel is decisive

Write a length-50 binary half in its two order-25 fibre channels,

```text
A_i       = p_i + alpha_i,
A_(i+25)  = p_i - alpha_i,
```

where exactly one of `p_i,alpha_i` is nonzero; similarly for `B` using `q,beta`.

The order-25 periodic projection constrains the `p,q` channel.  The missing channel is equivalently measured by the negaperiodic aperiodic signature

```text
NAF_A(r) = C_A(r) - C_A(50-r),  r=1,...,24,
```

and similarly for B.

For W127, exact opposite-lag equality requires

```text
NAF_A(r) + NAF_B(r) = 0  for every r=1,...,24.      (2)
```

The survivor above passes every retained periodic equation but has no choice of fibre signs satisfying the full even-correlation target.  This demonstrates concretely why further periodic quotient filtering alone cannot certify liftability.

## W131 / E574 compressed target

The same interface extends directly to the actual first-improvement target W131 (`E=574`).  Let

```text
d_r = C_(2r)/2.
```

The exact W131 multiset classification and opposite-lag parity leave at most two antisymmetric defects.  The center value determines the order-25 norm:

```text
d_25 = 1  => ||u||^2=||v||^2=26,
d_25 = 3  => ||u||^2=||v||^2=28.
```

For the 24 opposite-lag pairs define the pair weight

```text
w_r = (d_r + d_(50-r))/2.
```

The 12 independent order-25 PAF values are sums of two such weights under the order-25 fold.  The exact W131 branches reduce to only four weight multisets:

```text
norm 26:
  0^1 1^9  2^14      (W131-A, zero defects),
  1^11 2^13          (all two-defect branches),
  1^12 2^11 3^1      (W131-C, zero defects),

norm 28:
  1^12 2^12          (the one-defect branches).
```

Enumerating pairings of these multisets gives exactly

```text
17 distinct sorted PAF multisets at norm 26,
 7 distinct sorted PAF multisets at norm 28.
```

So an E574 compressed candidate can be searched as a compatible homometric pair `(u,v)` in only 24 target spectral-multiset types.

The missing fibre condition is also sparse:

```text
norm 26: NAF_A + NAF_B has support 0 or 2, each nonzero value +/-4,
norm 28: NAF_A + NAF_B has support exactly 1, value +/-4.
```

This is the direct compression/lifting formulation of the earlier `W131` sparse-near-NGP classification.

## Pilot evidence at W131

A 5-core local pilot used simulated annealing only to generate compressed `u` factors, exact coordinate-compatible homometric mate enumeration (capped per `u`), and then exhaustive fibre-lift checking for every discovered projection pair.

One 20-second run produced

```text
compressed spectral hits       = 5,587
unique affine u classes        = 2,976
mate states checked            = 507,116,708
order-25 projection pairs      = 20
  norm 26 pairs                = 18
  norm 28 pairs                = 2
fibre near-NGP signature hits  = 0
full W131 even lifts           = 0
```

This is **heuristic evidence only** because compressed-factor generation and mate enumeration were not exhaustive.  It must not be used as a W131 exclusion.

The useful conclusion is mechanistic: in every sampled branch the periodic order-25 constraints were satisfiable, while the missing fibre/negaperiodic channel killed the candidate before odd-perfectness was even tested.

## Next exact route

1. Keep exact order-25 support/cross enumeration for the remaining W127 and W131 support classes.
2. Attach the fibre signature during enumeration instead of generating all periodic survivors first.
3. Use the sparse W131 defect signatures above as exact keys: zero/two `+/-4` coordinates at norm 26, one at norm 28.
4. Only reconstruct full binary sequences after a periodic key and a fibre key both match.

This changes the computational objective from “enumerate more compressed survivors” to “prove that no compressed survivor has a compatible missing character channel”, which is a substantially smaller and more target-specific interface problem.
