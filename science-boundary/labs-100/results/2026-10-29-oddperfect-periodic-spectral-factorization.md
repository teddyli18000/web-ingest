# Periodic spectral factors on the odd-perfect layer

Date: 2026-10-29

## Purpose

The endpoint-defect hierarchy is now exact through `d=5`, but candidate quality did not improve as the excluded region grew. This note changes representation again. Starting from the global odd-perfect factorization

```text
A B^R + x B A^R = (x^50-1)Q,
D = A^2-xB^2,
```

we fold the Lagrange identity into the periodic and negaperiodic quotient rings. The result turns the remaining odd-perfect problem into an integer cyclic phase-retrieval problem with an unusually small target norm gap.

No `E<=574` sequence is claimed here.

## Setup

Split the length-100 sign sequence into length-50 Littlewood polynomials

```text
A(x)=sum s_(2i) x^i,
B(x)=sum s_(2i+1) x^i.
```

Let

```text
c_r = C_(2r),  r=1,...,49
```

be the even-lag autocorrelations of the original sequence. The universal opposite-lag congruence implies

```text
c_r/2 == c_(50-r)/2 (mod 2).
```

For `r=1,...,24` define integer pair coordinates

```text
u_r = (c_r+c_(50-r))/4,
v_r = (c_r-c_(50-r))/4,
```

and set

```text
u_25 = c_25/2.
```

Build two length-50 integer sequences

```text
U_0 = 25,
U_r = U_(50-r) = u_r,
U_25 = u_25,

V_0 = 25,
V_r = v_r,
V_(50-r) = -v_r,
V_25 = 0.
```

To avoid confusion with the even-lag energy, this note writes that energy as `E_even`.

## Folding D

Write

```text
D(x)=A(x)^2-xB(x)^2 = sum_(n=0)^99 d_n x^n.
```

The coefficient lattice proved in the global factorization note is

```text
d_n == +1 (mod 4),  0<=n<50,
d_n == -1 (mod 4),  50<=n<100.
```

Hence the periodic and anti-periodic folds

```text
R_j = (d_j+d_(j+50))/4,
T_j = (d_j-d_(j+50))/2,
```

are integer sequences for `j=0,...,49`; each `T_j` is odd.

## Exact periodic and negaperiodic identities

On the unit circle put

```text
P = A A* + B B*,
H = A B* + x B A*.
```

The algebraic Lagrange identity is

```text
P^2 = D D* + H H*.
```

Odd-perfectness gives

```text
x^49 H = (x^50-1)Q,
```

where `Q` is a length-50 anti-palindromic Littlewood polynomial.

### Modulo x^50-1

Here `H=0`. The folded forms of `D` and `P` are `4R` and `4U`, so

```text
boxed: R R* = U^2    in Z[x]/(x^50-1).        (1)
```

Thus `R` and `U` are integer homometric signals on the cyclic group `Z_50`.

Taking the zero coefficient in (1) gives

```text
||R||_2^2 = ||U||_2^2.                        (2)
```

### Modulo x^50+1

Now `x^50=-1`, so the odd-perfect factor contributes `-2Q`. The folded forms of `D` and `P` are `2T` and `4V`. Therefore

```text
boxed: T T* + Q Q* = 4 V^2    in Z[x]/(x^50+1).   (3)
```

Taking the zero coefficient and using `||Q||_2^2=50` gives

```text
||T||_2^2 + 50 = 4 ||V||_2^2.                 (4)
```

Equations (1) and (3) are exact, not heuristic relaxations.

## The target becomes a one-unit norm gap

The even energy is

```text
E_even = sum_(r=1)^49 c_r^2
       = 4 [ 2 sum_(r=1)^24 (u_r^2+v_r^2) + u_25^2 ].
```

Define the integer budget

```text
W = E_even/4
  = 2 sum_(r=1)^24 (u_r^2+v_r^2) + u_25^2.
```

Equivalently,

```text
||U||_2^2 + ||V||_2^2 = 1250 + W.
```

