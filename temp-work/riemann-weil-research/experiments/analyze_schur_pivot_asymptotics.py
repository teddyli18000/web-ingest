#!/usr/bin/env python3
"""Exploratory asymptotic diagnostics for rigorous even-sector Schur pivots.

The input pivots themselves come from Arb interval LDL^T certificates.  This
script only analyzes their reported midpoints; all fits are conjecture
generators, not proofs.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import median


def linear_fit(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return my, 0.0, float("inf")
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    rmse = math.sqrt(sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys)) / n)
    return a, b, rmse


def grid_plateau_fit(ns, ys, kind):
    best = None
    if kind == "inverse_power":
        params = [0.05 * k for k in range(2, 161)]  # p = 0.10 ... 8.00
        transform = lambda n, p: n ** (-p)
    elif kind == "exponential":
        params = [0.001 * k for k in range(1, 501)]  # k = .001 ... .500
        transform = lambda n, k: math.exp(-k * n)
    else:
        raise ValueError(kind)
    for p in params:
        xs = [transform(n, p) for n in ns]
        a, b, rmse = linear_fit(xs, ys)
        row = {"parameter": p, "asymptote_y": a, "amplitude": b, "rmse": rmse}
        if best is None or rmse < best["rmse"]:
            best = row
    return best


def summarize_window(rows, n0):
    tail = [r for r in rows if r["N"] >= n0]
    ns = [r["N"] for r in tail]
    ss = [r["s"] for r in tail]
    ys = [r["y"] for r in tail]
    deltas = [ys[i] - ys[i - 1] for i in range(1, len(ys))]
    positive_deltas = sum(d > 0 for d in deltas)
    negative_deltas = sum(d < 0 for d in deltas)

    models = {}
    transforms = {
        "linear_N": [float(n) for n in ns],
        "power_law_logN": [math.log(n) for n in ns],
        "stretched_sqrtN": [math.sqrt(n) for n in ns],
        "stretched_cuberootN": [n ** (1 / 3) for n in ns],
    }
    for name, xs in transforms.items():
        a, b, rmse = linear_fit(xs, ys)
        models[name] = {"intercept": a, "slope": b, "rmse": rmse}
    models["plateau_inverse_power"] = grid_plateau_fit(ns, ys, "inverse_power")
    models["plateau_exponential"] = grid_plateau_fit(ns, ys, "exponential")

    ranked = sorted((v["rmse"], k) for k, v in models.items())
    return {
        "N_min": n0,
        "count": len(tail),
        "pivot_min": min(ss),
        "pivot_min_at_N": tail[ss.index(min(ss))]["N"],
        "pivot_max": max(ss),
        "pivot_max_at_N": tail[ss.index(max(ss))]["N"],
        "y_last": ys[-1],
        "y_min": min(ys),
        "y_max": max(ys),
        "delta_y_median": median(deltas) if deltas else None,
        "delta_y_last": deltas[-1] if deltas else None,
        "delta_y_abs_max": max(map(abs, deltas)) if deltas else None,
        "delta_y_positive_count": positive_deltas,
        "delta_y_negative_count": negative_deltas,
        "models": models,
        "model_ranking_by_rmse": [{"model": k, "rmse": rmse} for rmse, k in ranked],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    src = json.loads(Path(args.input).read_text())
    pivots = src["pivots"]
    rows = []
    for p in pivots:
        s = float(p["pivot"]["mid"])
        if not (s > 0):
            raise SystemExit(f"nonpositive midpoint at N={p['N']}: {s}")
        rows.append({"N": int(p["N"]), "s": s, "y": -math.log10(s)})

    nmax = rows[-1]["N"]
    windows = [n for n in (16, 24, 32, 40, 48, 60, 70, 80, 90, 100) if n <= nmax - 5]
    out = {
        "status": "exploratory_midpoint_asymptotic_diagnostic",
        "warning": "All fitted asymptotics use midpoint values of separately rigorous positive Arb pivot intervals; fits are not proofs.",
        "source_status": src.get("status"),
        "c": src["c"],
        "Nmax": nmax,
        "all_source_pivots_have_strict_positive_lower_bound": all(float(p["pivot"]["lower"]) > 0 for p in pivots),
        "cross_precision_prefix_checks": src.get("cross_precision_prefix_checks", []),
        "tail_windows": [summarize_window(rows, n0) for n0 in windows],
        "last_41": rows[-41:],
        "selected": [rows[n] for n in (0, 1, 2, 4, 8, 16, 24, 32, 40, 48, 60, 70, 80, 90, 100, 110, 120) if n <= nmax],
    }
    Path(args.output).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "c": out["c"],
        "Nmax": nmax,
        "strict_positive_source": out["all_source_pivots_have_strict_positive_lower_bound"],
        "tail80_best": next((w["model_ranking_by_rmse"][0] for w in out["tail_windows"] if w["N_min"] == 80), None),
        "tail100_best": next((w["model_ranking_by_rmse"][0] for w in out["tail_windows"] if w["N_min"] == 100), None),
        "last": rows[-1],
    }, indent=2))


if __name__ == "__main__":
    main()
