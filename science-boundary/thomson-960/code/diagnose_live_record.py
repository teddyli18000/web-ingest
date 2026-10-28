#!/usr/bin/env python3
"""Diagnose the live merged Few Shots p007 record.

Usage:
  python diagnose_live_record.py /path/to/few-shots > diagnostic.txt

The script discovers the minimum claimed score among merged p007 shots, loads the
certificate, recomputes floating energy/gradient, and tests candidate C3 axes.
It uses only Python's standard library so the diagnostic itself is easy to rerun.
"""

from __future__ import annotations

import json
import math
import pathlib
import re
import sys


P007 = pathlib.Path("problems/p007-thomson-problem")


def parse_claimed_score(path: pathlib.Path) -> float:
    text = path.read_text(encoding="utf-8")
    m = re.search(r'^claimed_score\s*=\s*"([0-9.]+)"', text, re.M)
    if not m:
        raise ValueError(f"no claimed_score in {path}")
    return float(m.group(1))


def live_shot(root: pathlib.Path) -> tuple[float, pathlib.Path]:
    shots = root / P007 / "shots"
    best = None
    for shot_md in shots.glob("*/*/SHOT.md"):
        score = parse_claimed_score(shot_md)
        item = (score, shot_md.parent)
        if best is None or item[0] < best[0]:
            best = item
    if best is None:
        raise RuntimeError("no merged p007 shots found")
    return best


def load_points(cert: pathlib.Path) -> list[list[float]]:
    raw = json.loads(cert.read_text(encoding="utf-8"))
    pts = []
    for a, b, c, d in raw["points"]:
        pts.append([a / d, b / d, c / d])
    return pts


def energy_gradient(points: list[list[float]]) -> tuple[float, list[list[float]]]:
    n = len(points)
    g = [[0.0, 0.0, 0.0] for _ in range(n)]
    e = 0.0
    for i in range(n):
        xi = points[i]
        for j in range(i + 1, n):
            xj = points[j]
            dx = xi[0] - xj[0]
            dy = xi[1] - xj[1]
            dz = xi[2] - xj[2]
            r2 = dx * dx + dy * dy + dz * dz
            invr = 1.0 / math.sqrt(r2)
            e += invr
            invr3 = invr / r2
            # derivative of 1/r wrt xi is -(xi-xj)/r^3
            gx = -dx * invr3
            gy = -dy * invr3
            gz = -dz * invr3
            g[i][0] += gx
            g[i][1] += gy
            g[i][2] += gz
            g[j][0] -= gx
            g[j][1] -= gy
            g[j][2] -= gz
    # Project to tangent planes.
    for i, x in enumerate(points):
        dot = g[i][0] * x[0] + g[i][1] * x[1] + g[i][2] * x[2]
        g[i][0] -= dot * x[0]
        g[i][1] -= dot * x[1]
        g[i][2] -= dot * x[2]
    return e, g


def covariance(points: list[list[float]]) -> list[list[float]]:
    m = [[0.0] * 3 for _ in range(3)]
    for x in points:
        for a in range(3):
            for b in range(3):
                m[a][b] += x[a] * x[b]
    return m


def jacobi_eigh3(a0: list[list[float]]) -> tuple[list[float], list[list[float]]]:
    a = [row[:] for row in a0]
    v = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    for _ in range(64):
        p, q = max(((0, 1), (0, 2), (1, 2)), key=lambda ij: abs(a[ij[0]][ij[1]]))
        if abs(a[p][q]) < 1e-15:
            break
        phi = 0.5 * math.atan2(2.0 * a[p][q], a[q][q] - a[p][p])
        c, s = math.cos(phi), math.sin(phi)
        for k in range(3):
            apk, aqk = a[p][k], a[q][k]
            a[p][k] = c * apk - s * aqk
            a[q][k] = s * apk + c * aqk
        for k in range(3):
            akp, akq = a[k][p], a[k][q]
            a[k][p] = c * akp - s * akq
            a[k][q] = s * akp + c * akq
        for k in range(3):
            vkp, vkq = v[k][p], v[k][q]
            v[k][p] = c * vkp - s * vkq
            v[k][q] = s * vkp + c * vkq
    vals = [a[i][i] for i in range(3)]
    vecs = [[v[r][i] for r in range(3)] for i in range(3)]
    order = sorted(range(3), key=lambda i: vals[i])
    return [vals[i] for i in order], [vecs[i] for i in order]


def rotate(v: list[float], axis: list[float], angle: float) -> list[float]:
    ax, ay, az = axis
    vx, vy, vz = v
    c, s = math.cos(angle), math.sin(angle)
    dot = ax * vx + ay * vy + az * vz
    cx = ay * vz - az * vy
    cy = az * vx - ax * vz
    cz = ax * vy - ay * vx
    return [
        vx * c + cx * s + ax * dot * (1 - c),
        vy * c + cy * s + ay * dot * (1 - c),
        vz * c + cz * s + az * dot * (1 - c),
    ]


def symmetry_error(points: list[list[float]], axis: list[float]) -> tuple[float, float]:
    norm = math.sqrt(sum(t * t for t in axis))
    axis = [t / norm for t in axis]
    sum2 = 0.0
    worst = 0.0
    angle = 2.0 * math.pi / 3.0
    for x in points:
        y = rotate(x, axis, angle)
        best2 = float("inf")
        for z in points:
            d2 = (y[0] - z[0]) ** 2 + (y[1] - z[1]) ** 2 + (y[2] - z[2]) ** 2
            if d2 < best2:
                best2 = d2
        sum2 += best2
        worst = max(worst, math.sqrt(best2))
    return math.sqrt(sum2 / len(points)), worst


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: diagnose_live_record.py /path/to/few-shots")
    root = pathlib.Path(sys.argv[1]).resolve()
    score, shot = live_shot(root)
    cert = shot / "certificate.json"
    points = load_points(cert)
    e, g = energy_gradient(points)
    norms = [math.sqrt(sum(t * t for t in gi)) for gi in g]
    vals, vecs = jacobi_eigh3(covariance(points))

    print(f"shot={shot.relative_to(root)}")
    print(f"claimed_score={score:.10f}")
    print(f"n={len(points)}")
    print(f"double_energy={e:.15f}")
    print(f"score_minus_double={score - e:.3e}")
    print(f"tangent_grad_rms={math.sqrt(sum(x*x for x in norms)/len(norms)):.6e}")
    print(f"tangent_grad_max={max(norms):.6e}")
    print("cov_eigenvalues=" + " ".join(f"{x:.12f}" for x in vals))
    axes = [
        ("x", [1.0, 0.0, 0.0]),
        ("y", [0.0, 1.0, 0.0]),
        ("z", [0.0, 0.0, 1.0]),
    ] + [(f"cov_eig{i}", vecs[i]) for i in range(3)]
    for name, axis in axes:
        rms, worst = symmetry_error(points, axis)
        print(f"c3_axis={name} axis={' '.join(f'{t:.12g}' for t in axis)} rms_nn={rms:.6e} max_nn={worst:.6e}")


if __name__ == "__main__":
    main()
