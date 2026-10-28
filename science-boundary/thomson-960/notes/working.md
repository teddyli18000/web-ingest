# Working notes — Thomson N=960

Current live merged Few Shots record: `444368.3924061973` (`Ronnie2025/c3-replica-exchange-scars`), epsilon `1e-6`; next valid score <= `444368.3924051973`. Latest upstream check still shows no open p007 PR. Re-check before any claim.

## Decisions

- Work from the live C3 record, not the original Amore–Wales/T baseline.
- Upstream C3 replica exchange and D2 genetic search show that coherent global scar rearrangements matter more than local defect surgery.
- Amore–Wales 2026 neighboring-size propagation is useful, but a direct single-cycle `960→959→960` / `960→961→960` test from the new C3 record returned to the same basin or higher minima.
- Full-space physical tangent Hessian analysis is numerically clean and exposes several near-exact two-dimensional C3-breaking doublets.
- The softest doublet repeatedly exits to one low-lying neighbor at record + `~0.00328004`; the same neighbor was independently reached by the `960→961→960` size-bounce. Treat this as a verified basin-graph node and search *from that node* rather than only from the record.

## Completed experiments

1. Live-record diagnostic: z is the exact C3 axis to ~`2e-9` nearest-neighbor RMS after a 120° rotation; rationalization residual tangent gradient is ~`5e-6` RMS.
2. 40 exact-C3 smooth global-deformation starts (4 seeds × 10): no lower minimum. Small/moderate perturbations overwhelmingly return to the record; large ones land higher.
3. External neighboring-N CCD fetch attempt: invalid because guessed neighboring point-file URLs are not uniformly present; infrastructure failure only, not a scientific result.
4. Direct oscillating-size search from the live record:
   - `960→959→960`: best `444368.392406207859`, about `1.07e-8` above the polished record.
   - `960→961→960`: best `444368.392406216473`, about `1.93e-8` above; a distinct return basin near `444368.395686237` also appeared.
5. Full 1920-dimensional physical tangent Hessian diagnostic:
   - Hessian bilinear symmetry relative defect `1.94e-8`.
   - three rigid rotations cleanly removed (returned-mode rotation overlaps < `8e-25`).
   - lowest internal modes: `4.82417658, 4.82417750, 4.88882190, 5.88540229, 5.88540341, 6.28297677, ...`.
   - near-exact doublets 0/1, 3/4, 7/8, 10/11, 12/13. Direct C3 action on tested doublets is the real +/-120-degree rotation matrix to residual ~`1e-6`–`1e-5`.
6. First low-doublet escape batch (12 independent/random phase samples across 0/1 and 3/4): no improvement. Durable summary: `results/soft-pair-random-basis-summary.txt`.
   - Pair 0/1: every sampled phase crosses at ~`0.008 rad` RMS into the same `+0.00328004` basin (`E≈444368.39568624`).
   - Pair 3/4: repeated families `+0.003280`, `+0.010567`, `+0.029215`.
   - These repeated energies across independent Hessian channels are a stable low-energy basin graph, not floating optimizer noise.
7. Canonical-basis scan first completed point (0/1 pair, phase 10°): `0.006 rad` returns to record; every `0.010–0.045 rad` start converges to `444368.395686234...`; `0.064` goes higher. This confirms the `+0.003280` neighbor with a reproducible phase convention.
8. Deeper pair 10/11 first completed sample: `0.032 rad` converges to the same `+0.01056668` family already seen from pair 3/4.

## Active compute

- Canonical soft-pair phase scan, record modes 0/1 and 3/4: Actions run `40623968469`.
- Deeper record doublets 7/8 and 10/11: Actions run `40623877455`.
- Reproducible coordinate harvest of the `+0.003280` neighbor: Actions run `40624209787` (in progress at last check).

## Immediate next experiment

When the `+0.003280` neighbor coordinates are harvested:

1. Preserve the exact floating seed and analyze convex-hull/Delaunay coordination plus residual point-group symmetry.
2. Compute its full physical tangent Hessian.
3. Launch `code/search_from_seed_modes.py` along the lowest ~8 neighbor modes in both signs (16 second-hop routes), with full unconstrained relaxation.
4. Compare every returned basin directly to the live Few Shots record, not merely to the higher neighbor.
5. If any floating result is comfortably below the live threshold, freeze it, rationalize with `code/rationalize_candidate.py`, run the official p007 verifier and `tools/check.py`, then re-check upstream main/open PRs before submission.
