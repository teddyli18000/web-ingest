# Low11 W129/W131: complete all-affine fibre closure

Date: 2026-10-30

## Scope

This note closes the affine-coverage gap in the remaining `(20,0)` low11 order-25 branches

```text
W129-A,
W131-A2,
W131-B1.
```

For these three cases the periodic order-25 weight multiset is `1^11 2^13`.  Prior exact W127 computations exclude `kp=10,18,20,22,24`; `kp=16` has four compressed survivors, and the remaining norm splits are `kp=12,14`.  For `kp=12,14`, the support overlap

```text
t = |supp(p) intersect supp(c)|
```

is even and lies in `{2,4,6,8,10,12}`.

A subtlety matters: the periodic compressed target is invariant under affine transformations of `Z_25`, but the aperiodic binary fibre condition is not automatically invariant under every multiplier.  Therefore checking one compressed affine representative is insufficient.  Every affine image must be fibre-tested unless a separate invariance proof is supplied.

## Compressed exhaustion

The exact symmetric-difference computations give:

- `t=2,12`: zero compressed targets (`2026-10-30-low11-symdiff-extreme-overlaps.md`);
- `t=4`: zero compressed targets (`2026-10-30-low11-symdiff-t4-exclusion.md`);
- `t=6`: five compressed affine representatives;
- `t=8`: four compressed affine representatives;
- `t=10`: two compressed affine representatives (`2026-10-30-low11-symdiff-t10-fibre-exclusion.md`).

Thus only eleven compressed affine representatives require an aperiodic fibre audit.
They are frozen in

```text
science-boundary/labs-100/data/low11-affine-fibre-survivors.txt
```

with five from `t=6`, four from `t=8`, and two from `t=10`.

## Exact all-affine fibre audit

The workflow

```text
.github/workflows/temp-labs100-low11-all-affine-fibre.yml
```

expands each of the eleven representatives through the full affine group

```text
i -> a i + b mod 25,
gcd(a,25)=1,
b in Z_25.
```

Each representative has 500 distinct images, so exactly

```text
11 * 500 = 5500
```

compressed candidates are checked.

For every image the committed exact oracle

```text
science-boundary/labs-100/code/oddperfect_order25_fibre_mitm.cpp
```

checks both sparse aperiodic target families:

```text
defect=1  (W129-A),
defect=2  (W131-A2 / W131-B1).
```

The oracle exhausts all binary orientation lifts by an exact meet-in-the-middle lookup of the 24-coordinate negaperiodic autocorrelation-difference vector; it uses no heuristic solver and has no timeout-based exclusion.

Independent clean-checkout Action:

```text
run       41095198222
job       124199014358
artifact  labs100-low11-all-affine-fibre
artifact id 12995942988
artifact sha256 7598ed4969a1f1988071e8fd0930cc0921c2c8f7e8fc1f7271a682b7dedfb771
```

Exact artifact summary:

```text
AFFINE_FIBRE_SUMMARY images=5500 hit_images=0 sum_defect1=0 sum_defect2=0
```

The raw `affine-fibre.tsv` contains exactly 5500 rows.  A separate scan of that table finds zero rows with a nonzero defect-1 or defect-2 lift count.

## W127 affine audit

The same affine issue was separately checked for the four historical W127 `kp=16` compressed survivors.  Their 2000 affine images give

```text
AFFINE_FIBRE_SUMMARY images=2000 hit_images=0 sum_defect1=0 sum_defect2=0
```

in run `41044068470` / artifact `labs100-kp16-affine-fibre-audit`.
For W127 itself the relevant zero-defect fibre exclusion had already been established by the committed regression/original exhaustive lift computation; this 2000-image audit was introduced specifically to remove the later affine-representative ambiguity for the sparse-defect targets.

## Consequence

Within the low11 projection, every possible overlap layer is now exactly exhausted:

```text
t=2   compressed empty
t=4   compressed empty
t=6   all affine images fibre-empty
t=8   all affine images fibre-empty
t=10  all affine images fibre-empty
t=12  compressed empty
```

Therefore there is no `(20,0)` odd-perfect candidate in the three low11 target branches `W129-A`, `W131-A2`, or `W131-B1` at energy `<=574`.

This is a closure of those three branches, not a claim that every other `(20,0)` W129/W131 pattern or the entire odd-perfect layer has been excluded.  The next search should move to a genuinely different half-sum/structural region rather than extend the low11 compressed search.
