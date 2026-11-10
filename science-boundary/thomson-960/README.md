# Thomson problem for 960 points

## Question

Can we find a 960-point configuration on the unit sphere with Coulomb energy low enough to beat the live Few Shots p007 record by at least `1e-6`?

## Current state

- Few Shots p007 accepted record, rechecked 2026-11-04: `R = 444368.3924061973` (Ronnie2025 C3); official absolute epsilon is `1e-6`, so a new accepted shot must reach at most `444368.3924051973`.
- The fixed-N R/A/B basin network and certified fixed-N R/A first-order saddle were mapped earlier. Enlarging those low-mode scans did not improve R.
- The shared weighted N961 hub exhibits occupancy-dependent projection and nontrivial path hysteresis. Three distinguishable labels, 886, 960 and 380, define a constant-total-charge simplex `q886+q960+q380=2`.
- **New verified mechanism (2026-11-04):** at the common center `q886=q960=q380=2/3`, A and H weighted minima are connected by a genuine index-one saddle: `Ew=444373.852382868179`, physical gradient RMS `7.7574e-6`, lowest Hessian eigenvalues `[-10.160271,+2.616926,+4.307680]`. Complex-step Hessian has symmetry error `9.08e-15` and tiny Ritz residuals; five perturbation amplitudes for both signs descend reproducibly to H/A. All resulting real N960 deletions return known A/B/H380 configurations, best `A=444368.3956862257`, still above R. See `results/n961-weighted-ah-index1-2026-11-04.txt` and Action `41332447336`.
- **Completed saddle-ray experiment (2026-11-04):** three charged-particle index-one branches successfully continued to s=0.78 (ray886) and s=0.90 (rays960/380); see `results/n961-weighted-saddle-occupancy-rays-2026-11-04.txt`, Action `41719943255`. Except for one failed root corrector at s=0.90 on ray886, checked Hessians retained exactly one negative internal mode. Projection basins exhibit nonmonotonic A/R/B returns: e.g. ray960 delete886 gives R only at s=0.48 before returning A. On ray380, delete380 at s=0.78 and 0.90 discovers a distinct, but much higher, real N960 minimum at energy ≈444368.616310059 (R+0.223904). Best projection remains R to numerical noise, not a new record. The original three jobs were red due solely to a JSON trailer bug in their final summary; computation and artifacts succeeded, and the trailer writer was fixed in commit `e2deae6`.
- **Six completed 2D saddle chord experiments:** Action `41857433482`, all 6 jobs green; each independently continued pair agreed on the same index-one weighted saddle at the tested common occupancies (energy differences <1.2e-7, labelled-rotation-aligned geometry RMS <3.2e-5). No new low-energy N960 exit. Durable evidence: `results/n961-saddle-chord-holonomy-2026-11-06.txt`. **These occupancy calculations are paused**, not extended to exclude more parameter regions.
- **Constructive N960 Hamiltonian scar-braid first campaign completed:** Action `42250842594`, 3 × 240 unconstrained quench attempts, independent R/A/B parents. No E<R-2e-7 yet, but new genuine minima (not duplicate R/A/B) were produced: best `444368.42162124 = R+0.02921504`, then `444368.4436940799`, `444368.47177837125` etc. Independent legacy SciPy stable-relaxation confirmed eight new basins and committed their full 960-point geometries in `data/scar-braid-elites-2202-2026-11-06.json` (capture run `42253037254`, success). Vortex, dipole and multi-braid operators found new minima; original randomcap control nearly always collided and was revised to contract the perturbation on the sphere before quench.
- **Independent topological evidence:** `results/scar-braid-novel-topology-2026-11-06.txt` classifies all eight stored novel minima. The best new E=444368.42162124 has the same 36/900/24 and nine 7-7 twin edges as R, but a different *global* arrangement; other E+0.05–0.08 parents have eight twin edges, and E+0.18–0.21 parents have 23 dislocations. Thus the newly constructed low-energy field is an actual alternative geometric/elastic arrangement, not merely a numerical duplicate or a scalar topology-count artefact.
- **Completed constructive campaigns (2026-11-06):** 720 R/A/B Hamiltonian scar flows, 640 R/A/B/D2 cross-topology flows, 900 inherited-elite flows, and 1200 R→W/A/B nonlinear global-field event recombinations: **3460 complete N960 minimizations** in successful Actions `42250842594`, `42251234401`, `42252806055`, `42254893792`; none found E<R-2e-7. Eight genuinely distinct, independently repolished N960 minima from the first campaign remain in `data/scar-braid-elites-2202-2026-11-06.json`. Best new basin W=444368.42162124=R+0.02921504. W's tangent-field cosine overlaps with R→A and R→B are only 0.0934 and 0.5705 respectively, but nonlinear **whole-sphere** compositions still return known basins. Full evidence: `results/constructive-scar-campaigns-and-mosaic-reset-2026-11-06.txt`.
- **C2 reduced-space replica-exchange finished:** Action `42252230952`, two independent 6-replica ×120-sweep runs, no C2 basin better than D2 `444368.4040805305`. The old code released only C2 minima below R+0.10 and therefore had **zero full-space releases**; do not confuse this with evidence about higher C2 saddles or minima.
- **Defect-core mosaic completed** (2026-11-06): Action `42257750496`, 3 independent seeds × 450 = **1,350 genuine N960 quench attempts**, all succeeded, no E<R-2e-7. Lowest labeled new basin E=444368.4344266608 = R+0.0420204635, above previously independently verified W=R+0.02921504. More spatially localized donor recombination produces distinct geometries but has not improved the best *new* candidate. Preserve logs/interpretation in `results/defect-mosaic-outcome-and-metric-homotopy-2026-11-06.txt`. Do not merely increase sample count in same genotype space.
- **Riesz energy-law and anisotropic metric loops completed (2026-11-07):** Actions `42258720979` and `42261470927`, all four jobs green. Riesz 2×140 full N960 cycles, best new basin `444368.4412242053 = R+0.048818008`, worse than W; no sub-R candidate. Anisotropic two-axis metric loops 2×115 cycles; nontrivial metric legs (102 each) were poor record generators: best `444368.992068273` / `444368.882227587`; isotropic controls performed better. Both force-checked. These are evidence *only for these tested parameterized mechanisms*. Primary durable result `results/riesz-metric-outcomes-c3-ga-reset-2026-11-07.txt`. The original 2026 C3 winner had already noted negative Riesz-s homotopy results.
- **Constructive C3 symmetry search** (2026-11-07/08): `code/search_c3_replica_genetic.py`, Action `42455369621` (3 seeds, 115 six-temperature C3 sweeps + 3 symmetry-preserving genetic children per sweep). This combines accepted C3 winning 320-orbit replica-exchange and previous D2 winning Deaven-Ho cut-and-splice mechanism; all subrecord 960 candidates preserve coordinates for official verifier. First run `42455291835` failed only because the diagnostic full-energy elite archive tried to copy a `None` coordinate; fixed commit `268245a`; rerun passed all 5-sweep smoke checks.
- **New cross-origin structural parent**: the C3-only genetic pool starts with the current R, limiting combinatorial variation until an independent C3 basin is found. The old Cambridge/Amore-Wales 2026 T-symmetric 960-point elite `E≈444368.4373479895` is a structurally independent 12-scar configuration sharing a C3 subgroup. `--t-file` was added to the same code (commit `8f35dea`) to fit its threefold symmetry axis, convert it into the 320-orbit C3 quotient, and seed both the elite population and two hotter replica slots. New Action `42455931301` runs 2 seeds × 145 C3 sweeps, 3 genetic children/sweep; it first checks the public CCD 960x3 coordinates and true T energy, then executes a 5-sweep smoke before the full search. This is a matched constructive test of whether *different elite scar arrangements* improve genetic child quality beyond C3 record-only parental drift.
- **New representation: exact C3 triplet birth/death through N957/N963** (2026-11-07/08): `code/search_c3_orbit_size_exchange.py` explores (N960→N957→N960) by deleting one 3-particle C3 orbit and re-inserting a different orbit, and reverse (N960→N963→N960) by adding an orbit then deleting another. Both intermediate sizes and final C3 N960 are fully relaxed; candidate N960 then breaks symmetry and relaxes physically. Unlike earlier ±1 particle bounces, this preserves C3 over the topological size excursion. Original pilot Action `42456406401` (2 seeds ×95 cycles) checked out a biased orbit-deletion ranking; all final N960 scores are still evaluated with the real objective. Code corrected in commit `00b17dd` to use the exact removed energy (3p_{mathrm{outside}}+3/d_{mathrm{orbit}}), with independent full-pair-sum identity checks. The authoritative corrected rerun is Action `42456551742` (2×80 cycles). Reference `results/c3-triplet-orbit-search-reset-2026-11-07.txt`.
- **Critical C3 genetic correctness repair** (2026-11-07/08): initial GA energy deduplication threshold `3e-6` could suppress candidates improved by just `1e-6`; fixed threshold `3e-8` on `main`. Crossovers originally needed three distinct C3 parents, so R+T alone could not trigger GA; corrected to two. Initial cohorts `42455369621` and `42455931301` checked out the older source. New Action `42456573446` (one seed, 75 sweeps, verified old-T parent) **asserts actual GA offspring appear during 3-sweep smoke** before launching its corrected search. This protects the purpose of cross-origin recombination from being silently bypassed.
- **2026-11-08 C3 experiments fully validated, no breakthrough:** C3-only 3×115 six-replica sweeps Action `42455369621` (57/41/41 unconstrained releases), R+T cross-origin 2×145 Action `42455931301` (83/101 releases), epsilon-safe immediate R×T genetic 75 sweeps Action `42456573446` (64 releases; 9 actual early genetic children in smoke), and C3 ±3-orbit cycles: original 2×95 Action `42456406401` (545 physical releases) and corrected exact orbit-removal 2×80 Action `42456551742` (446 releases). All 10 jobs green, 0 numerical subrecord candidates, incumbent R retained; all mechanisms generated higher minima, but the best independently verified new global W=R+0.02921504 remains unbeaten. Complete logs and control/operator scores: `results/c3-genetic-triplet-results-c2-topology-pivot-2026-11-08.txt`.
- **Completed cross-topology C2 experiment (2026-11-10):** Action `42500890656` both jobs green, independent 20-dislocation D2 (`444368.4040805305`) × 24-dislocation T (`444368.4373479895`) in a 480-orbit C2 genetic / six-temperature search. 2×85 sweeps, **229 unconstrained N960 releases** (103+126), no sub-R candidates. One new C2-constrained `444368.404283112` is only ~0.000202582 above D2 and returns to D2 upon physical release; lowest different full-N960 basin from this family `444368.453912138` (R+0.061506), worse than known W (R+0.029215). Do not expand same C2 GA; full numeric evidence in `results/c2-genetic-outcome-adaptive-basin-filling-2026-11-10.txt`.
- **New independent full-space adaptive basin-filling search (2026-11-10):** `code/search_alignment_basin_filling.py` / Action `42851511543` (2 seeds × 105 cycles). This explicitly **does not constrain symmetry or change physical pair law**. It temporarily penalizes repeated visits to already known *rotation-aligned positional basins* R/A/B/W using history-dependent differentiable Gaussian hills in the RMS chord distance after optimal Kabsch SO(3) registration; each candidate is then fully quenched in the original N960 Coulomb objective. Repulsive hill heights adapt when already sampled basins recur. Built-in analytic gradient finite-difference check, source energy checks and true direct-physical controls passed their smoke stage in both jobs. This tests a new search representation, not thermodynamic metadynamics free-energy estimation. New record claims require >=1e-6 official verifier improvement.
- No new record is claimed. Numerical fluctuations `~1e-10` around the accepted score are not breakthroughs.

