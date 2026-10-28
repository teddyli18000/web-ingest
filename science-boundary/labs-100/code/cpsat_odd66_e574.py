#!/usr/bin/env python3
"""Exact CP-SAT feasibility model for LABS-100 E=574, odd energy O=66.

This is deliberately narrower and stronger than cpsat_odd66.py.  Exact E=574
has global sign product +1.  The arithmetic DP in target_arithmetic.py shows
that every O=66 candidate can be normalized to A_sum=0 and
B_sum in {0,4,8,12,16,20}.  The O=66 `double-same` defect pattern has the
wrong product class for E=574, so only `single18` and `double-mixed` remain.

The model adds redundant opposite-even-lag mod-4 tables, C_50 == 2 (mod 4),
exact even energy 508, the exact even-correlation sum, and the z=i Fourier
identity.  Any feasible assignment is independently rescored before output.
UNKNOWN is never treated as an exclusion.
"""
from __future__ import annotations

import argparse
import time
from ortools.sat.python import cp_model

N = 100
TARGET = 574
ODD_ENERGY = 66
EVEN_ENERGY = TARGET - ODD_ENERGY  # 508
VALID_BSUM = (0, 4, 8, 12, 16, 20)


def exact(seq: str) -> tuple[int, int, list[int], int, int]:
    s = [1 if ch == "+" else -1 for ch in seq]
    cs = [0] + [sum(s[i] * s[i + k] for i in range(N - k)) for k in range(1, N)]
    energy = sum(c * c for c in cs[1:])
    odd = sum(cs[k] * cs[k] for k in range(1, N, 2))
    asum = sum(s[0::2])
    bsum = sum(s[1::2])
    return energy, odd, cs, asum, bsum


def add_square_table(model: cp_model.CpModel, v, name: str, lo: int, hi: int):
    q = model.NewIntVar(0, max(lo * lo, hi * hi), name)
    model.AddAllowedAssignments([v, q], [(x, x * x) for x in range(lo, hi + 1)])
    return q


def pair_class(cs: list[int]) -> tuple[list[int], list[int], list[int]]:
    e18, pos10, neg10 = [], [], []
    for k in range(1, 50, 2):
        x, y = cs[k], cs[N - k]
        pe = x * x + y * y
        if pe == 18:
            e18.append(k)
        elif pe == 10:
            if x + y == 4:
                pos10.append(k)
            elif x + y == -4:
                neg10.append(k)
            else:
                raise ValueError("energy-10 pair has impossible sum")
        elif pe != 2:
            raise ValueError(f"unexpected odd-pair energy at k={k}: {pe}")
    return e18, pos10, neg10


