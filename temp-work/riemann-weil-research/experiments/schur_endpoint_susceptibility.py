#!/usr/bin/env python3
"""Rigorous endpoint-evaluation susceptibility for the cutoff-free CvS even block.

For the orthonormal even basis

    1, sqrt(2) cos(2 pi t), ..., sqrt(2) cos(2 pi N t),

let E_N be the cutoff-free Weil matrix and r_N=(1,sqrt(2),...,sqrt(2)).
When E_N>0 define

    chi_N = r_N^T E_N^{-1} r_N
          = sup_{v != 0} |r_N^T v|^2 / (v^T E_N v).

With nested LDL pivots s_j and Schur residuals R_j,

    chi_N - chi_{N-1} = R_j^2 / s_j,

so chi can be accumulated rigorously without forming an inverse.  The experiment
measures how badly endpoint evaluation can grow even when lambda_min is tiny.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from flint import arb, arb_mat, ctx


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("upstream", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def project_even(A: arb_mat, N: int) -> arb_mat:
    E = arb_mat(N + 1, N + 1)
    root2 = arb(2).sqrt()
    center = N
    E[0, 0] = A[center, center]
    for k in range(1, N + 1):
        E[0, k] = (A[center, center + k] + A[center, center - k]) / root2
        E[k, 0] = E[0, k]
    for k in range(1, N + 1):
        for j in range(k, N + 1):
            v = (
                A[center + k, center + j] + A[center + k, center - j]
                + A[center - k, center + j] + A[center - k, center - j]
            ) / 2
            E[k, j] = v
            E[j, k] = v
    return E


def positive_ldlt(E: arb_mat):
    n = E.nrows()
    L = [[arb(0) for _ in range(n)] for _ in range(n)]
    d = [None] * n
    for i in range(n):
        L[i][i] = arb(1)
        s = E[i, i]
        for k in range(i):
            s -= L[i][k] * L[i][k] * d[k]
        if not (s > 0):
            raise RuntimeError(f"pivot {i} not rigorously positive: {s}")
        d[i] = s
        for j in range(i + 1, n):
            t = E[j, i]
            for k in range(i):
                t -= L[j][k] * L[i][k] * d[k]
            L[j][i] = t / d[i]
    return L, d


def solve_Lt_prefix(L, ell, n):
    x = [arb(0) for _ in range(n)]
    for i in range(n - 1, -1, -1):
        t = ell[i]
        for j in range(i + 1, n):
            t -= L[j][i] * x[j]
        x[i] = t
    return x


def ball(x: arb, digits=60):
    return {
        "lower": x.lower().str(digits, radius=False),
        "mid": x.mid().str(digits, radius=False),
        "upper": x.upper().str(digits, radius=False),
        "rad": x.rad().str(20, radius=False),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream-script", type=Path, required=True)
    ap.add_argument("--upstream-commit", required=True)
    ap.add_argument("--c", type=int, required=True)
    ap.add_argument("--Nmax", type=int, required=True)
    ap.add_argument("--prec", type=int, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    ctx.prec = args.prec
    module = load_module(args.upstream_script)
    A, _ = module.build_arb_tau(args.c, args.Nmax, args.prec)
    E = project_even(A, args.Nmax)
    L, d = positive_ldlt(E)

    root2 = arb(2).sqrt()
    chi = arb(0)
    rows = []
    for N in range(args.Nmax + 1):
        if N == 0:
            R = arb(1)
        else:
            ell = [L[N][j] for j in range(N)]
            x = solve_Lt_prefix(L, ell, N)
            R = root2 - x[0]
            for j in range(1, N):
                R -= root2 * x[j]
        inc = (R * R) / d[N]
        chi += inc
        rows.append({
            "N": N,
            "pivot": ball(d[N]),
            "endpoint_residual": ball(R),
            "chi_increment_R2_over_s": ball(inc),
            "chi": ball(chi),
        })

    selected_idx = sorted(set([0,1,2,4,8,16,24,32,48,64,80,96,args.Nmax]))
    selected = [rows[n] for n in selected_idx if n <= args.Nmax]
    out = {
        "status": "rigorous_endpoint_susceptibility_via_schur_telescope",
        "meaning": "chi_N = r_N^T E_N^{-1} r_N is the squared norm of endpoint evaluation in the finite positive Weil space; chi_N-chi_{N-1}=R_N^2/s_N is accumulated with rigorous Arb balls.",
        "upstream_commit": args.upstream_commit,
        "c": args.c,
        "Nmax": args.Nmax,
        "prec_bits": args.prec,
        "all_pivots_rigorously_positive": True,
        "chi_monotone_by_construction": True,
        "selected": selected,
        "last": rows[-1],
        "warning": "This is a finite-dimensional certified diagnostic. It does not establish bounded endpoint evaluation as N->infinity and does not prove RH.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "c": args.c,
        "Nmax": args.Nmax,
        "chi_last_mid": out["last"]["chi"]["mid"],
        "last_increment_mid": out["last"]["chi_increment_R2_over_s"]["mid"],
        "last_residual_mid": out["last"]["endpoint_residual"]["mid"],
        "last_pivot_mid": out["last"]["pivot"]["mid"],
    }, indent=2))


if __name__ == "__main__":
    main()
