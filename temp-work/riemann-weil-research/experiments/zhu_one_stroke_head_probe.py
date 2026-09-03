#!/usr/bin/env python3
"""Independent exploratory reconstruction of Zhu 2608.24827v2 §5 head matrix.

This is deliberately NOT a certificate.  It reconstructs the leading reduced
matrix R = beta I + 2 p p^T + C from the formulas printed in the paper, using
high-precision Gauss-Legendre quadrature and a high-precision Miller recurrence
for spherical Bessel functions.  It is used only as a gate before building a
full interval/error-budget certificate.

No third-party source code is copied here.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import mpmath as mp

ARXIV_ID = "2608.24827v2"
ARXIV_MAIN_TEX_SHA256 = "14ec17c2b2e1d3d8069c1d424dae4f5aa6c92b75c73b89d10915ed868495f2c5"


def prime_comb_mass_and_terms(L: mp.mpf):
    # Sufficient for the target plateau L <= log(5)/2.  Fail closed above it.
    if 2 * L > mp.log(5) + mp.mpf("1e-40"):
        raise ValueError("probe is intentionally scoped to L <= log(5)/2")
    terms = []
    for n, lam in [(2, mp.log(2)), (3, mp.log(3)), (4, mp.log(2))]:
        if mp.log(n) < 2 * L:
            terms.append((n, 2 * lam / mp.sqrt(n), mp.log(n)))
    return mp.fsum(c for _, c, _ in terms), terms


def psi_symbol(t: mp.mpf, L: mp.mpf, terms) -> mp.mpf:
    h = mp.re(mp.digamma(mp.mpc(mp.mpf("0.25"), t / 2))) - mp.log(mp.pi)
    comb = mp.fsum(c * mp.cos(t * logn) for _, c, logn in terms)
    return h - comb


def spherical_j_all(x: mp.mpf, nmax: int):
    """j_0(x),...,j_nmax(x) by Miller backward recurrence.

    Normalize against whichever of exact j0/j1 is farther from zero.  Gauss
    nodes never hit x=0, but the small-x branch avoids accidental instability.
    """
    ax = abs(x)
    if ax < mp.mpf("1e-20"):
        # Series-leading terms are enough only for the never-used emergency case.
        vals = [mp.mpf(0)] * (nmax + 1)
        vals[0] = mp.mpf(1) - x*x/6
        if nmax >= 1:
            vals[1] = x/3 - x**3/30
        # upward recurrence is stable in this tiny-x emergency only for low n;
        # use direct Bessel representation for the rest.
        for n in range(2, nmax + 1):
            vals[n] = mp.sqrt(mp.pi/(2*x)) * mp.besselj(n + mp.mpf("0.5"), x)
        return vals

    M = max(nmax + 60, int(mp.floor(ax)) + 70)
    jkp1 = mp.mpf(0)   # unnormalised j_{M+1}
    jk = mp.mpf(1)     # unnormalised j_M
    vals = [None] * (nmax + 1)
    for k in range(M, 0, -1):
        jkm1 = ((2*k + 1) / x) * jk - jkp1
        if k - 1 <= nmax:
            vals[k - 1] = jkm1
        jkp1, jk = jk, jkm1

    true0 = mp.sin(x) / x
    true1 = mp.sin(x)/(x*x) - mp.cos(x)/x
    u0 = vals[0]
    u1 = vals[1] if nmax >= 1 else None
    if nmax >= 1 and abs(true1) > abs(true0):
        scale = true1 / u1
    else:
        scale = true0 / u0
    return [v * scale for v in vals]


def pole_vector(L: mp.mpf, orders):
    # p_n = F_n(i/2) = integral T_n(x) exp(x/2) dx.
    # For even n, the phase in eq. (6) cancels the i^n of j_n(iL/2), so
    # p_n = 2 sqrt(L nu_n) i_n(L/2), i_n modified spherical Bessel.
    y = L / 2
    out = []
    for n in orders:
        nu = mp.mpf(n) + mp.mpf("0.5")
        imod = mp.sqrt(mp.pi/(2*y)) * mp.besseli(n + mp.mpf("0.5"), y)
        out.append(2 * mp.sqrt(L * nu) * imod)
    return out


def build_head(L, T, N, panels, gauss_order, dps):
    mp.mp.dps = dps
    L = mp.mpf(L)
    T = mp.mpf(T)
    A, terms = prime_comb_mass_and_terms(L)
    beta = mp.log(T/(2*mp.pi)) - 1/T - A
    if beta <= 0:
        raise ValueError(f"beta must be positive; got {beta}")

    orders = [2*k for k in range(N)]
    p = pole_vector(L, orders)
    C = [[mp.mpf(0) for _ in range(N)] for _ in range(N)]

    nodes, weights = mp.gauss_quadrature(gauss_order, "legendre")
    width = T / panels
    half = width / 2

    t_start = time.time()
    sample_count = 0
    nmax = orders[-1]
    for panel in range(panels):
        mid = (mp.mpf(panel) + mp.mpf("0.5")) * width
        for q in range(gauss_order):
            t = mid + half * nodes[q]
            wt = half * weights[q]
            symbol = psi_symbol(t, L, terms) - beta
            js = spherical_j_all(t * L, nmax)
            F = []
            for n in orders:
                nu = mp.mpf(n) + mp.mpf("0.5")
                sign = -1 if ((n // 2) % 2) else 1
                F.append(sign * 2 * mp.sqrt(L * nu) * js[n])
            fac = wt * symbol / mp.pi
            for i in range(N):
                vi = fac * F[i]
                row = C[i]
                for j in range(i + 1):
                    row[j] += vi * F[j]
            sample_count += 1
        if (panel + 1) % max(1, panels // 20) == 0:
            elapsed = time.time() - t_start
            print(f"panel {panel+1}/{panels} elapsed={elapsed:.1f}s", flush=True)

    M = mp.matrix(N)
    for i in range(N):
        for j in range(i + 1):
            cij = C[i][j]
            val = cij + (beta if i == j else 0) + 2 * p[i] * p[j]
            M[i,j] = val
            M[j,i] = val

    eigvals, eigvecs = mp.eigsy(M)
    lam = eigvals[0]
    v = eigvecs[:,0]
    # Residual in the assembled midpoint matrix only (NOT a certified residual).
    res = mp.norm(M*v - lam*v)
    return {
        "status": "exploratory_independent_head_reconstruction_not_certificate",
        "arxiv": ARXIV_ID,
        "arxiv_main_tex_sha256": ARXIV_MAIN_TEX_SHA256,
        "L": mp.nstr(L, 50),
        "T_sharp": mp.nstr(T, 50),
        "N_even_modes": N,
        "orders": [orders[0], orders[-1]],
        "panels": panels,
        "gauss_order": gauss_order,
        "dps": dps,
        "quadrature_samples": sample_count,
        "A_L": mp.nstr(A, 60),
        "active_prime_powers": [n for n,_,_ in terms],
        "beta_star": mp.nstr(beta, 60),
        "lambda_min_head_midpoint": mp.nstr(lam, 80),
        "assembled_eigenpair_residual_l2": mp.nstr(res, 30),
        "warning": "No Bernstein ellipse, tail/coupling, or interval-rounding budget is applied here. Sign is exploratory only.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", required=True, help="decimal or expression token 'log5over2'")
    ap.add_argument("--T", default="200")
    ap.add_argument("--N", type=int, default=24)
    ap.add_argument("--panels", type=int, default=800)
    ap.add_argument("--gauss", type=int, default=32)
    ap.add_argument("--dps", type=int, default=50)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    mp.mp.dps = args.dps
    L = mp.log(5)/2 if args.L == "log5over2" else mp.mpf(args.L)
    result = build_head(L, mp.mpf(args.T), args.N, args.panels, args.gauss, args.dps)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
