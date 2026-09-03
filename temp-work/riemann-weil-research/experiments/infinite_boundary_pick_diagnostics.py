#!/usr/bin/env python3
"""Explore infinite-boundary Pick diagnostics for the cutoff-free CvS even sector.

The cutoff-free full Weil matrix is built with the pinned Arb implementation.
Its even compression is congruent to the squared-grid confluent Loewner matrix
P_N=L_N(G_C) on x_k=k^2.  This script converts one high-precision Arb matrix
to a high-precision midpoint Loewner matrix and recursively maintains every
prefix inverse by the Schur block-inverse formula.

The reported capacities and Weyl disks are exploratory high-precision midpoint
diagnostics, not interval certificates.  The endpoint capacity is checked
against the independently meaningful Schur pivot at each recursive step.
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
    """Project full [-N,N] matrix to 1,sqrt(2)cos,... ordering in Arb."""
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


def arb_mid_to_mpf(x, digits: int) -> mp.mpf:
    return mp.mpf(x.mid().str(digits, radius=False))


def loewner_midpoint(E: arb_mat, N: int, digits: int) -> mp.matrix:
    """Undo E=D L D with D=diag(1,sqrt(2),...,sqrt(2))."""
    L = mp.matrix(N + 1, N + 1)
    root2 = mp.sqrt(2)
    scales = [mp.mpf(1)] + [root2] * N
    for i in range(N + 1):
        for j in range(N + 1):
            L[i, j] = arb_mid_to_mpf(E[i, j], digits) / (scales[i] * scales[j])
    return L


def mpstr(x, digits: int = 80) -> str:
    return mp.nstr(x, digits)


def log10_string(x: mp.mpf, digits: int = 50):
    if x <= 0:
        return None
    return mp.nstr(mp.log10(x), digits)


def recursive_inverse_extend(M: mp.matrix | None, b: mp.matrix | None, d: mp.mpf):
    """Append one row/column and return (new_inverse, Schur_pivot)."""
    if M is None:
        if d <= 0:
            raise RuntimeError(f"nonpositive initial pivot: {d}")
        out = mp.matrix(1, 1)
        out[0, 0] = 1 / d
        return out, d

    assert b is not None
    n = M.rows
    y = M * b
    s = d - (b.T * y)[0]
    if s <= 0:
        raise RuntimeError(f"nonpositive midpoint Schur pivot at appended N={n}: {s}")

    out = mp.matrix(n + 1, n + 1)
    invs = 1 / s
    for i in range(n):
        for j in range(n):
            out[i, j] = M[i, j] + y[i] * y[j] * invs
        out[i, n] = -y[i] * invs
        out[n, i] = out[i, n]
    out[n, n] = invs
    return out, s


def reconstruct_values(P: mp.matrix) -> list[mp.mpf]:
    """Use G_C(0)=0 and P[0,k]=(G(k^2)-G(0))/k^2."""
    N = P.rows - 1
    w = [mp.mpf(0)] * (N + 1)
    for k in range(1, N + 1):
        w[k] = mp.mpf(k * k) * P[0, k]
    return w


def value_disk(M: mp.matrix, values: list[mp.mpf], z0: mp.mpc):
    """Weyl value disk from the augmented upper-half-plane Pick matrix."""
    n = M.rows
    if len(values) != n:
        raise ValueError("value length mismatch")
    q = mp.im(z0)
    if q <= 0:
        raise ValueError("z0 must be in upper half-plane")

    a = mp.matrix(n, 1)
    c = mp.matrix(n, 1)
    for j in range(n):
        x = mp.mpf(j * j)
        den = x - mp.conj(z0)
        a[j] = 1 / den
        c[j] = values[j] / den

    ya = M * a
    yc = M * c
    A = mp.fsum(mp.conj(a[j]) * ya[j] for j in range(n))
    B = mp.fsum(mp.conj(a[j]) * yc[j] for j in range(n))
    C = mp.fsum(mp.conj(c[j]) * yc[j] for j in range(n))

    A = mp.re(A)
    C = mp.re(C)
    if A <= 0:
        raise RuntimeError(f"nonpositive A in value disk: {A}")

    shift = mp.mpc(0, 1) / (2 * q)
    discriminant = abs(B - shift) ** 2 - A * C
    scale = max(mp.mpf(1), abs(B - shift) ** 2, abs(A * C))
    tolerance = mp.power(10, -max(30, mp.mp.dps // 2)) * scale
    clipped = False
    if discriminant < 0:
        if abs(discriminant) <= tolerance:
            discriminant = mp.mpf(0)
            clipped = True
        else:
            raise RuntimeError(
                f"negative value-disk discriminant beyond tolerance at z0={z0}: {discriminant}"
            )

    center = (mp.conj(B) + shift) / A
    radius = mp.sqrt(discriminant) / A
    return {
        "center_re": mpstr(mp.re(center), 100),
        "center_im": mpstr(mp.im(center), 100),
        "radius": mpstr(radius, 100),
        "log10_radius": log10_string(radius, 60),
        "discriminant": mpstr(discriminant, 100),
        "discriminant_clipped_to_zero": clipped,
        "A": mpstr(A, 100),
        "B_re": mpstr(mp.re(B), 100),
        "B_im": mpstr(mp.im(B), 100),
        "C": mpstr(C, 100),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--upstream-script", type=Path, required=True)
    p.add_argument("--upstream-commit", required=True)
    p.add_argument("--c", type=int, required=True)
    p.add_argument("--Nmax", type=int, default=48)
    p.add_argument("--prec", type=int, default=3000, help="Arb build precision in bits")
    p.add_argument("--dps", type=int, default=700, help="midpoint diagnostic precision")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    if args.Nmax < 4:
        raise ValueError("Nmax must be >=4")
    mp.mp.dps = args.dps

    module = load_upstream(args.upstream_script)
    A_full, _ = module.build_arb_tau(args.c, args.Nmax, args.prec)
    E = project_even(A_full, args.Nmax)
    P = loewner_midpoint(E, args.Nmax, args.dps + 40)
    values_all = reconstruct_values(P)

    fixed_js = [0, 1, 2, 3]
    selected = {4, 8, 12, 16, 24, 32, 48, args.Nmax}
    selected = {n for n in selected if 0 <= n <= args.Nmax}
    zpoints = {
        "i": mp.mpc(0, 1),
        "2i": mp.mpc(0, 2),
        "1_plus_i": mp.mpc(1, 1),
    }

    M = None
    rows = []
    prior_disks = {}
    nesting_checks = []

    for n in range(args.Nmax + 1):
        if n == 0:
            M, pivot = recursive_inverse_extend(None, None, P[0, 0])
        else:
            b = mp.matrix(n, 1)
            for j in range(n):
                b[j] = P[j, n]
            M, pivot = recursive_inverse_extend(M, b, P[n, n])

        endpoint_capacity = 1 / M[n, n]
        endpoint_relerr = abs(endpoint_capacity - pivot) / max(abs(pivot), mp.mpf(1e-999))
        if endpoint_relerr > mp.power(10, -max(30, args.dps // 3)):
            raise RuntimeError(
                f"endpoint capacity / Schur pivot mismatch at N={n}: relerr={endpoint_relerr}"
            )

        if n not in selected:
            continue

        capacities = {}
        for j in fixed_js:
            if j <= n:
                cap = 1 / M[j, j]
                capacities[str(j)] = {
                    "capacity": mpstr(cap, 100),
                    "log10_capacity": log10_string(cap, 60),
                }

        values = values_all[: n + 1]
        disks = {}
        for name, z0 in zpoints.items():
            disk = value_disk(M, values, z0)
            disks[name] = disk
            if name in prior_disks:
                old = prior_disks[name]
                old_center = mp.mpc(old["center_re"], old["center_im"])
                new_center = mp.mpc(disk["center_re"], disk["center_im"])
                old_radius = mp.mpf(old["radius"])
                new_radius = mp.mpf(disk["radius"])
                nesting_margin = old_radius - (abs(new_center - old_center) + new_radius)
                nesting_checks.append({
                    "z0": name,
                    "N_from": old["N"],
                    "N_to": n,
                    "nesting_margin": mpstr(nesting_margin, 80),
                    "nested_with_midpoint_tolerance": bool(
                        nesting_margin >= -mp.power(10, -max(25, args.dps // 3))
                    ),
                })
            prior_disks[name] = {**disk, "N": n}

        rows.append({
            "N": n,
            "schur_pivot_midpoint": mpstr(pivot, 100),
            "log10_schur_pivot_midpoint": log10_string(pivot, 60),
            "endpoint_capacity": mpstr(endpoint_capacity, 100),
            "endpoint_capacity_relative_error_vs_pivot": mpstr(endpoint_relerr, 50),
            "fixed_node_slack_capacities": capacities,
            "value_disks": disks,
        })

    payload = {
        "status": "exploratory_infinite_boundary_pick_diagnostics",
        "warning": (
            "The cutoff-free source matrix is built in Arb, but inverse capacities and value disks "
            "are computed from high-precision interval midpoints. They are diagnostics, not interval certificates."
        ),
        "upstream_commit": args.upstream_commit,
        "c": args.c,
        "Nmax": args.Nmax,
        "arb_build_prec_bits": args.prec,
        "midpoint_dps": args.dps,
        "nodes": "x_k=k^2",
        "matrix": "P_N=L_N(G_C)=D_N^{-1} E_N D_N^{-1}",
        "fixed_capacity_definition": "c_{j,N}=1/(P_N^{-1})_{jj}",
        "value_disk_points": {k: str(v) for k, v in zpoints.items()},
        "rows": rows,
        "nesting_checks": nesting_checks,
        "all_reported_disk_nesting_checks_pass": all(
            item["nested_with_midpoint_tolerance"] for item in nesting_checks
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
