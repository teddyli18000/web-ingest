# Working notes — Thomson N=960

Current live merged Few Shots record: `444368.3924061973` (`Ronnie2025/c3-replica-exchange-scars`), epsilon `1e-6`; re-check before any claim.

## Decisions

- Work from the live C3 record, not the original Amore–Wales/T baseline.
- Upstream C3 replica exchange and D2 genetic search show that coherent global scar rearrangements matter more than local defect surgery.
- Amore–Wales 2026 neighboring-size propagation is useful, but a direct single-cycle `960→959→960` / `960→961→960` test from the new C3 record returned to the same basin.
- Next route: compute the lowest full-space tangent Hessian modes of the current C3 minimum and make symmetry-breaking basin escapes along those directions. This is supported by Wales-style energy-landscape work: low-eigenvalue modes are efficient directions for finding nearby low barriers / transition states.

## Completed experiments

1. Live-record diagnostic: z is the exact C3 axis to ~`2e-9` nearest-neighbor RMS after a 120° rotation; rationalization residual tangent gradient is ~`5e-6` RMS.
2. 40 exact-C3 smooth global-deformation starts (4 seeds × 10): no lower minimum. Small/moderate perturbations overwhelmingly return to the record; large ones land higher.
3. External neighboring-N CCD fetch attempt: invalid because guessed neighboring point-file URLs are not uniformly present; infrastructure failure only, not a scientific result.
4. Direct oscillating-size search from the live record:
   - `960→959→960`: best `444368.392406207859`, about `1.07e-8` above the polished record.
   - `960→961→960`: best `444368.392406216473`, about `1.93e-8` above.
   Both routes returned to the record basin for their best branches.

## Immediate next experiment

Compute 12–16 lowest **physical tangent-space** Hessian eigenmodes in all 1920 tangent degrees of freedom. Use the sphere metric (mass-weighted angular coordinates), penalize the three rigid-rotation zero modes, validate Hessian-vector symmetry/residuals, then scan both signs and increasing RMS angular amplitudes along the lowest non-rigid modes. If individual modes fail, test combinations within near-degenerate soft-mode pairs.