## Why this may be a frontier

The accepted Few Shots record already improves the contemporary Cambridge Cluster Database value and is judged by an exact-integer verifier after rationalization. At N=960 the relevant energy gaps between very good minima are tiny, while the global defect arrangement changes through collective rearrangements rather than isolated local edits.

Recent public work by Amore and Wales (J. Chem. Phys. 165, 164104, 2026) shows that propagating low-energy structures across neighboring particle counts is productive at large N. Earlier Thomson transition-network work explicitly used DNEB plus hybrid eigenvector following to find rearrangement pathways. The project has now reproduced the value of both ideas: neighboring-size motion exposes a shared structural hub, while fixed-N transition-state searches explain the local R/A/B network. The unresolved question is whether the auxiliary N961 occupancy interface exposes a branch that the already-saturated fixed-N network does not.

## Established low-energy structure

### Record R and nearby same-topology minima

Durable summary: `results/basin-graph-same-topology-summary.txt`.

Repeatedly identified 24-dislocation minima include:

- `R = 444368.3924061973` — accepted record;
- `A ≈ 444368.3956862258` — `R + 0.0032800285`;
- `B ≈ 444368.4029728613` — `R + 0.0105666640`;
- `D ≈ 444368.4109930844` — another same-topology minimum encountered in higher-stationary-state work.

