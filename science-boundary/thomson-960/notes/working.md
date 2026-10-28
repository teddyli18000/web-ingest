# Working notes — Thomson N=960

Current live merged Few Shots record: `444368.3924061973` (`Ronnie2025/c3-replica-exchange-scars`), epsilon `1e-6`; next valid score <= `444368.3924051973`. Latest upstream re-check still shows this record and zero open Few Shots PRs. Re-check before any claim.

## Decisions

- Work from the live C3 record, never the older T baseline.
- Minimum-centered exploration is substantially saturated: exact-C3 smooth moves, neighboring-N propagation through depth 3, record/A/B low modes and combinations, multi-hop basin exploration, defect-reducing flips, same-/cross-topology crossover, topology morphs, and composed shear all failed to improve R.
- The active formulation is a **stationary-state / transition network**, not another random perturb-and-relax campaign.
- Distinguish minima from symmetry-constrained stationary states by the full-space Hessian. This matters critically: the formerly named `C` configuration is index-2, not a minimum.
- Stable local minimization uses termwise pair-energy differences accumulated in long double; raw ~`4.4e5` objective values lose scientifically relevant changes under ordinary L-BFGS stopping tests.

## Confirmed low-energy minima

Let R be the live record.

- `R`: `444368.3924061973`; C3; coordination 36/900/24 (24 dislocations).
- `A`: `~444368.395686226 = R+0.003280029`; symmetry-broken, 36/900/24. Durable `data/neighbor-soft-003280.json`.
- `B`: `444368.402972861484 = R+0.010566664`; symmetry-broken, 36/900/24. Durable `data/basin-b-010566.json`.
- `D`: `444368.41099308443 = R+0.0185868871`; symmetry-broken, 36/900/24. Deterministically harvested from the A↔B saddle positive-mode-2 negative branch at transverse RMS 0.012. Full-space Hessian lowest mode `+0.423627576`; zero negative modes among 14 computed, so D is a genuine minimum.

## Higher-index stationary state C

`C = 444368.41141788312 = R+0.0190116858`, coordination 36/900/24, exact/high C3 symmetry. It is robustly reconstructed by composing all three C3-equivalent nonlinear R→A shear events. Symmetric relaxation converges to it because the symmetric subspace suppresses its unstable directions.

Full-space Hessian run `40732118945`:

- physical gradient RMS `7.57e-6`;
- `lambda0 = -0.931826777147`;
- `lambda1 = -0.931747227271`;
- `lambda2 = +1.56333826701`;
- all later computed low modes positive.

Therefore C is an **index-2 stationary point**, not a basin. The nearly degenerate negative pair is consistent with a nontrivial real C3 doublet and defines a two-dimensional symmetry-breaking unstable manifold.

This explains the earlier D↔C string: its maximum collapsed onto the C endpoint because D is downhill from C; an intervening index-1 saddle is not required.

## Saturated minimum-centered routes

- 40 exact-C3 coherent smooth deformations: no lower minimum.
- `960→959/961→960` and multi-step neighboring-N beams through `960±3`: no lower minimum; best paths return R/A/B.
- Record/A/B Hessian low-mode scans and combinations: only R/A/B plus higher minima.
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

### B↔D

A 9-image string in run `40731597265` lowered its maximum from `444368.4344175272` to `444368.4125963093` after 240 iterations, barrier `~0.00962345` relative B. This is an interior maximum and a plausible index-1 interface, but it has not yet been stationary-point certified.

## C unstable-manifold frontier

The correct next task is not another D↔C barrier search. C has a complete two-dimensional negative eigenspace. `code/search_seed_c3_negative_pair.py`:

1. computes the lowest full-space Hessian pair;
2. canonicalizes that pair under +120° C3 action with a deterministic anchor;
3. samples an oriented phase fundamental sector;
4. fully relaxes each direction without symmetry using the stable difference objective;
5. clusters endpoints by energy and preserves one representative geometry per basin.

Active run `40732550803` samples phases `0,5,...,55°` and amplitudes `0.0015,0.003,0.006,0.012` (48 relaxations). This is an exhaustive symmetry-reduced downward search of the known negative subspace, not a random kick campaign.

## Recent method corrections

- `harvest_saddle_branch.py`: deterministic minimum harvest from a selected transverse branch of a saved saddle.
- `diagnose_seed_modes.py`: arbitrary-seed full-space Hessian/Morse-index diagnostic.
- `string_between_seeds.py`: now retains local path geometry and treats endpoint collapse as data rather than an exception.
- `refine_saddle_path_tangent.py`: preserves a string reaction coordinate for genuinely shallow index-1 interfaces instead of reselecting a potentially wrong lowest eigenmode every cycle.
- `search_seed_c3_negative_pair.py`: symmetry-reduced downward search from C's negative doublet.
- Detailed D/C evidence: `results/d-node-transition-summary.txt`.

## Immediate next

1. Collect `40732550803` and identify all distinct minima reached from C's negative doublet. Any new low basin is frozen and Hessian-classified.
2. If the C unstable manifold closes only on known/symmetry-equivalent D variants, mark C downward connectivity mapped and move to D itself: its `lambda0≈0.424` is substantially softer than R/A/B, making D-centered low-mode and saddle searches the next justified formulation.
3. Certify the B↔D interior string maximum with hybrid or retained-path-tangent refinement; branch its positive modes only after a genuine index-1 state is obtained.
4. Never treat C as a basin again unless a later independent full-space Hessian contradicts the index-2 result.
5. Any relaxed endpoint below `live_score-2e-7` triggers: live upstream re-check -> stable repolish -> rationalization -> official p007 verifier and `tools/check.py`; submit only a verified >=`1e-6` improvement.
