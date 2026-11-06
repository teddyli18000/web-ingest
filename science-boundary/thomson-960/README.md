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
- **Active genuinely different candidate representation:** Action `42257750496`, 3 independent 450-trial N960 searches, code `code/search_mosaic_scar_genomes.py`. For *each of 12 distinct R scar cores*, choose a different donor from R/W/A/B/D2 and its three C3-related field variants; spatially stitch the local displacement contributions, cross over/mutate the 12-site donor genome, and physically quench all 960 particles. This stops treating a rearrangement as one globally applied displacement field. Retain any E<R-2e-7 coordinates for independent polish/rational verification.
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

## Next decision — actual lower-energy 960 candidates

1. Inspect all 3 defect-core mosaic jobs in Action `42257750496`. Compare their newly created N960 basins and best energies against prior R/A/B/D2/W. A numerical result below R-2e-7 must immediately be independently repolished, rationalized, and checked by the official Few Shots exact p007 verifier; improvement must exceed 1e-6.
2. If local core-wise mosaics improve the elite frontier, use their verified 960-point coordinates as new patch donors and actively exploit cross-elite coordinated motifs. Track best **new** basin energy, not only overall best R or counts of higher minima.
3. If mosaic candidate quality stays flat, do not blindly expand more of the same genome trials. Change physical representation again: independently optimize positions/orientations of the 12 defect cores and compatible long-range elastic fields, or concerted topology-changing transitions whose global deformation is not representable as a donor displacement mix.
4. Persist scored candidate coordinates, computation logs and upstream status in `data/`, `results/`; remove temporary workflows once the evidence is secured.

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
