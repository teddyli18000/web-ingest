#!/usr/bin/env python3
"""Exact CP-SAT feasibility model for LABS N=100.

Requires OR-Tools.  The model uses one Boolean spin bit x_i, Boolean XOR
variables for every pair contributing to a lag, integer autocorrelations, and
exact square constraints.  Any FEASIBLE result is independently rescored
before it is printed.
"""

from __future__ import annotations

import argparse
import time

import ortools
from ortools.sat.python import cp_model

N = 100
INCUMBENT = "++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-"


def energy(seq: str) -> int:
    s = [1 if ch == "+" else -1 for ch in seq]
    return sum(
        sum(s[i] * s[i + k] for i in range(N - k)) ** 2
        for k in range(1, N)
    )


def build(bound: int, hint: bool) -> tuple[cp_model.CpModel, list[cp_model.IntVar], cp_model.IntVar]:
    m = cp_model.CpModel()
    x = [m.new_bool_var(f"x{i}") for i in range(N)]  # 0 => +1, 1 => -1

    # Global sign plus alternation/global-sign composition can normalize the
    # first two signs to +1 without changing energy.
    m.add(x[0] == 0)
    m.add(x[1] == 0)

    squares = []
    for k in range(1, N):
        length = N - k
        diffs = []
        for i in range(length):
            d = m.new_bool_var(f"d_{i}_{i+k}")
            # d = x_i XOR x_{i+k}: x_i XOR x_j XOR (not d) is true.
            m.add_bool_xor([x[i], x[i + k], d.negated()])
            diffs.append(d)
        h = m.new_int_var(0, length, f"h{k}")
        m.add(h == sum(diffs))
        c = m.new_int_var(-length, length, f"c{k}")
        m.add(c == length - 2 * h)
        sq = m.new_int_var(0, min(length * length, bound), f"sq{k}")
        m.add_multiplication_equality(sq, [c, c])
        squares.append(sq)

    total = m.new_int_var(0, bound, "energy")
    m.add(total == sum(squares))
    m.add(total <= bound)

    if hint:
        for var, ch in zip(x, INCUMBENT):
            m.add_hint(var, 0 if ch == "+" else 1)

    return m, x, total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bound", type=int, required=True)
    ap.add_argument("--seconds", type=float, default=60.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--hint", action="store_true")
    ap.add_argument("--log", action="store_true")
    args = ap.parse_args()

    print(f"ORTOOLS {ortools.__version__}")
    print(f"MODEL N={N} bound={args.bound} hint={int(args.hint)} workers={args.workers} seconds={args.seconds}")
    t0 = time.time()
    model, x, total = build(args.bound, args.hint)
    print(f"BUILD seconds={time.time()-t0:.3f}")

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = args.workers
    solver.parameters.log_search_progress = args.log
    solver.parameters.random_seed = 1
    status = solver.solve(model)
    print(
        "STATUS",
        solver.status_name(status),
        f"wall={solver.wall_time:.3f}",
        f"branches={solver.num_branches}",
        f"conflicts={solver.num_conflicts}",
    )
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        seq = "".join("-" if solver.value(v) else "+" for v in x)
        reported = solver.value(total)
        checked = energy(seq)
        print(f"SOLUTION reported={reported} checked={checked} seq={seq}")
        if checked != reported or checked > args.bound:
            raise RuntimeError("independent score mismatch")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