R/A/B are connected by many low-mode and nonlinear routes. Larger mixed-mode pushes and simple spatial crossovers collapse back into this network rather than reveal a fourth low basin.

### Certified fixed-N R/A transition state

Durable summary: `results/transition-network-ra-summary.txt`.

The optimized R/A first-order saddle has approximately:

- energy `444368.403948984458`;
- physical gradient RMS `6.31e-6`;
- exactly one negative internal mode;
- lowest eigenvalue `-5.865579689...`;
- reaction-side perturbations certified to relax to A on one side and R on the other.

Positive-mode transverse scans found R, A, B, and higher minima only. A later experiment parallel-transported the approximately orthogonal `e432/B -> A` incoming field to this certified saddle and scanned both signs; it again produced only R/A/B/e432/higher basins. See `results/two-saddle-transport-2026-10-30.txt`.

**Implication:** do not restart R/A DNEB or extend isolated saddle-mode numbers as if this interface were unexplored.

### Cross-topology 20 ↔ 24 dislocation work

Durable summaries: `results/cross-topology-summary.txt`, `results/topology-midpoint-summary.txt`.

- Direct D2/record spherical cut-and-splice is seam-collision dominated.
- Continuous ICP/Hungarian D2→record morphs show a sharp basin switch, not a low 22-dislocation branch.
- The morph midpoint relaxes to a much higher 25-dislocation minimum (`~444370.53055`).
- Forced local defect-reducing Delaunay flips heal back to R, including a stronger start that temporarily reached a 22-dislocation coordination count.