def build(case: str, bsum_value: int):
    if case not in {"single18", "double-mixed"}:
        raise ValueError("case must be single18 or double-mixed")
    if bsum_value not in VALID_BSUM:
        raise ValueError("bsum must be one of 0,4,8,12,16,20")

    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"x{i}") for i in range(N)]  # 0 => +1, 1 => -1

    asum = model.NewIntVar(0, 0, "asum")
    bsum = model.NewIntVar(bsum_value, bsum_value, "bsum")
    model.Add(asum == 50 - 2 * sum(x[0::2]))
    model.Add(bsum == 50 - 2 * sum(x[1::2]))

    # Alternation flips the even-index half and preserves A_sum=0, B_sum and
    # energy, so use it to fix x0=0 (+1) as a symmetry representative.
    model.Add(x[0] == 0)

    corr: dict[int, cp_model.IntVar] = {}
    even_q = []
    even_corr = []

    for k in range(1, N):
        length = N - k
        z = []
        for i in range(length):
            d = model.NewBoolVar(f"z_{k}_{i}")
            # d == x_i XOR x_{i+k}; d=1 means a -1 product.
            model.AddBoolXOr([x[i], x[i + k], d.Not()])
            z.append(d)
        m = model.NewIntVar(0, length, f"m{k}")
        model.Add(m == sum(z))
        c = model.NewIntVar(-length, length, f"c{k}")
        model.Add(c == length - 2 * m)
        corr[k] = c

        if k % 2 == 0:
            q = model.NewIntVar(0, EVEN_ENERGY, f"q{k}")
            rows = [
                (value, value * value)
                for value in range(-length, length + 1, 2)
                if value * value <= EVEN_ENERGY
            ]
            model.AddAllowedAssignments([c, q], rows)
            even_q.append(q)
            even_corr.append(c)

    # Exact O=66 odd-pair pattern.
    if case == "single18":
        flags = []
        for k in range(1, 50, 2):
            j = N - k
            h = model.NewBoolVar(f"d18_{k}")
            model.AddAllowedAssignments(
                [corr[k], corr[j], h],
                [(-1, 1, 0), (1, -1, 0), (-3, 3, 1), (3, -3, 1)],
            )
            flags.append(h)
        model.Add(sum(flags) == 1)
    else:
        states = []
        nonzero = []
        for k in range(1, 50, 2):
            j = N - k
            st = model.NewIntVar(-1, 1, f"d10state_{k}")
            model.AddAllowedAssignments(
                [corr[k], corr[j], st],
                [
                    (-1, 1, 0), (1, -1, 0),
                    (1, 3, 1), (3, 1, 1),
                    (-1, -3, -1), (-3, -1, -1),
                ],
            )
            nz = model.NewBoolVar(f"d10nz_{k}")
            model.AddAllowedAssignments([st, nz], [(-1, 1), (0, 0), (1, 1)])
            states.append(st)
            nonzero.append(nz)
        model.Add(sum(states) == 0)
        model.Add(sum(nonzero) == 2)

    # Exact total E=574 once O=66 is fixed.
    model.Add(sum(even_q) == EVEN_ENERGY)

    # Sum of even correlations: 2*sum(C_even)=a^2+b^2-100.
    model.Add(2 * sum(even_corr) == bsum_value * bsum_value - 100)

    # Redundant exact opposite-even-lag congruence C_k+C_{100-k}=0 (mod 4).
    # It is implied by the sequence variables but is useful propagation.
    for k in range(2, 50, 2):
        j = N - k
        l1, l2 = N - k, k
        rows = [
            (u, v)
            for u in range(-l1, l1 + 1, 2)
            for v in range(-l2, l2 + 1, 2)
            if (u + v) % 4 == 0 and u * u + v * v <= EVEN_ENERGY
        ]
        model.AddAllowedAssignments([corr[k], corr[j]], rows)

    # Global product +1 for exact E=574 implies C_50 == 2 (mod 4).
    model.AddAllowedAssignments(
        [corr[50]],
        [(v,) for v in range(-50, 51, 2) if v % 4 == 2 and v * v <= EVEN_ENERGY],
    )

    # z=i Fourier identity.  A_alt=q0-q2, B_alt=q1-q3.
    a_alt = model.NewIntVar(-50, 50, "a_alt")
    b_alt = model.NewIntVar(-50, 50, "b_alt")
    model.Add(
        a_alt == sum((1 if j % 2 == 0 else -1) * (1 - 2 * x[2 * j]) for j in range(50))
    )
    model.Add(
        b_alt == sum((1 if j % 2 == 0 else -1) * (1 - 2 * x[2 * j + 1]) for j in range(50))
    )
    a2 = add_square_table(model, a_alt, "a_alt_sq", -50, 50)
    b2 = add_square_table(model, b_alt, "b_alt_sq", -50, 50)
    alternating_even = sum(
        (1 if r % 2 == 0 else -1) * corr[2 * r] for r in range(1, 50)
    )
    model.Add(a2 + b2 == N + 2 * alternating_even)

    return model, x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", choices=["single18", "double-mixed"], required=True)
    ap.add_argument("--bsum", type=int, choices=VALID_BSUM, required=True)
    ap.add_argument("--seconds", type=float, default=300.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    model, x = build(args.case, args.bsum)
    validation = model.Validate()
    if validation:
        raise SystemExit(f"MODEL_INVALID {validation}")

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
        f"case={args.case}",
        f"bsum={args.bsum}",
        solver.StatusName(status),
        f"wall={time.time()-start:.3f}",
        f"branches={solver.NumBranches()}",
        f"conflicts={solver.NumConflicts()}",
    )
    if status == cp_model.INFEASIBLE:
        print(f"PROVED_INFEASIBLE case={args.case} bsum={args.bsum}")
        return
    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        print(f"UNRESOLVED case={args.case} bsum={args.bsum}")
        return

    seq = "".join("-" if solver.Value(v) else "+" for v in x)
    e, o, cs, a, b = exact(seq)
    classes = pair_class(cs)
    print(
        f"FOUND case={args.case} bsum={args.bsum} energy={e} odd={o} "
        f"asum={a} actual_bsum={b} classes={classes} seq={seq}"
    )
    if e != TARGET or o != ODD_ENERGY or a != 0 or b != args.bsum:
        raise SystemExit("independent exact score/half-sum check failed")
    e18, pos10, neg10 = classes
    if args.case == "single18":
        ok = len(e18) == 1 and not pos10 and not neg10
    else:
        ok = not e18 and len(pos10) == 1 and len(neg10) == 1
    if not ok:
        raise SystemExit("independent odd-pattern check failed")


if __name__ == "__main__":
    main()
