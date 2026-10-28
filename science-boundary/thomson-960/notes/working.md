# Working notes — Thomson N=960

Current live merged Few Shots record: `444368.3924061973` (`Ronnie2025/c3-replica-exchange-scars`), epsilon `1e-6`; next valid score <= `444368.3924051973`. Latest upstream check still shows no open p007 PR. Re-check before any claim.

## Decisions

- Work from the live C3 record, not the original Amore–Wales/T baseline.
- Upstream C3 replica exchange and D2 genetic search show that coherent global scar rearrangements matter more than local defect surgery.
- Same-topology local basin exploration is now fairly saturated around the current record: exact-C3 smooth moves, ±1 size oscillation, individual full-space soft modes, low-mode combinations, and simple same-topology cut/splice all collapse into a tiny three-node low-energy network.
- Current pivot: **cross defect topology** between the merged 20-dislocation D2 family and 24-dislocation C3 / symmetry-broken families, using screened cut-and-splice plus a continuous ICP+Hungarian geodesic morph.
- Local relaxation should minimize a termwise pair-energy difference relative to its start (long-double accumulation), not the raw ~`4.4e5` absolute energy; otherwise L-BFGS `ftol`/line-search loses resolution around `1e-8` changes.

## Established low-energy basin graph

Let R be the live record.

- `R`: `444368.3924061973` verifier score; C3, 36 five / 900 six / 24 seven (24 dislocations).
- `A`: symmetry-broken same-topology neighbor near `444368.395686226` after stable polishing, `R + ~0.003280029`. Durable coordinates: `data/neighbor-soft-003280.json` (harvest artifact before stable repolish is `444368.395686237141`). Structure: 36/900/24; z-C3 matching RMS ~`5.68e-3`.
- `B`: second symmetry-broken same-topology node near `444368.402972861`, `R + ~0.010566664`. Local coordinates currently in scratch; structure also 36/900/24; z-C3 matching RMS ~`5.39e-3`.

Repeated independent mechanisms show edges `R <-> A <-> B` and some direct `R <-> B` returns. No lower node has appeared from this local network.

## Completed experiments

1. Live-record diagnostic: z is the exact C3 axis to ~`2e-9` nearest-neighbor RMS after a 120° rotation; rationalization residual tangent gradient is ~`5e-6` RMS.
2. 40 exact-C3 smooth global-deformation starts (4 seeds × 10): no lower minimum. Small/moderate perturbations overwhelmingly return to R; large ones land higher.
3. External neighboring-N CCD fetch attempt: guessed neighboring point-file URLs are not uniformly present; infrastructure failure only, not a scientific result.
4. Direct oscillating-size search:
   - `960→959→960`: best `444368.392406207859` (~`1.07e-8` above R).
   - `960→961→960`: best `444368.392406216473` (~`1.93e-8` above R); also independently found A.
5. Record full-space Hessian:
   - physical tangent coordinates, rigid rotations lifted; Hessian symmetry relative defect `1.94e-8`.
   - lowest modes `4.82417658, 4.82417750, 4.88882190, 5.88540229, 5.88540341, 6.28297677, ...` with multiple C3-breaking doublets.
6. Record soft-mode scans:
   - softest 0/1 doublet robustly exits to A at ~`0.008–0.010 rad` RMS over many phases.
   - 3/4 and deeper doublets repeatedly find A, B, and a `+0.029215` family; no improvement.
7. A was reproducibly harvested and persisted. Full-space Hessian of A (local independent computation): lowest internal modes approximately `2.80383834, 4.02949457, 4.57411004, 5.05622790, 5.67154221, 6.06109536, ...`; no doublet degeneracy, consistent with broken C3.
8. Second-hop A soft-mode search:
   - mode 0/+ and mode 1/-/mode 2- directions can return to R at suitable amplitudes.
   - mode 1/2 also repeatedly go to B.
   - Actions run `40624586144` is independently checking modes 0..7 × both signs; first 9 completed artifacts (through part of mode 4) are all tiny result-only artifacts, hence no candidate better than R by `2e-7`.
9. B harvested locally from A mode 2/- at `0.012 rad`: stable energy `444368.40297286137`. B Hessian lowest modes approximately `1.42143383, 2.73430561, 3.59487562, 4.06473996, 5.15833004, ...`, substantially softer than A or R.
10. Third-hop local scans from B:
    - mode 0/+ returns A; modes 1/2 toggle A/B; mode 3/+ at `0.018–0.024 rad` returns R; no fourth low node.
    - six screened random combinations of B's first eight soft modes: 3 relaxed to A and 3 to B; no fourth node.
11. Same-topology global crossover:
    - R × A, 5 random equal-half splices: low-seam children return R or A; bad seams land >`R+0.36`.
    - R × B, 5 random equal-half splices: low-seam children return A; bad seams land >`R+0.40`.
    - stronger screen: 160 random R×B cut planes/split fractions; among 59 collision-safe children, relax the five lowest raw-energy starts (`444368.8997` to `444368.9562`): **5/5 all converge to A**. This move family is strongly basin-dominated by A and is now a dead end unless the topology of one parent changes.
12. Numerical-method fix committed in `code/search_from_seed_modes.py`: stable termwise difference objective. Local stable repolish only lowers A by ~`1.1e-8`, so A is a real basin, not an underconverged artifact.

## Active compute

- Neighbor second-hop modes 0..7 × ±: Actions run `40624586144`; 9/16 artifacts complete at latest check, all non-candidates.
- Canonical record soft-pair phase scan: run `40623968469` (lower priority; no known candidate).
- Deeper record doublets 7/8 and 10/11: run `40623877455` (lower priority; no known candidate).
- **Cross-topology screened crossover**: run `40626019263`, matrix over parent A = live record / symmetry-broken A and two random seeds; D2 merged shot supplies the 20-dislocation parent.
- **Continuous D2→C3 topology morph** workflow launched from commit `ece3fbf15963d8b035fae929b623194118da0587`; two independent ICP seeds, Hungarian one-to-one correspondence, geodesic t-grid `0.12..0.88`, full stable relaxation.

## Immediate next

1. Watch cross-topology crossover and topology-morph artifacts first; any large artifact containing `best_points` gets immediate official-verifier treatment.
2. Finish second-hop A modes 5–7; summarize and retire the workflow if all fail.
3. If cross-topology routes yield new low nodes (especially 22-dislocation or alternative 20/24-dislocation configurations), freeze their coordinates, analyze topology, and recurse with Hessian/basin-graph search from those nodes.
4. If they only return known D2/C3/A/B families, next justified route is explicit transition-state / saddle-network search or a topology-changing dislocation-pair move, not more same-topology random kicks.
5. Before any claim: re-check Few Shots main and open p007 PRs, rationalize, run official verifier and `tools/check.py`, then submit only a verified improvement.