These results rule out the tested operators, not all cross-topology mechanisms.

### Higher stationary-state maps

Durable summary: `results/c-solution-landscape-summary.txt` and the B/D saddle result files.

A low C3-constrained state `C ≈ 444368.4114178831` is an index-2 full-space stationary state with a nearly degenerate negative doublet. Its direct unstable manifold was exhaustively sampled and drains into A/B/D. Several B/D and e432/B transition interfaces were also mapped. They expanded the transition network but did not expose a lower-than-R basin.

## N=961 shared-hub mechanism

Durable summaries:

- `results/live-size-bounce-scout-results-2026-10-31.txt`
- `results/A-R-neighbor-size-hub-2026-10-31.txt`
- `results/n961-hub-reformulation-2026-10-31.txt`
- `results/n961-occupancy-bifurcation-2026-10-31.txt`
- `results/n961-fractional-projection-boundary-2026-10-31.txt`
- `results/n961-fractional-boundary-modes-2026-10-31.txt`

### Shared hub

Starting from A, the rank-3 Voronoi insertion at triangle `(599,282,502)` and full N961 relaxation reaches the same N961 minimum independently encountered from the live-record neighboring-size search:

- `E961 ≈ 445303.24736958207`;
- coordination `35/903/23`.

At the unmodified hub:

- delete label 886 → R;
- delete label 960 → A.

Thus the hub is a genuine structural junction, not merely a reversible insertion bookkeeping artifact.

### Fractional occupancy and hysteresis

Let the distinguished particle charge vary continuously while all 961 coordinates remain mobile.

- Fading label886 returns R.
- Fading label960 from charge 1 to 0 also returns R, even though hard-deleting label960 at the original hub returns A.
- A two-label exchange `q886=t`, `q960=1-t` shows continuation-direction hysteresis: the same endpoint occupancy can retain a different N960 projection history.

This is stronger than an ordinary local soft-mode observation: an auxiliary occupancy coordinate changes which genuine N960 attraction basin the geometry enters without an obvious change in the coarse defect count.

### Projection boundary

On the A-derived label960 fade branch:

- `lambda >= 0.15` in the sampled schedule projects to A;
- `lambda <= 0.10` projects to R;
- all sampled projections retain coordination `36/900/24`.

The scientifically relevant object is therefore an intra-topology basin boundary in the enlarged occupancy × geometry representation, not simply a defect-count transition.

### Full weighted-mode result

Run `41197100187` evaluated low full weighted-N961 modes at `lambda=0.15`, `0.125`, and `0.10`, both signs and multiple amplitudes. Endpoints were only R/A/B; best sub-live numbers were `~1e-10` numerical noise.

The low modes visibly repeat the known A/R switch. Simply adding more full modes or amplitudes is not justified.

## Fixed-N cascade / scar-walk result

Durable summaries:

- `results/dynamic-scar-walk-follower-softening-2026-10-31.txt`
- `results/cascade-and-soft-crosssize-frontier-2026-10-31.txt`
- `results/cascade-aware-v2-summary-2026-10-31.txt`
- `results/A-centered-cascade-summary-2026-10-31.txt`
- `results/follower-order-and-mobile-crosssize-2026-10-31.txt`

