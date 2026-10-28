#!/usr/bin/env python3
"""Exact CP-SAT feasibility model for the first non-odd-perfect LABS-100 layer.

For N=100 the 50 odd-lag correlations are odd integers.  Pairing k with
100-k gives C_k + C_{100-k} == 0 (mod 4).  If their total squared energy is
58, exactly one of the 25 pairs contributes 10 rather than 2.  Hence, after
using the standard symmetries to make both parity-half sums +2, the structure
is:

* one selected odd pair is (1,3) or (3,1);
* every other odd pair is (1,-1) or (-1,1);
* the even-lag squared energy is at most target-58.

This script fixes the exceptional pair and solves the remaining exact Boolean
model.  A feasible assignment is independently rescored before being printed.
"""

from __future__ import annotations

import argparse
import time
from ortools.sat.python import cp_model

N = 100
SMOKE = (
    "++-++++-+-+-++++--++++++-++------++-+-++-+-++---+-+---+--+++++-----"
    "++-+-+--+++-+-+--++-+-------+-+++"
)


def exact(seq: str) -> tuple[int, int, list[int], int, int]:
    s = [1 if ch == "+" else -1 for ch in seq]
    cs = [0] + [sum(s[i] * s[i + k] for i in range(N - k)) for k in range(1, N)]
    energy = sum(c * c for c in cs[1:])
    odd = sum(cs[k] * cs[k] for k in range(1, N, 2))
    asum = sum(s[0::2])
    bsum = sum(s[1::2])
    return energy, odd, cs, asum, bsum


def add_square_table(model: cp_model.CpModel, v, name: str):
    q = model.NewIntVar(0, 2500, name)
    model.AddAllowedAssignments([v, q], [(x, x * x) for x in range(-50, 51)])
    return q


def build(defect: int, target: int, hint: str | None):
    if defect < 1 or defect >= 50 or defect % 2 == 0:
        raise ValueError("defect must be an odd k in 1..49")
    if target < 58:
        raise ValueError("target must be at least 58")

    model = cp_model.CpModel()
    # x_i = 0 means +1, x_i = 1 means -1.
    x = [model.NewBoolVar(f"x{i}") for i in range(N)]

    # Independent global-sign/alternation symmetries let every O=58 solution be
    # represented with both parity-half sums +2.  Reversal remains a symmetry.
    model.Add(50 - 2 * sum(x[0::2]) == 2)
    model.Add(50 - 2 * sum(x[1::2]) == 2)
    model.Add(x[0] <= x[99])

    corr: dict[int, cp_model.IntVar] = {}
    even_q = []
    even_corr = []

    for k in range(1, N):
        length = N - k
        z = []
        for i in range(length):
            d = model.NewBoolVar(f"z_{k}_{i}")
            # d == x_i XOR x_{i+k}.
            model.AddBoolXOr([x[i], x[i + k], d.Not()])
            z.append(d)
        m = model.NewIntVar(0, length, f"m{k}")
        model.Add(m == sum(z))
        c = model.NewIntVar(-length, length, f"c{k}")
        model.Add(c == length - 2 * m)
        corr[k] = c

        if k % 2 == 0:
            q = model.NewIntVar(0, target - 58, f"q{k}")
            rows = []
            for value in range(-length, length + 1, 2):
                if value * value <= target - 58:
                    rows.append((value, value * value))
            model.AddAllowedAssignments([c, q], rows)
            even_q.append(q)
            even_corr.append(c)

    # Exact O=58 pair pattern.  With parity-half product +4 the exceptional
    # pair must have positive sum +4; normal pairs have sum zero.
    for k in range(1, 50, 2):
        j = N - k
        if k == defect:
            model.AddAllowedAssignments([corr[k], corr[j]], [(1, 3), (3, 1)])
        else:
            model.AddAllowedAssignments([corr[k], corr[j]], [(1, -1), (-1, 1)])

    model.Add(sum(even_q) <= target - 58)

    # Since A_sum=B_sum=2,
    # sum_r C_{2r}=(A_sum^2+B_sum^2-N)/2 = -46.
    model.Add(sum(even_corr) == -46)

    # Redundant z=i Fourier identity.  For A_j=s_{2j}, B_j=s_{2j+1},
    # |S(i)|^2=A_alt^2+B_alt^2=100+2*sum_r (-1)^r C_{2r}.
    a_alt = model.NewIntVar(-50, 50, "a_alt")
    b_alt = model.NewIntVar(-50, 50, "b_alt")
    a_terms = []
    b_terms = []
    for j in range(50):
        coeff = 1 if j % 2 == 0 else -1
        # sign = 1-2*x, so coeff*sign contributes coeff-2*coeff*x.
        a_terms.append(coeff * (1 - 2 * x[2 * j]))
        b_terms.append(coeff * (1 - 2 * x[2 * j + 1]))
    model.Add(a_alt == sum(a_terms))
    model.Add(b_alt == sum(b_terms))
    a2 = add_square_table(model, a_alt, "a_alt_sq")
    b2 = add_square_table(model, b_alt, "b_alt_sq")
    alternating_even = sum(
        (1 if (r % 2 == 0) else -1) * corr[2 * r] for r in range(1, 50)
    )
    model.Add(a2 + b2 == N + 2 * alternating_even)

    if hint is not None:
        if len(hint) != N or any(ch not in "+-" for ch in hint):
            raise ValueError("bad hint sequence")
        for var, ch in zip(x, hint):
            model.AddHint(var, 0 if ch == "+" else 1)

    return model, x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--defect", type=int, required=True, help="odd k in 1..49")
    ap.add_argument("--target", type=int, default=574)
    ap.add_argument("--seconds", type=float, default=600.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    if args.smoke:
        e, o, cs, a, b = exact(SMOKE)
        defects = [
            k for k in range(1, 50, 2)
            if cs[k] * cs[k] + cs[N - k] * cs[N - k] == 10
        ]
        print(f"SMOKE energy={e} odd={o} asum={a} bsum={b} defects={defects}")
        if (e, o, a, b, defects) != (3654, 58, 2, 2, [25]):
            raise SystemExit("smoke structural check failed")

    hint = SMOKE if args.defect == 25 and args.target >= 3654 else None
    model, x = build(args.defect, args.target, hint)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = args.seed
    solver.parameters.randomize_search = True
    solver.parameters.cp_model_presolve = True
    solver.parameters.symmetry_level = 2

    start = time.time()
    status = solver.Solve(model)
    print(
        "STATUS",
        f"defect={args.defect}",
        solver.StatusName(status),
        f"wall={time.time()-start:.3f}",
        f"branches={solver.NumBranches()}",
        f"conflicts={solver.NumConflicts()}",
    )
    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        print(f"NO_CERTIFICATE defect={args.defect}")
        return

    seq = "".join("-" if solver.Value(v) else "+" for v in x)
    e, o, cs, a, b = exact(seq)
    defects = [
        k for k in range(1, 50, 2)
        if cs[k] * cs[k] + cs[N - k] * cs[N - k] == 10
    ]
    print(
        f"FOUND defect={args.defect} energy={e} odd={o} even={e-o} "
        f"asum={a} bsum={b} defects={defects} seq={seq}"
    )
    if e > args.target or o != 58 or a != 2 or b != 2 or defects != [args.defect]:
        raise SystemExit("independent exact check failed")


if __name__ == "__main__":
    main()
