#!/usr/bin/env python3
"""Exploratory Weyl-disk collapse diagnostic for squared-node CvS boundary jets.

This does NOT invent a new determinacy criterion.  It implements the classical
Agler--Young boundary Julia reduction / linear-fractional parametrization and
measures, at one fixed point z in the upper half-plane, the value disk allowed
by the first n boundary Hermite conditions.

Input data are recovered from a pinned cutoff-free Arb CvS matrix via the exact
congruence

    E_N = D_N L_N(G_C) D_N,

on squared nodes x_k=k^2.  We set the irrelevant additive gauge G_C(0)=0.
All reported Weyl radii are high-precision midpoint diagnostics; the input
matrix itself is built with Arb, but the Julia reductions are not interval
certificates.
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
    E = arb_mat(N + 1, N + 1)
    root2 = arb(2).sqrt()
    center = N
    E[0, 0] = A[center, center]
    for k in range(1, N + 1):
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


def arb_mid_mpf(x: arb, digits: int) -> mp.mpf:
    return mp.mpf(x.mid().str(digits, radius=False))


def recover_squared_grid_jets(E: arb_mat, N: int, digits: int):
    """Recover x_k, G(x_k), G'(x_k) with G(0)=0 from E=DLD."""
    root2 = mp.sqrt(2)
    x = [mp.mpf(k * k) for k in range(N + 1)]
    w = [mp.mpf(0)] * (N + 1)
    v = [mp.mpf(0)] * (N + 1)
    v[0] = arb_mid_mpf(E[0, 0], digits)
    for k in range(1, N + 1):
        e0k = arb_mid_mpf(E[0, k], digits)
        ekk = arb_mid_mpf(E[k, k], digits)
        w[k] = x[k] * e0k / root2
        v[k] = ekk / 2
    return x, w, v


def matmul2(A, B):
    return [
        [A[0][0] * B[0][0] + A[0][1] * B[1][0],
         A[0][0] * B[0][1] + A[0][1] * B[1][1]],
        [A[1][0] * B[0][0] + A[1][1] * B[1][0],
         A[1][0] * B[0][1] + A[1][1] * B[1][1]],
    ]


def normalize2(M):
    scale = max(abs(M[i][j]) for i in range(2) for j in range(2))
    if scale == 0:
        raise RuntimeError("zero transfer matrix")
    return [[M[i][j] / scale for j in range(2)] for i in range(2)]


def disk_geometry(M):
    """Return center/radius of LFT image of upper half-plane.

    For f=(a h+b)/(c h+d), Im(h)>=0 becomes
        A |f|^2 + Im(K f) + C >= 0,
    where A=-Im(d conj(c)), K=d conj(a)-conj(b)c,
    C=-Im(b conj(a)).  In our Pick parametrizations A<0 and this is a disk.
    The radius also equals |det M|/(2|A|).
    """
    a, b = M[0]
    c, d = M[1]
    A = -mp.im(d * mp.conj(c))
    K = d * mp.conj(a) - mp.conj(b) * c
    C = -mp.im(b * mp.conj(a))
    det = a * d - b * c
    if A == 0:
        return None
    center = -1j * mp.conj(K) / (2 * A)
    radius_det = abs(det) / (2 * abs(A))
    radius_sq = abs(K) ** 2 / (4 * A ** 2) - C / A
    radius_quad = mp.sqrt(max(mp.mpf(0), mp.re(radius_sq)))
    return {
        "A": A,
        "center": center,
        "radius": radius_det,
        "radius_quad": radius_quad,
        "radius_formula_relerr": abs(radius_det - radius_quad) / max(radius_det, mp.mpf("1e-999999")),
    }


