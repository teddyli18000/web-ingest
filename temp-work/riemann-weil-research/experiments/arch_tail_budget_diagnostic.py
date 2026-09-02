#!/usr/bin/env python3
"""Rigorous Arb upper bounds for the omitted CvS archimedean tail.

Adapted from the public verification script accompanying Akiva Groskin,
"A finite Guinand-Weil dictionary and archimedean tail order for the
truncated Weil quadratic form" (2026), MIT-licensed verification code.

For T > max(rho*N, 7), the paper proves

    0 <= Q_infty - Q_T <= B_T I,

and the trace upper bound produced here is a valid scalar B_T.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from flint import acb, arb, ctx


def h_plus(tau: arb) -> arb:
    z = acb(arb("0.25"), tau / 2)
    return z.digamma().real - arb.pi().log()


def j_log_tail(a0: arb, n: int, rho: arb) -> arb:
    nn = arb(n)
    if n == 0:
        return ((rho * a0).log() + 1) / a0
    return (rho * a0).log() / (a0 - nn) + (a0 / (a0 - nn)).log() / nn


def trace_norm_integral(a0: arb, a1: arb, nmax: int) -> arb:
    total = arb(0)
    for n in range(-nmax, nmax + 1):
        nn = arb(n)
        total += 1 / (a0 - nn) - 1 / (a1 - nn)
        total += 1 / (a0 + nn) - 1 / (a1 + nn)
    return total


def trace_log_tail(a0: arb, nmax: int, rho: arb) -> arb:
    total = arb(0)
    for n in range(-nmax, nmax + 1):
        total += j_log_tail(a0, n, rho)
        total += j_log_tail(a0, -n, rho)
    return total


def text(x: arb) -> str:
    return str(x).replace("\n", " ")


def compute(c: int, nmax: int, cutoff: int, prec: int, dyadic_count: int) -> dict:
    ctx.prec = prec
    pi = arb.pi()
    L = arb(c).log()
    rho = 2 * pi / L
    T = arb(cutoff)

    threshold_pass = bool(T > rho * nmax and T > arb(7))
    if not threshold_pass:
        return {
            "c": c,
            "N": nmax,
            "T": cutoff,
            "threshold_pass": False,
            "rho_N": text(rho * nmax),
            "status": "NO CERTIFICATE: T must exceed both rho*N and 7",
        }

    trace_sum = arb(0)
    A = T
    for _ in range(dyadic_count):
        B = 2 * A
        a0 = A / rho
        a1 = B / rho
        hB = h_plus(B).upper()
        trace_sum += hB / (pi * pi) * trace_norm_integral(a0, a1, nmax)
        A = B

    R = A
    aR = R / rho
    # Groskin Lemma 3.1 proves h_plus(tau) <= log(tau) for every tau >= 7,
    # so the analytic log-tail can be used from R onward.  We still drive R
    # far out to match the released verifier's dyadic/interval methodology.
    trace_tail = trace_log_tail(aR, nmax, rho) / (pi * pi)
    trace_total = trace_sum + trace_tail

    return {
        "c": c,
        "N": nmax,
        "dimension": 2 * nmax + 1,
        "T": cutoff,
        "prec_bits": prec,
        "dyadic_count": dyadic_count,
        "threshold_pass": True,
        "rho": text(rho),
        "rho_N": text(rho * nmax),
        "tail_after_R": text(R),
        "finite_dyadic_trace_sum": text(trace_sum),
        "log_tail_trace_remainder": text(trace_tail),
        "B_T_trace_upper_interval": text(trace_total),
        "B_T_trace_upper_numeric_upper": text(trace_total.upper()),
        "status": "RIGOROUS: 0 <= Q_infty-Q_T <= B_T I using trace upper bound",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--c", type=int, required=True)
    parser.add_argument("--N", type=int, required=True)
    parser.add_argument("--Ts", default="120,240,480")
    parser.add_argument("--prec", type=int, default=300)
    parser.add_argument("--dyadic-count", type=int, default=20)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    values = [int(x) for x in args.Ts.split(",") if x.strip()]
    payload = {
        "source": "Groskin 2026 archimedean tail-order verifier, adapted",
        "results": [compute(args.c, args.N, T, args.prec, args.dyadic_count) for T in values],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