A validated multi-glide R→A cascade demonstrated real remote follower softening. However, stronger cascade-aware beam searches and explicit A-centered dependent chains still returned known minima. In particular, some branches showed very strong remote softening (`cascade_effective > 2`) yet remained in A/B/R. Therefore “largest remote softening” is not sufficient as a candidate-quality ranking by itself; persistence under collective release matters separately.

Do not scale this same fixed-N scar-walk representation merely by widening the beam or permuting the same followers.

## Retired / saturated tested representations

These are negative results for the tested families, not global impossibility claims.

- 40 exact-C3 low-order smooth deformations from the record.
- Broad minimum-centered same-topology low-mode kicks and mixed low-mode combinations around R/A/B.
- Simple same-topology spatial crossover.
- Direct D2↔record cut-and-splice and continuous one-to-one morphs.
- Forced local defect deletion without accompanying global reorganization.
- Direct transverse enumeration around the certified fixed-N R/A saddle.
- Linear transport of the e432/B→A interface field to the R/A saddle.
- Fixed-N cascade-aware beam widening and tested A-centered follower permutations.
- Fixed-ghost and mobile N972 fractional-charge teacher continuations; both undergo finite-occupancy scar reorganization and finish well above R.
- Unmodified shared-N961-hub low-mode scan.
- Full weighted low-mode scan at the N961 fractional A/R projection boundary.

## Active experiments

### 1. Active-only transverse N961 modes

Code: `code/search_n961_active_transverse_modes.py`  
Run: `41197569521`

At the midpoint `lambda=0.125`, this representation:

1. excludes the fading label960 tangent degrees of freedom because that particle is deleted before the genuine N960 return;
2. Kabsch-aligns the `lambda=0.15` and `0.10` fractional states around the midpoint;
3. forms the active 960-particle physical log-map secant between those states;
4. projects out rigid rotations and this empirical A/R crossing direction;
5. diagonalizes the remaining active weighted-Hessian block and scans low transverse modes before full genuine-N960 relaxation.

This tests side exits of the occupancy-induced boundary rather than repeating motion through it.

### 2. Occupancy holonomy / closed loops

Code: `code/search_n961_occupancy_holonomy.py`  
Run: `41197844226`

Prior two-label exchange proves path dependence. The new experiment starts at the R-side fractional endpoint `(q886,q960)=(1,0)`, executes closed rectangular loops in the independent two-occupancy plane in both orientations and two scales, then returns to exactly the same endpoint occupancy.

At every corner and at loop closure, both distinguished deletion projections are fully repolished as ordinary unit-charge N960 configurations. A nontrivial loop can therefore reveal whether occupancy operations are noncommutative at the level of the relaxed geometry and whether the same endpoint can acquire a new genuine-N960 exit.

## Weighted A/H saddle and present experiment (2026-11-04)

The 11-image spherical string approached the A/H interface but had a physical-gradient RMS of about 0.0052. Eigenvector-following subsequently produced a fixed-parameter stationary index-one geometry at `444373.852382868179`. Independent complex-step Hessian validation counted exactly one non-rigid negative mode (the next eigenvalue is positive `+2.6169256817`). Each of five signed perturbations relaxed to the expected A- or H-sheet. Genuine N960 deletions from the relaxed sides yielded only A/A/H380 or B/B/H380. This is a verified *auxiliary-landscape* transition state, not a p007 record. Details and run/artifact IDs are preserved in `results/n961-weighted-ah-index1-2026-11-04.txt`.

The successor experiment `code/continue_n961_weighted_saddle_simplex.py` follows the stationary point along occupancy rays, starting with `s=0.01` and targeting `s=0.9`. Each step corrects the root of the physical tangent force with rotation-gauged complex-step Hessian Newton-MINRES, independently classifies the lowest Hessian modes, tests real N960 projections, and sometimes releases both unstable sides. A failed corrector is marked as a **numerical failure**, not proof of a fold. Three parallel runs are in Action `41719943255`; artifacts `thomson-weighted-saddle-ray-{886,960,380}` should contain complete coordinates for every accepted stationary step.

### Outcome of saddle-ray experiment and two-dimensional follow-up

