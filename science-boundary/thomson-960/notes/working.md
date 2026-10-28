# Working notes — Thomson N=960

Current live merged Few Shots record: `444368.3924061973` (`Ronnie2025/c3-replica-exchange-scars`), epsilon `1e-6`; next valid score <= `444368.3924051973`. Latest upstream check still shows no open p007 PR. Re-check before any claim.

## Decisions

- Work from the live C3 record, not the original Amore–Wales/T baseline.
- Same-topology local exploration around the record is now substantially saturated: exact-C3 smooth moves, ±1 size oscillation, full-space soft modes, two/three-hop low-mode basin exploration, low-mode combinations, and simple same-topology spatial crossover all collapse into a small low-energy network.
- Simple 20-dislocation D2 × 24-dislocation spatial crossover is seam-dominated; continuous D2→C3 morph shows a sharp endpoint basin switch and a much higher 25-dislocation transition-region minimum.
- Targeted local Delaunay deletion can construct a genuine 22-dislocation start, but full relaxation regenerates the missing defects and returns the 24-dislocation record. Local scar surgery is not enough; stable topology change needs global reorganization.
- Local relaxation should use a termwise pair-energy-difference objective accumulated in long double, not the raw ~`4.4e5` absolute energy, so L-BFGS can resolve scientifically relevant `1e-8`–`1e-3` changes.

## Established low-energy basin graph

Let R be the live record.

- `R`: verifier `444368.3924061973`; C3; 36 five / 900 six / 24 seven (24 dislocations).
- `A`: symmetry-broken same-topology neighbor near `444368.395686226`, `R + ~0.003280029`. Durable `data/neighbor-soft-003280.json`; structure 36/900/24; z-C3 match RMS ~`5.68e-3`.
- `B`: symmetry-broken same-topology node near `444368.402972861`, `R + ~0.010566664`; structure 36/900/24.
- `C`: C3-symmetric low node `444368.4114178827`, `R + 0.0190116854`; 36/900/24. It first appeared in the original C3 smooth campaign and is now reproducibly reached by composing all three C3-equivalent nonlinear R→A shear events sequentially. Thus C has a structural interpretation as a three-event closed global-shear/scar-rearrangement state, not a random isolated minimum.

Independent mechanisms repeatedly show `R <-> A <-> B`, some direct `R <-> B`, and nonlinear composed-shear routes from R into C. Bare corresponding-point geodesic barriers are ~0.0367 (R→A), ~0.0379 (A→B), ~0.0739 (R→B), consistent with A being a genuine intermediate basin.

## Completed experiments

