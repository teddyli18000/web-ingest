#!/usr/bin/env python3
"""Rigorous Arb Rayleigh quotients for the sine-power/binomial source family.

For m >= 1, the source T_m(s) = sin(pi*s)^(2m) has full Fourier weights

    w_k = (-1)^k binom(2m, m-k),  |k| <= m,

up to the irrelevant common 4^(-m) factor.  This script contracts those exact
integer weights against the pinned cutoff-free CvS/Groskin Arb matrix and
reports a rigorous interval for the Rayleigh quotient w^T A w / w^T w.

A negative certified interval would be qualitatively important; a positive
interval is only an upper bound on the minimum of the corresponding finite
restriction and does not prove Weil positivity.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path

from flint import arb


def load_upstream(path: Path):
    spec = importlib.util.spec_from_file_location("groskin_arb_ldlt", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load upstream verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def interval_payload(x: arb, digits: int = 70) -> dict:
    return {
        "lower": str(x.lower()),
        "mid": x.mid().str(digits, radius=False),
        "upper": str(x.upper()),
        "rad": str(x.rad()),
    }


def midpoint_log10(x: arb, digits: int = 50) -> str | None:
    mid = x.mid()
    if mid <= 0:
        return None
    value = mid.log() / arb(10).log()
    return value.mid().str(digits, radius=False)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--upstream-script", type=Path, required=True)
    p.add_argument("--upstream-commit", required=True)
    p.add_argument("--c", type=int, default=100)
    p.add_argument("--m-max", type=int, default=40)
    p.add_argument("--prec", type=int, default=4000)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    if args.m_max < 1:
        raise SystemExit("m-max must be positive")
    module = load_upstream(args.upstream_script)
    A, dim = module.build_arb_tau(args.c, args.m_max, args.prec)
    center = args.m_max

    rows = []
    for m in range(1, args.m_max + 1):
        weights = {}
        for k in range(-m, m + 1):
            # (-1)^k is well-defined for integer k; use parity instead of float pow.
            sign = -1 if (k & 1) else 1
            weights[k] = sign * math.comb(2 * m, m - k)

        denom_int = sum(v * v for v in weights.values())
        num = arb(0)
        for k, wk in weights.items():
            i = center + k
            aw = arb(str(wk))
            for joff, wj in weights.items():
                j = center + joff
                num += aw * A[i, j] * arb(str(wj))
        q = num / arb(str(denom_int))
        log10_mid = midpoint_log10(q)

        rows.append({
            "m": m,
            "support_dimension": 2 * m + 1,
            "rayleigh": interval_payload(q),
            "certified_positive": bool(q.lower() > 0),
            "certified_negative": bool(q.upper() < 0),
            "log10_mid_nonrigorous": log10_mid,
            "minus_log10_mid_nonrigorous": None if log10_mid is None else str(-arb(log10_mid)),
        })

    # Select by Arb midpoint comparisons, without converting tiny numbers to float.
    positive_rows = [r for r in rows if r["certified_positive"]]
    best = None
    if positive_rows:
        best = min(positive_rows, key=lambda r: arb(r["rayleigh"]["mid"]))

    payload = {
        "status": "rigorous_cutoff_free_sine_power_rayleigh",
        "upstream_commit": args.upstream_commit,
        "c": args.c,
        "m_max": args.m_max,
        "prec_bits": args.prec,
        "family": "T_m(s) proportional to sin(pi*s)^(2m), with exact centered-binomial Fourier weights",
        "rows": rows,
        "best_positive_midpoint_row_nonrigorous_selection": best,
        "meaning": "Each Rayleigh interval is a direct Arb contraction against the cutoff-free CvS matrix. Positive values are variational upper bounds, not positivity certificates for the full space.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": payload["status"],
        "c": args.c,
        "best": best,
        "negative_m": [r["m"] for r in rows if r["certified_negative"]],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
