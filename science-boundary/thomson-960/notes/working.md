# Working notes — Thomson N=960

Current live merged Few Shots record: `444368.3924061973` (`Ronnie2025/c3-replica-exchange-scars`), epsilon `1e-6`; next valid score <= `444368.3924051973`. Latest upstream check still shows no open p007 PR. Re-check before any claim.

## Decisions

- Work from the live C3 record, not the original Amore–Wales/T baseline.
- Same-topology local exploration around the record is now substantially saturated: exact-C3 smooth moves, ±1 size oscillation, full-space soft modes, two/three-hop low-mode basin exploration, low-mode combinations, and simple same-topology spatial crossover all collapse into a tiny three-node low-energy network.
- Simple 20-dislocation D2 × 24-dislocation spatial crossover is seam-dominated; continuous D2→C3 morph instead shows a sharp basin switch with only high transition-region minima near t=0.5.
- Targeted local Delaunay deletion can construct a genuine 22-dislocation start, but full relaxation regenerates the missing defects and returns the 24-dislocation record. Local scar surgery is therefore not enough; a stable lower-topology state would require global reorganization.
- Local relaxation should use a termwise pair-energy-difference objective accumulated in long double, not the raw ~`4.4e5` absolute energy, so L-BFGS can resolve scientifically relevant `1e-8`–`1e-3` changes.

## Established low-energy basin graph

Let R be the live record.

- `R`: verifier `444368.3924061973`; C3; 36 five / 900 six / 24 seven (24 dislocations).
- `A`: symmetry-broken same-topology neighbor near `444368.395686226` after stable polishing, `R + ~0.003280029`. Durable coordinates: `data/neighbor-soft-003280.json`. Structure 36/900/24; z-C3 match RMS ~`5.68e-3`.
- `B`: second symmetry-broken same-topology node near `444368.402972861`, `R + ~0.010566664`. Structure 36/900/24; z-C3 match RMS ~`5.39e-3`.

Independent mechanisms repeatedly show edges `R <-> A <-> B` plus some direct `R <-> B` returns. Bare corresponding-point geodesic barriers are ~0.0367 (R→A), ~0.0379 (A→B), ~0.0739 (R→B), consistent with A being a genuine intermediate basin.

## Completed experiments

1. Live-record diagnostic: z is the C3 axis to ~`2e-9` RMS after 120° rotation; rationalization residual tangent gradient is tiny.
2. 40 exact-C3 coherent smooth deformations: no lower minimum.
3. Direct size oscillation: `960→959→960` and `960→961→960` both return the record to ~`1e-8`; the size-up route independently found A.
4. Record full-space physical tangent Hessian: lowest modes `4.82417658, 4.82417750, 4.88882190, 5.88540229, 5.88540341, 6.28297677, ...`; multiple C3-breaking doublets; Hessian symmetry relative defect `1.94e-8`.
5. Record soft-mode scans: softest 0/1 doublet robustly reaches A; deeper doublets repeatedly reach A, B and a `+0.029215` family; no improvement. Canonical and deeper Actions scans are complete and their workflows were removed.
6. A full-space Hessian lowest modes ~`2.80383834, 4.02949457, 4.57411004, 5.05622790, 5.67154221, 6.06109536, ...`.
7. A second-hop Actions scan (modes 0..7 × ±, run `40624586144`) produced **16/16 result-only artifacts <0.9 KB**, hence no floating candidate better than R by the `2e-7` save threshold. The workflow was removed. Individual directions only return R/A/B, the `+0.029215` family, or much higher minima.
8. B stable energy ~`444368.40297286137`; Hessian lowest modes ~`1.42143383, 2.73430561, 3.59487562, 4.06473996, 5.15833004, ...`. Single modes and random combinations of the first eight modes only return R/A/B; larger mixed-mode starts also collapse into A/B.
9. Same-topology cut-and-splice: R×A and R×B clean children return R/A; a stronger R×B screen over 160 random cut planes found 59 collision-safe children, and the five lowest raw-energy starts all 5/5 converged to A. Durable summary: `results/basin-graph-same-topology-summary.txt`.
10. Cross-topology D2(20) × record/A(24) spherical cut-and-splice, run `40626019263`: ICP mismatch ~0.042; almost all 72-sample children fail seam-distance safety; rare safe child relaxed to `R+1.498`. No candidate. Durable summary: `results/cross-topology-summary.txt`; workflow removed.
11. Continuous D2→C3 ICP+Hungarian spherical morph, run `40626089044`, two independent ICP seeds:
    - `t<=0.4` -> R (36/900/24);
    - `t>=0.6` -> D2 (32/908/20);
    - `t=0.5` -> independent high transition-region basins at `R+2.138` and `R+2.634`.
   Thus there is no simple stable low-energy 22-dislocation intermediate along these correspondences. Workflow removed.
12. Targeted record Delaunay edge flips: single, double, and C3-triple defect-reducing flips all heal back to R. A stronger double-flip start was genuinely 34 five / 904 six / 22 seven before relaxation, but regenerated the missing defects and returned R.
13. Numerical-method fix: stable termwise-difference objective. Repolishing A changes it by only ~`1.1e-8`, confirming A is a real basin rather than optimizer underconvergence.

## Active compute / current frontier

- **Topology-morph midpoint harvest**: run `40627218698` is actively reproducing seed5011, t=0.5 and will always save coordinates + Delaunay coordination counts. If this high basin has a mixed/22-dislocation topology, use it as a transition-node for Hessian/downhill search; otherwise record it as a generic high transition minimum.
- **Nonlinear C3-equivalent shear composition**: run `40627802546`, six jobs queued. Code `search_composed_shears.py` takes the full nonlinear R→A sphere-log displacement field, generates its two C3-equivalent copies, and applies them simultaneously or sequentially with exact sphere parallel transport. This tests accumulation of two/three global scar-shear events, not linear Hessian kicks.
- Local preliminary composed-shear test: a two-event simultaneous field at one moderate scale relaxed to B; a symmetric three-event sum at a smaller scale returned R. Full reproducible grid is delegated to run `40627802546`.

## Immediate next

1. Inspect midpoint topology as soon as run `40627218698` completes. If non-20/24 topology, freeze it durably, compute full tangent Hessian, and descend its lowest modes in both directions.
2. Collect composed-shear run `40627802546`. Any large artifact with `best_points` triggers immediate exact-certificate pipeline; otherwise map which sequences return R/A/B vs new nodes.
3. If both routes fail to create a new low node, pivot to an explicit transition-state / dimer / eigenvector-following saddle network seeded by the R↔A and A↔B barrier directions. Do not spend more compute on ordinary random kicks, same-topology half-space splices, or local defect deletion.
4. Before any claim/submission: re-check Few Shots main/open p007 PRs, rationalize, run the official verifier and `tools/check.py`, then submit only a verified >=`1e-6` improvement.
