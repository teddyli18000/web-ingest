#!/usr/bin/env python3
"""Search around the live p007 record in exact C3 orbit space.

This deliberately explores *global smooth* C3-preserving deformations, rather than
repeating the local defect kicks reported as dead ends upstream.  The rationalized
live certificate is regrouped into 320 C3 orbits about z, averaged back to exact
C3 symmetry, and locally polished.  Random low-order m=0,3,6 tangent fields then
seed independent L-BFGS minimizations.

Requires numpy and scipy.  Usage:
  python search_c3_smooth.py /path/to/few-shots --seed 101 --trials 24 \
      --out result.json
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re

import numpy as np
from scipy.optimize import minimize

P007 = pathlib.Path("problems/p007-thomson-problem")
TWOPI = 2.0 * math.pi
PERIOD = TWOPI / 3.0


def find_live(root: pathlib.Path) -> tuple[float, pathlib.Path]:
    best = None
    for md in (root / P007 / "shots").glob("*/*/SHOT.md"):
        m = re.search(r'^claimed_score\s*=\s*"([0-9.]+)"', md.read_text(), re.M)
        if not m:
            continue
        item = (float(m.group(1)), md.parent)
        if best is None or item[0] < best[0]:
            best = item
    if best is None:
        raise RuntimeError("no merged p007 shot")
    return best


def load_cert(path: pathlib.Path) -> np.ndarray:
    raw = json.loads(path.read_text())
    p = np.array([[a / d, b / d, c / d] for a, b, c, d in raw["points"]], dtype=float)
    p /= np.linalg.norm(p, axis=1)[:, None]
    return p


def rz(points: np.ndarray, angle: float) -> np.ndarray:
    c, s = math.cos(angle), math.sin(angle)
    out = points.copy()
    out[:, 0] = c * points[:, 0] - s * points[:, 1]
    out[:, 1] = s * points[:, 0] + c * points[:, 1]
    return out


def c3_representatives(points: np.ndarray) -> np.ndarray:
    """Greedily group rationalized points with their ±120° partners."""
    n = len(points)
    unused = set(range(n))
    reps = []
    while unused:
        i = min(unused)
        x = points[i:i+1]
        ids = [i]
        aligned = [points[i]]
        for k in (1, 2):
            target = rz(x, k * PERIOD)[0]
            cand = np.fromiter(unused - set(ids), dtype=int)
            if len(cand) == 0:
                raise RuntimeError("broken C3 grouping")
            d2 = np.sum((points[cand] - target) ** 2, axis=1)
            j = int(cand[int(np.argmin(d2))])
            if float(np.min(d2)) > 1e-12:
                raise RuntimeError(f"C3 partner too far: {math.sqrt(float(np.min(d2)))}")
            ids.append(j)
            # rotate partner back to representative frame before averaging
            aligned.append(rz(points[j:j+1], -k * PERIOD)[0])
        for j in ids:
            unused.remove(j)
        y = np.mean(np.array(aligned), axis=0)
        y /= np.linalg.norm(y)
        reps.append(y)
    reps = np.array(reps)
    if len(reps) != 320:
        raise RuntimeError(f"expected 320 reps, got {len(reps)}")
    return reps


def xyz_to_vars(reps: np.ndarray) -> np.ndarray:
    theta = np.arccos(np.clip(reps[:, 2], -1.0, 1.0))
    phi = np.arctan2(reps[:, 1], reps[:, 0])
    return np.column_stack([theta, phi]).ravel()


def vars_to_full(v: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = v.reshape(-1, 2)
    th = a[:, 0]
    ph = a[:, 1]
    st, ct = np.sin(th), np.cos(th)
    all_x = []
    all_dth = []
    all_dph = []
    for k in range(3):
        q = ph + k * PERIOD
        cq, sq = np.cos(q), np.sin(q)
        x = np.column_stack([st * cq, st * sq, ct])
        dth = np.column_stack([ct * cq, ct * sq, -st])
        dph = np.column_stack([-st * sq, st * cq, np.zeros_like(st)])
        all_x.append(x)
        all_dth.append(dth)
        all_dph.append(dph)
    return np.vstack(all_x), np.vstack(all_dth), np.vstack(all_dph)


def fg(v: np.ndarray) -> tuple[float, np.ndarray]:
    x, dth, dph = vars_to_full(v)
    dots = x @ x.T
    r2 = np.maximum(2.0 - 2.0 * dots, 1e-300)
    np.fill_diagonal(r2, np.inf)
    invr = 1.0 / np.sqrt(r2)
    f = float(np.sum(np.triu(invr, 1)))
    w = invr / r2
    np.fill_diagonal(w, 0.0)
    gc = w @ x - np.sum(w, axis=1)[:, None] * x
    gt = np.sum(gc * dth, axis=1).reshape(3, -1).sum(axis=0)
    gp = np.sum(gc * dph, axis=1).reshape(3, -1).sum(axis=0)
    g = np.column_stack([gt, gp]).ravel()
    return f, g


def polish(v: np.ndarray, maxiter: int = 600):
    return minimize(fg, v, jac=True, method="L-BFGS-B",
                    options={"maxiter": maxiter, "gtol": 2e-9,
                             "ftol": 1e-15, "maxls": 40, "maxcor": 20})


def perturb(v: np.ndarray, rng: np.random.Generator, scale: float) -> np.ndarray:
    a = v.reshape(-1, 2).copy()
    th, ph = a[:, 0], a[:, 1]
    z = np.cos(th)
    # Smooth basis fields. m=3,6 preserves C3. Coefficients are normalized so
    # scale is roughly the RMS angular displacement in radians.
    basis = np.column_stack([
        np.ones_like(z), z, 0.5 * (3*z*z - 1),
        np.cos(3*ph), np.sin(3*ph),
        z*np.cos(3*ph), z*np.sin(3*ph),
        np.cos(6*ph), np.sin(6*ph),
    ])
    c1 = rng.normal(size=basis.shape[1])
    c2 = rng.normal(size=basis.shape[1])
    dth = basis @ c1
    # dphi contributes physical displacement sin(theta)*dphi, so scale that
    # quantity and avoid pole blow-up.
    tang_phi = basis @ c2
    rms = math.sqrt(float(np.mean(dth*dth + tang_phi*tang_phi)))
    dth *= scale / rms
    tang_phi *= scale / rms
    sinth = np.maximum(np.sin(th), 0.15)
    dph = tang_phi / sinth
    a[:, 0] = np.clip(th + dth, 1e-5, math.pi - 1e-5)
    a[:, 1] = ph + dph
    return a.ravel()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("few_shots")
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--trials", type=int, default=24)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    root = pathlib.Path(args.few_shots)
    live_score, shot = find_live(root)
    points = load_cert(shot / "certificate.json")
    reps = c3_representatives(points)
    v0 = xyz_to_vars(reps)
    base0, g0 = fg(v0)
    base_res = polish(v0, 1200)
    incumbent = float(base_res.fun)
    best_v = base_res.x.copy()
    rng = np.random.default_rng(args.seed)
    rows = []
    print(f"live_shot={shot.relative_to(root)} live_score={live_score:.10f}")
    print(f"exact_c3_rebuild={base0:.12f} grad_inf={np.max(np.abs(g0)):.3e}")
    print(f"polished_c3={incumbent:.12f} success={base_res.success} nit={base_res.nit}")

    scales = np.geomspace(0.008, 0.20, 9)
    for t in range(args.trials):
        scale = float(scales[t % len(scales)] * math.exp(rng.normal(0.0, 0.18)))
        start = perturb(base_res.x, rng, scale)
        start_e, _ = fg(start)
        res = polish(start)
        e = float(res.fun)
        if e < incumbent:
            incumbent = e
            best_v = res.x.copy()
        row = {"trial": t, "scale": scale, "start": start_e, "energy": e,
               "nit": int(res.nit), "success": bool(res.success)}
        rows.append(row)
        print(f"trial={t:02d} scale={scale:.5f} start={start_e:.9f} min={e:.12f} nit={res.nit} success={res.success}", flush=True)

    best_x, _, _ = vars_to_full(best_v)
    output = {
        "seed": args.seed,
        "trials": args.trials,
        "live_score": live_score,
        "live_shot": str(shot.relative_to(root)),
        "rebuild_energy": base0,
        "polished_record_energy": float(base_res.fun),
        "best_float_energy": incumbent,
        "improvement_vs_polished": float(base_res.fun) - incumbent,
        "trials_log": rows,
        "best_points": best_x.tolist() if incumbent < float(base_res.fun) - 1e-8 else None,
    }
    pathlib.Path(args.out).write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
