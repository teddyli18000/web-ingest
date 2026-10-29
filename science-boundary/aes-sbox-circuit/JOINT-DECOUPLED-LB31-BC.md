# Joint-decoupled LB31 B/C local exact exclusion

Date: 2026-10-29 (+08:00)

## Scope

This note records a local exact follow-up to the retained-18-core joint-decoupled product-plane search. It covers the two non-A LB=31 exact semilinear orbit representatives

- B: `P(x)=0x9d*x^8` (`c=0x9d,k=3`)
- C: `P(x)=0x5b*x^8` (`c=0x5b,k=3`)

The live A representative `(0x01,0)` was already excluded by `prove_joint_decoupled_frontier.cpp`. The generic frontier code in `screen_joint_decoupled_instance.cpp` and the transported instances emitted by `emit_joint_decoupled_instance.py` were reproduced locally; final score-35/36 checks used the same exact target-closure and at-most-two-helper logic as the A proof, generalized to the transported plane/output/correction masks.

This is a local exact result. The separately launched GitHub Actions B/C frontier jobs may still be queued; do not describe those jobs as independent verification until their actual outputs are read.

## Frontier regression

Local generic frontier counts:

```text
A/live: pass0=464931, helper frontier=9761
        score 35: 136, score 36: 9625

B:      pass0=416777, helper frontier=2635
        score 35: 34,  score 36: 2601
        middle support 3:724, 4:1911
        distance 0:1960, 1:631, 2:44

C:      pass0=424050, helper frontier=3004
        score 35: 68,  score 36: 2936
        middle support 3:1121, 4:1883
        distance 0:1997, 1:1007
```

The A counts reproduce the retained regression exactly.

## B final screen

Score-36 was split into four disjoint row shards. All shards had zero candidates and no rank-deficient or helper-budget gap:

```text
shard 0: systems=163, output_killed=648, target_killed=163, pre_killed=0, candidates=0
shard 1: systems= 85, output_killed=645, target_killed= 85, pre_killed=0, candidates=0
shard 2: systems=245, output_killed=645, target_killed=245, pre_killed=0, candidates=0
shard 3: systems=248, output_killed=642, target_killed=248, pre_killed=0, candidates=0
```

For score 35, exact correction enumeration left one target-count boundary case:

```text
front=final=4992
support=3
support mask=42
correction values=[243,209,21]
prelinear distinct non-input targets=18
exact output cost=15
remaining helper budget=0
```

Exact target-only closure fails for that prelinear target set. Therefore the single target-count survivor is not realizable in the 36-gate variable budget. B has no <=101 witness in this joint-decoupled family.

## C final screen

Score-36, again four disjoint shards:

```text
shard 0: systems=899, output_killed=715, target_killed=890, pre_killed= 9, candidates=0
shard 1: systems=816, output_killed=718, target_killed=767, pre_killed=49, candidates=0
shard 2: systems=653, output_killed=721, target_killed=607, pre_killed=46, candidates=0
shard 3: systems=814, output_killed=720, target_killed=789, pre_killed=25, candidates=0
```

No shard had a rank-deficient minimum-support system or an unresolved helper budget.

Score 35 left exactly nine target-count boundary cases. Every one has `front=final`, support 3, support mask 97, 17 prelinear non-input targets, exact output cost 16, and zero remaining helper budget. The IDs and correction triples are:

```text
15055 -> [ 81,4,196]
15046 -> [ 81,4,105]
15064 -> [ 81,4,  9]
 1933 -> [202,4,196]
 1924 -> [202,4,105]
 1942 -> [202,4,  9]
 8494 -> [172,4,196]
 8485 -> [172,4,105]
 8503 -> [172,4,  9]
```

Exact target-only closure fails for all nine. Thus C also has no <=101 witness in this joint-decoupled family.

## Consequence

Together with the existing exact A proof and the proved six-element semilinear orbit equivalences, the joint-decoupled front/final product-plane extension of all three LB=31 orbit representatives yields no 101-gate retained-core circuit.

This closes a broader family than the same-orientation semilinear searches: front norm-product orientations and final product/output orientations were allowed to differ independently.

## Reproduction notes

The local computation used 5 vCPUs / 5.8 GiB. Frontier enumeration was C++ `-O3 -std=c++20`. B/C frontier passes took tens of seconds. Final checks were sharded by frontier row modulo 4; each shard independently recomputed the transported frontier and then applied exact correction and linear-closure checks. Score-35 boundary cases were re-run separately to confirm the zero-helper closure failures.

Before promoting this note into the main status summary, read the queued B/C Action outputs if available and record whether they independently reproduce the frontier counts. A separate generic final-checker Action would be useful independent verification of the local exclusion.