For an odd-perfect sequence total energy is `50+E_even`.

- In the global-product `+1` class, an `E<=574` breakthrough requires `W<=131`.
- In the global-product `-1` class, the largest admissible score below 578 is 570, so `W<=130`.
- The public E578 incumbent has `E_even=528`, hence `W=132`.

So the first possible improvement is literally one unit below the incumbent in this normalized integer budget.

For the incumbent,

```text
||U||_2^2 = 717,
||V||_2^2 = 665,
W = 132.
```

## Trivial phase factors are exactly cyclic near-skew cuts

The same Lagrange algebra gives two stronger identities before taking norms:

```text
D A* = A P,
D B* = -x B P.
```

Modulo `x^50-1` these become

```text
R A* = U A,
R B* = -x U B.                                (5)
```

Suppose the cyclic homometric mate is a monomial phase factor,

```text
R = sigma x^m U.
```

Binary consistency in (5) forces

```text
sigma = (-1)^m,
```

and coefficient comparison yields

```text
A_j = (-1)^m A_(m-j mod 50),
B_j = (-1)^(m+1) B_(m-1-j mod 50).
```

After interleaving A and B, the original length-100 sequence satisfies

```text
boxed: s_p = (-1)^(m+p) s_((2m-p) mod 100).    (6)
```

Conversely, (6) implies `R=(-x)^m U`.

Therefore the monomial/trivial phase-retrieval family is exactly the family obtained by choosing a cyclic cut of a near-skew circle. The ordinary canonical near-skew form is only the `m=0` cut.

This explains a previously puzzling search basin. The reproducible odd-perfect `E=1162` state recorded as a `3-bit boundary + skew97` tail has cyclic axis `m=1` and satisfies

```text
R = -x U.
```

It is therefore not a genuinely new spectral family; it is the same trivial cyclic phase geometry viewed through a different cut. The E578 incumbent has `m=0` and `R=U`.

## Pilot search outside every cyclic near-skew cut

The earlier `oddperfect_outside_nss.cpp` excluded only the standard LABS symmetry orbit of the canonical near-skew form. A stronger classifier checks (6) for every `m=0,...,49`.

A short exact-odd-perfect tabu pilot using that classifier found the following genuinely non-monomial state:

```text
-+---++-+-++++--+++---+-+-+--++-+--++++++-++-------+-+--+++-+-+--++++--+++++++-++-++--+-+++++--+---+
```

Independent rescoring gives

```text
E = 1538
odd energy = 50
even energy = 1488
parity-half sums = (10,0)
cyclic near-skew axes = none
W = 372
```

The corresponding `R` is not any signed cyclic shift of `U`.

This is only heuristic evidence about the geometry, not a lower bound. Its value is qualitative: once all trivial cyclic cuts are removed, the first basin found by the calibrated odd-perfect walk is still very far from the target budget `W<=130/131`.

A deterministic reproduction from the committed search kernel is

```text
--runs 1 --steps 9000 --threads 1 --seed 5868043999101447584
```

and should return the E1538 state above.

## A sharp arithmetic corner: half sums (20,0)

For an odd-perfect target with parity-half sums `(20,0)`,

```text
sum_(r=1)^49 c_r = (20^2-100)/2 = 150.
```

Set

```text
d_r = c_r/2.
```

Then every `d_r` is an integer and

```text
sum d_r = 75,
sum d_r^2 = W <= 131.
```

Write `d_r=1+y_r`. Since there are 49 variables,

```text
sum y_r = 26,
sum d_r^2 = 101 + sum y_r^2.
```

Because `y(y-1)>=0` for every integer `y`, the absolute minimum is

```text
W >= 127.
```

Moreover the entire target range is classified by the tiny excess

```text
sum [y_r(y_r-1)] = W-127 <= 4.
```

Hence every even correlation is nonnegative and the only possible multisets are:

