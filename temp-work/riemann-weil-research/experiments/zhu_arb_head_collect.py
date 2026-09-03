#!/usr/bin/env python3
"""Collect rigorous Arb panel matrices and certify Zhu one-stroke head floor.

Inputs are partial C matrices from zhu_arb_head_panel.py.  The collector sums
all 800 panel enclosures, adds beta I and the exact pole rank-one term, and
then asks Arb's validated eigenvalue routine to isolate the finite head
spectrum.  Zhu's Bernstein-ellipse Gauss-32 remainder is subtracted as a
separate operator-norm budget.

If a tail-budget JSON is supplied, the final two-block lower bound is also
reported.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

from flint import acb, acb_mat, arb, arb_mat, ctx


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
    """Zhu Lemma 5.1 specialized to width-1/4 panels and Gauss order 32."""
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
    L = arb(parts[0]["L"])
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
        if not arb(p["L"]).overlaps(L) or not arb(p["beta_star"]).overlaps(beta):
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

    pvec = build_pole_vector(L, N)
    Mquad = C
    for i in range(N):
        Mquad[i, i] = Mquad[i, i] + beta
        for j in range(i + 1):
            add = 2 * pvec[i] * pvec[j]
            Mquad[i, j] = Mquad[i, j] + add
            if i != j:
                Mquad[j, i] = Mquad[j, i] + add

    per_panel, eps_Q, c_err = quadrature_budget(L, N)

    # Validated eigenvalue isolation.  Rump is slower but is the tighter
    # certification algorithm exposed by python-flint.
    eigs = acb_mat(Mquad).eig(algorithm="rump")
    if len(eigs) != N:
        raise RuntimeError("unexpected eigenvalue count")
    # Every exact matrix represented here is real symmetric; require every
    # returned eigenball to overlap the real axis, then sort by real midpoint.
    for e in eigs:
        if not e.imag.contains(arb(0)):
            raise RuntimeError(f"eigenvalue ball does not meet real axis: {e}")
    eigs_sorted = sorted(eigs, key=lambda e: float(e.real.mid()))
    ground = eigs_sorted[0].real
    second = eigs_sorted[1].real if N > 1 else None
    head_exact_lower = ground.lower() - c_err.upper()

    payload = {
        "status": "rigorous_arb_one_stroke_head_certificate",
        "arxiv": "2608.24827v2",
        "N": N,
        "L": ball(L),
        "T_sharp": ball(T),
        "beta_star": ball(beta),
        "partial_file_count": len(parts),
        "panel_ranges": ranges,
        "precision_bits": args.prec,
        "gauss_per_panel_error_bound": ball(per_panel),
        "gauss_per_entry_total_error_bound": ball(eps_Q),
        "gauss_matrix_operator_norm_budget": ball(c_err),
        "quadrature_matrix_ground_eigenvalue_ball": ball(ground),
        "quadrature_matrix_second_eigenvalue_ball": ball(second) if second is not None else None,
        "exact_head_lower_after_gauss_budget": head_exact_lower.str(80, radius=False),
        "tail_budget_used": None,
        "final_infinite_dimensional_lower_bound": None,
        "warning": "The certificate uses Arb-enclosed Gauss nodes/weights and function values plus Zhu's analytic Bernstein-ellipse quadrature remainder."
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
