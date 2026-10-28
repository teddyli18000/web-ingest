# Working notes — Thomson N=960

Current live merged Few Shots record: `444368.3924061973` (`Ronnie2025/c3-replica-exchange-scars`), epsilon `1e-6`; next valid score <= `444368.3924051973`. Latest upstream re-check still shows this record and zero open Few Shots PRs. Re-check before any claim.

## Decisions

- Work from the live C3 record, never the older T baseline.
- Minimum-centered exploration is substantially saturated: exact-C3 smooth moves, neighboring-N propagation through depth 3, record/A/B/D low modes and combinations, multi-hop basin exploration, defect-reducing flips, same-/cross-topology crossover, topology morphs, and composed shear all failed to improve R.
- The active formulation is a **stationary-state / transition network**, not another random perturb-and-relax campaign.
- Distinguish minima from symmetry-constrained stationary states by the full-space Hessian. This matters critically: the formerly named `C` configuration is index-2, not a minimum.
- Stable local minimization uses termwise pair-energy differences accumulated in long double; raw ~`4.4e5` objective values lose scientifically relevant changes under ordinary L-BFGS stopping tests.

## Confirmed low-energy minima

Let R be the live record.

- `R`: `444368.3924061973`; C3; coordination 36/900/24 (24 dislocations).
- `A`: `~444368.395686226 = R+0.003280029`; symmetry-broken, 36/900/24. Durable `data/neighbor-soft-003280.json`.
- `B`: `444368.402972861484 = R+0.010566664`; symmetry-broken, 36/900/24. Durable `data/basin-b-010566.json`.
- `D`: `444368.41099308443 = R+0.0185868871`; symmetry-broken, 36/900/24. Full-space Hessian lowest mode `+0.423627576`; zero negative modes among 14 computed, so D is a genuine minimum. Durable `data/basin-d-018586.json`.

## Higher-index stationary state C

`C = 444368.41141788312 = R+0.0190116858`, coordination 36/900/24, exact/high C3 symmetry. It is robustly reconstructed by composing all three C3-equivalent nonlinear R→A shear events. Symmetric relaxation converges to it because the symmetric subspace suppresses its unstable directions.

Full-space Hessian run `40732118945`:

- physical gradient RMS `7.57e-6`;
- `lambda0 = -0.931826777147`;
- `lambda1 = -0.931747227271`;
- `lambda2 = +1.56333826701`;
- all later computed low modes positive.

Therefore C is an **index-2 stationary point**, not a basin. The nearly degenerate negative pair is a real C3 doublet and defines a two-dimensional symmetry-breaking unstable manifold. This explains the earlier D↔C string: its maximum collapsed onto C because D is downhill from C; an intervening D↔C index-1 saddle is not required.

## C unstable-manifold results

The negative pair transforms under +120° C3 approximately as
`[[-1/2,-sqrt(3)/2],[sqrt(3)/2,-1/2]]`; C3 mapping error is only ~`3.5e-7`, with pair-subspace representation residual ~`4.6e-5`.

Half-domain run `40732986870`, phases `0,5,...,55°` × amplitudes `0.0015,0.003,0.006,0.012` (48 full unconstrained relaxations), completed successfully:

- **No record candidate and no new minimum.**
- `B` receives 43/48 trajectories and dominates phases 0–40° at every tested amplitude.
- `D` receives 3/48: phases 45/50/55° at the smallest amplitude 0.0015.
- `A` receives 2/48: phases 50/55° at amplitude 0.012.
- Every endpoint has the same 36/900/24 defect composition.

This makes C a clear organizing index-2 state above A/B/D rather than a wide portal to unknown low basins. However C3 alone identifies phase modulo 120°, not 60°: theta and theta+60° need not be equivalent because cubic C3 invariants distinguish them. Therefore run `40733401539`, phases 0..115° step 5 × four amplitudes = 96 relaxations, is the authoritative saturation test and remains active.

## Saturated minimum-centered routes

- 40 exact-C3 coherent smooth deformations: no lower minimum.
- `960→959/961→960` and multi-step neighboring-N beams through `960±3`: no lower minimum; best paths return R/A/B.
- Record/A/B Hessian low-mode scans and combinations: only R/A/B plus higher minima.
- D Hessian modes 0..3 × ±, amplitudes through 0.045 (run `40733174426`): all eight directions close on A/B/D or much higher states; no new low basin. D mode0 both signs robustly feed B for amplitudes 0.0015..0.032. This fixed-mode D search is retired.
- Same-topology R×A/R×B crossover: returns R/A.
- D2(20-dislocation) × R/A(24) crossover: seam-incompatible or high.
- D2→C3 morph: midpoint creates a 25-dislocation state near `R+2.138`; its low-mode exits remain high.
- Defect-reducing Delaunay flips regenerate defects and return R.
- C3 symmetry-preserving crossover: no record candidate.
- MOTO-like R-centered saddle search found only known/higher transition branches.