```text
W=127:  d=1 x23, d=2 x26.

W=129:  either
        d=0 x1, d=1 x21, d=2 x27,
        or
        d=1 x24, d=2 x24, d=3 x1.

W=131:  either
        d=0 x2, d=1 x19, d=2 x28,
        or
        d=0 x1, d=1 x22, d=2 x25, d=3 x1,
        or
        d=1 x25, d=2 x22, d=3 x2.
```

Since the `(20,0)` class has global product `+1`, its allowed odd-perfect breakthrough budgets are odd, exactly `W=127,129,131` inside this range.

This is much stronger than a generic energy bound: every even autocorrelation would have to lie in `{0,2,4,6}`, with almost all equal to 2 or 4.

## Exact low-order spectral projections

Equation (5), or directly `H=0` at every 50th root of unity, permits exact quotient projections.

For order 5 define residue sums

```text
alpha_r = sum_(i == r mod 5) A_i,
beta_r  = sum_(i == r mod 5) B_i.
```

Each lies in `{-10,-8,...,10}`. In `Z[x]/(x^5-1)` the condition is

```text
alpha beta* + x beta alpha* = 0.               (7)
```

If

```text
K_j = sum_i alpha_i beta_(i-j),
```

then (7) is exactly

```text
K_0+K_1=0,
K_2+K_4=0,
K_3=0.
```

For `(20,0)`, there are `3526 * 8801` raw `(alpha,beta)` profiles. Exactly `57,566` satisfy (7). Adding the rigorous convex lower bound on the three order-5 autocorrelation groups leaves only `3,435` profiles capable of `E_even<=524`.

Those `3,435` profiles split by their order-5 energy lower bound as

```text
508 : 1415 profiles
516 :  760 profiles
524 : 1260 profiles.
```

Thus even the coarsest nontrivial spectral projection removes more than 99.98% of the raw profile pairs in this class.

The order-10 lift uses the differences between the two five-term subresidue sums. If

```text
delta_r   = sum_(i == r mod 10) A_i - sum_(i == r+5 mod 10) A_i,
epsilon_r = sum_(i == r mod 10) B_i - sum_(i == r+5 mod 10) B_i,
```

then in `Z[x]/(x^5+1)` the exact condition is

```text
delta epsilon* + x epsilon delta* = 0.          (8)
```

Writing `E=delta epsilon*`, (8) has only two independent coefficient equations:

```text
E_0+E_1=0,
E_2-E_4=0.
```

This permits exact linear elimination of two `epsilon` coordinates after fixing `delta`; no Cartesian product over all subresidue splits is required.

A complete local enumeration of all 3,435 order-5 survivors found

```text
37,510,880 exact order-10 lifts,
287,440 lifts whose order-10 convex even-energy lower bound is <=524,
minimum order-10 lower bound = 508.
```

So order 10 is useful but does not by itself close `(20,0)`. The stronger correlation-multiset classification above should be combined with the next projection rather than scaling the same filter blindly.

## Relation to phase-retrieval literature

Equation (1) is a finite cyclic homometry problem. Classical homometric-set work gives structural factorization results in torsion-free settings, while finite cyclic phase retrieval is known to admit nontrivial homometric pairs. Therefore the existence of (1) alone does not justify cancelling to a trivial shift/reflection. The LABS-specific leverage is the additional Littlewood origin (5), the negaperiodic identity (3), and the extremely small budget `W<=130/131`.

Relevant references include Rosenblatt-Seymour on homometric integer sums and modern finite-alphabet phase retrieval on cyclic groups. They motivate the factorization viewpoint but do not currently provide the needed `Z_50` rigidity theorem at this norm threshold.

## Next route

The useful dichotomy is now:

1. **trivial monomial phase** `R=(-x)^m U`, exactly the cyclic-near-skew cut family;
2. **genuine nontrivial cyclic homometry**, which must still satisfy the binary coupling identities (5), the negaperiodic identity (3), and `W<=130/131`.

The next exact attack should combine the sharp target half-sum arithmetic with finer quotient projections (especially order 25 / full `Z_50` constraints), rather than returning to endpoint defect 6 or spending more compute on trivial cyclic-near-skew basins.
