# Moving-backbone correction: release and replace inherited constraints (2026-11-05)

## Why permanent locking is a limited representation

[Exact 66-third-optimum source-orbit compatibility](results/known_third_target_lock_geometry.json) finds that under nearest-Hamming A/B orientation, randomly locking 50% of B disagreement positions is compatible with a best-chosen symmetry of another known optimum with median probability **0.233% at N47** and **0.0206% at N50**. Locking all B disagreement sites excludes every listed third optimum, although unrestricted later local repair can undo the locks. This is a *known-target oracle obstruction*, not a negative result about unseen LABS optima.

Instead of simply increasing a protected B backbone to 100%, consider a **moving donor quota**: maintain only approximately half of D(A,B) positions locked to B, but repeatedly release energy-conflicting inherited sites and swap in alternatives. At each trial, repair the nonlocked coordinates under original LABS energy, then evaluate the offspring by identical unrestricted full repair. The lock identity changes, not merely the energy objective or fixed mask size.

## Frozen arms
On the identical 9 truly distinct elite source pairs / same source optima and budgets as [protected monotone path relinking](README.md), compare:
0. Single-elite short-radius ILS.
1. Monotone protected A→B relinking (previous arm 4).
2. Fixed half-D donor quota with protected repair but **no exchange**.
3. Half-D quota, greedy exact-E *lock release plus replacement* among six proposed exchanges.
4. Same half-D exchange geometry but **random exchange** control.
5. Same half-D exchange geometry selected by true exact parent lag-envelope score.
6. Same exchange rule with lag-label **shuffled envelope** placebo.
7. Equal-cardinality random virtual B donor (per seed) and exact-E exchange, testing second-parent spatial information.

One source-pair/rep/arm gets **400ms measured whole time**, including all candidate generation, exact E, protected Tabu, full steepest→64 tabu→steepest endpoint repair, and model/virtual donor creation. A donor site's B value is allowed to be undone (released); the current quota remains constant. The budget does not reuse target C identities. Report independently verified new source-novel <=5/10% offspring orbits, distinct source-canonical orbit IDs, final repaired E, throughput, source-pair bootstrap and time.

**Decision:** More successful raw states or lower average E without any increased **novel <=5/10%** yield is not evidence for AI4S. If release/replacement also stalls, stop modifying fixed quotas; test a qualitatively different basin-space transition rather than extending this family.

This mechanism draws on existing path-relinking/re-optimization concepts, not a claim of first discovery. Relevant comparison [Laguna et al. 2025 EJOR review](https://doi.org/10.1016/j.ejor.2025.02.022). Experimental outputs under `results/exchange_v1/`; no `labs-100/` edits.
