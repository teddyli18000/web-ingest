# Working notes — Thomson N=960

Current live merged Few Shots record: `444368.3924061973` (`Ronnie2025/c3-replica-exchange-scars`), epsilon `1e-6`; next valid score <= `444368.3924051973`. Latest upstream check on 2026-10-28 still shows no open p007 PR. Re-check before any claim.

## Decisions

- Work from the live C3 record, never the older Amore–Wales/T baseline.
- Minimum-centered exploration around the record is now substantially saturated: exact-C3 smooth moves, one- and multi-step neighboring-N propagation, full-space soft modes, multi-hop soft-mode basin exploration, low-mode combinations, local topology deletion, and simple same-/cross-topology crossover all fail to improve R.
- The active formulation is now a **transition-state network**, not another perturb-and-relax campaign. R<->A has a reproducible low barrier and a clean one-negative-mode Hessian signature after string/eigenvector-following refinement.
- Stable local minimization must use a termwise pair-energy-difference objective accumulated in long double rather than raw ~`4.4e5` absolute energy; otherwise L-BFGS `ftol` loses scientifically relevant `1e-8`–`1e-3` changes.

## Established low-energy basin graph

Let R be the live record.

- `R`: verifier `444368.3924061973`; C3; coordination 36 five / 900 six / 24 seven (24 dislocations).
- `A`: symmetry-broken same-topology neighbor near `444368.395686226`, `R + ~0.003280029`. Durable coordinates `data/neighbor-soft-003280.json`; 36/900/24; z-C3 match RMS ~`5.68e-3`.
- `B`: symmetry-broken same-topology node `444368.402972861484`, `R + ~0.010566664`. Durable coordinates now `data/basin-b-010566.json` (persisted by run `40633594145`); 36/900/24.
- `C`: C3-symmetric node `444368.4114178827`, `R + 0.0190116854`; 36/900/24. Both sequential orders `0,1,2` and `0,2,1` of the three C3-equivalent nonlinear R→A shear events converge to C over all tested event scales 0.55–1.35, so C is structurally a closed three-event global-shear/scar-rearrangement state.

Independent mechanisms repeatedly show `R <-> A <-> B`, some direct `R <-> B`, and nonlinear composed-shear routes R→C. Bare corresponding-point geodesic barriers were ~0.0367 (R→A), ~0.0379 (A→B), ~0.0739 (R→B).

## Completed experiments / ruled-out move families

1. Live-record diagnostic: z is the C3 axis to ~`2e-9` RMS after 120° rotation; rationalization residual tangent gradient is tiny.
2. 40 exact-C3 coherent smooth deformations: no lower minimum.
3. One-cycle `960→959→960` and `960→961→960`: best returns only ~`1e-8` above R; size-up independently found A.
4. Record full-space Hessian: lowest internal modes `4.82417658, 4.82417750, 4.88882190, 5.88540229, 5.88540341, 6.28297677, ...`; multiple C3-breaking doublets; Hessian symmetry relative defect `1.94e-8`.
5. Record soft-mode scans: softest 0/1 doublet robustly reaches A; deeper doublets reach A, B and `+0.029215`; no improvement.
6. A Hessian lowest modes ~`2.80383834, 4.02949457, 4.57411004, 5.05622790, 5.67154221, 6.06109536, ...`. A second-hop Actions scan modes 0..7 × ± (run `40624586144`) yielded no candidate; directions return R/A/B, `+0.029215`, or high minima.
7. B stable energy `444368.402972861484`; Hessian lowest modes ~`1.42143383, 2.73430561, 3.59487562, 4.06473996, 5.15833004, ...`. Single modes and random combinations of first eight modes only return R/A/B.
8. Same-topology cut-and-splice: R×A/R×B clean children return R/A. A 160-cut R×B screen found 59 collision-safe children; the five lowest raw-energy starts all converged to A. Summary `results/basin-graph-same-topology-summary.txt`.
9. D2(20-dislocation) × R/A(24) spherical cut-and-splice, run `40626019263`: ICP mismatch ~0.042; almost all children fail seam safety; rare safe child relaxed to `R+1.498`. Summary `results/cross-topology-summary.txt`.
10. Continuous D2→C3 ICP+Hungarian morph, run `40626089044`: `t<=0.4 -> R`, `t>=0.6 -> D2`; `t=0.5` gives high transition minima. The reproducible seed5011 midpoint is `444370.5305536334 = R+2.138147436`, coordination **37/898/25 = 25 dislocations**. Thus this 24→20 route first creates an extra dislocation rather than monotonically deleting defects.
11. 25-dislocation midpoint low-mode exits, run `40627982217`, modes 0..3 × ±: all eight jobs completed with no record candidate. Best observed mode0/- exit at amp 0.022 is `444370.0275016348 = R+1.635095437`; route retired.
12. Targeted Delaunay edge flips: single, double, and C3-triple defect-reducing flips heal to R. A genuine 34/904/22 start also regenerates defects and returns R.
13. Nonlinear composed-shear run `40627802546`: all six jobs completed, no record candidate. Completing all three equivalent events robustly gives C; two-event/simultaneous variants do not produce a lower node.
14. C3 symmetry-preserving crossover run `40628147767`: no candidate. For R×C, 60 children produced 16 collision-safe children; the six lowest screened starts relaxed no lower than `444369.076885462 = R+0.684479265`. A farther C3 parent also failed.
15. Multi-step neighboring-N beam run `40628365874`: no candidate.
    - up depth 2 (`960→962→960`): best `444368.392406197323`, numerically R; second A.
    - down depth 2 (`960→958→960`): best `444368.392406197556`, numerically R.
    - up depth 3 (`960→963→960`): best B `444368.402972861251`.
    - down depth 3 (`960→957→960`): best `444368.835897036537 = R+0.443490839`.
   Narrow-beam neighboring-size propagation is therefore locally saturated through depth 3.

