#!/usr/bin/env python3
"""Transfer a nearby Cambridge Thomson configuration to N=960 and relax it.

For source N>960, greedily remove the point with the largest per-particle energy
contribution.  For source N<960, add points at approximate minima of the potential
created by the existing points.  Then perform a full unconstrained angular L-BFGS
relaxation at N=960.

This is intentionally a direct test of the neighboring-size propagation idea in
Amore & Wales (2026), against the newer Few Shots C3 record.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import pathlib
import urllib.request

import numpy as np
from scipy.optimize import minimize

TARGET = 960
PI = math.pi


def fetch_ccd(n: int) -> np.ndarray:
    url = f"https://www-wales.ch.cam.ac.uk/~wales/CCD/Thomson/site/s_1/dat/points_{n}_1.dat"
    with urllib.request.urlopen(url, timeout=60) as r:
        text = r.read().decode("utf-8")
    pts = np.loadtxt(io.StringIO(text), dtype=float)
    if pts.shape != (n, 3):
        raise RuntimeError(f"unexpected CCD shape for N={n}: {pts.shape}")
    pts /= np.linalg.norm(pts, axis=1)[:, None]
    return pts


def xyz_to_vars(x: np.ndarray) -> np.ndarray:
    th = np.arccos(np.clip(x[:, 2], -1.0, 1.0))
    ph = np.arctan2(x[:, 1], x[:, 0])
    return np.column_stack([th, ph]).ravel()


def vars_to_xyz(v: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = v.reshape(-1, 2)
    th, ph = a[:, 0], a[:, 1]
    st, ct = np.sin(th), np.cos(th)
    cp, sp = np.cos(ph), np.sin(ph)
    x = np.column_stack([st*cp, st*sp, ct])
    dth = np.column_stack([ct*cp, ct*sp, -st])
    dph = np.column_stack([-st*sp, st*cp, np.zeros_like(st)])
    return x, dth, dph


def cart_energy_contrib(x: np.ndarray) -> tuple[float, np.ndarray]:
    dots = np.clip(x @ x.T, -1.0, 1.0)
    r2 = np.maximum(2.0 - 2.0*dots, 1e-300)
    np.fill_diagonal(r2, np.inf)
    inv = 1.0 / np.sqrt(r2)
    e = float(np.sum(np.triu(inv, 1)))
    return e, np.sum(inv, axis=1)


def fg(v: np.ndarray) -> tuple[float, np.ndarray]:
    x, dth, dph = vars_to_xyz(v)
    dots = np.clip(x @ x.T, -1.0, 1.0)
    r2 = np.maximum(2.0 - 2.0*dots, 1e-300)
    np.fill_diagonal(r2, np.inf)
    inv = 1.0 / np.sqrt(r2)
    f = float(np.sum(np.triu(inv, 1)))
    w = inv / r2
    np.fill_diagonal(w, 0.0)
    gc = w @ x - np.sum(w, axis=1)[:, None] * x
    gt = np.sum(gc*dth, axis=1)
    gp = np.sum(gc*dph, axis=1)
    return f, np.column_stack([gt, gp]).ravel()


def relax(x: np.ndarray, maxiter: int = 1800):
    v0 = xyz_to_vars(x)
    bounds = [(1e-7, PI-1e-7), (None, None)] * len(x)
    return minimize(fg, v0, jac=True, method="L-BFGS-B", bounds=bounds,
                    options={"maxiter": maxiter, "gtol": 3e-9,
                             "ftol": 1e-15, "maxls": 40, "maxcor": 20})


def fibonacci_sphere(n: int) -> np.ndarray:
    i = np.arange(n, dtype=float) + 0.5
    z = 1.0 - 2.0*i/n
    phi = (PI * (3.0 - math.sqrt(5.0))) * i
    r = np.sqrt(np.maximum(0.0, 1.0-z*z))
    return np.column_stack([r*np.cos(phi), r*np.sin(phi), z])


def potential_at_angles(v: np.ndarray, x: np.ndarray) -> tuple[float, np.ndarray]:
    th, ph = float(v[0]), float(v[1])
    st, ct, cp, sp = math.sin(th), math.cos(th), math.cos(ph), math.sin(ph)
    y = np.array([st*cp, st*sp, ct])
    dth = np.array([ct*cp, ct*sp, -st])
    dph = np.array([-st*sp, st*cp, 0.0])
    d = y[None, :] - x
    r2 = np.sum(d*d, axis=1)
    inv = 1.0 / np.sqrt(r2)
    f = float(np.sum(inv))
    gc = np.sum(-d * (inv/r2)[:, None], axis=0)
    return f, np.array([float(gc@dth), float(gc@dph)])


def add_low_potential_point(x: np.ndarray, samples: int = 24000) -> np.ndarray:
    cand = fibonacci_sphere(samples)
    best_val = float("inf")
    best = None
    for lo in range(0, samples, 600):
        c = cand[lo:lo+600]
        dots = np.clip(c @ x.T, -1.0, 1.0)
        vals = np.sum(1.0 / np.sqrt(np.maximum(2.0 - 2.0*dots, 1e-15)), axis=1)
        j = int(np.argmin(vals))
        if float(vals[j]) < best_val:
            best_val = float(vals[j])
            best = c[j]
    th0 = math.acos(float(np.clip(best[2], -1.0, 1.0)))
    ph0 = math.atan2(float(best[1]), float(best[0]))
    res = minimize(lambda v: potential_at_angles(v, x), np.array([th0, ph0]), jac=True,
                   method="L-BFGS-B", bounds=[(1e-7, PI-1e-7), (None, None)],
                   options={"gtol": 1e-10, "ftol": 1e-15, "maxiter": 300})
    th, ph = res.x
    y = np.array([math.sin(th)*math.cos(ph), math.sin(th)*math.sin(ph), math.cos(th)])
    return np.vstack([x, y])


def resize_to_960(x: np.ndarray) -> np.ndarray:
    while len(x) > TARGET:
        e, contrib = cart_energy_contrib(x)
        j = int(np.argmax(contrib))
        print(f"remove n={len(x)} index={j} energy={e:.9f} contrib={contrib[j]:.9f}", flush=True)
        x = np.delete(x, j, axis=0)
    while len(x) < TARGET:
        e, _ = cart_energy_contrib(x)
        print(f"add n={len(x)} energy={e:.9f}", flush=True)
        x = add_low_potential_point(x)
    return x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-n", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    x = fetch_ccd(args.source_n)
    e0, _ = cart_energy_contrib(x)
    print(f"source_n={args.source_n} source_energy={e0:.12f}")
    x = resize_to_960(x)
    e1, _ = cart_energy_contrib(x)
    print(f"resized_energy={e1:.12f}")
    res = relax(x)
    ef = float(res.fun)
    print(f"relaxed_energy={ef:.12f} nit={res.nit} success={res.success} message={res.message}")
    best_x, _, _ = vars_to_xyz(res.x)
    out = {"source_n": args.source_n, "source_energy": e0,
           "resized_energy": e1, "relaxed_energy": ef,
           "nit": int(res.nit), "success": bool(res.success),
           "points": best_x.tolist() if ef < 444368.45 else None}
    pathlib.Path(args.out).write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
