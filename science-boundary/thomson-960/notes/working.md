# Working notes — Thomson N=960

Current live merged Few Shots record: `444368.3924061973` (`Ronnie2025/c3-replica-exchange-scars`), epsilon `1e-6`; next valid score <= `444368.3924051973`. Upstream re-check on 2026-10-28: record unchanged and zero open Few Shots PRs. Re-check again before any claim.

## Decisions

- Work from the live C3 record, never the older T baseline.
- Minimum-centered exploration is substantially saturated: exact-C3 smooth moves, neighboring-N propagation through depth 3, full-space soft modes and combinations, multi-hop basin exploration, defect-reducing flips, same-/cross-topology crossover, topology morphs, and composed shear all failed to improve R.
- The active formulation is a **transition-state network**. Search new interfaces between low minima rather than extending the same local perturbation family.
- Stable local minimization uses termwise pair-energy differences accumulated in long double; raw ~`4.4e5` objective values lose scientifically relevant changes under ordinary L-BFGS stopping tests.

## Low-energy basin graph

Let R be the live record.

- `R`: `444368.3924061973`; C3; coordination 36/900/24 (24 dislocations).
- `A`: `~444368.395686226 = R+0.003280029`; symmetry-broken, same 36/900/24 topology. Durable `data/neighbor-soft-003280.json`.
- `B`: `444368.402972861484 = R+0.010566664`; symmetry-broken, same topology. Durable `data/basin-b-010566.json`.
- `C`: `444368.4114178827 = R+0.0190116854`; C3, same topology. It is the robust endpoint of sequentially composing all three C3-equivalent nonlinear R→A shear events. `code/harvest_basin_c.py` now reproduces it; run `40647978833` is intended to freeze the coordinates and continue B↔C.

Independent mechanisms repeatedly show `R <-> A <-> B`; composed global-shear events connect toward C.

## Saturated minimum-centered routes

- 40 exact-C3 coherent smooth deformations: no lower minimum.
- `960→959/961→960` and multi-step neighboring-N beams through `960±3`: no lower minimum; best paths return R/A/B.
- Record/A/B Hessian low-mode scans and combinations: only R/A/B plus higher minima.
- Same-topology R×A/R×B crossover: returns R/A.
- D2(20-dislocation) × R/A(24) crossover: seam-incompatible or high.
- D2→C3 morph: midpoint creates a 25-dislocation state near `R+2.138`; its low-mode exits remain high.
- Defect-reducing Delaunay flips regenerate defects and return R.
- Nonlinear composed shear robustly finds C but not a record.
- C3 symmetry-preserving crossover: no candidate.

## Transition network

### R↔A — certified and locally saturated

Spherical string run `40628689846` reduced the bare corresponding-point barrier from ~`R+0.03670` to ~`R+0.0125`. Minimum-mode and truncated-Newton refinement identified a consistent index-1 branch.

Hybrid refinement run `40633736125` produced the clean saddle:

- `E = 444368.403948984458`
- physical tangent gradient RMS `6.3102083e-6`
- exactly one negative internal mode
- reaction eigenvalue `lambda0 = -5.86557968936`.

Reaction-only descent verifies the two signs go to R and A.

Transverse search is now retired:

- standard saddle modes 1..4 × ±, run `40633502573`: low endpoints only R/A/B.
- high-accuracy hybrid saddle modes 5..7 × ±, run `40634209722`, amplitudes through 0.022 rad: again low endpoints only R/A/B; large mode-7 excursions enter high basins `R+0.20..0.38`.
- apparent values `~1e-10` below R are summation noise, not candidates.

Conclusion: fixed-eigenmode transverse exploration of the R↔A saddle through mode 7 is locally saturated. Do not extend mode numbers mechanically.

### MOTO-like R-centered saddle exploration — negative

Run `40634914233`, seeds 8101/8102, used diverse combinations of R's low modes with feasibility and `lambda2-lambda1` spectral-gap ranking. It found only known/higher transition structure (a higher A↔A branch and a higher R↔A branch); other starts did not converge to clean index-1 saddles. This formulation remains too R-centric.

### A↔B — clean index-1 saddle found

A first spherical string showed a path maximum near `444368.42214`; naive climbing was unstable and is not treated as a saddle. Re-running without climbing and applying hybrid eigenvector-following in run `40634347073` produced a clean first-order saddle:

- `E ≈ 444368.4117741096`
- physical tangent gradient RMS `≈8.94e-6`
- exactly one negative internal mode
- reaction eigenvalue `≈-9.5888`.

Active follow-up run `40647777986` downloads this saddle and performs:

- reaction-mode descent at ±0.0015/0.003 RMS to certify A↔B connectivity;
- transverse modes 1..3 × ± at amplitudes 0.003/0.006/0.012/0.020 with reaction offsets ±0.0006/0.

Any genuinely new low endpoint is to be frozen and recursively mapped. Any endpoint below `live_score-2e-7` triggers stable repolish immediately.

### B↔C — active interface change

C previously had no permanent coordinates despite being reproducible. `code/harvest_basin_c.py` now reconstructs C from the three C3-equivalent R→A shear events.

Run `40647978833` will:

1. reproduce and validate C;
2. optimize a 7-image B↔C spherical string with climbing disabled;
3. feed the string maximum directly to hybrid eigenvector-following;
4. preserve C/string/saddle artifacts.

If C is reproduced at the expected `~444368.411417883` with 36/900/24 and the hybrid state is index-1, freeze C durably and certify/branch the B↔C saddle next.

## Current frontier

- `40647777986`: A↔B reaction certification + low transverse branches. Currently queued at the last check.
- `40647978833`: reproduce C + B↔C string + hybrid saddle. Currently queued at the last check.
- No record candidate exists at present.

## Next decisions

1. Collect A↔B. If reaction signs map to A/B and modes 1..3 reveal no new low node, mark this local interface mapped.
2. Collect B↔C. If clean, persist C and map B↔C reaction/transverse exits rather than returning to R-centered kicks.
3. If A↔B and B↔C both close on known nodes, next interface should be R↔B or a B/C-centered diversity/spectral-gap saddle search; do not return to ordinary random kicks, local flips, shallow neighboring-N moves, or more R↔A fixed modes.
4. Before any claim/submission: re-check Few Shots main/open p007 PRs, rationalize, run official verifier and `tools/check.py`, and submit only a verified improvement of at least `1e-6`.
