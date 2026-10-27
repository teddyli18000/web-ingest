# 2026-10-27 unrestricted priority-queue probe

## Motivation

Pšeničnik, Mlinarič, Brest and Bošković's dual-step LABS method (arXiv:2409.07222; published in Digital Signal Processing in 2025) uses a second unrestricted stage guided by a min-priority queue. Each lowest-energy pivot contributes its unexplored one-bit neighbors, and bounded left/right cyclic rotations of those neighbors are also inserted so the search can reach regions inaccessible to ordinary local bit flips.

This experiment asks whether that basin-jumping mechanism can escape either of the two unusually deep length-100 basins already identified here.

## Implementation

`code/priority_queue.cpp` independently implements the described mechanism for N=100:

- minimum-energy priority queue;
- exact one-bit neighbor energies from a freshly recomputed pivot correlation vector;
- global visited hash set;
- left/right cyclic rotations by 1 through `Tr` positions for each neighbor;
- `u` counts pivot expansions since the last global best improvement and stops at `Tu`;
- deterministic insertion-order tie breaking.

The paper describes `Tu` and `Tr` as controls but the exact values used for its large-length campaigns were not established from the accessible text during this experiment. Therefore the runs below are **mechanism probes with locally chosen parameters**, not claims of exact reproduction.

## Incumbent seed

Seed: public N=100 incumbent, exact energy 578.

Parameters:

```text
Tu = 5000
Tr = 3
max_seen = 5,000,000
```

Result:

```text
initial=578
best=578
popped=5000
seen=2,166,357
queued=2,161,357
seconds=4.84
```

No energy below 578 was found among approximately 2.17 million distinct visited states.

As a small structural sanity check, rotating the incumbent left by one position also has energy 578, but it is one of the standard eight LABS symmetry images of the incumbent, so it is not a distinct record basin.

## N=99-transfer seed

Seed: best direct N=99->100 transfer from the 2025 unrestricted N=99 record, exact energy 606.

Same parameters:

```text
Tu = 5000
Tr = 3
max_seen = 5,000,000
```

Result:

```text
initial=606
best=606
popped=5000
seen=2,470,113
queued=2,465,113
seconds=5.87
```

No energy below 606 was found among approximately 2.47 million distinct visited states.

## Interpretation

The cyclic-rotation priority-queue mechanism is materially broader than a simple one-bit descent and visits millions of states quickly at N=100, but these two seeds remain stable under this initial probe. Together with their exact local Hamming exclusions, this reinforces the picture of very deep basins.

This result does **not** rule out the published dual-step method: the original algorithm is seeded by first-stage candidates from restricted/skew searches (or constructions), is run in many independent instances, and may use different `Tu`/`Tr` tuning. A next use of this code should therefore focus on generating diverse high-quality seeds rather than simply increasing `Tu` from the same incumbent.

## Source

- Blaž Pšeničnik, Rene Mlinarič, Janez Brest, Borko Bošković, *Dual-Step Optimization for Binary Sequences with High Merit Factors*, arXiv:2409.07222; Digital Signal Processing 165 (2025), 105316: <https://arxiv.org/abs/2409.07222>
