# Joint-decoupled LB33 exact exclusion

Date: 2026-10-29 (+08:00)

## Scope

This note extends the retained-18-core joint-decoupled front/final product-plane search to the complete LB33 semilinear tier.

The already verified global scan has 24 LB33 transforms. The exact six-element semilinear orbit theorem partitions them into four orbits. Using the verified global-summary artifact and grouping its 24 LB33 rows by the exact unordered transported input/output plane keys gives the four representatives:

```text
J: (c,k) = (0x1d,2)
K: (c,k) = (0x09,3)
L: (c,k) = (0x12,3)
M: (c,k) = (0x59,3)
```

Each group contains exactly six members, reproducing the established `LB33: 4 exact orbits` count.

As in the LB31/LB32 follow-up, the search is broader than the original same-orientation semilinear family: the nine front norm-product orientations and the nine final-product/output orientations may differ independently. The prelinear network must synthesize the union of both operand sets.

## Complete helper-aware joint frontier

`screen_joint_decoupled_instance.cpp` was run locally on all four transported representatives. The program implicitly exhausts all `3^18` front/final orientation pairs after precomputing the `4^9` possible prelinear-union states and the `3^9` output states. It first applies target-only closure lower bounds, then exact one-helper closure on every surviving pre/output target set.

Results:

```text
J (0x1d,2): pass0=3,549, helper_frontier=0
K (0x09,3): pass0=4,801, helper_frontier=0
L (0x12,3): pass0=5,287, helper_frontier=0
M (0x59,3): pass0=5,689, helper_frontier=0
```

`pass0` is the number of orientation pairs surviving the initial zero-helper lower bound with variable cost <=36. `helper_frontier=0` means every one of those pairs is rigorously pushed above the 36-gate variable budget after exact one-helper linear-network closure is applied to the relevant prelinear and output target sets.

No score-34/35/36 frontier row survives. Therefore no middle-correction materialization or stronger two-helper final checker is needed for this tier.

## Consequence

All four LB33 exact orbit representatives are excluded from a 101-gate retained-18-core circuit even in the joint-decoupled front/final plane family. By the proved exact six-element semilinear orbit equivalence, this transports to **all 24 LB33 transforms**.

The retained-core semilinear search can therefore move directly to LB34, which contains 78 transforms / **13 exact six-element orbits**.

This result is specific to the retained 18-gate inversion core and its transported middle/final product structure. It does not exclude a changed inversion core or a changed middle/core interface.

## Reproduction

The four local scans ran in parallel on four CPU cores. Individual runtimes were roughly 8–15 seconds and peak RSS about 13 MiB per process. The generic frontier implementation had already reproduced the live-field A regression exactly (`464931 -> 9761`, with the known score/distance histograms) before being used on these transported instances.
