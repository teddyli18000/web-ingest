# W127: exact `ka=10` exclusion and `ka=16` order-10 lift exclusion

Date: 2026-10-29

## Scope

In the odd-perfect `(20,0), W=127` branch, the order-25 compression

```text
p_i=(A_i+A_(i+25))/2,
q_i=(B_i+B_(i+25))/2,
c=x^13 q
```

produces ternary length-25 sequences satisfying

```text
sum p=10,
sum c=0,
||p||^2+||c||^2=26,
p c*+c p*=0 mod (x^25-1),
PAF_p(r)+PAF_c(r) in {2,3,4}, r=1,...,12.
```

Let `ka=||p||^2`. This note records two new exact results:

```text
ka=10: no order-25 W127 target exists.
ka=16: exactly four order-25 orbit representatives survive,
       but none is compatible with any exact order-10 cross+NGP profile.
```

Hence neither shard can lift to a W127 length-50 pair.

## `ka=10,kc=16`

Here

```text
p: ten +1 entries and fifteen zeros,
c: eight +1, eight -1, nine zeros.
```

The p support therefore contains all of the p information. Under the affine group of `Z_25`, all

```text
C(25,10)=3,268,760
```

p supports reduce to exactly

```text
6,578 affine support orbits.
```

Modulo 2, the cyclic cross equation depends only on the p and c supports. For each p-support representative the GF(2) kernel is computed exactly and only weight-9 zero masks for c are retained. Quotienting these by the stabilizer of the p support gives exactly

```text
3,909,436 support-pair orbits.
```

For each support pair, write c as all-plus on its 16-point support followed by flipping an 8-subset to negative. The 13 independent integer cross equations are solved exactly with an 8+8 meet-in-the-middle. The complete 13-vector is encoded injectively in a base-17 64-bit key; global `c -> -c` symmetry fixes one support coordinate positive. A target hit is independently checked against all 25 original cyclic cross coefficients.

Implementation:

```text
code/oddperfect_w127_ka10_kernel_mitm.cpp
```

Independent four-core GitHub Actions result:

```text
p_support_orbits=6578
support_pair_orbits=3909436
SUMMARY support_pair_orbits=3909436 cross=18960355 target=0
```

Thus `ka=10` is impossible already in the order-25 projection.

## `ka=16,kc=10`: order-25 survivors

Here

```text
p: thirteen +1, three -1, nine zeros,
c: five +1, five -1, fifteen zeros.
```

The exact search fixes c, applies the GF(2)-kernel condition to the nine-zero mask of p, and solves the remaining three-negative subset by an injective base-19 integer MITM. Affine support symmetry plus support stabilizers and `c -> -c` are handled by explicit orbit marking.

The exact coverage counts are

```text
6,578 c-support orbits,
824,362 signed c orbit representatives.
```

Implementation:

```text
code/oddperfect_w127_ka16_kernel_mitm.cpp
```

Independent four-core GitHub Actions result:

```text
SUMMARY supports=6578 c_reps=824362 cross=35894201 target=4
```

So the order-25 projection is not empty. The enumerator freezes the four projected survivors in `ka16_survivors.txt` for the next independent test.

## Exact order-10 lift compatibility

The already established order-10 W127 calculation is independently regenerated from

```text
code/oddperfect_h20_w127_h10_profiles.cpp
code/oddperfect_h20_w127_ngp10.cpp
```

and again gives

```text
63,660 exact order-10 cross profiles,
4,220 profiles that also satisfy the projected NGP condition.
```

For a fixed order-25 p and an order-10 A residue-sum profile `s_0,...,s_9`, consider one residue class `r mod 5`. Let

```text
f_r = sum_{i == r mod 5} p_i,
z_r = number of zero p_i in that class.
```

The five opposite A-pairs in this class contribute

```text
s_r+s_(r+5) = 2 f_r.
```

Each zero p-pair has orientation `(+1,-1)` or `(-1,+1)`, so with

```text
d_r=(s_r-s_(r+5))/2
```

an A lift exists exactly when

```text
|d_r| <= z_r,
d_r == z_r (mod 2).
```

The same test applies to q and the B profile. The durable order-25 convention is

```text
c=x^13 q,
```

so the compatibility checker reconstructs `q_i=c_(i+13)` before testing B.

Implementation:

```text
code/oddperfect_w127_ka16_order10_compat.py
```

The four projected survivors give

```text
survivor 1: 0 compatible order-10 profiles
survivor 2: 0 compatible order-10 profiles
survivor 3: 0 compatible order-10 profiles
survivor 4: 0 compatible order-10 profiles
SUMMARY survivors=4 profiles=4220 compatible_pairs=0
```

Therefore none can lift to a length-50 `(A,B)` pair satisfying the necessary order-10 cross+NGP equations. Hence `ka=16` is impossible for W127.

## Independent reproduction

Both `ka=10` and `ka=16`, the 4,220-profile regeneration, and the lift-compatibility test were run sequentially in one hosted runner so that each compute-heavy kernel used all four runner CPUs without creating a matrix of queued jobs.

Workflow run:

```text
41000197790
```

The exact compute steps returned the expected counts above and the workflow completed successfully.

## Consequence

The original W127 support split was

```text
ka=10,12,14,16,18,20,22,24.
```

Exact exclusions now remove

```text
10,16,18,20,22,24.
```

Only

```text
boxed: ka=12 or ka=14
```

remain in the W127 order-25 branch.

The lower-support pair layers are substantially denser under a naive support-orbit enumeration. The next useful representation should therefore incorporate order-10 residue information before generating the full order-25 support-pair space, rather than mechanically scaling the same enumeration.
