#!/usr/bin/env python3
"""High-precision ground-vector diagnostic for the cutoff-free CvS matrix.

The matrix entries come from the pinned public Groskin Arb cutoff-free builder.
Arb is used to construct the matrix, then high-precision midpoint arithmetic is
used only for exploratory eigenvector diagnostics.  The vector diagnostics are
NOT interval certificates; finite-matrix eigenvalue signs are certified
separately by cutoff_free_lambda_bracket_v2.py.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import mpmath as mp


def load_upstream(path: Path):
    spec = importlib.util.spec_from_file_location("groskin_arb_ldlt", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load upstream verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def arb_mid_to_mpf(x, digits: int) -> mp.mpf:
    return mp.mpf(x.mid().str(digits, radius=False))


def endpoint_mass(coeffs: list[mp.mpf], N: int, eps: mp.mpf) -> mp.mpf:
    """Exact finite-sum integral of |T(s)|^2 over both endpoint strips."""
    if eps <= 0 or eps > mp.mpf("0.5"):
        raise ValueError("eps must be in (0, 0.5]")
    total = mp.mpc(0)
    for i, um in enumerate(coeffs):
        m = i - N
        for j, un in enumerate(coeffs):
            n = j - N
            r = m - n
            if r == 0:
                integral = eps
            else:
                integral = (mp.e ** (2j * mp.pi * r * eps) - 1) / (2j * mp.pi * r)
            total += um * un * integral
    # T is reversal-even, hence the [1-eps,1] strip equals [0,eps].
    return 2 * mp.re(total)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-script", type=Path, required=True)
    parser.add_argument("--upstream-commit", required=True)
    parser.add_argument("--c", type=int, default=100)
    parser.add_argument("--N", type=int, required=True)
    parser.add_argument("--prec", type=int, required=True)
    parser.add_argument("--dps", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    module = load_upstream(args.upstream_script)
    A_arb, dim = module.build_arb_tau(args.c, args.N, args.prec)

    mp.mp.dps = args.dps
    A = mp.matrix(dim, dim)
    for i in range(dim):
        for j in range(dim):
            A[i, j] = arb_mid_to_mpf(A_arb[i, j], args.dps + 20)

    eigvals, eigvecs = mp.eigsy(A)
    lam0 = eigvals[0]
    lam1 = eigvals[1]
    v = mp.matrix(dim, 1)
    for i in range(dim):
        v[i] = eigvecs[i, 0]

    norm = mp.sqrt(mp.fsum(v[i] ** 2 for i in range(dim)))
    for i in range(dim):
        v[i] /= norm

    # Fix the arbitrary global sign to make nested comparisons deterministic.
    center = args.N
    if v[center] < 0:
        for i in range(dim):
            v[i] = -v[i]

    coeffs = [mp.mpf(v[i]) for i in range(dim)]
    residual = A * v - lam0 * v
    residual_norm = mp.sqrt(mp.fsum(residual[i] ** 2 for i in range(dim)))

    log_energy = mp.fsum(
        coeffs[i] ** 2 * mp.log(mp.e + abs(i - args.N))
        for i in range(dim)
    )

    outer_threshold = mp.mpf("0.75") * args.N
    outer_mass = mp.fsum(
        coeffs[i] ** 2
        for i in range(dim)
        if abs(i - args.N) >= outer_threshold
    )

    payload = {
        "status": "nonrigorous_vector_diagnostic_from_cutoff_free_arb_midpoints",
        "warning": (
            "Eigenvector diagnostics use high-precision midpoints and are exploratory. "
            "Use the separate Arb shifted-LDL results for rigorous eigenvalue signs."
        ),
        "upstream_commit": args.upstream_commit,
        "c": args.c,
        "N": args.N,
        "dimension": dim,
        "arb_prec_bits": args.prec,
        "mpmath_dps": args.dps,
        "ground_eigenvalue_midpoint": mp.nstr(lam0, 90),
        "second_eigenvalue_midpoint": mp.nstr(lam1, 90),
        "spectral_gap_midpoint": mp.nstr(lam1 - lam0, 90),
        "relative_residual_norm": mp.nstr(residual_norm / max(abs(lam0), mp.mpf("1e-100000")), 50),
        "absolute_residual_norm": mp.nstr(residual_norm, 50),
        "periodic_log_energy": mp.nstr(log_energy, 80),
        "outer_25pct_frequency_mass": mp.nstr(outer_mass, 80),
        "endpoint_mass_eps_0.05": mp.nstr(endpoint_mass(coeffs, args.N, mp.mpf("0.05")), 80),
        "endpoint_mass_eps_0.10": mp.nstr(endpoint_mass(coeffs, args.N, mp.mpf("0.10")), 80),
        "endpoint_mass_eps_1_over_N": mp.nstr(endpoint_mass(coeffs, args.N, 1 / mp.mpf(args.N)), 80),
        "source_T_at_0": mp.nstr(mp.fsum(coeffs), 80),
        "source_T_at_half": mp.nstr(mp.fsum(coeffs[i] * ((-1) ** (i - args.N)) for i in range(dim)), 80),
        "coefficients_minusN_to_N": [mp.nstr(x, 90) for x in coeffs],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in payload.items() if k != "coefficients_minusN_to_N"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