All three rays retained index one over their accepted parameter intervals. The projection-preimage boundaries are not monotonic functions of the ray parameter, and the tested ray380 path exposes a new higher-energy (non-record) N960 basin around s=0.78. This is evidence for complex projection geometry, not for a new N960 global minimum or for a fold in the smooth weighted saddle branch. Primary durable table: `results/n961-weighted-saddle-occupancy-rays-2026-11-04.txt`.

We are testing two-way chord continuation from pairs (886,960), (886,380), and (960,380), at matched radii s=0.48 and s=0.78. At each common midpoint, two independent root corrections are compared after labelled rotation alignment and by Hessian-index checks. The paths intentionally do not linearly interpolate *geometry* between endpoints, because that would force an artificial connection. Positive tests would yield genuine saddle-sheet multistability at identical charges; negative controls constrain this representation only.

## Next decision — full-space adaptive physical candidates

1. Check Action `42851511543`: both seeds passed finite difference and known R/A/B/W source verification. Compare true full-N960 energy and genuinely new low basin quality for 105 biased/physical control cycles per seed. Review logged `INITIAL_DISTANCES`, `HILL_VISITS` and `BEST_ELITES`, not just count of new high minima.
2. If any physically polished E<R-2e-7 appears, independently repolish, rationalize `code/rationalize_candidate.py`, run the Few Shots exact verifier; the new score must be <=444368.3924051973. Submit only after actual numeric certificate.
3. If basin filling makes better new elite(s), exploit them and possibly adjust collective-variable widths based on observed R/A/B/W SO(3)-aligned physical distances. If quality remains flat, reassess the representation with a joint discrete scar motif + global elastic response move, not more C2/C3 recombination/size exchanges.
4. Preserve source, full scores, best coordinates and failures under this research topic; retire completed one-shot workflow files.

## Sources

Primary/current sources checked for this direction include:

- Few Shots p007 problem/verifier: https://github.com/few-shots/few-shots/tree/main/problems/p007-thomson-problem
- Few Shots p007 record chain: https://github.com/few-shots/few-shots/blob/main/problems/p007-thomson-problem/FEWSHOT.md
- D2 record shot: https://github.com/few-shots/few-shots/tree/main/problems/p007-thomson-problem/shots/Abreto/thomson960-d2-ga
- C3 accepted record shot: https://github.com/few-shots/few-shots/tree/main/problems/p007-thomson-problem/shots/Ronnie2025/c3-replica-exchange-scars
- P. Amore and D. J. Wales, *Efficient searches for low-energy structures in clusters with thousands of particles: Application to the Thomson problem*, J. Chem. Phys. 165, 164104 (2026), DOI `10.1063/5.0355867`.
- P. Amore et al., *Exploring the energy landscape of the Thomson problem: local minima and stationary states*, arXiv:2506.08398 (2025).
- D. J. Wales and S. Ulker, *Structure and dynamics of spherical crystals characterized for the Thomson problem*, Phys. Rev. B 74, 212101 (2006), DOI `10.1103/PhysRevB.74.212101`.
- D. Mehta et al., *Kinetic Transition Networks for the Thomson Problem and Smale's Seventh Problem*, Phys. Rev. Lett. 117, 028301 (2016), DOI `10.1103/PhysRevLett.117.028301`.
- D. Mehta et al., *Exploring the potential energy landscape of the Thomson problem via Newton homotopies*, J. Chem. Phys. 142, 194113 (2015), DOI `10.1063/1.4921163`.
- T. F. Middleton and D. J. Wales, soft-mode/eigenvector-following landscape study, Phys. Rev. B 64, 024205 (2001), DOI `10.1103/PhysRevB.64.024205`.
- Cambridge Cluster Database, Thomson/Riesz `s=1`: https://www-wales.ch.cam.ac.uk/~wales/CCD/Thomson/site/s_1/index.html

## Work log

### 2026-10-27

Opened the durable direction, synchronized to the newly merged C3 record, confirmed its symmetry, and tested exact-C3 smooth deformations plus simple neighboring-size cycles. Began full physical-tangent Hessian work.

### 2026-10-28 to 2026-10-30

Mapped the same-topology R/A/B basin graph, tested cross-topology D2/record operators, classified higher stationary states, and built transition-state machinery. Certified the fixed-N R/A first-order saddle and tested direct/transported transverse directions. These experiments expanded the low-energy network but found no lower-than-R basin.

### 2026-10-31

Shifted from fixed-N local perturbations to mechanisms that change the search representation. Neighboring-size scouts revealed a common N961 A/R hub. Fractional occupancy exposed an A/R projection bifurcation and path hysteresis. Fixed-N cascade/follower searches were closed out after strong softening signals failed to translate into better candidates. The full weighted-mode boundary scan returned only R/A/B and was retired.