def lft(M, h):
    a, b = M[0]
    c, d = M[1]
    return (a * h + b) / (c * h + d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream-script", type=Path, required=True)
    ap.add_argument("--upstream-commit", required=True)
    ap.add_argument("--c", type=int, required=True)
    ap.add_argument("--Nmax", type=int, required=True)
    ap.add_argument("--prec", type=int, required=True)
    ap.add_argument("--dps", type=int, required=True)
    ap.add_argument("--z-re", default="0")
    ap.add_argument("--z-im", default="1")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    mp.mp.dps = args.dps
    module = load_upstream(args.upstream_script)
    A_full, _ = module.build_arb_tau(args.c, args.Nmax, args.prec)
    E = project_even(A_full, args.Nmax)
    x, w, v = recover_squared_grid_jets(E, args.Nmax, args.dps + 30)

    wr = list(w)
    vr = list(v)
    z = mp.mpc(args.z_re, args.z_im)
    M = [[mp.mpc(1), mp.mpc(0)], [mp.mpc(0), mp.mpc(1)]]
    rows = []

    for k in range(args.Nmax + 1):
        s = wr[k]
        t = vr[k]
        if not (t > 0):
            raise RuntimeError(f"nonpositive reduced derivative at step {k}: {mp.nstr(t, 50)}")
        dz = z - x[k]
        Ak = [
            [s * t * dz, -t * dz - s],
            [t * dz, -1],
        ]
        M = normalize2(matmul2(M, Ak))
        geom = disk_geometry(M)
        if geom is None:
            raise RuntimeError(f"half-plane rather than finite disk at step {k}")
        center = geom["center"]
        radius = geom["radius"]
        sample = lft(M, 1j)
        inside_ratio = abs(sample - center) / radius
        rows.append({
            "N": k,
            "reduced_value_s": mp.nstr(s, 80),
            "reduced_derivative_t": mp.nstr(t, 80),
            "log10_reduced_derivative": mp.nstr(mp.log10(t), 40),
            "disk_center_re": mp.nstr(mp.re(center), 60),
            "disk_center_im": mp.nstr(mp.im(center), 60),
            "disk_radius": mp.nstr(radius, 80),
            "log10_disk_radius": mp.nstr(mp.log10(radius), 50),
            "sample_h_i_inside_ratio": mp.nstr(inside_ratio, 40),
            "radius_formula_relerr": mp.nstr(geom["radius_formula_relerr"], 20),
        })

        # Julia-reduce the remaining boundary data at x_k.
        for j in range(k + 1, args.Nmax + 1):
            dx = x[j] - x[k]
            dw = wr[j] - s
            if dw == 0:
                raise RuntimeError(f"equal reduced values at k={k}, j={j}; infinity branch not implemented")
            old_v = vr[j]
            wr[j] = -1 / dw + 1 / (t * dx)
            vr[j] = old_v / (dw * dw) - 1 / (t * dx * dx)

    payload = {
        "status": "exploratory_boundary_pick_weyl_disk",
        "warning": (
            "The cutoff-free CvS matrix is built with Arb, but squared-grid jets, Julia reductions, "
            "transfer matrices, and disk radii use high-precision midpoints. This is a diagnostic, "
            "not an interval determinacy certificate."
        ),
        "theory": (
            "Agler-Young boundary Julia reductions; all finite solutions are an LFT of a free Pick "
            "parameter. At fixed z, the solution values form a nested disk. Infinite-data uniqueness "
            "requires these disks to collapse (limit-point/determinate case)."
        ),
        "upstream_commit": args.upstream_commit,
        "c": args.c,
        "Nmax": args.Nmax,
        "prec_bits": args.prec,
        "mpmath_dps": args.dps,
        "z_test": [args.z_re, args.z_im],
        "gauge": "G_C(0)=0; additive real constants do not change the Loewner matrix or disk radii",
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    selected = [r for r in rows if r["N"] in {0,1,2,4,8,12,16,24,32,48,64,80}]
    print(json.dumps({"c": args.c, "selected": selected, "last": rows[-1]}, indent=2))


if __name__ == "__main__":
    main()
