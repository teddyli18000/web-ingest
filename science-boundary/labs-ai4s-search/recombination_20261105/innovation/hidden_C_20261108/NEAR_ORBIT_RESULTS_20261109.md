# Full-event near-frontier orbit audit — exact verified 2026-11-09

## Scope, source fingerprints and why E-only summaries are insufficient

[Predeclared endpoint specification](NEAR_ORBIT_AUDIT.md), [independent exact bitcount scorer](audit_near_orbits.py), resulting [N46](results/near_orbit_N46/near_orbit_audit.json), [N47](results/near_orbit_N47/near_orbit_audit.json), and [N50](results/near_orbit_N50/near_orbit_audit.json) are the complete, successfully executed, costed-history audits. All three Actions matrix jobs passed. The full repair search and first C check had already finished; this additional audit does **not** tune the policies, does **not** pass archived target C to them, and independently verifies every retained near-frontier sequence with integer LABS E and all eight exact symmetry transformations.

**Known-source registry** (entire frozen `combined10.tsv`, not just A/B) has N46:3, N47:6, N50:4 distinct symmetry orbits (N50 includes 3 optima E153 plus an E161 near-optimum; E161 is intentionally excluded when designating an *optimum*, but included when excluding `new` rediscoveries). Thresholds were fixed before looking at audit: `E <= floor(1.05 E*)`, `E <= floor(1.10 E*)`, and an additional parent-independent geometry screen symmetry-aware Hamming distance to **each** given parent of at least `ceil(N/5)=10` spins. No near-frontier symmetry orbit is automatically a distinct attraction basin.

## Primary result: no archive-new near-5% orbit

**At N46, N47 and N50, in A/B-blind and C-shell, in all six candidate policies, and for single-incumbent / alternating original X and N50 always-X, the number of entirely corpus-new ≤5% near-optimal eightfold orbits is ZERO.** There are no front-line new solution structures in these experiments.

Some `near5` hits are known archive optima not equal to provided A/B, i.e. **hidden C recovered**, not discovery of a new near-best symmetry orbit.

## What survives at near10: counts of A/B-blind source-new success *states*

For each length, each arm tests 72 matched A/B-blind initial damaged states; a state is successful if its archived actual repair trajectory includes any ≤10% source-registry-new orbit after the initial direct repair. Repeated hits of the same canonical orbit are **not** counted as separate new orbit identities.

| N | State management | A-only | Real B | Fake B | learned joint + history | learned cheap history | single-source ILS |
|---|---|---:|---:|---:|---:|---:|---:|
| 46 | one incumbent | 1 | 1 | 2 | 1 | 1 | **9** |
| 46 | alternating X | 1 | 4 | 3 | 2 | 2 | **11** |
| 47 | one incumbent | 0 | 0 | 0 | 0 | 0 | **4** |
| 47 | alternating X | **4** | 2 | 1 | 1 | 1 | 2 |
| 50 | one incumbent | 1 | 0 | 1 | 0 | 0 | 1 |
| 50 | alternating X | 0 | 0 | 0 | 1 | 1 | 1 |
| 50 | **always-X classic** | 1 | 1 | **4** | 1 | 1 | 1 |

These are rare events from just 3 or 6 shared C-orbit lineages and do **not** establish significant learned cross-length performance. Most events correspond to 1–3 unique global new symmetry orbits per arm even when there are more successful context seeds. E.g. N50 always-X fake B 4 successful states across only **2 unique** corpus-new ≤10% orbits.

The equal-cost fixed-X N50 C-shell repair recovery was more reliable than alternating-X, but **X is privileged C-conditioned in C-shell**. This cannot be interpreted as genuine A/B-compositional C discovery.

**Scientific decision:** current results support the very general *do not discard structurally informative search anchors* heuristic, not neural dual-parent encoding or use of real B as a necessary donor. High-quality source-new generation (≤5%) has not succeeded. To justify a learned action policy, first demonstrate source-new quality gain over classical repeated-X restarts and full modern LABS strong solvers, on genuinely unseen optimum-orbit populations—not simply reduced postrepair E or memorized historical C. Prospective strict N50 target-orbit status was consumed in the first test; all later N50 experiments are posthoc.

## Reproduction and data provenance

Source and models: [readme](README.md), [frozen forced model](results/forced_models_v1/training_audit.json). Complete raw histories are preserved as lossless gzip with independent SHA256 for N46, N47 and N50; original source/orbit classes are available in the verified per-run `verdict.json`, while this reanalysis saves archive-event SHA256. Labels are computed only after searches, not features. No changes to independent `science-boundary/labs-100/`.