1. Live-record diagnostic: z is the C3 axis to ~`2e-9` RMS after 120° rotation; rationalization residual tangent gradient is tiny.
2. 40 exact-C3 coherent smooth deformations: no lower minimum.
3. Direct one-cycle size oscillation: `960→959→960` and `960→961→960` both return R to ~`1e-8`; size-up independently found A.
4. Record full-space physical tangent Hessian: lowest modes `4.82417658, 4.82417750, 4.88882190, 5.88540229, 5.88540341, 6.28297677, ...`; multiple C3-breaking doublets; Hessian symmetry relative defect `1.94e-8`.
5. Record soft-mode scans: softest 0/1 doublet robustly reaches A; deeper doublets repeatedly reach A, B and a `+0.029215` family; no improvement. Canonical and deeper Actions scans completed and workflows removed.
6. A Hessian lowest modes ~`2.80383834, 4.02949457, 4.57411004, 5.05622790, 5.67154221, 6.06109536, ...`.
7. A second-hop Actions scan (modes 0..7 × ±, run `40624586144`) produced **16/16 result-only artifacts <0.9 KB**, hence no floating candidate better than R by the `2e-7` save threshold. Workflow removed. Directions only return R/A/B, `+0.029215`, or high minima.
8. B stable energy ~`444368.40297286137`; Hessian lowest modes ~`1.42143383, 2.73430561, 3.59487562, 4.06473996, 5.15833004, ...`. Single modes and random combinations of first eight modes only return R/A/B; larger mixed-mode starts also collapse into A/B.
9. Same-topology cut-and-splice: R×A and R×B clean children return R/A; stronger R×B screen over 160 random cuts found 59 collision-safe children; five lowest raw-energy starts all 5/5 converged to A. Summary `results/basin-graph-same-topology-summary.txt`.
10. Cross-topology D2(20) × record/A(24) spherical cut-and-splice, run `40626019263`: ICP mismatch ~0.042; almost all children fail seam-distance safety; rare safe child relaxed to `R+1.498`. No candidate. Summary `results/cross-topology-summary.txt`; workflow removed.
11. Continuous D2→C3 ICP+Hungarian spherical morph, run `40626089044`, two independent ICP seeds: `t<=0.4 -> R`, `t>=0.6 -> D2`, `t=0.5 -> high transition-region minima`. No simple low 22-dislocation intermediate. Workflow removed.
12. The reproducibly harvested seed5011 t=0.5 transition node is `444370.530553633405 = R+2.138147436`, coordination **37/898/25 = 25 dislocations**, not 22/24/20. Durable summary `results/topology-midpoint-summary.txt`. This means the continuous 24→20 topology transition first *creates* an extra dislocation in this basin rather than monotonically removing them.
13. Targeted record Delaunay edge flips: single, double and C3-triple defect-reducing flips all heal to R. A stronger double-flip start was genuinely 34/904/22 before relaxation, but regenerated defects and returned R.
14. Stable-objective numerical fix: repolishing A changes it only ~`1.1e-8`, confirming A is real.
15. Nonlinear composed-shear run `40627802546`: first completed job `sequential 0,1,2` sends every tested scale 0.55,0.75,0.95,1.15,1.35 to **C = 444368.4114178827**, 36/900/24. This confirms C is the basin associated with completing all three C3-equivalent R→A global shear events in sequence.

## Active compute / current frontier

- **25-dislocation transition-node exits**: run `40627982217`, modes 0..3 × ±, bounded amplitudes. At latest check mode0/- is actively computing; others queued. Purpose: see whether the high 25-dislocation node has distinct annihilation exits into alternative 24/23/22/20-dislocation minima.
- **Nonlinear C3-equivalent shear composition**: run `40627802546`; six simultaneous/sequential event combinations. `seq012` completed -> C at all scales; five combinations remain queued/active.
- **C3 symmetry-preserving crossover**: run `40628147767`, two jobs. Reproduces distinct C3 parents (low C ~R+0.0190 and farther ~R+0.1721) and combines them with R using C3-invariant wavy cut-and-splice over whole C3 orbits; 60 screened children, relax top six. This explicitly combines the GA mechanism that broke D2 with the C3 orbit-space family that holds the current record.
- **Multi-step neighboring-N beam**: run `40628365874`. Routes down/up with depth 2 and 3. Each intermediate N branches top removals / Voronoi insertions, fully relaxes, energy-deduplicates, and keeps a two-state beam. This tests two/three accumulated size-induced defect rearrangements, materially stronger than the completed single-cycle ±1 search. `up2` is actively computing at latest check.
- `code/string_record_neighbor.py` is ready for a spherical string/climbing-image R↔A saddle calculation once current queue pressure drops. Goal: locate the actual low R-A saddle and probe transverse exits rather than random kicks.

## Immediate next

1. Collect transition-node modes, composed shears, C3 crossover and multi-step size beam. Any artifact containing `best_points` triggers immediate stable repolish → rationalization → official verifier.
2. If the 25-dislocation node exits only to R/D2/high families, retire it and do not spend more on high transition minima.
3. If composed shears/crossover produce new low C3 nodes, freeze them and add them to the basin graph before deciding whether to recurse.
4. If multi-step size beam finds a genuinely new low N=960 basin, analyze topology and recurse; if it collapses to R/A/B/C, record neighboring-size propagation as locally saturated to depth 3.
5. Otherwise launch the explicit R↔A spherical string / climbing-image route and use transverse saddle modes to search exits that linear minimum-mode kicks cannot reach.
6. Before any claim/submission: re-check Few Shots main/open p007 PRs, rationalize, run official verifier and `tools/check.py`, then submit only a verified >=`1e-6` improvement.
