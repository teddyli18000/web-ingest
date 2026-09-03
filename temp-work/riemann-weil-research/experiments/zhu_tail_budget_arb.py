#!/usr/bin/env python3
"""Rigorous Arb tail/coupling budget for Zhu 2608.24827v2 Theorem 1.1.

This script does NOT certify the finite leading block.  It certifies only the
infinite Legendre tail quantities epsilon_D and epsilon_B in the two-block
bound, using deliberately conservative pointwise estimates.

For even normalized Legendre order n,

    F_n(t) = 2 sqrt(L (n+1/2)) (-1)^(n/2) j_n(L t).

For 0 <= t <= T we use

    |j_n(L t)| <= (L T)^n / (2n+1)!!,

and for the pole coefficient F_n(i/2) the Poisson-integral continuation gives

    |j_n(i L/2)| <= exp(L/2) (L/2)^n / (2n+1)!!.

We also retain an explicit T/pi factor in the C_nm integral.  This is more
conservative than the abbreviated row estimate printed in Zhu's Section 4,
but makes the bound immediate from pointwise domination:

    |C_nm| <= (T/pi) M a_n b_m             (tail n, leading m)
    |C_nm| <= (T/pi) M a_n a_m             (tail n,m)

where M >= max_[0,T] |Psi_L-beta*|, a_n is the forbidden-region Fourier
bound, and b_m = 2 sqrt(L(m+1/2)).

The positive rank-one pole block is discarded when bounding the tail diagonal
D from below.  Its leading-tail coupling is retained explicitly.

Every reported inequality is decided with Arb balls; midpoint diagnostics are
not used for certification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from flint import arb, ctx


def ball(x: arb, digits: int = 50) -> dict[str, str]:
    return {
        "lower": x.lower().str(digits, radius=False),
        "upper": x.upper().str(digits, radius=False),
        "mid": x.mid().str(digits, radius=False),
        "rad": x.rad().str(20, radius=False),
    }


def even_q_values(y: arb, nmax: int) -> dict[int, arb]:
    """q_n(y)=y^n/(2n+1)!! for even n <= nmax, by exact recurrence."""
    if nmax % 2:
        raise ValueError("nmax must be even")
    out = {0: arb(1)}
    n = 0
    while n < nmax:
        out[n + 2] = out[n] * y * y / ((2 * n + 3) * (2 * n + 5))
        n += 2
    return out


def coeff_prefactor(L: arb, n: int) -> arb:
    return arb(2) * (L * (arb(n) + arb("0.5"))).sqrt()


def ratio_even(Lscale: arb, n: int) -> arb:
    """Ratio a_{n+2}/a_n for a_n = 2 sqrt(L nu_n) q_n(Lscale)."""
    root_ratio = ((arb(n) + arb("2.5")) / (arb(n) + arb("0.5"))).sqrt()
    return root_ratio * Lscale * Lscale / ((2 * n + 3) * (2 * n + 5))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, required=True, help="number of retained even modes; first discarded order is 2N")
    ap.add_argument("--L", default="log5over2", help="decimal or log5over2")
    ap.add_argument("--T", default="200")
    ap.add_argument("--symbol-bound", default="20")
    ap.add_argument("--prec", type=int, default=256)
    ap.add_argument("--target", default="1e-19", help="optional gate for epsilon_B")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    if args.N < 2:
        raise ValueError("N must be >= 2")
    ctx.prec = args.prec

    L = arb(5).log() / 2 if args.L == "log5over2" else arb(args.L)
    T = arb(args.T)
    M = arb(args.symbol_bound)
    n0 = 2 * args.N
    x = L * T
    y = L / 2

    qx = even_q_values(x, n0)
    qy = even_q_values(y, n0)

    def a(n: int) -> arb:
        return coeff_prefactor(L, n) * qx[n]

    def b(n: int) -> arb:
        return coeff_prefactor(L, n)

    def p(n: int) -> arb:
        # Rigorous entire-continuation majorant for |F_n(i/2)|.
        return coeff_prefactor(L, n) * y.exp() * qy[n]

    a0 = a(n0)
    p0 = p(n0)
    ra = ratio_even(x, n0)
    rp = ratio_even(y, n0)
    if not (ra < 1):
        raise RuntimeError(f"Fourier tail ratio is not certified < 1: {ra}")
    if not (rp < 1):
        raise RuntimeError(f"pole tail ratio is not certified < 1: {rp}")

    # The same-parity ratios decrease beyond the forbidden-region cut; using
    # the first ratio therefore bounds the infinite sums geometrically.
    sum_a_tail = a0 / (1 - ra)
    sum_p_tail = p0 / (1 - rp)

    lead_orders = list(range(0, n0, 2))
    sum_b_lead = sum((b(n) for n in lead_orders), arb(0))
    sum_p_lead = sum((p(n) for n in lead_orders), arb(0))
    bmax_lead = b(lead_orders[-1])

    K = M * T / arb.pi()

    # Tail diagonal: discard +2 p p^T since it is positive semidefinite.
    eps_D = K * a0 * sum_a_tail

    # Rectangular coupling.  Bound the maximum tail-row sum and maximum
    # leading-column sum separately, then apply the Schur test.
    row_max = K * a0 * sum_b_lead + 2 * p0 * sum_p_lead
    col_max = K * bmax_lead * sum_a_tail + 2 * sum_p_lead * sum_p_tail
    eps_B = (row_max * col_max).sqrt()

    target = arb(args.target)
    payload = {
        "status": "rigorous_arb_tail_coupling_budget",
        "scope": "Zhu 2608.24827v2 one-stroke Legendre tail only; finite leading block not certified here",
        "L": ball(L),
        "T_sharp": ball(T),
        "N_retained_even_modes": args.N,
        "first_discarded_legendre_order": n0,
        "symbol_abs_bound_assumed": args.symbol_bound,
        "integral_factor": "M*T/pi retained explicitly (conservative)",
        "a_first_tail": ball(a0),
        "pole_first_tail": ball(p0),
        "fourier_same_parity_ratio_at_cut": ball(ra),
        "pole_same_parity_ratio_at_cut": ball(rp),
        "sum_a_tail_upper_ball": ball(sum_a_tail),
        "sum_pole_tail_upper_ball": ball(sum_p_tail),
        "coupling_row_sum_upper_ball": ball(row_max),
        "coupling_col_sum_upper_ball": ball(col_max),
        "epsilon_D": ball(eps_D),
        "epsilon_B": ball(eps_B),
        "target_epsilon_B": args.target,
        "epsilon_B_strictly_below_target": bool(eps_B < target),
        "precision_bits": args.prec,
        "warning": "The geometric-series step uses monotone decrease of the explicit same-parity ratio beyond the cut; this is elementary for the displayed rational ratio and should be included in any final proof writeup.",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))

    if not (eps_B < target):
        raise SystemExit(f"epsilon_B is not certified below target {args.target}: {eps_B}")


if __name__ == "__main__":
    main()
