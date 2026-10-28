#!/usr/bin/env python3
"""Exact CP-SAT feasibility model for canonical N=100 near-skew via parity halves.

After global-sign and alternating-sign normalization, write

    A_j = s_{2j}, B_j = s_{2j+1}, j=0..49.

Canonical near-skew gives A_0=B_0=+1, A_j=A_{50-j}, and
B_{49-j}=-B_j. Hence A has 25 free signs and B has 24 free signs.
All odd N=100 correlations have magnitude one. For r=1..49,

    C_{2r}(s) = C_A(r) + C_B(r) = 2 D_r,
    D_r = (50-r) - mism_A(r) - mism_B(r).

Therefore E<=574 is exactly sum_r D_r^2 <= 131. This formulation models
that scaled objective directly and states the exact near-skew parity relation
D_r mod 2 = 1 iff A_r=-1.
"""
from __future__ import annotations

import argparse
import time
from ortools.sat.python import cp_model

N = 50
INC = "++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-"


def exact_full(seq: str):
    s = [1 if c == "+" else -1 for c in seq]
    cs = [sum(s[i] * s[i + k] for i in range(100 - k)) for k in range(1, 100)]
    e = sum(c * c for c in cs)
    odd = sum(cs[k - 1] ** 2 for k in range(1, 100, 2))
    return e, odd, cs


def direct_nss(seq: str) -> bool:
    s = [1 if c == "+" else -1 for c in seq]
    return s[0] == 1 and s[1] == 1 and all(
        s[p] * s[100 - p] == (-1 if p & 1 else 1) for p in range(1, 50)
    )


def _balanced_integer_squares(n: int, total: int) -> int:
    if n == 0:
        return 0 if total == 0 else 10**18
    q, r = divmod(total, n)
    return (n - r) * q * q + r * (q + 1) * (q + 1)


def _same_parity_group_bound(n: int, total: int, parity: int) -> int:
    if n == 0:
        return 0 if total == 0 else 10**18
    if (total - n * parity) & 1:
        return 10**18
    zsum = (total - n * parity) // 2
    return 4 * _balanced_integer_squares(n, zsum) + 4 * parity * zsum + n * parity


def class_bound(asum: int, qcap: int):
    m = (50 - asum) // 2
    if not 0 <= m <= 49:
        return -1, 10**18
    target_sum = (asum * asum - 100) // 4
    # q=sum D_r^2 has parity m. Tighten 131 to the largest attainable parity.
    effective = qcap - ((qcap - (m & 1)) & 1)
    best = 10**18
    for odd_sum in range(-300, 301):
        v = _same_parity_group_bound(m, odd_sum, 1)
        v += _same_parity_group_bound(49 - m, target_sum - odd_sum, 0)
        best = min(best, v)
    return effective, best


def xor_var(model: cp_model.CpModel, x, y, name: str):
    z = model.NewBoolVar(name)
    model.AddBoolXOr([x, y, z.Not()])
    return z


def build(asum: int, target: int, smoke: bool):
    if asum < -20 or asum > 20 or asum % 2:
        raise ValueError("asum must be even in [-20,20]")

    model = cp_model.CpModel()
    A = [model.NewBoolVar(f"A{j}") for j in range(N)]  # 0 => +1
    B = [model.NewBoolVar(f"B{j}") for j in range(N)]
    model.Add(A[0] == 0)
    model.Add(B[0] == 0)
    for j in range(1, 25):
        model.Add(A[50 - j] == A[j])
    for j in range(0, 25):
        model.Add(B[49 - j] != B[j])

    model.Add(50 - 2 * sum(A) == asum)
    m = (50 - asum) // 2
    # All noncentral A negatives occur in equal pairs, so the center bit is
    # exactly the parity of the total number of negatives.
    model.Add(A[25] == (m & 1))

    raw_qcap = (target - 50) // 4
    qcap, arithmetic_lb = class_bound(asum, raw_qcap)
    if arithmetic_lb > qcap:
        model.Add(0 == 1)

    dvars = []
    qvars = []
    for r in range(1, 50):
        L = 50 - r
        za = [xor_var(model, A[i], A[i + r], f"za_{r}_{i}") for i in range(L)]
        zb = [xor_var(model, B[i], B[i + r], f"zb_{r}_{i}") for i in range(L)]
        d = model.NewIntVar(-L, L, f"d{r}")
        model.Add(d == L - sum(za) - sum(zb))

        # Exact residue specialized to near-skew: D_r is odd iff A_r=-1.
        h = model.NewIntVar(-L, L, f"h{r}")
        model.Add(d == 2 * h + A[r])

        q = model.NewIntVar(0, raw_qcap, f"q{r}")
        rows = [(v, v * v) for v in range(-L, L + 1) if v * v <= raw_qcap]
        model.AddAllowedAssignments([d, q], rows)
        dvars.append(d)
        qvars.append(q)

    model.Add(sum(qvars) <= qcap)
    model.Add(sum(dvars) == (asum * asum - 100) // 4)

    inc_bits = [0 if ch == "+" else 1 for ch in INC]
    for j in range(50):
        model.AddHint(A[j], inc_bits[2 * j])
        model.AddHint(B[j], inc_bits[2 * j + 1])
    if smoke:
        for j in range(50):
            model.Add(A[j] == inc_bits[2 * j])
            model.Add(B[j] == inc_bits[2 * j + 1])

    return model, A, B, qcap, arithmetic_lb


def reconstruct(solver, A, B) -> str:
    out = []
    for j in range(50):
        out.append("-" if solver.Value(A[j]) else "+")
        out.append("-" if solver.Value(B[j]) else "+")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asum", type=int, required=True)
    ap.add_argument("--target", type=int, default=574)
    ap.add_argument("--seconds", type=float, default=120.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    ie, io, _ = exact_full(INC)
    assert (ie, io) == (578, 50) and direct_nss(INC)
    model, A, B, qcap, lb = build(args.asum, args.target, args.smoke)
    print("CLASS", f"asum={args.asum}", f"qcap={qcap}", f"arithmetic_lb={lb}")

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = args.seed
    solver.parameters.cp_model_presolve = True
    solver.parameters.symmetry_level = 2

    t0 = time.time()
    status = solver.Solve(model)
    wall = time.time() - t0
    print(
        "STATUS",
        solver.StatusName(status),
        f"asum={args.asum}",
        f"wall={wall:.3f}",
        f"branches={solver.NumBranches()}",
        f"conflicts={solver.NumConflicts()}",
    )
    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        print("NO_CERTIFICATE")
        return

    seq = reconstruct(solver, A, B)
    e, odd, _ = exact_full(seq)
    asum = sum(1 if seq[i] == "+" else -1 for i in range(0, 100, 2))
    bsum = sum(1 if seq[i] == "+" else -1 for i in range(1, 100, 2))
    print(
        "FOUND",
        f"energy={e}",
        f"odd={odd}",
        f"even={e-odd}",
        f"asum={asum}",
        f"bsum={bsum}",
        f"nss={direct_nss(seq)}",
        f"seq={seq}",
    )
    if e > args.target or odd != 50 or not direct_nss(seq) or asum != args.asum or bsum != 0:
        raise SystemExit("independent exact validation failed")


if __name__ == "__main__":
    main()
