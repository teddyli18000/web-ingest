#!/usr/bin/env python3
"""Diagnose Galerkin ground states for source-space escape.

This is a research probe, not an RH certificate.  It uses the public
``connes-cvs`` package to build one finite-T CvS Galerkin matrix at a chosen
cutoff, extracts even-sector ground states from nested central submatrices,
and measures the *source* trigonometric polynomial

    T_v(s) = sum_{k=-N}^N u_k exp(2*pi*i*k*s),  0 <= s <= 1.

The source is the object appearing in the exact finite Guinand--Weil
dictionary v -> T_v -> K_v -> g_v.  For symmetric coefficients,
K_v(1-r) is twice the autocorrelation of the zero-extended T_v at lag r.

Metrics here are designed to distinguish compact source behavior from the
boundary/high-frequency escape seen in finite truncations.  They do not by
themselves prove that a matrix eigenvalue has the sign of the full Weil form.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import mpmath as mp

from connes_cvs.operator import build_galerkin_matrix, compute_ground_state


def central_submatrix(q: mp.matrix, n_full: int, n: int) -> mp.matrix:
    """Return the central (2n+1)-square principal submatrix."""
    if n > n_full:
        raise ValueError("n cannot exceed n_full")
    dim = 2 * n + 1
    offset = n_full - n
    out = mp.matrix(dim, dim)
    for i in range(dim):
        for j in range(dim):
            out[i, j] = q[offset + i, offset + j]
    return out


def vector_coefficients(v: mp.matrix) -> tuple[int, list[mp.mpf]]:
    if v.cols != 1 or v.rows % 2 != 1:
        raise ValueError("expected a (2N+1)x1 coefficient vector")
    n = (v.rows - 1) // 2
    coeffs = [mp.mpf(v[i, 0]) for i in range(v.rows)]
    norm2 = mp.fsum(x * x for x in coeffs)
    if norm2 <= 0:
        raise ValueError("zero coefficient vector")
    scale = mp.sqrt(norm2)
    coeffs = [x / scale for x in coeffs]
    return n, coeffs


def periodic_log_energy(v: mp.matrix) -> mp.mpf:
    """Exact source-space log-frequency moment on the unit circle.

    E_per(v) = sum |u_k|^2 log(e + |k|).

    This is not claimed to equal the Dirichlet logarithmic-Laplacian form used
    elsewhere in the research notes.  It is a clean compactness diagnostic:
    bounded E_per gives precompactness in L2(S^1), while edge localization at
    finer Fourier scales forces E_per upward.
    """
    n, coeffs = vector_coefficients(v)
    return mp.fsum(
        coeffs[k + n] ** 2 * mp.log(mp.e + abs(k))
        for k in range(-n, n + 1)
    )


def high_frequency_mass(v: mp.matrix, fraction: float = 0.75) -> mp.mpf:
    """Coefficient mass in the outer ``fraction*N`` through N modes."""
    n, coeffs = vector_coefficients(v)
    if n == 0:
        return mp.mpf("0")
    cutoff = max(1, int(math.ceil(fraction * n)))
    return mp.fsum(
        coeffs[k + n] ** 2
        for k in range(-n, n + 1)
        if abs(k) >= cutoff
    )


def interval_fourier_integral(d: int, a: mp.mpf, b: mp.mpf) -> mp.mpc:
    """Integral_a^b exp(2*pi*i*d*s) ds."""
    if d == 0:
        return mp.mpc(b - a)
    two_pi_i_d = 2 * mp.pi * 1j * d
    return (mp.e ** (two_pi_i_d * b) - mp.e ** (two_pi_i_d * a)) / two_pi_i_d


def spatial_mass(v: mp.matrix, intervals: list[tuple[mp.mpf, mp.mpf]]) -> mp.mpf:
    """Exact quadratic integral of |T_v|^2 over a union of intervals."""
    n, coeffs = vector_coefficients(v)
    total = mp.mpc("0")
    for m in range(-n, n + 1):
        um = coeffs[m + n]
        for k in range(-n, n + 1):
            uk = coeffs[k + n]
            d = m - k
            integral = mp.fsum(
                interval_fourier_integral(d, a, b)
                for a, b in intervals
            )
            total += um * uk * integral
    # Roundoff may leave a tiny imaginary part or tiny excursion outside [0,1].
    value = mp.re(total)
    if abs(mp.im(total)) > mp.mpf("1e-30"):
        raise RuntimeError(f"unexpected imaginary mass: {mp.nstr(mp.im(total), 8)}")
    return value


def endpoint_mass(v: mp.matrix, eps: mp.mpf) -> mp.mpf:
    if not (0 < eps <= mp.mpf("0.5")):
        raise ValueError("eps must lie in (0, 1/2]")
    return spatial_mass(v, [(mp.mpf("0"), eps), (1 - eps, mp.mpf("1"))])


def source_value(v: mp.matrix, s: mp.mpf) -> mp.mpf:
    n, coeffs = vector_coefficients(v)
    value = mp.fsum(
        coeffs[k + n] * mp.e ** (2 * mp.pi * 1j * k * s)
        for k in range(-n, n + 1)
    )
    if abs(mp.im(value)) > mp.mpf("1e-30"):
        raise RuntimeError("even source unexpectedly complex")
    return mp.re(value)


def mpstr(x: mp.mpf, digits: int = 30) -> str:
    return mp.nstr(x, digits)


def diagnose_cutoff(c: int, n_values: list[int], t_cut: int, dps: int) -> dict:
    n_full = max(n_values)
    started = time.time()
    q_full = build_galerkin_matrix(c=c, N=n_full, T=t_cut, dps=dps)
    build_seconds = time.time() - started

    rows = []
    for n in n_values:
        qn = central_submatrix(q_full, n_full, n)
        eig_started = time.time()
        lam, vec = compute_ground_state(qn)
        eig_seconds = time.time() - eig_started

        eps_dynamic = mp.mpf(1) / max(4, n)
        row = {
            "N": n,
            "dimension": 2 * n + 1,
            "finite_T_ground_eigenvalue": mpstr(lam),
            "periodic_log_energy": mpstr(periodic_log_energy(vec)),
            "outer_25pct_frequency_mass": mpstr(high_frequency_mass(vec, 0.75)),
            "endpoint_mass_eps_0.10": mpstr(endpoint_mass(vec, mp.mpf("0.10"))),
            "endpoint_mass_eps_0.05": mpstr(endpoint_mass(vec, mp.mpf("0.05"))),
            "endpoint_mass_eps_1_over_N": mpstr(endpoint_mass(vec, eps_dynamic)),
            "endpoint_epsilon_1_over_N": mpstr(eps_dynamic),
            "source_T_at_0": mpstr(source_value(vec, mp.mpf("0"))),
            "source_T_at_half": mpstr(source_value(vec, mp.mpf("0.5"))),
            "eigensolve_seconds": eig_seconds,
        }
        rows.append(row)

    return {
        "c": c,
        "L_log_c": mpstr(mp.log(c)),
        "T_archimedean_cutoff": t_cut,
        "dps": dps,
        "N_full_built": n_full,
        "matrix_build_seconds": build_seconds,
        "diagnostics": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cutoffs", default="13,100")
    parser.add_argument("--Ns", default="4,8,12,16")
    parser.add_argument("--T", type=int, default=120)
    parser.add_argument("--dps", type=int, default=60)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    cutoffs = [int(x) for x in args.cutoffs.split(",") if x.strip()]
    n_values = sorted({int(x) for x in args.Ns.split(",") if x.strip()})
    if not cutoffs or not n_values or min(n_values) < 1:
        raise SystemExit("nonempty positive --cutoffs and --Ns are required")

    mp.mp.dps = args.dps
    payload = {
        "status": "research_probe_only",
        "interpretation": {
            "warning": "Finite-T eigenvalue signs are not RH certificates.",
            "periodic_log_energy": "sum |u_k|^2 log(e+|k|); compactness/high-frequency escape diagnostic on the source circle",
            "endpoint_mass": "exact integral of |T_v(s)|^2 in endpoint strips of [0,1]",
        },
        "runs": [
            diagnose_cutoff(c, n_values, args.T, args.dps)
            for c in cutoffs
        ],
    }

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