## Transition-state route

### R↔A spherical string

Run `40628689846`, code `code/string_record_neighbor.py`.

- Bare corresponding-point path: max barrier `R + 0.0366976953`.
- 160 spherical-string iterations lowered the maximum image to about `444368.40807238`.
- 120 climbing-image steps reached `444368.40489008825`, roughly `R + 0.012483891`, while gradient RMS fell from ~0.0154 to ~0.00658.
- This is strong evidence that R and A are separated by a much lower optimized barrier than the bare geodesic suggested, but the climbing image was not yet stationary.

### Minimum-mode/eigenvector-following refinement

Run `40632990227` completed both refinements from the climbing image.

- conservative: `E=444368.403955672286`, gradient RMS `0.00139739`, lowest modes `-3.09616865,+3.50214671,+4.79765302,+5.24363225,...`, exactly one internal negative mode.
- standard: `E=444368.403916123265`, gradient RMS `0.0010026875`, lowest modes `-3.19930950,+3.49535993,+4.79762153,+5.22922276,...`, exactly one internal negative mode.
- rotation overlaps are ~`1e-19` or smaller and low-mode residuals ~`3e-5`, so both jobs independently locate the same first-order-saddle branch.

Run `40633364828` then applied truncated Newton in the first ten Hessian modes:

- damp05: `E=444368.403965246282`, gradient RMS `8.43633e-4`, exactly one negative mode, final `lambda0=-5.55542462`; reaction-gradient coefficient was reduced from about `-0.034` to `~1.5e-4`.
- damp08 drove the reaction-mode coefficient to `~1e-6` but left total gradient RMS worse (`1.436e-3`).
- Interpretation: reaction-coordinate stationarity is nearly solved; most residual gradient lives in the large unresolved positive-curvature subspace. This motivated `code/refine_saddle_hybrid.py`, which alternates constrained all-dimensional positive-subspace L-BFGS with reaction-mode Newton updates.

### First transverse branch evidence

Run `40633502573` scans positive saddle modes 1..4 × both signs with transverse RMS amplitudes `0.002,0.004,0.008,0.014` and reaction offsets `-0.0008,0,+0.0008`.

The first completed job, positive mode 2 / negative sign (`lambda≈4.79762153`), produced only known low basins:

- small/moderate branches relax to R or A depending reaction-side bias;
- at transverse `0.014` with reaction `-0.0008`, the endpoint is B: `444368.402972861484`;
- no endpoint below R beyond `~1e-10` floating summation noise.

This is important structural evidence: the R↔A saddle neighborhood has a transverse route that directly enters B at larger amplitude, so R/A/B genuinely share a nearby low-energy transition network rather than merely being minima found by unrelated perturbations. No fourth node from this direction.

## Active compute / current frontier

- `40633736125`: hybrid R↔A saddle refinement, using all-dimensional constrained minimization plus reaction-mode Newton; active.
- `40633502573`: remaining R↔A transverse modes 1..4 × ±; active. Any new low endpoint gets frozen and recursively mapped; any record candidate triggers verifier immediately.
- `40633962357`: reaction-only validation of the standard one-negative-mode saddle; four starts at ±0.0015/0.003 RMS should verify that the two negative-mode sides descend to R and A.
- `40633926646`: A↔B spherical string. It reproduces B locally then optimizes a 7-image string and climbing image. Generic tool is `code/string_between_seeds.py`; B is now durable so future runs need not reproduce it.
- `code/refine_saddle_hybrid.py` and `code/search_saddle_transverse.py` are the active transition-network infrastructure.

## Immediate next

1. Finish R↔A transverse modes and reaction-only endpoint validation. If all low transverse exits are R/A/B, treat the local three-basin neighborhood as mapped rather than extending random amplitudes indefinitely.
2. Finish hybrid saddle refinement; use the hybrid saddle for a second transverse pass only if it materially changes the saddle location or low eigenspace.
3. Finish A↔B string; if it yields a clean low saddle, refine and scan its transverse exits. This changes the interface being searched rather than repeating R↔A.
4. Deduplicate all relaxed endpoints against R/A/B/C. Any genuinely new low node is frozen durably and recursively mapped; any candidate below `live_score-2e-7` immediately triggers stable repolish and exact-verifier pipeline.
5. If R↔A and A↔B transition neighborhoods are saturated, next justified edge is R↔B or B↔C; do not return to ordinary random kicks, same-topology splices, local flips, or shallow neighboring-N moves.
6. Before any claim/submission: re-check Few Shots main/open p007 PRs, rationalize, run official verifier and `tools/check.py`, then submit only a verified >=`1e-6` improvement.
