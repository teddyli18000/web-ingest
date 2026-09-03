#!/usr/bin/env python3
"""Collect Arb panel matrices and certify a positive one-stroke head floor.

The exact Gauss-32 panel sums are enclosed by ``zhu_arb_head_panel.py``.
This collector adds beta*I and the exact pole rank-one term, then certifies
``A - eta I > 0`` by a preconditioned congruence rather than trying to isolate
the extremely clustered full spectrum.

For a trial shift eta:

1. take the high-precision midpoint of ``A - eta I``;
2. compute an ordinary high-precision Cholesky factor L of that midpoint;
3. form a fixed decimal lower-triangular matrix T approximating L^{-1};
4. evaluate the interval congruence ``C = T (A-eta I) T^T`` with Arb;
5. prove ``C > 0`` by strict Gershgorin lower bounds.

Only step 4--5 is load-bearing.  The midpoint Cholesky is merely a way to
choose an effective fixed invertible congruence.  Since every diagonal entry
of T is certified nonzero, T is invertible and Sylvester inertia is preserved.

The analytic Bernstein-ellipse Gauss remainder is then subtracted as an
operator-norm budget.  If a tail budget is supplied, the final two-block
infinite-dimensional lower bound is also reported.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import mpmath as mp
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
    """Bernstein-ellipse Gauss-32 remainder for width-1/4 panels."""
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


def midpoint_mpf(x: arb, digits: int) -> mp.mpf:
    return mp.mpf(x.mid().str(digits, radius=False))


def midpoint_cholesky_inverse(A: arb_mat, shift: arb, digits: int):
    """Return a high-precision midpoint Cholesky inverse, or None if not PD.

    This is NOT a certificate.  It only constructs a numerical preconditioner.
    """
    n = A.nrows()
    shift_mp = midpoint_mpf(shift, digits)
    M = mp.matrix(n, n)
    for i in range(n):
        for j in range(n):
            v = midpoint_mpf(A[i, j], digits)
            if i == j:
                v -= shift_mp
            M[i, j] = v

    L = mp.matrix(n, n)
    min_mid_pivot = None
    for i in range(n):
        for j in range(i + 1):
            s = M[i, j]
            for k in range(j):
                s -= L[i, k] * L[j, k]
            if i == j:
                if not mp.isfinite(s) or s <= 0:
                    return None, {
                        "midpoint_cholesky_positive": False,
                        "failed_pivot": i,
                        "pivot": mp.nstr(s, 30),
                    }
                if min_mid_pivot is None or s < min_mid_pivot:
                    min_mid_pivot = s
                L[i, j] = mp.sqrt(s)
            else:
                L[i, j] = s / L[j, j]

    # Solve L*T = I column by column.  T is lower triangular.
    T = mp.matrix(n, n)
    for col in range(n):
        for i in range(n):
            rhs = mp.mpf(1) if i == col else mp.mpf(0)
            for k in range(i):
                rhs -= L[i, k] * T[k, col]
            T[i, col] = rhs / L[i, i]

    return T, {
        "midpoint_cholesky_positive": True,
        "failed_pivot": None,
        "min_midpoint_ldl_pivot": mp.nstr(min_mid_pivot, 40),
    }


def preconditioned_gershgorin_positive(A: arb_mat, shift: arb, digits: int) -> dict:
    """Rigorous positivity test via a fixed preconditioned congruence."""
    n = A.nrows()
    T_mp, midpoint_meta = midpoint_cholesky_inverse(A, shift, digits)
    if T_mp is None:
        return {
            "positive": False,
            "stage": "midpoint_cholesky",
            **midpoint_meta,
        }

    # Convert the numerical preconditioner to tiny Arb balls.  We do not need
    # these balls to contain an exact inverse: any fixed invertible T works.
    # The interval congruence encloses all T in these balls, in particular a
    # fixed representative.  Nonzero diagonal balls certify triangular
    # invertibility for every represented T.
    T = arb_mat(n, n)
    min_diag_abs_lower = None
    for i in range(n):
        for j in range(n):
            if j > i:
                v = arb(0)
            else:
                v = arb(mp.nstr(T_mp[i, j], digits))
            T[i, j] = v
        d = T[i, i]
        if d.contains(arb(0)):
            return {
                "positive": False,
                "stage": "preconditioner_invertibility",
                "failed_diagonal": i,
                "diagonal_ball": ball(d),
                **midpoint_meta,
            }
        alo = d.abs().lower()
        if min_diag_abs_lower is None or alo < min_diag_abs_lower:
            min_diag_abs_lower = alo

    Ashift = arb_mat(n, n)
    for i in range(n):
        for j in range(n):
            v = A[i, j]
            if i == j:
                v = v - shift
            Ashift[i, j] = v

    C = T * Ashift * T.transpose()
    # The exact congruence is symmetric. Averaging two interval enclosures is
    # still a valid enclosure and removes harmless asymmetric rounding noise.
    C = (C + C.transpose()) / 2

    min_margin = None
    worst_row = None
    worst_diag = None
    worst_radius = None
    max_offdiag_abs = arb(0)
    for i in range(n):
        radius = arb(0)
        for j in range(n):
            if i == j:
                continue
            a = C[i, j].abs_upper()
            radius += a
            if a > max_offdiag_abs:
                max_offdiag_abs = a
        margin = C[i, i].lower() - radius.upper()
        if min_margin is None or margin < min_margin:
            min_margin = margin
            worst_row = i
            worst_diag = C[i, i]
            worst_radius = radius

    positive = bool(min_margin is not None and min_margin > 0)
    return {
        "positive": positive,
        "stage": "gershgorin",
        "worst_row": worst_row,
        "min_gershgorin_margin": min_margin.str(60, radius=False) if min_margin is not None else None,
        "worst_diagonal_ball": ball(worst_diag) if worst_diag is not None else None,
        "worst_row_radius_ball": ball(worst_radius) if worst_radius is not None else None,
        "max_offdiagonal_abs_upper": max_offdiag_abs.str(50, radius=False),
        "preconditioner_min_diagonal_abs_lower": min_diag_abs_lower.str(50, radius=False),
        **midpoint_meta,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--partials-glob", required=True)
    ap.add_argument("--prec", type=int, default=512)
    ap.add_argument("--tail-json", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    ctx.prec = args.prec

    # Plenty of guard digits for the numerical preconditioner.  This does not
    # determine rigor; Arb below does.
    mid_digits = max(100, int(args.prec * 0.30103) - 24)
    mp.mp.dps = mid_digits + 30

    paths = sorted(Path(p) for p in glob.glob(args.partials_glob))
    if not paths:
        raise RuntimeError("no partial matrices matched")
    parts = [parse_partial(p) for p in paths]
    N = int(parts[0]["N"])
    Lwin = arb(parts[0]["L"])
    Tsharp = arb(parts[0]["T_sharp"])
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

    candidate_strings = [
        "8e-18", "6e-18", "5e-18", "4e-18", "3e-18", "2e-18", "1e-18",
        "5e-19", "2e-19", "1e-19", "5e-20", "2e-20", "1e-20",
    ]
    shift_tests = []
    certified_shift = None
    certified_test = None
    for s in candidate_strings:
        shift = arb(s)
        test = preconditioned_gershgorin_positive(Mquad, shift, mid_digits)
        shift_tests.append({"shift": s, **test})
        if test["positive"]:
            certified_shift = shift
            certified_test = test
            break

    if certified_shift is None:
        zero_test = preconditioned_gershgorin_positive(Mquad, arb(0), mid_digits)
        shift_tests.append({"shift": "0", **zero_test})
        raise SystemExit(
            "failed to certify a useful positive head shift by preconditioned congruence; "
            f"zero_shift_result={zero_test}"
        )

    head_exact_lower = certified_shift - c_err.upper()

    payload = {
        "status": "rigorous_arb_preconditioned_congruence_head_certificate",
        "source_arxiv_id": "2608.24827",
        "N": N,
        "L": ball(Lwin),
        "T_sharp": ball(Tsharp),
        "beta_star": ball(beta),
        "partial_file_count": len(parts),
        "panel_ranges": ranges,
        "precision_bits": args.prec,
        "midpoint_preconditioner_digits": mid_digits,
        "gauss_per_panel_error_bound": ball(per_panel),
        "gauss_per_entry_total_error_bound": ball(eps_Q),
        "gauss_matrix_operator_norm_budget": ball(c_err),
        "preconditioned_shift_tests": shift_tests,
        "certified_quadrature_matrix_floor": certified_shift.str(60, radius=False),
        "certified_congruence_gershgorin_margin": certified_test["min_gershgorin_margin"],
        "exact_head_lower_after_gauss_budget": head_exact_lower.str(80, radius=False),
        "tail_budget_used": None,
        "final_infinite_dimensional_lower_bound": None,
        "warning": (
            "The numerical midpoint Cholesky is used only to choose a fixed invertible "
            "preconditioner. The load-bearing positivity test is the Arb-enclosed congruence "
            "followed by strict Gershgorin bounds; the analytic quadrature remainder and "
            "optional infinite tail/coupling budgets are then subtracted separately."
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
