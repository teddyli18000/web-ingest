# BPZ Definition-2 t=9 frontier

This note records only completed, replayable results from the 2026-10-27 search. Queued, running, failed, or resource-exhausted jobs are deliberately excluded from negative claims.

## Target

For a five-dimensional Definition-2 gadget with `|I|=|X|=367` and `t` private pairs, Gao's product has

`(367-t)^2 + 2*t*367 = 367^2 + t^2`.

The published BPZ/Tan gadget has `t=8`, hence `134753`. A valid `t=9` gadget would immediately give `134770` points in `C7^10`.

Public BPZ/Tan source is pinned at `tandonravi/C7-Shannon-Capacity-Heterogeneous-Recursion@c753408492dde92a239708986d16c15dbf6c3235`.

## Fixed BPZ base

With the published `I0` and `X` held fixed, exhaustive ambient enumeration finds exactly eight unique-owner private candidates in all of `C7^5`. Therefore a ninth private pair does not exist for the fixed pair `(I0,X)`; this is stronger than an orientation-SAT failure.

The exact fixed-base search is `code/bpz_t9_private_pairs.py`.

## Main-set private-swap component

A private one-for-one swap replaces an owner `r in I` by an outside point `q` whose closed neighbourhood meets `I` exactly in `{r}`. Exhausting this move graph from the published BPZ `I0` gives **243 distinct 367-point independent sets**.

An earlier depth-limited diagnostic reported 235; that number was not the full component and must not be reused.

Across the complete 243-state component:

- 11 states have at least nine distinct private owners;
- there are 20 eligible nine-pair subsets;
- all `20 * 2^9 = 10240` complementary orientations were checked;
- 640 orientations have both transversals individually independent;
- these reduce to **160 distinct obstruction masks** `D = N(PH) intersect N(PV)`.

No orientation is compatible with the published auxiliary `X`.

The complete joint-component search is `code/bpz_t9_joint_components.py`.

## Best exact near miss

One strongest witness is reached from `I0` by

- `6110 -> 3716`;
- `13677 -> 14027`.

Its nine private pairs are

```text
(1553,15910)
(3716,6110)
(8888,6494)
(10708,13158)
(13065,13358)
(14027,13677)
(14329,12277)
(15075,14733)
(15384,15685)
```

with orientation

```text
0 0 1 1 0 1 1 0 0
```

and transversals

```text
PH = 1553 3716 6494 13158 13065 13677 12277 15075 15384
PV = 15910 6110 8888 10708 13358 14027 14329 14733 15685
```

For this witness, `|D|=1098` and the published BPZ `X` meets `D` in exactly one point, `10665`.

## Obstruction census

Over all 160 distinct obstruction masks:

- minimum `|D|` is **1098**;
- maximum `|D|` is 1128;
- exactly 20 masks have size 1098;
- minimum number of hits by the published BPZ `X` is **1**;
- exactly 20 masks have one published-X hit.

Size histogram:

```text
1098 : 20
1102 : 20
1104 : 10
1110 : 20
1116 : 10
1118 : 40
1124 : 20
1128 : 20
```

Published-X hit histogram:

```text
1 : 20
2 : 30
4 : 30
5 : 60
6 : 10
8 : 10
```

Thus the chosen 1098/one-hit witness is simultaneously optimal within this complete component under both the obstruction-size and published-X-hit criteria.

## Closed local auxiliary repairs

For the one-hit near misses, the following exact searches found no repair:

- all one-for-one auxiliary replacements;
- the complete one-point private-swap component of the auxiliary set;
- simultaneous two-for-two bridges from the published auxiliary set;
- closure under exact one-for-one and simultaneous two-for-two moves: the auxiliary component remains exactly **243 states**, with `17550` two-swap addition pairs tested and `two_swap_new_states=0`;
- all three-for-three repairs of the displayed best witness that must remove `10665`: all `66795` owner triples were checked, and every eligible addition pool has size at most 2, so three additions cannot be made.

The corresponding reusable code includes `bpz_t9_x_repair.py`, `bpz_t9_x_two_swap_bridge.py`, `bpz_t9_x12_closure.py`, and `bpz_t9_x_repair3.py`.

## Closed automorphism probes

For the same 160 obstruction family:

- all `7^5 = 16807` relative translations of the published BPZ `X` were checked; only the identity reaches minimum hit count 1, while every nonidentity translation has at least 10 hits;
- all `5! * 2^5 = 3840` zero-translation signed coordinate permutations were checked for both BPZ `X` and BPZ `I0` as auxiliary seeds; none avoids an obstruction, and the original BPZ `X` identity remains the unique one-hit case in that scan.

These results make simple relative automorphisms of the published BPZ seeds a low-priority direction.

## Simultaneous main-set two-swap bridge from I0

Against the published `I0`, there are 8 support-1 and 254 support-2 outside candidates relevant to a two-for-two bridge. Exhausting the owner pools finds no valid simultaneous two-swap state outside the 243-state one-swap component. Thus a single simultaneous two-for-two move from `I0` does not escape the known component.

## What remains open

The local BPZ exchange geometry is now tightly constrained, but this does **not** rule out `t=9` in general. The most important open question is global:

> For one of the 160 obstruction masks `D`, does `C7^5 \ D` contain an independent set of size 367?

This is being attacked directly with exact cube-cover cardinality models, compact radius-repair models, public 367-set seed/translation scans, and unrestricted augmentation search. A SAT answer for any obstruction immediately gives a `134770`-point `C7^10` construction.

Independently, a 368-point independent set in `C7^5` would square to `135424` points in `C7^10`; global exact searches for 368 are also active. No completed job in this note establishes either result yet.