Current takeover work preserved previously unfinished negative summaries, refreshed this handoff, and launched two changed-representation tests: active-only transverse modes at the N961 projection boundary and closed two-occupancy holonomy loops.

### 2026-11-04

Preserved the fixed-charge weighted A/H first-order saddle validation, including independent Hessian symmetry/Ritz checks and bidirectional descent; no better N960 projection. Started a new three-ray constant-total-charge Newton-MINRES occupancy continuation (run 41719943255), to investigate whether the saddle branch can expose genuine new basin exits or softening rather than repeating known A/H perturbations.

### 2026-11-04 (continued)

Recovered all 3 prior occupancy-ray artifacts after discovering their numeric continuations succeeded but a literal backslash-newline broke the final JSON summary. Preserved all 184 compact evidence lines in `results/n961-weighted-saddle-occupancy-rays-2026-11-04.txt` and fixed the writer. The ray380 deletion at s>=0.78 reaches a new but high N960 minimum (~R+0.223904). Started 6 common-occupancy two-path saddle checks in Action `41857433482`, rather than extending 1D rays further.

### 2026-11-06

After six common-parameter N961 chord tests all converged to one weighted saddle with only known N960 projections, the user explicitly redirected the research from exclusion/boundary mapping toward a **constructive record hunt**. Preserved the chord summary. Launched complete N960 candidate generation via composition of area-preserving local scar vortices and dipoles, independent randomcap control, compiled stable L-BFGS, and a near-record elite population. Includes distinct 24-dislocation R/A/B and 20-dislocation D2 parents across 5 independent Actions jobs. Runs: 42250842594, 42251234401. No record claim until actual outputs and official verifier success.

### 2026-11-06 (construction campaign)

Hamiltonian multi-scar flow search, independent D2 seed family, and C2 six-temperature orbit-space search launched as the user's explicitly requested breakthrough-oriented direction. Initial 720 full N960 minimizations generated multiple genuinely new local minima but no record improvement, best new `444368.42162124`; 8 geometries independently repolished and persisted (`data/scar-braid-elites-2202-2026-11-06.json`, commit via Action `42253037254`). This is positive candidate-generation evidence, not a winning p007 shot. Two later campaigns were launched to exploit new parent basins and the 20-dislocation D2/C2 family (`42251234401`, `42252806055`, `42252230952`); check their completed scores before further scaling.

### 2026-11-06 (learned novel motif event)

Validated first three independent R/A/B Hamiltonian scar-braid searches (720 complete N960 relaxations, no sub-record): best newly obtained local minimum R+0.02921504. Two R/A/B/D2 cross-topology runs (640 proposals) likewise found no sub-R, but independently rediscovered this W minimum. Captured 8 new elite point sets and their defect motifs in durable data/results. Started 3×400 nonlinear event recombination runs from the independent R→W displacement field and its C3 orbit variants combined with R→A/B fields (Action `42254893792`). Objective is a genuinely improved final N960 energy, not more saddle/boundary elimination.

### 2026-11-06 (verified constructive campaign outcome and new representation)

All five prior constructive campaigns completed without an accepted improvement: 3460 true N960 relaxations in three full-space families plus two independent 6-replica C2 campaigns (which deliberately performed zero N960 releases due to too-narrow a C2 energy gate). The best *new* independently verified 960-point minimum remains W=R+0.02921504. W is a physically distinct displacement from A/B (field cosines 0.093/0.571), but 1200 full-sphere W/A/B event compositions still return only known minima. Replaced the global-event assumption with a 12-scar-core donor mosaic genotype search; 3×450 candidate-generating trials in Action `42257750496`. Full reproducible evidence is in `results/constructive-scar-campaigns-and-mosaic-reset-2026-11-06.txt`.

### 2026-11-06 (two genuinely different candidate constructions)

Started a second representation in parallel with the 12-core mosaic: Riesz exponent homotopy, directly altering interactions among the same 960 particles and allowing scar rearrangements in soft/logarithmic-like and hard-packing-like landscapes before physical Coulomb projection. This has separate support from published sphere optimization work (Lai et al., 2024). Action `42258720979`, 2 × 140 full transfer cycles with analytic-gradient self-tests and true N960 scoring, is independent of mosaic Action `42257750496`; both must be assessed by actual new lowest energy, not exclusion volume.

### 2026-11-06 (continued after 12-core mosaic)

