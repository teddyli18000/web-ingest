#!/usr/bin/env python3
"""Rigorous bracket for the smallest cutoff-free CvS Weil eigenvalue.

This wrapper imports the exact public Groskin Arb matrix builder from a pinned
checkout and brackets lambda_min(A) by shifted interval LDL^T tests:

    A - mu I positive definite  => lambda_min(A) > mu
    A - mu I has negative inertia => lambda_min(A) < mu

The only non-rigorous number is the midpoint eigensolve used to choose a useful
starting scale.  It does not enter the final certificate.
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


def arb_mid_to_mpf(x, digits: int) -> mp.mpf:
    return mp.mpf(x.mid().str(digits, radius=False))


def shifted_copy(A, dim: int, shift: mp.mpf, digits: int) -> arb_mat:
    B = arb_mat(dim, dim)
    shift_ball = arb(mp.nstr(shift, digits))
    for i in range(dim):
        for j in range(dim):
            value = A[i, j]
            if i == j:
                value = value - shift_ball
            B[i, j] = value
    return B


def classify(module, A, dim: int, shift: mp.mpf, digits: int) -> dict:
    B = shifted_copy(A, dim, shift, digits)
    n_pos, n_neg, undet, _ = module.certified_inertia(B, dim, heartbeat=0)
    return {
        "shift": mp.nstr(shift, digits),
        "n_pos": n_pos,
        "n_neg": n_neg,
        "undetermined_pivot": undet,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-script", type=Path, required=True)
    parser.add_argument("--upstream-commit", required=True)
    parser.add_argument("--c", type=int, default=100)
    parser.add_argument("--N", type=int, required=True)
    parser.add_argument("--prec", type=int, default=600)
    parser.add_argument("--steps", type=int, default=72)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    module = load_upstream(args.upstream_script)
    A, dim = module.build_arb_tau(args.c, args.N, args.prec)

    decimal_digits = max(90, int(args.prec * 0.30103) - 20)
    mp.mp.dps = decimal_digits
    midpoint = mp.matrix(dim, dim)
    for i in range(dim):
        for j in range(dim):
            midpoint[i, j] = arb_mid_to_mpf(A[i, j], decimal_digits)
    eigs, _ = mp.eigsy(midpoint)
    approx = eigs[0]

    zero_test = classify(module, A, dim, mp.mpf("0"), decimal_digits)
    if zero_test["undetermined_pivot"] is not None or zero_test["n_neg"] != 0:
        raise SystemExit(
            "cutoff-free matrix was not certified positive definite at shift 0; "
            f"result={zero_test}"
        )

    scale_floor = mp.mpf(10) ** (-(decimal_digits // 2))
    high = max(abs(approx) * 4, scale_floor)
    high_test = None
    for _ in range(256):
        candidate = classify(module, A, dim, high, decimal_digits)
        if candidate["undetermined_pivot"] is None and candidate["n_neg"] > 0:
            high_test = candidate
            break
        high *= 2
    if high_test is None:
        raise SystemExit("failed to find a certified upper shift with negative inertia")

    low = mp.mpf("0")
    low_test = zero_test
    unresolved = None
    for step in range(args.steps):
        mid = (low + high) / 2
        test = classify(module, A, dim, mid, decimal_digits)
        if test["undetermined_pivot"] is not None:
            unresolved = {"step": step, **test}
            break
        if test["n_neg"] == 0:
            low = mid
            low_test = test
        else:
            high = mid
            high_test = test

    payload = {
        "status": "rigorous_shifted_interval_ldlt_bracket",
        "source": "Akiva Groskin 2026 cutoff-free Arb verifier",
        "upstream_commit": args.upstream_commit,
        "c": args.c,
        "N": args.N,
        "dimension": dim,
        "prec_bits": args.prec,
        "bisection_steps_requested": args.steps,
        "midpoint_eigenvalue_nonrigorous": mp.nstr(approx, 60),
        "lambda_min_rigorous_lower": mp.nstr(low, 80),
        "lambda_min_rigorous_upper": mp.nstr(high, 80),
        "bracket_width": mp.nstr(high - low, 80),
        "lower_certificate": low_test,
        "upper_certificate": high_test,
        "unresolved_test": unresolved,
        "meaning": (
            "The exact cutoff-free interval matrix is positive definite after subtracting "
            "the lower shift, and has at least one negative eigenvalue after subtracting "
            "the upper shift. Hence lambda_min lies strictly between these shifts."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
