#!/usr/bin/env python3
"""Explore cutoff-free CvS/Groskin ground states for collapse versus escape.

The cutoff-free matrix is built with the pinned public Arb implementation used
by the separate interval-LDL sign certificates.  The eigenvector in this file
is obtained from a high-precision midpoint matrix and is therefore exploratory,
not an interval certificate.  Its associated finite-matrix eigenvalue sign is
certified independently by the cutoff-free bracket experiment.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
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


def midpoint_matrix(A, dim: int, digits: int) -> mp.matrix:
    M = mp.matrix(dim, dim)
    for i in range(dim):
        for j in range(dim):
            M[i, j] = arb_mid_to_mpf(A[i, j], digits)
    return M


def even_ground_state(M: mp.matrix) -> tuple[mp.mpf, list[mp.mpf]]:
    dim = M.rows
    if dim != M.cols or dim % 2 != 1:
        raise ValueError("expected odd square matrix")
    N = (dim - 1) // 2
    V = mp.matrix(dim, N + 1)
    V[N, 0] = 1
    inv_sqrt2 = 1 / mp.sqrt(2)
    for k in range(1, N + 1):
        V[N - k, k] = inv_sqrt2
        V[N + k, k] = inv_sqrt2
    E = V.T * M * V
    vals, vecs = mp.eigsy(E)
    coeff_even = [mp.mpf(vecs[i, 0]) for i in range(N + 1)]
    full = [mp.mpf("0") for _ in range(dim)]
    full[N] = coeff_even[0]
    for k in range(1, N + 1):
        full[N - k] = coeff_even[k] * inv_sqrt2
        full[N + k] = coeff_even[k] * inv_sqrt2
    norm = mp.sqrt(mp.fsum(x * x for x in full))
    full = [x / norm for x in full]
    # Deterministic sign: make the source value at s=1/2 nonnegative when possible.
    at_half = mp.fsum(full[k + N] * ((-1) ** k) for k in range(-N, N + 1))
    if at_half < 0:
        full = [-x for x in full]
    return mp.mpf(vals[0]), full


def log_energy(coeffs: list[mp.mpf]) -> mp.mpf:
    N = (len(coeffs) - 1) // 2
    return mp.fsum(coeffs[k + N] ** 2 * mp.log(mp.e + abs(k)) for k in range(-N, N + 1))


def outer_mass(coeffs: list[mp.mpf], fraction: float) -> mp.mpf:
    N = (len(coeffs) - 1) // 2
    cutoff = max(1, int(math.ceil(fraction * N)))
    return mp.fsum(coeffs[k + N] ** 2 for k in range(-N, N + 1) if abs(k) >= cutoff)


def interval_fourier_integral(d: int, a: mp.mpf, b: mp.mpf) -> mp.mpc:
    if d == 0:
        return mp.mpc(b - a)
    z = 2 * mp.pi * 1j * d
    return (mp.e ** (z * b) - mp.e ** (z * a)) / z


def endpoint_mass(coeffs: list[mp.mpf], eps: mp.mpf) -> mp.mpf:
    N = (len(coeffs) - 1) // 2
    intervals = [(mp.mpf("0"), eps), (1 - eps, mp.mpf("1"))]
    total = mp.mpc("0")
    for m in range(-N, N + 1):
        um = coeffs[m + N]
        for k in range(-N, N + 1):
            uk = coeffs[k + N]
            integ = mp.fsum(interval_fourier_integral(m - k, a, b) for a, b in intervals)
            total += um * uk * integ
    return mp.re(total)


def source_value(coeffs: list[mp.mpf], s: mp.mpf) -> mp.mpf:
    N = (len(coeffs) - 1) // 2
    return mp.re(mp.fsum(coeffs[k + N] * mp.e ** (2 * mp.pi * 1j * k * s) for k in range(-N, N + 1)))


def mpstr(x, digits: int = 60) -> str:
    return mp.nstr(x, digits)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--upstream-script", type=Path, required=True)
    p.add_argument("--upstream-commit", required=True)
    p.add_argument("--c", type=int, default=100)
    p.add_argument("--N", type=int, required=True)
    p.add_argument("--prec", type=int, default=900, help="Arb build precision in bits")
    p.add_argument("--dps", type=int, default=220, help="midpoint eigensolve decimal precision")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    module = load_upstream(args.upstream_script)
    A, dim = module.build_arb_tau(args.c, args.N, args.prec)
    mp.mp.dps = args.dps
    M = midpoint_matrix(A, dim, args.dps + 15)
    lam, coeffs = even_ground_state(M)

    eps_dynamic = mp.mpf(1) / max(4, args.N)
    row = {
        "status": "exploratory_cutoff_free_midpoint_ground_state",
        "upstream_commit": args.upstream_commit,
        "c": args.c,
        "N": args.N,
        "dimension": dim,
        "arb_build_prec_bits": args.prec,
        "midpoint_eigensolve_dps": args.dps,
        "midpoint_ground_eigenvalue_nonrigorous": mpstr(lam, 100),
        "periodic_log_energy": mpstr(log_energy(coeffs), 80),
        "outer_25pct_frequency_mass": mpstr(outer_mass(coeffs, 0.75), 80),
        "outer_50pct_frequency_mass": mpstr(outer_mass(coeffs, 0.50), 80),
        "endpoint_mass_eps_0.10": mpstr(endpoint_mass(coeffs, mp.mpf("0.10")), 80),
        "endpoint_mass_eps_0.05": mpstr(endpoint_mass(coeffs, mp.mpf("0.05")), 80),
        "endpoint_epsilon_1_over_N": mpstr(eps_dynamic, 40),
        "endpoint_mass_eps_1_over_N": mpstr(endpoint_mass(coeffs, eps_dynamic), 80),
        "source_T_at_0": mpstr(source_value(coeffs, mp.mpf("0")), 80),
        "source_T_at_half": mpstr(source_value(coeffs, mp.mpf("0.5")), 80),
        "coefficients_minusN_to_N": [mpstr(x, 100) for x in coeffs],
        "warning": "Eigenvector diagnostics use a high-precision midpoint matrix; only the separate interval-LDL experiment certifies eigenvalue signs.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
    print(json.dumps(row, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
