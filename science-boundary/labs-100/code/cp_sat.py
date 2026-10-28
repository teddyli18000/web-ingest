#!/usr/bin/env python3
"""CP-SAT formulation for LABS.

This is a feasibility/optimization probe in a representation different from the
local-search kernels used elsewhere in this topic.  For every lag k we introduce
Boolean XOR variables for whether s_i and s_{i+k} disagree.  If m_k is their
sum then C_k = (N-k)-2*m_k, so C_k^2 is an exact element lookup rather than a
floating-point or relaxed nonlinear objective.

For N=100, use --upper 578 with the public incumbent as a complete solution hint
and ask CP-SAT to minimize energy.  A result <=574 is a Few Shots candidate and
must still be independently checked by code/verify.py and the official verifier.
"""

from __future__ import annotations

import argparse
import sys
from ortools.sat.python import cp_model

INCUMBENT_100 = (
    "++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--"
    "+-+-+-+-++---++---++-+-++-+-++--+-+-"
)


def spin_linear(bits, coeffs):
    """Return sum coeff_i * (2*b_i-1)."""
    return 2 * sum(c * b for c, b in zip(coeffs, bits)) - sum(coeffs)


def add_square_table(model: cp_model.CpModel, x, lo: int, hi: int, name: str):
    y = model.NewIntVar(0, max(lo * lo, hi * hi), name)
    model.AddAllowedAssignments([x, y], [(v, v * v) for v in range(lo, hi + 1)])
    return y


def build_model(n: int, upper: int | None, hint: str | None):
    model = cp_model.CpModel()
    b = [model.NewBoolVar(f"b{i}") for i in range(n)]

    # Global complement symmetry: every equivalence class has a representative
    # with the first spin +1.
    model.Add(b[0] == 1)

    corr = []
    sq = []
    for k in range(1, n):
        length = n - k
        xors = []
        for i in range(length):
            a, d = b[i], b[i + k]
            z = model.NewBoolVar(f"x_{k}_{i}")
            # z == a XOR d, encoded linearly.
            model.Add(z >= a - d)
            model.Add(z >= d - a)
            model.Add(z <= a + d)
            model.Add(z <= 2 - a - d)
            xors.append(z)

        m = model.NewIntVar(0, length, f"m{k}")
        model.Add(m == sum(xors))
        c = model.NewIntVar(-length, length, f"c{k}")
        model.Add(c == length - 2 * m)
        corr.append(c)

        # Exact lookup q_k = ((N-k)-2*m_k)^2.
        values = [(length - 2 * j) ** 2 for j in range(length + 1)]
        q = model.NewIntVar(0, length * length, f"q{k}")
        model.AddElement(m, values, q)
        sq.append(q)

    energy = model.NewIntVar(0, sum((n - k) ** 2 for k in range(1, n)), "energy")
    model.Add(energy == sum(sq))
    if upper is not None:
        model.Add(energy <= upper)
    model.Minimize(energy)

    # Redundant exact Fourier identities.  They are implied by the XOR model,
    # but expose long-range consistency to CP-SAT propagation.
    s = model.NewIntVar(-n, n, "S1")
    model.Add(s == spin_linear(b, [1] * n))
    s2 = add_square_table(model, s, -n, n, "S1sq")
    model.Add(2 * sum(corr) == s2 - n)

    alt_coeff = [1 if (i % 2 == 0) else -1 for i in range(n)]
    t = model.NewIntVar(-n, n, "Sm1")
    model.Add(t == spin_linear(b, alt_coeff))
    t2 = add_square_table(model, t, -n, n, "Sm1sq")
    model.Add(2 * sum(((-1) ** (k + 1)) * corr[k] for k in range(n - 1)) == t2 - n)

    # z=i identity: |sum_j s_j i^j|^2 = N + 2*sum_{even k}(-1)^(k/2) C_k.
    re_coeff = [1 if i % 4 == 0 else -1 if i % 4 == 2 else 0 for i in range(n)]
    im_coeff = [1 if i % 4 == 1 else -1 if i % 4 == 3 else 0 for i in range(n)]
    re = model.NewIntVar(-n, n, "Si_re")
    im = model.NewIntVar(-n, n, "Si_im")
    model.Add(re == spin_linear(b, re_coeff))
    model.Add(im == spin_linear(b, im_coeff))
    re2 = add_square_table(model, re, -n, n, "Si_re_sq")
    im2 = add_square_table(model, im, -n, n, "Si_im_sq")
    even_fourier = []
    for k in range(2, n, 2):
        # corr[k-1] is C_k.
        even_fourier.append((1 if (k // 2) % 2 == 0 else -1) * corr[k - 1])
    model.Add(re2 + im2 == n + 2 * sum(even_fourier))

    if hint is not None:
        if len(hint) != n or any(ch not in "+-" for ch in hint):
            raise ValueError("hint must be a +/- sequence of length n")
        if hint[0] != "+":
            raise ValueError("hint must respect b[0]=1 symmetry")
        for var, ch in zip(b, hint):
            model.AddHint(var, 1 if ch == "+" else 0)

    return model, b, energy, corr


def exact_energy(seq: str) -> tuple[int, list[int]]:
    s = [1 if ch == "+" else -1 for ch in seq]
    cs = [sum(s[i] * s[i + k] for i in range(len(s) - k)) for k in range(1, len(s))]
    return sum(c * c for c in cs), cs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--upper", type=int, default=None)
    ap.add_argument("--goal", type=int, default=None)
    ap.add_argument("--seconds", type=float, default=60.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--no-hint", action="store_true")
    ap.add_argument("--log", action="store_true")
    args = ap.parse_args()

    hint = None
    if args.n == 100 and not args.no_hint:
        hint = INCUMBENT_100
        e, _ = exact_energy(hint)
        if e != 578:
            raise RuntimeError(f"incumbent self-check failed: {e}")
        if args.upper is not None and e > args.upper:
            hint = None

    model, bits, energy, corr = build_model(args.n, args.upper, hint)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = args.seed
    solver.parameters.randomize_search = True
    solver.parameters.log_search_progress = args.log

    status = solver.Solve(model)
    name = solver.StatusName(status)
    print(
        f"STATUS {name} wall={solver.WallTime():.3f} branches={solver.NumBranches()} "
        f"conflicts={solver.NumConflicts()} bound={solver.BestObjectiveBound()}"
    )

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return 0

    seq = "".join("+" if solver.Value(v) else "-" for v in bits)
    checked, cs = exact_energy(seq)
    reported = solver.Value(energy)
    if checked != reported:
        raise RuntimeError(f"independent score mismatch: solver={reported} exact={checked}")
    # Also make sure the explicit C_k variables agree with a fresh computation.
    for k, (cv, c) in enumerate(zip(corr, cs), start=1):
        if solver.Value(cv) != c:
            raise RuntimeError(f"correlation mismatch at k={k}")

    print(f"SOLUTION energy={checked} seq={seq}")
    if args.goal is not None and checked <= args.goal:
        print(f"CANDIDATE goal={args.goal} energy={checked} seq={seq}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
