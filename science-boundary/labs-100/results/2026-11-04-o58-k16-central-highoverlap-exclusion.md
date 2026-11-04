# O=58, K=16: central high-overlap necessary-Q exact exclusion

Date: 2026-11-04

## Scope

The two central compression norm splits (kp,kc)=(5,11),(7,9) have multiple support-overlap classes. This result excludes their **six maximal-overlap subbranches** (and swapped necessary-Q counterparts), not the entire K16 layer.

With normalized half sums (a,b)=(2,2), K16 and O58 imply E=382+8(Q+R) and E<=574 requires Q+R<=24. The exact coupled one-sparse periodic/negacyclic cross equations and 2Q=SG+SH therefore give a necessary upper bound SG+SH<=48.

## Complete uncapped exact computation

Workflow (completed, then retained via run/artifact evidence):

    .github/workflows/temp-labs100-o58-k16-central-highoverlap.yml

Producer:

    code/o58_k16_compressed_uncapped.cpp

Fibre oracle:

    code/o58_k16_qgroup_exact.cpp

GitHub Actions **run 41851120769**, job **126647385464**, completed **success**. Artifact `labs100-o58-k16-central-highoverlap` holds the complete producer/fibre logs. Branch processes used one OpenMP thread each and were parallelized with xargs across the single runner.

Unlike the preceding compressed prototype, the exact producer retains and emits **every** `HIT`; there is no 10,000-row cap. The workflow asserts in each case that `qhits=` equals the number of emitted rows before invoking the exact fibre solver. The latter enumerates all signed negacyclic fibres for each affine-canonical complementary support class and conservatively compares groupwise minimum SG to exact SH.

| kp | kc | support overlap t | defect class | compressed hits | fibre support groups | Qpass | min(SG+SH-48) |
|---:|---:|---:|---|---:|---:|---:|---:|
| 5 | 11 | 4 | unit | 2,887 | 2,853 | 0 | 30 |
| 5 | 11 | 4 | five | 800 | 786 | 0 | 18 |
| 5 | 11 | 5 | center | 44 | 38 | 0 | 30 |
| 7 | 9 | 6 | unit | 369 | 359 | 0 | 54 |
| 7 | 9 | 6 | five | 95 | 95 | 0 | 42 |
| 7 | 9 | 7 | center | 4 | 1 | 0 | 30 |

All six branches have strictly positive necessary-budget margins. Swapping p and c preserves the periodic cross equation, SG, complementary supports and SH; it sends the negacyclic commutator orientation to its negative. Both orientations of the unit/five classes are included in the exact fibre oracle, so the absence of a necessary-Q survivor also excludes the swapped norm splits at the corresponding overlap classes. This symmetry is not used to equate aperiodic energies of individual full binary lifts.

## Frontier

The K16 extreme splits (1,15),(3,13),(13,3),(15,1) were previously excluded in run 41719753889. The present result additionally closes the largest-overlap six cases of (5,11),(7,9) and their swapped necessary-Q counterparts.

The remaining smaller-overlap central K16 cases are not excluded by this note. The result does not prove all of K16 impossible, nor does it find any E<=574 candidate.

Given repeated exact edge exclusions with no unrestricted energy improvement, do not simply scale the same exhaustive pipeline to every lower-overlap case without checking whether central K22/24/26 or higher odd-energy target classes offer qualitatively better candidates.