Completed all three 12-defect genetic mosaic campaigns (1,350 genuine N960 quenches), no accepted record improvement; best labeled novel E=444368.4344266608 remains worse than W=444368.42162124. Since flat candidate quality indicates representation limitations, launched a new physically distinct SPD Coulomb metric-hysteresis family (two seeds, Action `42261470927`) in parallel with existing Riesz exponent homotopy (Action `42258720979`). Both continuously change the interacting-particle energy landscape, then quench in original Coulomb law; anisotropic metric code has its own finite-difference and Q=I matching self-tests. Details: `results/defect-mosaic-outcome-and-metric-homotopy-2026-11-06.txt`.

### 2026-11-07

Completed all Riesz/anisotropic potential-cycling tests, still no new record and no better candidate than independent W=R+0.02921504. Consulted the two accepted p007 shots' primary SHOT.md: actual winning search was C3 320-orbit six-temperature replica exchange, whereas D2 result came from symmetry-respecting genetic cut-and-splice; both otherwise reported broad failures of unconstrained perturbations (including Riesz). Launched their *combined constructive* C3 orbit genetic/replica search rather than another deformation. Initial Action `42455291835` exposed and led to repair of an elite logger bug; rerun `42455369621` is the current search. Source and evidence links: `results/riesz-metric-outcomes-c3-ga-reset-2026-11-07.txt`.

### 2026-11-07/08 cross-origin C3 genetic extension

Compared the winning original SHOT.md sources and modern Amore-Wales 2026 cross-size framework. Identified that the baseline 6× C3 RE genetic experiment seeded from only R, so symmetry-respecting parent mixing starts without an independent structural parent. Added a verified public T-symmetric old record (12-scar T arrangement, E=444368.4373479895), fit its exact threefold symmetry and seeded as independent C3 population member plus two hot replicas. Original action `42455369621`, new independent-parent action `42455931301`. Both write real N960 release scores and potential winning coordinates; no breakthrough yet claimed.

### 2026-11-07/08 C3 ±3 orbit topology and corrected genetic controls

Identified two correctness defects in the C3 GA source that could suppress a record-level ~1e-6 improvement and postpone actual R×T crossover until an unrelated third elite appears; fixed source (commit `6c928097`) and launched a corrected early-GA assertion control (Action `42456573446`). Independently constructed full C3 orbit birth/death N960↔N957/N963 candidate search (Action `42456406401`); found an internal removal-contribution ranking sign mistake and corrected it, with independent energy identity tests before the restarted run `42456551742`. The original Action's generated physical endpoints remain valid observations but use biased sampling. Full reproducible hypotheses and run IDs in `results/c3-triplet-orbit-search-reset-2026-11-07.txt`. No p007 record claim pending verification.

### 2026-11-08 C2 topology-changing construction

All five earlier C3 GA/triplet experimental batches (10 jobs total) finished successfully without E<R-2e-7, even though distinct C3 and N960 basins were generated; best new near-record W unchanged. Informed by current Amore & Wales 2026 JCP 165 paper about independent symmetric seeds and contiguous-size propagation, re-formulated crossover in C2 quotient, using *independent 20-dislocation D2 and 24-dislocation T* elite parents. Program `code/search_c2_cross_topology_genetic.py` includes an optimized tetrahedral C2 axis fit and a 6-temperature, 480-orbit genetic / replica-exchange search. First Action `42500722842` failed during smoke on a five-vs-four tuple unpack; fixed and rerun as `42500890656`. Evidence: `results/c3-genetic-triplet-results-c2-topology-pivot-2026-11-08.txt`. No result should be claimed before finished N960 physical releases.

### 2026-11-10: C2 GA saturation and new basin-filling formulation

Final C2 20/24-dislocation cross-topology results Action `42500890656`: both successful, 170 total six-replica sweeps, 229 true N960 unconstrained releases, zero subrecord; the new near-D2 C2 state 444368.404283112 returns to D2 after release, so the best genuinely new full-N960 basin from the family is R+0.061506, still above W. Confirmed Few Shots official record unchanged and reviewed published Amore–Wales 2026 + metadynamics collective-variable principles. Stopped expanding C2 GA and launched full-coordinate, rotation-invariant adaptive basin filling with physical Coulomb restoration and direct controls (Action `42851511543`); smoke gradient/source tests green, independent jobs in formal search. Evidence: `results/c2-genetic-outcome-adaptive-basin-filling-2026-11-10.txt`.
