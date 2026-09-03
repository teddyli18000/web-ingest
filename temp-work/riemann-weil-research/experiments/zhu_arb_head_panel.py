#!/usr/bin/env python3
"""Rigorous Arb enclosure of a panel range of Zhu's one-stroke C matrix.

The exact 32-point Gauss-Legendre rule on every width-1/4 panel is enclosed
using rigorously bracketed roots of P_32 and interval weights.  Function values
(digamma, cosine, spherical Bessel) are then evaluated with Arb/Acb balls.
The analytic Gauss remainder is deliberately NOT included here; the collector
adds Zhu's Bernstein-ellipse remainder separately.

The script writes the lower triangle of the partial C matrix as parseable Arb
strings.  Different panel ranges may be computed independently and summed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import mpmath as mp
from flint import acb, arb, arb_mat, ctx


def legendre_with_derivative(n: int, x: arb) -> tuple[arb, arb]:
    if n == 0:
        return arb(1), arb(0)
    p0, d0 = arb(1), arb(0)
    p1, d1 = x, arb(1)
    if n == 1:
        return p1, d1
    for k in range(1, n):
        kp1 = k + 1
        p2 = ((2 * k + 1) * x * p1 - k * p0) / kp1
        d2 = ((2 * k + 1) * (p1 + x * d1) - k * d0) / kp1
        p0, p1 = p1, p2
        d0, d1 = d1, d2
    return p1, d1


def rigorous_gauss32(root_radius: str = "1e-95") -> tuple[list[arb], list[arb], dict]:
    """Return rigorous nodes/weights for the 32-point Legendre rule.

    mpmath supplies only proposals.  Every positive proposal is independently
    certified by an Arb sign change of the exact recurrence for P_32.  The 16
    positive disjoint brackets and symmetry then account for all 32 real roots.
    Weights are evaluated as Arb functions over the certified root brackets.
    """
    mp.mp.dps = 150
    xs, _ = mp.gauss_quadrature(32, "legendre")
    proposals = sorted(mp.mpf(xs[i]) for i in range(32) if xs[i] > 0)
    if len(proposals) != 16:
        raise RuntimeError(f"expected 16 positive Gauss nodes, got {len(proposals)}")

    rad = arb(root_radius)
    positive_nodes: list[arb] = []
    positive_weights: list[arb] = []
    sign_checks = []
    last_hi = None
    for proposal in proposals:
        s = mp.nstr(proposal, 130)
        mid = arb(s)
        lo, hi = mid - rad, mid + rad
        plo, _ = legendre_with_derivative(32, lo)
        phi, _ = legendre_with_derivative(32, hi)
        opposite = (plo < 0 and phi > 0) or (plo > 0 and phi < 0)
        if not opposite:
            raise RuntimeError(f"P32 sign-change certification failed near {s}: {plo}, {phi}")
        if last_hi is not None and not (last_hi < lo):
            raise RuntimeError("Gauss root brackets overlap")
        last_hi = hi

        xb = arb(s, root_radius)
        _, dp = legendre_with_derivative(32, xb)
        denom = (1 - xb * xb) * dp * dp
        if not (denom > 0):
            raise RuntimeError(f"Gauss weight denominator not positive at {s}: {denom}")
        wb = 2 / denom
        positive_nodes.append(xb)
        positive_weights.append(wb)
        sign_checks.append({"mid": s, "P_lo": plo.str(20), "P_hi": phi.str(20)})

    nodes = [-x for x in reversed(positive_nodes)] + positive_nodes
    weights = list(reversed(positive_weights)) + positive_weights
    total_w = sum(weights, arb(0))
    if not total_w.contains(arb(2)):
        raise RuntimeError(f"Gauss weights do not enclose total mass 2: {total_w}")
    return nodes, weights, {
        "root_radius": root_radius,
        "positive_root_count": 16,
        "weight_sum": total_w.str(60, more=True),
        "first_positive_sign_check": sign_checks[0],
        "last_positive_sign_check": sign_checks[-1],
    }


def spherical_j_direct(n: int, x: arb) -> arb:
    if not (x > 0):
        raise ValueError(f"spherical_j_direct requires x>0, got {x}")
    order = arb(n) + arb("0.5")
    J = acb(x).bessel_j(order).real
    return (arb.pi() / (2 * x)).sqrt() * J


def spherical_j_sequence(x: arb, nmax: int) -> tuple[list[arb], arb]:
    """Rigorous downward recurrence seeded by two direct Acb Bessel balls."""
    K = nmax + 1
    jk = spherical_j_direct(K, x)
    jkp1 = spherical_j_direct(K + 1, x)
    vals: list[arb | None] = [None] * (nmax + 1)
    for k in range(K, 0, -1):
        jkm1 = ((2 * k + 1) / x) * jk - jkp1
        if k - 1 <= nmax:
            vals[k - 1] = jkm1
        jkp1, jk = jk, jkm1
    out = [v for v in vals if v is not None]
    if len(out) != nmax + 1:
        raise RuntimeError("incomplete spherical Bessel recurrence")
    exact_j0 = x.sin() / x
    defect = out[0] - exact_j0
    if not defect.contains(arb(0)):
        raise RuntimeError(f"downward recurrence failed j0 overlap: defect={defect}")
    return out, defect


def prime_data() -> list[tuple[int, arb, arb]]:
    # (n, coefficient 2 Lambda(n)/sqrt(n), log n)
    log2, log3 = arb(2).log(), arb(3).log()
    return [
        (2, 2 * log2 / arb(2).sqrt(), log2),
        (3, 2 * log3 / arb(3).sqrt(), log3),
        (4, log2, arb(4).log()),
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--L", default="log5over2")
    ap.add_argument("--T", default="200")
    ap.add_argument("--panel-start", type=int, required=True)
    ap.add_argument("--panel-end", type=int, required=True, help="exclusive; max 800")
    ap.add_argument("--prec", type=int, default=384)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    if not (0 <= args.panel_start < args.panel_end <= 800):
        raise ValueError("panel range must satisfy 0 <= start < end <= 800")
    ctx.prec = args.prec
    L = arb(5).log() / 2 if args.L == "log5over2" else arb(args.L)
    T = arb(args.T)
    if not (L <= arb(5).log() / 2):
        raise ValueError("this assembler is scoped to the {2,3,4} prime plateau through log(5)/2")

    pdata = prime_data()
    A_L = sum((coef for _, coef, _ in pdata), arb(0))
    beta = (T / (2 * arb.pi())).log() - 1 / T - A_L
    if not (beta > 0):
        raise RuntimeError(f"beta is not positive: {beta}")

    nodes, weights, gauss_meta = rigorous_gauss32()
    width = arb(1) / 4
    half = width / 2
    orders = [2 * k for k in range(args.N)]
    nmax = orders[-1]
    pref = [2 * (L * (arb(n) + arb("0.5"))).sqrt() for n in orders]
    signs = [arb(1) if (n // 2) % 2 == 0 else arb(-1) for n in orders]

    C = arb_mat(args.N, args.N)
    logpi = arb.pi().log()
    max_j0_defect = arb(0)

    for panel in range(args.panel_start, args.panel_end):
        mid = (arb(panel) + arb("0.5")) * width
        F = arb_mat(32, args.N)
        WF = arb_mat(32, args.N)
        for q in range(32):
            t = mid + half * nodes[q]
            x = L * t
            js, defect = spherical_j_sequence(x, nmax)
            dabs = defect.abs_upper()
            if dabs > max_j0_defect:
                max_j0_defect = dabs

            z = acb(arb("0.25"), t / 2)
            h = z.digamma().real - logpi
            comb = arb(0)
            for _, coef, logn in pdata:
                comb += coef * (t * logn).cos()
            symbol_minus_beta = h - comb - beta
            fac = half * weights[q] * symbol_minus_beta / arb.pi()

            for j, n in enumerate(orders):
                value = signs[j] * pref[j] * js[n]
                F[q, j] = value
                WF[q, j] = fac * value

        panel_C = F.transpose() * WF
        C = C + panel_C

    # Force a common symmetric enclosure, preserving both independently
    # evaluated triangular entries.
    C = (C + C.transpose()) / 2
    rows = []
    for i in range(args.N):
        rows.append([C[i, j].str(100, more=True) for j in range(i + 1)])

    payload = {
        "status": "rigorous_arb_gauss32_partial_C",
        "arxiv": "2608.24827v2",
        "N": args.N,
        "L": L.str(80, more=True),
        "T_sharp": T.str(50, more=True),
        "beta_star": beta.str(80, more=True),
        "active_prime_powers": [2, 3, 4],
        "panel_start": args.panel_start,
        "panel_end": args.panel_end,
        "precision_bits": args.prec,
        "gauss_certification": gauss_meta,
        "max_j0_recurrence_defect_abs_upper": max_j0_defect.str(40, more=True),
        "lower_triangle": rows,
        "warning": "This encloses the exact Gauss-32 quadrature sum over this panel range; analytic Gauss remainder is added only by the collector.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "lower_triangle"}, indent=2))


if __name__ == "__main__":
    main()
