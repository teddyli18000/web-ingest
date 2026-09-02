#!/usr/bin/env python3
"""Rigorous nested Schur pivots for the cutoff-free even CvS Weil matrix.

One cutoff-free full Arb matrix at Nmax is projected to the orthonormal even
basis

    1, sqrt(2) cos(2*pi*t), ..., sqrt(2) cos(2*pi*Nmax*t).

An unpivoted interval LDL^T factorization in that order returns pivots d_N.
Because each prefix is exactly the even matrix E_N, d_N is exactly the scalar
Schur complement

    d_N = c_N - b_N^T E_{N-1}^{-1} b_N.

Strict positivity of every interval pivot certifies positive definiteness of
every nested even prefix through Nmax.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import mpmath as mp
from flint import arb, arb_mat


def load_upstream(path: Path):
    spec = importlib.util.spec_from_file_location("groskin_arb_ldlt", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load upstream verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def project_even(A: arb_mat, N: int) -> arb_mat:
    """Project full [-N,N] matrix to 1,sqrt(2)cos,... ordering."""
    E = arb_mat(N + 1, N + 1)
    root2 = arb(2).sqrt()
    center = N
    E[0, 0] = A[center, center]
    for k in range(1, N + 1):
        # (e_k + e_-k)/sqrt(2), using the exact matrix entries directly.
        E[0, k] = (A[center, center + k] + A[center, center - k]) / root2
        E[k, 0] = E[0, k]
    for k in range(1, N + 1):
        for j in range(k, N + 1):
            value = (
                A[center + k, center + j]
                + A[center + k, center - j]
                + A[center - k, center + j]
                + A[center - k, center - j]
            ) / 2
            E[k, j] = value
            E[j, k] = value
    return E


def interval_ldlt_pivots(E: arb_mat, dim: int):
    d = [None] * dim
    L = [[arb(0) for _ in range(dim)] for _ in range(dim)]
    rows = []
    for i in range(dim):
        s = E[i, i]
        for k in range(i):
            s = s - L[i][k] * L[i][k] * d[k]
        d[i] = s
        if not (s > 0):
            raise RuntimeError(
                f"undetermined/nonpositive even Schur pivot at N={i}: {s}"
            )
        for j in range(i + 1, dim):
            t = E[j, i]
            for k in range(i):
                t = t - L[j][k] * L[i][k] * d[k]
            L[j][i] = t / d[i]
        rows.append((i, s, E[i, i]))
    return rows


def ball_strings(x: arb, digits: int = 80):
    return {
        "lower": x.lower().str(digits, radius=False),
        "upper": x.upper().str(digits, radius=False),
        "mid": x.mid().str(digits, radius=False),
        "rad": x.rad().str(30, radius=False),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-script", type=Path, required=True)
    parser.add_argument("--upstream-commit", required=True)
    parser.add_argument("--c", type=int, default=100)
    parser.add_argument("--Nmax", type=int, required=True)
    parser.add_argument("--prec", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    module = load_upstream(args.upstream_script)
    A, dim_full = module.build_arb_tau(args.c, args.Nmax, args.prec)
    E = project_even(A, args.Nmax)
    pivots = interval_ldlt_pivots(E, args.Nmax + 1)

    # Midpoint-derived log scales are diagnostics only. Sign and interval
    # endpoints remain rigorous Arb quantities.
    mp.mp.dps = max(100, int(args.prec * 0.30103) - 30)
    result_rows = []
    for n, pivot, diagonal in pivots:
        p_mid = mp.mpf(pivot.mid().str(mp.mp.dps, radius=False))
        c_mid = mp.mpf(diagonal.mid().str(mp.mp.dps, radius=False))
        ratio_mid = p_mid / c_mid
        result_rows.append({
            "N": n,
            "pivot": ball_strings(pivot),
            "diagonal": ball_strings(diagonal),
            "log10_pivot_mid_nonrigorous": mp.nstr(mp.log10(p_mid), 40),
            "pivot_over_diagonal_mid_nonrigorous": mp.nstr(ratio_mid, 50),
            "minus_log10_pivot_mid_nonrigorous": mp.nstr(-mp.log10(p_mid), 40),
        })

    payload = {
        "status": "rigorous_even_nested_schur_pivots",
        "meaning": (
            "Each reported pivot interval is strictly positive. In the nested orthonormal "
            "even basis it is the Schur complement for adding mode N, hence every even "
            "prefix E_N through Nmax is rigorously positive definite."
        ),
        "warning": "log10 and pivot/diagonal summaries use interval midpoints only",
        "upstream_commit": args.upstream_commit,
        "c": args.c,
        "Nmax": args.Nmax,
        "full_dimension": dim_full,
        "even_dimension": args.Nmax + 1,
        "prec_bits": args.prec,
        "pivots": result_rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": payload["status"],
        "c": args.c,
        "Nmax": args.Nmax,
        "prec_bits": args.prec,
        "last": result_rows[-1],
        "selected": [result_rows[n] for n in [0, 1, 2, 4, 8, 16, 24, 32, 48] if n <= args.Nmax],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
