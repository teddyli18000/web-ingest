# O=58, K=18: exact center-defect exclusion for kp=3 and its kp=15 Q-swap

Date: 2026-11-02

## Scope

This note closes one exact branch of the current odd-energy-58 attack:

```text
odd energy O = 58,
normalized half sums (a,b)=(2,2),
order-25 center K=18,
center defect class,
(kp,kc)=(3,15),
```

and separately audits its exact Q-stage swap `(kp,kc)=(15,3)` at the original length-100 LABS objective.

It does **not** close all of K18. The unit/five defect classes and the other norm splits remain separate branches.

## Arithmetic budget

For O=58 and E<=574 the even-energy budget is 516. At K=18,

```text
m = K-25 = -7,
W = m^2 + 2(Q+R),
Q+R <= 40.
```

For compressed spectrum `G` and negacyclic fibre spectrum `H`,

```text
2Q = SG + SH,
SG = sum G_j^2,
SH = sum H_j^2.
```

Hence every target must satisfy

```text
SG + SH <= 80.
```

## Complete compressed census

The exact generic compressed solver with support-only qmin DP pruning covers both allowed center overlaps for kp=3:

```text
t=1:
  diff_reps=4,113
  support_orbits=2,262
  fixedtests=6,786
  Hmatches=8,355
  qhits=819
  groups=341

t=3:
  diff_reps=10,452
  support_orbits=1,826
  fixedtests=5,478
  Hmatches=6,849
  qhits=826
  groups=220
```

The 1,645 qhits therefore reduce to exactly 561 canonical fibre-support groups.

Implementation:

```text
code/o58_k_compressed_groups_dp.cpp
```

## Exact fibre-Q census

The complete center negacyclic census gives

```text
canonical_groups=561
outer sign states=287,232
exact half-fibre solutions=8,220,680
Q-feasible half-pairs=2
minSH=30
minmargin=0
```

Both Q-feasible half-pairs live on the same canonical support pair and exactly saturate Q=40:

```text
as=4194303
gs=1195794
minSG=50
SH=30

amask=3402252, gmask=2834
amask=792051,  gmask=2834
```

Thus there are no hidden positive-margin Q survivors: the two displayed half-pairs are the complete Q boundary.

Implementation:

```text
code/o58_k_qgroup_groups.cpp
```

## Targeted signed compressed recovery

Re-running the complete compressed enumeration in targeted-recovery mode for the only Q-feasible support pair gives

```text
t=1: emitted=0
t=3: emitted=2
```

The two signed compressed representatives are therefore complete for this Q boundary, rather than manually selected examples.

## Direct length-100 audit

`code/o58_k18_kp3_center_final.cpp` maps both recovered compressed representatives to the canonical fibre support, restores both independent global fibre signs, pairs them with both QHITs, and exhausts all 500 induced full-length affine transforms.

For the original kp=3 side:

```text
base lifts=16
affine transforms=8,000
odd-energy-58 passes=0
E<=574 passes=0
minimum full energy=1438
minimum odd energy=282
```

Because the Q-stage equations are exactly symmetric under

```text
(p,c,alpha,gamma) -> (c,p,gamma,alpha),
```

the verifier also constructs the corresponding kp=15 side explicitly instead of assuming aperiodic-energy invariance. Its direct audit is identical:

```text
base lifts=16
affine transforms=8,000
odd-energy-58 passes=0
E<=574 passes=0
minimum full energy=1438
minimum odd energy=282
```

So the two Q-feasible boundary half-pairs are extremely far from the required aperiodic odd-energy layer even though they exactly saturate the cyclic Q budget.

## Reproduction

Clean GitHub Actions run:

```text
run 41334511674
artifact labs100-o58-k18-kp3-center-exact
```

The downloaded artifact was independently inspected after the run. It contains exactly two `QHIT` lines, exactly two targeted `SIGNEDHIT` lines, and the two final zero-pass summaries above.

## Consequence / search lesson

The complete center-defect `(kp,kc)=(3,15)` K18 branch, and its explicit `(15,3)` Q-swap, contain no O=58 E<=574 sequence.

More importantly, K18 is the first layer where the cyclic Q bound is no longer sufficient by itself: two exact Q-boundary fibres survive but fail catastrophically at the aperiodic odd-correlation layer. Future K18 work should therefore bring the individual odd-correlation / R constraints into survivor handling as early as practical rather than scaling fibre-Q enumeration alone.