## Certified transition edges

### R↔A

Clean hybrid saddle, run `40633736125`:
- `E = 444368.403948984458`;
- gradient RMS `6.310208e-6`;
- exactly one negative internal mode, `lambda0=-5.86557968936`;
- reaction sides descend to R and A.

R↔A fixed-eigenmode transverse exploration through positive mode 7 is retired: low endpoints are only R/A/B; large excursions reach much higher basins. Apparent ~`1e-10` improvements are summation noise.

### A↔B

Clean hybrid saddle, run `40634347073` / certification `40647777986`:
- `E = 444368.4117741097`;
- gradient RMS `8.93599e-6`;
- exactly one negative internal mode, `lambda0=-9.58883287`;
- negative reaction side -> B; positive reaction side -> A for both tested amplitudes.

A↔B transverse modes 1..3 × both signs found no record candidate but did reveal D reproducibly. Thus the transition-state representation found a new minimum that minimum-centered searches had missed.

## B↔D: not yet certified, string method corrected

Old strings (runs `40731597265` and `40733671982`) reduced the interior maximum to roughly `444368.4121–444368.4126`, but the 360-step maximum still had gradient RMS `4.52e-3`, of which about **96.7% was perpendicular to the path tangent** (`~4.37e-3`). Therefore the old string was nowhere near a minimum-energy path even though image step sizes had become small.

Applying stationary refiners prematurely confirmed the diagnosis:
- retained-path-tangent refiner ended at `444368.4107401687`, gradient `2.78e-3`, index 1, but below D and therefore not a B↔D barrier;
- hybrid eigenfollow ended at `444368.4109179036`, gradient `3.95e-4`, index 0 with `lambda0≈+0.00785`, also below D.

`code/string_between_seeds.py` has therefore been rewritten to standard string dynamics: each interior image moves only under the **gradient component perpendicular to the local path tangent**, followed by arc-length reparameterization. It now monitors `max_perpendicular_gradient_rms`, saves all images, and uses perpendicular-force tolerance as the MEP convergence criterion.

Run `40735463455` is the corrected B↔D calculation: 15 images, up to 2500 iterations, `perp_tol=2e-5`. Do not attempt climbing/index-1 certification until this transverse-force criterion is satisfied.

Geometrically, the old B↔D path maximum is closer to C than to D (RMS angular distance about 0.00238 to C versus 0.00270 to D), suggesting the true B↔D route may pass through an **index-1 descendant of C** rather than a direct isolated saddle.

## CHiSD / solution-landscape formulation

Recent constrained high-index saddle dynamics work explicitly treats the Thomson problem by recursively mapping `index-k -> index-(k-1) -> ... -> minima`. This exactly matches the newly discovered role of C.

Two complementary searches are now active:

1. `code/downward_index2_to_index1.py`: CHiSD-inspired **C index-2 -> index-1** downward search. It perturbs within C's negative doublet, retains the orthogonal unstable direction as the desired reaction mode, and tracks that mode by eigenvector overlap to prevent eigenvalue-order switching. Run `40735119192` samples phases 0,20,40,60,80,100°.
2. `code/upward_index1_eigenfollow.py`: **D minimum -> index-1** upward eigenvector following. The selected stable mode is stepped uphill while positive; once its curvature turns negative the same sign rule becomes saddle-Newton, while all other directions descend. This is more appropriate than ordinary mode kicks because D mode0± both relax to B. Run `40735848367` launches both signs of D's softest mode.

Agreement between a C-downward saddle and a D-upward saddle would strongly certify the corresponding network edge independently of string initialization.

## Symmetry-constrained stationary-state portals

`code/search_c3_smooth.py` optimizes in the exact 640-dimensional C3 orbit space; it does **not** release full-space symmetry-breaking modes during minimization. Therefore C demonstrates a general opportunity: other low-energy C3-constrained "minima" may actually be useful full-space higher-index stationary states whose downward manifolds lead to hidden minima.

Do not launch a broad portal census until the complete C manifold is collected. If the authoritative 0..115° C search closes only on A/B/D, the next justified representation change is to harvest distinct low-energy C3 constrained stationary states from the prior search family, classify each full-space Morse index, and apply CHiSD downward search rather than ordinary unconstrained relaxation.

## Current frontier

1. `40733401539`: authoritative full 120° C negative-doublet portrait — active.
2. `40735119192`: C index-2 -> index-1 overlap-tracked downward search — active.
3. `40735463455`: corrected perpendicular-force B↔D MEP — active.
4. `40735848367`: D softest-mode upward index-1 search — queued/starting.
5. No current endpoint is below R. Any relaxed endpoint below `live_score-2e-7` immediately triggers live upstream re-check -> stable repolish -> rationalization -> official p007 verifier and `tools/check.py`; submit only a verified >=`1e-6` improvement.
