# Thomson problem for 960 points

## Question

Can we find a 960-point configuration on the unit sphere with Coulomb energy low enough to beat the live Few Shots p007 record by at least `1e-6`?

## Current state

- Few Shots p007 is a minimization problem with absolute epsilon `1e-6`.
- Accepted merged record rechecked on **2026-10-31**: `R = 444368.3924061973`, shot `Ronnie2025/c3-replica-exchange-scars`. No open p007 pull request was visible at that check.
- Therefore an accepted replacement must score at most `444368.3924051973`, subject to another upstream check immediately before any claim or submission.
- The record is C3-symmetric and has coordination `36/900/24`, i.e. 24 neutral dislocations. The previous merged D2 record has 20 dislocations.
- Fixed-N local exploration around R is no longer the main frontier. The low same-topology network `R <-> A <-> B` has been mapped, an R/A first-order saddle has been certified, direct saddle-transverse searches have been run, and simple 20-dislocation D2 ↔ 24-dislocation morph/crossover routes have been tested without improvement.
- The strongest current mechanism is a **shared N=961 hub** connecting R and the very close same-topology minimum `A ≈ 444368.3956862258` (`R + 0.0032800285`). At the same N961 minimum, deleting label 886 returns R while deleting inserted label 960 returns A.
- Continuous fractional occupancy reveals genuine path dependence: hard deletion of label960 at the unmodified hub gives A, but adiabatically fading that same label to zero gives R. A two-label occupancy exchange also shows endpoint hysteresis.
- Along the A-derived single-particle fade, the genuine-N960 projection switches from A at `lambda=0.15` to R at `lambda=0.10` while the N960 coordination count remains `36/900/24`.
- Full weighted-N961 low Hessian modes at `lambda=0.15, 0.125, 0.10` only traverse the known R/A/B basins. This representation is retired rather than widened mechanically.
- Two mechanism-changing experiments are active:
  1. **active-only transverse boundary modes**, excluding the fading particle's tangent coordinates and projecting out the empirical A/R continuation secant — run `41197569521`;
  2. **two-occupancy closed loops**, testing whether noncommuting paths in `(q886,q960)` return the same endpoint occupancy on a different geometric branch — run `41197844226`.

No record improvement is currently claimed. Apparent differences of order `1e-10` around R are ordinary floating summation/relaxation noise.

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

## Next decision

1. Finish and preserve the active-only transverse run and occupancy-loop run.
2. Any internally stable candidate below R by more than `2e-7` immediately stops exploratory branching and triggers independent high-precision repolish plus current Few Shots verification. An accepted result still needs at least `1e-6` improvement.
3. If both active mechanisms return only known basins, do **not** scale the same searches indefinitely. Reassess the enlarged N961 interface itself:
   - map the A/R/B basin-boundary preimage in occupancy × geometry space and locate genuine junction/fold regions, or
   - retire this auxiliary family if closed loops show no useful branch transport and move to a structurally distinct parent/topology family.
4. Immediately before any record claim, re-check Few Shots `main`, open p007 PRs, rationalize the candidate under the official constraints, run the p007 verifier, and run the repository/Few Shots checks required for submission.

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
