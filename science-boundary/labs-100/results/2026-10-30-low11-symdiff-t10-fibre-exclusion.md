# Low11 symmetric-difference `t=10`: exact compressed exhaustion and fibre exclusion

Date: 2026-10-30

## Scope

Continue the symmetric-difference decomposition from
[`2026-10-30-low11-symdiff-extreme-overlaps.md`](2026-10-30-low11-symdiff-extreme-overlaps.md).
For the remaining low11 `(20,0)` order-25 projection, let

```text
kp=||p||^2, kc=||c||^2, kp+kc=26,
t=|supp(p) intersect supp(c)|.
```

This note closes the complete overlap layer

```text
t=10
```

for both remaining norm splits `(kp,kc)=(12,14),(14,12)` and for both target
fibre defects relevant to W129/W131.

## Exact compressed enumeration

For `t=10`, the support symmetric difference has weight

```text
|D| = 26-2t = 6.
```

There are exactly 366 affine orbits of six-subsets of `Z_25`.  For each orbit,
`code/oddperfect_low11_symdiff_exact.cpp` solves the support equation

```text
P D* + D P* = 0    over GF(2),
```

then exhausts all signed `p,c` assignments satisfying the 13 independent
integer cyclic cross equations and the full low11 order-25 PAF target.

To remove load imbalance, the 366 affine difference orbits were partitioned
into twelve contiguous ranges for each `kp` value.  All 24 ranges were run
inside one hosted runner using four concurrent exact C++ processes.  The
workflow explicitly verified that the ranges form a disjoint partition of
`[0,366)` for both norm splits.

Workflow:

```text
run 41048664833
artifact labs100-low11-symdiff-t10
```

Aggregate exact counts from the 24 transcripts are

```text
kp  kc  support-pair orbits  p-sign tests  integer-H matches  compressed hits
12  14  285,602              3,427,224     56,662             0
14  12  285,602             25,989,782  1,952,548             2
```

Thus the `(12,14)` split is already impossible at the compressed order-25
level.  The `(14,12)` split leaves exactly two compressed candidates, both in
the affine-orbit range `[31,62)`.

## The two compressed survivors

An independently instrumented exact enumerator reproduced that hit shard and
returned the two representatives:

```text
candidate 1
p =  1 -1  1  0  1  1  0  1 -1  1  1  1  0  0  0  1  0  0  0  1  0  0  0  1  1
c =  0  1  1 -1  0  0  1 -1 -1  0 -1 -1  0  0  0  1  0  0  0 -1  0  0  0  1  1

candidate 2
p =  0  0  1  1  0  0  1  1  0  0 -1  1  0  1  0  1  1  0  1  1  0  1  0  1 -1
c =  1  0  0  0  0  0  0  0  0 -1 -1 -1  0  1  0 -1  1  0 -1  1  0 -1  0  1  1
```

Both have `kp=14,kc=12`, satisfy the complete periodic compressed cross
condition, and satisfy the complete low11 order-25 PAF target.  Therefore the
compressed projection itself is genuinely nonempty; a fibre check is needed.

## Exact fibre exclusion

The fixed-candidate oracle

```text
code/oddperfect_order25_fibre_mitm.cpp
```

exhausts every orientation of the zero compressed pairs and matches the full
24-coordinate negaperiodic autocorrelation defect vector exactly by
meet-in-the-middle.  It was run for each survivor for both target defect sizes:

```text
defect=1  (W129-A)
defect=2  (W131-A2 / W131-B1)
```

Independent hosted-runner result:

```text
run 41049306824
artifact labs100-t10-two-candidates-fibre

candidate 1 defect 1: compatible_probe_lifts=0
candidate 1 defect 2: compatible_probe_lifts=0
candidate 2 defect 1: compatible_probe_lifts=0
candidate 2 defect 2: compatible_probe_lifts=0
```

For each candidate the oracle hashed all `2^13=8192` lifts on the larger zero
fibre and probed all `2^11=2048` lifts on the smaller fibre against every exact
one- or two-defect target.  No compatible lift exists.

## Consequence

The complete low11 overlap layer `t=10` is therefore impossible for all three
remaining sparse near-NGP structural cases W129-A, W131-A2 and W131-B1.

Together with the exact `t=2` and `t=12` exclusions, only

```text
t = 4,6,8
```

remain in the low11 order-25 branch.

This result also changes the search priority: the compressed order-25 space is
not itself empty, but the full fibre defect constraint kills its rare survivors.
For the middle overlap layers it is preferable to push order-10 / near-NGP /
fibre information earlier in the enumeration instead of merely scaling the
signed compressed search.
