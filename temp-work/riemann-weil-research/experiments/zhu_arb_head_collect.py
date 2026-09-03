#!/usr/bin/env python3
"""Collect rigorous Arb panel matrices and certify a one-stroke head floor.

Inputs are partial C matrices from zhu_arb_head_panel.py. The collector sums
all 800 panel enclosures, adds beta I and the exact pole rank-one term, and
then proves a lower spectral floor by interval LDL^T at a positive shift.
This is deliberately narrower and more robust than isolating the full highly
clustered spectrum: for the one-stroke theorem we only need A-eta I > 0.

The analytic Bernstein-ellipse Gauss remainder is subtracted as a separate
operator-norm budget. If a tail-budget JSON is supplied, the final two-block
infinite-dimensional lower bound is also reported.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

from flint import acb, arb, arb_mat, ctx


def ball(x: arb, digits: int = 60) -> dict[str, str]:
    return {
        "lower": x.lower().str(digits, radius=False),
        "upper": x.upper().str(digits, radius=False),
        "mid": x.mid().str(digits, radius=False),
        "rad": x.rad().str(30, radius=False),
    }


def parse_partial(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_pole_vector(L: arb, N: int) -> list[arb]:
    y = L / 2
    sphere_factor = (arb.pi() / (2 * y)).sqrt()
    out = []
    for k in range(N):
        n = 2 * k
        nu = arb(n) + arb("0.5")
        ordinary_I = acb(y).bessel_i(nu).real
        i_n = sphere_factor * ordinary_I
        out.append(2 * (L * nu).sqrt() * i_n)
    return out


def quadrature_budget(L: arb, N: int, panels: int = 800) -> tuple[arb, arb, arb]:
    """Bernstein-ellipse Gauss-32 remainder specialized to width-1/4 panels."""
    rho = arb("6.55")
    nmax = 2 * (N - 1)
    nu_max = arb(nmax) + arb("0.5")
    # On |Im t| <= 0.4: |Psi-beta| <= 20 on the unchanged {2,3,4}
    # prime plateau, and |F_n F_m| <= 4 L sqrt(nu_n nu_m) e^(0.8 L).
    M = 20 * 4 * L * nu_max * (arb("0.8") * L).exp()
    per_panel = 4 * M * rho / ((rho - 1) * (rho ** 64 - 1))
    eps_Q = panels * per_panel
    c_err = N * eps_Q
    return per_panel, eps_Q, c_err


def tail_upper_from_json(data: dict, key: str) -> arb:
    return arb(data[key]["upper"])


def shifted_interval_ldlt_positive(A: arb_mat, shift: arb) -> dict:
    """Rigorous unpivoted LDL^T positivity test for A-shift*I.

    Interval arithmetic encloses every exact Schur pivot compatible with the
    entry balls. If every pivot interval is strictly positive, Sylvester's
    criterion certifies A-shift*I positive definite. An undetermined pivot is
    a precision/enclosure failure, never evidence of nonpositivity.
    """
    n = A.nrows()
    L = [[arb(0) for _ in range(n)] for _ in range(n)]
    pivots: list[arb] = []
    min_lower = None
    for i in range(n):
        d = A[i, i] - shift
        for k in range(i):
            d = d - L[i][k] * L[i][k] * pivots[k]
        lo = d.lower()
        if min_lower is None or lo < min_lower:
            min_lower = lo
        if not (d > 0):
            return {
                "positive": False,
                "undetermined_pivot": i,
                "pivot_ball": ball(d),
                "min_pivot_lower_so_far": min_lower.str(50, radius=False),
            }
        pivots.append(d)
        for j in range(i + 1, n):
            num = A[j, i]
            for k in range(i):
                num = num - L[j][k] * L[i][k] * pivots[k]
            L[j][i] = num / d
    return {
        "positive": True,
        "undetermined_pivot": None,
        "pivot_ball": None,
        "min_pivot_lower_so_far": min_lower.str(50, radius=False),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--partials-glob", required=True)
    ap.add_argument("--prec", type=int, default=512)
    ap.add_argument("--tail-json", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    ctx.prec = args.prec

    paths = sorted(Path(p) for p in glob.glob(args.partials_glob))
    if not paths:
        raise RuntimeError("no partial matrices matched")
    parts = [parse_partial(p) for p in paths]
    N = int(parts[0]["N"])
    Lwin = arb(parts[0]["L"])
    T = arb(parts[0]["T_sharp"])
    beta = arb(parts[0]["beta_star"])

    ranges = sorted((int(p["panel_start"]), int(p["panel_end"])) for p in parts)
    cursor = 0
    for start, end in ranges:
        if start != cursor:
            raise RuntimeError(f"panel coverage gap/overlap: expected start {cursor}, got {start}")
        cursor = end
    if cursor != 800:
        raise RuntimeError(f"partial matrices cover panels only through {cursor}, expected 800")
    for p in parts:
        if int(p["N"]) != N:
            raise RuntimeError("N mismatch among partial matrices")
        if not arb(p["L"]).overlaps(Lwin) or not arb(p["beta_star"]).overlaps(beta):
            raise RuntimeError("L/beta mismatch among partial matrices")

    C = arb_mat(N, N)
    for p in parts:
        tri = p["lower_triangle"]
        if len(tri) != N:
            raise RuntimeError("partial triangle dimension mismatch")
        for i in range(N):
            if len(tri[i]) != i + 1:
                raise RuntimeError("partial triangle row dimension mismatch")
            for j in range(i + 1):
                v = arb(tri[i][j])
                C[i, j] = C[i, j] + v
                if i != j:
                    C[j, i] = C[j, i] + v

    pvec = build_pole_vector(Lwin, N)
    Mquad = C
    for i in range(N):
        Mquad[i, i] = Mquad[i, i] + beta
        for j in range(i + 1):
            add = 2 * pvec[i] * pvec[j]
            Mquad[i, j] = Mquad[i, j] + add
            if i != j:
                Mquad[j, i] = Mquad[j, i] + add

    per_panel, eps_Q, c_err = quadrature_budget(Lwin, N)

    # Try useful positive shifts from strongest to weakest. Every accepted
    # shift is independently rigorous; the ladder is only a search heuristic.
    candidate_strings = [
        "5e-18", "4e-18", "3e-18", "2e-18", "1e-18",
        "5e-19", "2e-19", "1e-19", "5e-20", "2e-20", "1e-20",
    ]
    shift_tests = []
    certified_shift = None
    certified_test = None
    for s in candidate_strings:
        shift = arb(s)
        test = shifted_interval_ldlt_positive(Mquad, shift)
        shift_tests.append({"shift": s, **test})
        if test["positive"]:
            certified_shift = shift
            certified_test = test
            break

    if certified_shift is None:
        zero_test = shifted_interval_ldlt_positive(Mquad, arb(0))
        shift_tests.append({"shift": "0", **zero_test})
        raise SystemExit(
            "failed to certify a useful positive head shift; "
            f"zero_shift_result={zero_test}"
        )

    head_exact_lower = certified_shift - c_err.upper()

    payload = {
        "status": "rigorous_arb_shifted_ldlt_one_stroke_head_certificate",
        "source_arxiv_id": "2608.24827",
        "N": N,
        "L": ball(Lwin),
        "T_sharp": ball(T),
        "beta_star": ball(beta),
        "partial_file_count": len(parts),
        "panel_ranges": ranges,
        "precision_bits": args.prec,
        "gauss_per_panel_error_bound": ball(per_panel),
        "gauss_per_entry_total_error_bound": ball(eps_Q),
        "gauss_matrix_operator_norm_budget": ball(c_err),
        "ldlt_shift_tests": shift_tests,
        "certified_quadrature_matrix_floor": certified_shift.str(60, radius=False),
        "certified_shift_min_pivot_lower": certified_test["min_pivot_lower_so_far"],
        "exact_head_lower_after_gauss_budget": head_exact_lower.str(80, radius=False),
        "tail_budget_used": None,
        "final_infinite_dimensional_lower_bound": None,
        "warning": (
            "The head certificate uses Arb-enclosed Gauss nodes/weights and function values, "
            "an analytic Bernstein-ellipse quadrature remainder, and interval LDL^T at a "
            "strictly positive shift. It does not rely on full-spectrum eigenvalue isolation."
        ),
    }

    if args.tail_json is not None:
        tail = json.loads(args.tail_json.read_text(encoding="utf-8"))
        if int(tail["N_retained_even_modes"]) != N:
            raise RuntimeError("tail N does not match head N")
        eps_D = tail_upper_from_json(tail, "epsilon_D")
        eps_B = tail_upper_from_json(tail, "epsilon_B")
        tail_floor = beta.lower() - eps_D
        head_floor = head_exact_lower
        base_floor = head_floor if head_floor < tail_floor else tail_floor
        final_floor = base_floor - eps_B
        payload["tail_budget_used"] = {
            "epsilon_D_upper": eps_D.str(60, radius=False),
            "epsilon_B_upper": eps_B.str(60, radius=False),
            "tail_diagonal_floor": tail_floor.str(60, radius=False),
        }
        payload["final_infinite_dimensional_lower_bound"] = final_floor.str(80, radius=False)
        payload["final_bound_strictly_positive"] = bool(final_floor > 0)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))

    if not (head_exact_lower > 0):
        raise SystemExit(f"exact head lower bound not positive: {head_exact_lower}")
    if args.tail_json is not None and not payload.get("final_bound_strictly_positive", False):
        raise SystemExit("final infinite-dimensional lower bound not positive")


if __name__ == "__main__":
    main()
