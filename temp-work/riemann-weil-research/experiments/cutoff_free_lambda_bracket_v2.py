#!/usr/bin/env python3
"""Rigorous two-sided bracket for the smallest cutoff-free CvS Weil eigenvalue.

Uses the pinned public Groskin Arb cutoff-free matrix builder. Midpoint floating
arithmetic is used only to choose a scale; every reported lower/upper endpoint
is backed by interval LDL^T inertia:

    A - lo I positive definite  => lambda_min(A) > lo
    A - hi I has negative inertia => lambda_min(A) < hi

An interval-undetermined test is treated as a numerical precision barrier, not
as evidence about the sign. The search probes away from such a point instead
of stopping immediately.
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
    if undet is not None:
        kind = "undetermined"
    elif n_neg == 0 and n_pos == dim:
        kind = "positive"
    elif n_neg > 0:
        kind = "negative"
    else:
        kind = "unexpected"
    return {
        "shift": mp.nstr(shift, digits),
        "n_pos": n_pos,
        "n_neg": n_neg,
        "undetermined_pivot": undet,
        "kind": kind,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-script", type=Path, required=True)
    parser.add_argument("--upstream-commit", required=True)
    parser.add_argument("--c", type=int, default=100)
    parser.add_argument("--N", type=int, required=True)
    parser.add_argument("--prec", type=int, required=True)
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    module = load_upstream(args.upstream_script)
    A, dim = module.build_arb_tau(args.c, args.N, args.prec)

    decimal_digits = max(100, int(args.prec * 0.30103) - 24)
    mp.mp.dps = decimal_digits
    midpoint = mp.matrix(dim, dim)
    for i in range(dim):
        for j in range(dim):
            midpoint[i, j] = arb_mid_to_mpf(A[i, j], decimal_digits)
    eigs, _ = mp.eigsy(midpoint)
    approx = eigs[0]
    if not mp.isfinite(approx) or approx <= 0:
        raise SystemExit(f"midpoint matrix did not have a positive finite ground value: {approx}")

    zero_test = classify(module, A, dim, mp.mpf("0"), decimal_digits)
    if zero_test["kind"] != "positive":
        raise SystemExit(
            "precision insufficient to certify cutoff-free positive definiteness at shift 0; "
            f"result={zero_test}"
        )

    # Find a strictly positive certified lower endpoint. Starting below the
    # midpoint estimate is only a search heuristic; the returned endpoint is
    # rigorous because its shifted LDL test is rigorous.
    low = approx / 2
    low_test = None
    for _ in range(256):
        candidate = classify(module, A, dim, low, decimal_digits)
        if candidate["kind"] == "positive":
            low_test = candidate
            break
        low /= 2
    if low_test is None or low <= 0:
        raise SystemExit("failed to obtain a strictly positive certified lower shift")

    # Find a certified upper endpoint above lambda_min.
    high = approx * 2
    high_test = None
    for _ in range(256):
        candidate = classify(module, A, dim, high, decimal_digits)
        if candidate["kind"] == "negative":
            high_test = candidate
            break
        high *= 2
    if high_test is None:
        raise SystemExit("failed to obtain a certified upper shift with negative inertia")

    undetermined_tests = []
    for step in range(args.steps):
        if high <= low:
            raise RuntimeError("invalid bracket ordering")
        mid = (low + high) / 2
        test = classify(module, A, dim, mid, decimal_digits)
        if test["kind"] == "positive":
            low, low_test = mid, test
            continue
        if test["kind"] == "negative":
            high, high_test = mid, test
            continue

        undetermined_tests.append({"step": step, **test})

        # The ambiguous band is normally concentrated very close to the true
        # eigenvalue. Probe the quarter points, which are farther from it.
        left = (3 * low + high) / 4
        right = (low + 3 * high) / 4
        left_test = classify(module, A, dim, left, decimal_digits)
        right_test = classify(module, A, dim, right, decimal_digits)

        changed = False
        if left_test["kind"] == "positive":
            low, low_test = left, left_test
            changed = True
        elif left_test["kind"] == "undetermined":
            undetermined_tests.append({"step": step, "probe": "left", **left_test})

        if right_test["kind"] == "negative":
            high, high_test = right, right_test
            changed = True
        elif right_test["kind"] == "undetermined":
            undetermined_tests.append({"step": step, "probe": "right", **right_test})

        if not changed:
            break

    payload = {
        "status": "rigorous_shifted_interval_ldlt_bracket_v2",
        "source": "Akiva Groskin 2026 cutoff-free Arb verifier",
        "upstream_commit": args.upstream_commit,
        "c": args.c,
        "N": args.N,
        "dimension": dim,
        "prec_bits": args.prec,
        "midpoint_eigenvalue_nonrigorous": mp.nstr(approx, 80),
        "lambda_min_rigorous_lower": mp.nstr(low, 100),
        "lambda_min_rigorous_upper": mp.nstr(high, 100),
        "bracket_width": mp.nstr(high - low, 100),
        "relative_bracket_width": mp.nstr((high - low) / low, 60),
        "lower_certificate": low_test,
        "upper_certificate": high_test,
        "zero_certificate": zero_test,
        "undetermined_tests": undetermined_tests[-12:],
        "meaning": (
            "For the exact cutoff-free interval matrix, A-lo*I is rigorously positive definite "
            "and A-hi*I rigorously has negative inertia. Therefore lo < lambda_min(A) < hi."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
