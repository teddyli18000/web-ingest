# Odd-perfect `(20,0)`, `W=127`: reduction to NGP50 and Paley-class exclusion

Date: 2026-10-29

## Scope

This note isolates the lowest possible normalized even-energy budget in the odd-perfect half-sum class `(20,0)`.

For an odd-perfect length-100 sequence, write

```text
A_i=s_(2i), B_i=s_(2i+1),
c_r=C_(2r),
d_r=c_r/2,
W=sum_(r=1)^49 d_r^2=E_even/4.
```

The `(20,0)` class has

```text
sum d_r = 75.
```

The general integer convexity calculation recorded in the periodic-spectral note gives `W>=127`. At equality the multiset is forced:

```text
d_r = 1  for 23 lags,
d_r = 2  for 26 lags.
```

Thus total LABS energy would be

```text
E = 50 + 4*127 = 558.
```

No E=558 sequence is claimed here.

## Equality forces a negaperiodic Golay pair

For every `r=1,...,24`, the universal opposite-even-lag congruence says

```text
d_r == d_(50-r) (mod 2).
```

At `W=127`, every `d_r` lies in `{1,2}`. Equal parity therefore forces exact equality

```text
d_r=d_(50-r),  r=1,...,24.
```

Equivalently, in the periodic-spectral coordinates

```text
v_r=(c_r-c_(50-r))/4=0
```

for every paired lag.

But

```text
c_r = AF_r(A)+AF_r(B),
```

so

```text
c_r-c_(50-r)
 = NAF_r(A)+NAF_r(B).
```

Hence `(A,B)` must be a binary **negaperiodic Golay pair of length 50** (NGP50).

The exact remaining LABS conditions are strictly stronger than being an NGP50: the interleaving must also satisfy the odd-perfect cross equations. A cheap necessary part of those equations is the periodic cross condition

```text
A B* + x B A* = 0   in Z[x]/(x^50-1).          (1)
```

Therefore every E558 candidate in this half-sum class must lie in

```text
NGP50  intersect  {pairs satisfying (1)}
```

and must then pass the original aperiodic odd-correlation `|C_k|=1` test.

## Public NGP50 constructions

Balonin and Djokovic introduced the modern NGP terminology and gave two Paley series. The first Paley construction produces an `NGP_(q+1)` for every odd prime power `q`; `q=49` therefore gives an explicit NGP50. Their appendix lists the corresponding length-50 conference row.

Egan's later equivalence paper states that Ito had listed associated pairs (the same objects as NGPs) for every even length through 90, while a complete equivalence classification was only carried out through length 20. Thus the existence of NGP50 is classical, but the public literature checked here does **not** provide a complete classification of all NGP50 equivalence classes.

References:

- N. A. Balonin and D. Z. Djokovic, *Negaperiodic Golay pairs and Hadamard matrices*, 2015.
- R. Egan, *On equivalence of negaperiodic Golay pairs*, Designs, Codes and Cryptography 85 (2017), 523-532.
- N. Ito, *On Hadamard Groups IV*, J. Algebra 234 (2000), 651-663.

## Exact test of the first-Paley length-50 class

Implementation:

```text
code/ngp50_paley_orbit_cross.cpp
```

The program reconstructs the first-Paley NGP50 from the published `q=49` conference row, verifies the NGP equations from scratch, and exhausts its standard NGP equivalence orbit using the operations recorded by Balonin-Djokovic/Egan:

1. independent reversal of the two sequences;
2. independent negacyclic shifts;
3. swapping the sequences;
4. simultaneous signed multipliers coprime to 50;
5. simultaneous alternation.

Independent global signs do not affect equation (1); restricting each negashift exponent to `0..49` therefore represents shifts modulo the generated sign. Likewise multipliers `k` and `k+50` differ by the explicitly included simultaneous alternation. The implemented normal form tests

```text
20 multipliers
* 2 * 2 reversal choices
* 50 * 50 independent negashifts
* 2 alternation choices
* 2 swap choices
= 800,000 representatives.
```

Every representative is tested against (1).

Exact result:

```text
SUMMARY tested=800000 hits=0 best=-1
```

Therefore **no member of the standard equivalence class of the first-Paley NGP50 satisfies even the periodic cross condition required by an odd-perfect E558 LABS candidate.**

This is a rigorous exclusion of that construction class, not of all NGP50s.

## Consequence / next step

The W127 branch is now best viewed as a simultaneous-design problem rather than a generic LABS search:

```text
NGP50 + periodic cross orthogonality + aperiodic odd-perfectness + half sums (20,0).
```

The next useful routes are:

1. locate additional public NGP50 representatives/classes (especially Ito's associated-pair example at order 50) and test their complete standard equivalence orbits;
2. derive a direct incompatibility theorem between the NGP equation and the cross factorization under half sums `(20,0)`;
3. treat W129/W131 as sparse near-NGP layers, because the antisymmetric even-correlation defect has squared support budget only 1 or 2.

Do not infer global NGP50 nonexistence or complete classification from the 800,000-pair Paley orbit test.
