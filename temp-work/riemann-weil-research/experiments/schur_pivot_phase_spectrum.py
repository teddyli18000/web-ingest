#!/usr/bin/env python3
"""Exploratory prime-phase analysis of the c=100 Schur-pivot oscillations.

The rigorous input is the strictly-positive Arb pivot sequence.  This script
uses only pivot midpoints to ask whether the large-N oscillation contains a
simple linear Fourier signature at frequencies log(q)/log(c), q=p^k<c.

A permutation max-statistic is included to avoid mistaking a dense candidate
frequency set for evidence.  This is a falsification-oriented diagnostic: a
null result is useful and rules out the simplest phase model.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def prime_powers_below(c: int):
    out = []
    for p in range(2, c):
        if not is_prime(p):
            continue
        q = p
        k = 1
        while q < c:
            out.append((q, p, k))
            q *= p
            k += 1
    out.sort()
    return out


def fold_frequency(a: float) -> float:
    a = a % 1.0
    return min(a, 1.0 - a)


def detrend_poly(ns: np.ndarray, ys: np.ndarray, degree: int):
    x = (ns - ns.mean()) / max(float(ns.std()), 1.0)
    coefs = np.polyfit(x, ys, degree)
    trend = np.polyval(coefs, x)
    return ys - trend, coefs.tolist(), trend


def trig_r2(ns: np.ndarray, residual: np.ndarray, freq: float) -> float:
    if freq <= 1e-12 or abs(freq - 0.5) <= 1e-12:
        X = np.column_stack([np.cos(2 * np.pi * freq * ns)])
    else:
        X = np.column_stack([
            np.cos(2 * np.pi * freq * ns),
            np.sin(2 * np.pi * freq * ns),
        ])
    beta, *_ = np.linalg.lstsq(X, residual, rcond=None)
    fitted = X @ beta
    denom = float(residual @ residual)
    return 0.0 if denom == 0 else max(0.0, min(1.0, float(fitted @ fitted) / denom))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--Nmin", type=int, default=32)
    ap.add_argument("--degree", type=int, default=2)
    ap.add_argument("--permutations", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260902)
    args = ap.parse_args()

    src = json.loads(Path(args.input).read_text())
    rows = [p for p in src["pivots"] if int(p["N"]) >= args.Nmin]
    ns = np.array([int(p["N"]) for p in rows], dtype=float)
    ys = np.array([-math.log10(float(p["pivot"]["mid"])) for p in rows], dtype=float)
    residual, poly, trend = detrend_poly(ns, ys, args.degree)
    residual -= residual.mean()

    c = int(src["c"])
    candidates = []
    seen = set()
    for q, p, k in prime_powers_below(c):
        base = math.log(q) / math.log(c)
        for h in (1, 2, 3):
            f = fold_frequency(h * base)
            key = round(f, 14)
            # Preserve one representative when exact prime-power/harmonic aliases occur.
            if key in seen or f < 1e-10:
                continue
            seen.add(key)
            candidates.append({"q": q, "p": p, "k": k, "harmonic": h, "frequency": f})

    for row in candidates:
        row["r2"] = trig_r2(ns, residual, row["frequency"])
    candidates.sort(key=lambda r: r["r2"], reverse=True)

    # Ordinary DFT bins as a model-free picture of the residual.
    fft = np.fft.rfft(residual)
    freqs = np.fft.rfftfreq(len(residual), d=1.0)
    power = np.abs(fft) ** 2
    dft_rows = []
    total_power = float(power[1:].sum())
    for i in range(1, len(freqs)):
        dft_rows.append({
            "bin": i,
            "frequency": float(freqs[i]),
            "power_fraction": 0.0 if total_power == 0 else float(power[i] / total_power),
        })
    dft_rows.sort(key=lambda r: r["power_fraction"], reverse=True)

    # Family-wise null: shuffle the residual and record the maximum R^2 over
    # the entire prime-power/harmonic candidate family.
    rng = np.random.default_rng(args.seed)
    null_max = np.empty(args.permutations, dtype=float)
    freqs_candidate = [r["frequency"] for r in candidates]
    for j in range(args.permutations):
        shuffled = rng.permutation(residual)
        null_max[j] = max(trig_r2(ns, shuffled, f) for f in freqs_candidate)
    observed_max = candidates[0]["r2"] if candidates else 0.0
    p_fwer = float((1 + np.sum(null_max >= observed_max)) / (args.permutations + 1))

    # Also report nearest DFT bin for each leading arithmetic candidate.
    resolution = 1.0 / len(residual)
    for row in candidates[:20]:
        idx = int(np.argmin(np.abs(freqs - row["frequency"])))
        row["nearest_dft_bin"] = int(idx)
        row["nearest_dft_frequency"] = float(freqs[idx])
        row["frequency_offset_in_bins"] = float(abs(freqs[idx] - row["frequency"]) / resolution)

    out = {
        "status": "exploratory_schur_prime_phase_spectrum",
        "warning": "Uses rigorous-pivot midpoints only. Fourier fits do not prove arithmetic causation.",
        "c": c,
        "Nmin": args.Nmin,
        "Nmax": int(ns[-1]),
        "sample_count": len(ns),
        "detrend_polynomial_degree": args.degree,
        "detrend_coefficients_scaled_N": poly,
        "residual_std": float(residual.std()),
        "frequency_resolution": resolution,
        "candidate_family_size": len(candidates),
        "permutations": args.permutations,
        "observed_max_candidate_r2": observed_max,
        "familywise_permutation_p_value": p_fwer,
        "null_max_r2_quantiles": {
            "q50": float(np.quantile(null_max, 0.50)),
            "q90": float(np.quantile(null_max, 0.90)),
            "q95": float(np.quantile(null_max, 0.95)),
            "q99": float(np.quantile(null_max, 0.99)),
        },
        "top_arithmetic_candidates": candidates[:30],
        "top_dft_bins": dft_rows[:20],
        "interpretation_rule": (
            "A small family-wise p-value would support a simple single-frequency prime-phase signature. "
            "A non-small value falsifies that simple model but not nonlinear Schur/prime interactions."
        ),
    }
    Path(args.output).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "status": out["status"],
        "observed_max_candidate_r2": observed_max,
        "familywise_permutation_p_value": p_fwer,
        "top_candidate": candidates[0] if candidates else None,
        "top_dft_bins": dft_rows[:5],
    }, indent=2))


if __name__ == "__main__":
    main()
