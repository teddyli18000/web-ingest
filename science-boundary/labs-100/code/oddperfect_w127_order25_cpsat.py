#!/usr/bin/env python3
"""Exact order-25 necessary-condition test for the odd-perfect W=127 branch.

For an odd-perfect N=100 LABS candidate in normalized half-sum class (20,0),
W=E_even/4=127 forces the 49 even-correlation halves d_r=C_(2r)/2 to be
23 copies of 1 and 26 copies of 2.  Opposite-lag parity then forces
 d_r=d_(50-r), so the parity halves form a negaperiodic Golay pair.

Compress A and B modulo 25.  Write
  p_i=(A_i+A_(i+25))/2, q_i=(B_i+B_(i+25))/2,
so p,q are ternary {-1,0,1} sequences of length 25 with sums (10,0).
The periodic odd-perfect cross equation is
  p q* + x q p* = 0  in Z[x]/(x^25-1).
Since 2*13 == 1 (mod 25), putting c=x^13 q makes this
  p c* + c p* = 0.

At W=127, the combined periodic autocorrelation after this compression has
  ||p||^2+||c||^2 = 26,
  PAF_p(r)+PAF_c(r) in {2,3,4},  r != 0.

This script checks those necessary conditions exactly with CP-SAT.  The support
size ka=||p||^2 is sharded over the only possible values 10,12,...,24.  A
rotation symmetry is removed by fixing p_0=+1, which is safe because sum p=10.

A proof of INFEASIBLE for every ka shard excludes the entire W=127 / E=558
branch.  FEASIBLE only means the order-25 projection survives; it is not a LABS
certificate.
"""

import argparse
import json
import os
import sys
from ortools.sat.python import cp_model

N = 25


def product(model, x, y, name):
    z = model.NewIntVar(-1, 1, name)
    model.AddMultiplicationEquality(z, [x, y])
    return z


def build_model(ka: int):
    if ka not in range(10, 25, 2):
        raise ValueError("ka must be one of 10,12,...,24")
    kc = 26 - ka

    m = cp_model.CpModel()
    a = [m.NewIntVar(-1, 1, f"a{i}") for i in range(N)]
    c = [m.NewIntVar(-1, 1, f"c{i}") for i in range(N)]
    aa = [m.NewIntVar(0, 1, f"aa{i}") for i in range(N)]
    cc = [m.NewIntVar(0, 1, f"cc{i}") for i in range(N)]
    for i in range(N):
        m.AddAbsEquality(aa[i], a[i])
        m.AddAbsEquality(cc[i], c[i])

    m.Add(sum(a) == 10)
    m.Add(sum(c) == 0)
    m.Add(sum(aa) == ka)
    m.Add(sum(cc) == kc)

    # Rotation symmetry.  Since sum(a)=10, some a_i=+1; rotate it to index 0.
    m.Add(a[0] == 1)

    # Cross condition is self-reciprocal, so r=0..12 is complete.
    for r in range(13):
        terms = []
        for i in range(N):
            j = (i - r) % N
            terms.append(product(m, a[i], c[j], f"xac_{r}_{i}"))
            terms.append(product(m, c[i], a[j], f"xca_{r}_{i}"))
        m.Add(sum(terms) == 0)

    # Combined autocorrelation is symmetric, so r=1..12 is complete.
    corr = []
    for r in range(1, 13):
        terms = []
        for i in range(N):
            j = (i + r) % N
            terms.append(product(m, a[i], a[j], f"xaa_{r}_{i}"))
            terms.append(product(m, c[i], c[j], f"xcc_{r}_{i}"))
        cr = m.NewIntVar(2, 4, f"corr{r}")
        m.Add(cr == sum(terms))
        corr.append(cr)

    # sum_r PAF(r) = (sum a)^2+(sum c)^2 = 100.  With PAF(0)=26,
    # the 12 paired nonzero correlations sum to 37.  This is redundant but
    # materially strengthens propagation.
    m.Add(sum(corr) == 37)
    return m, a, c, corr


def verify_projection(av, cv):
    assert len(av) == len(cv) == N
    assert all(x in (-1, 0, 1) for x in av + cv)
    if sum(av) != 10 or sum(cv) != 0:
        return False, "bad sums"
    if sum(x * x for x in av) + sum(x * x for x in cv) != 26:
        return False, "bad norm"
    for r in range(N):
        s = sum(av[i] * cv[(i - r) % N] + cv[i] * av[(i - r) % N] for i in range(N))
        if s != 0:
            return False, f"cross r={r} value={s}"
    cors = []
    for r in range(1, N):
        s = sum(av[i] * av[(i + r) % N] + cv[i] * cv[(i + r) % N] for i in range(N))
        if s not in (2, 3, 4):
            return False, f"autocorr r={r} value={s}"
        cors.append(s)
    if sum(cors) != 74:
        return False, f"bad nonzero autocorr sum={sum(cors)}"
    return True, "ok"


def solve(ka: int, seconds: float, workers: int, seed: int):
    model, a, c, corr = build_model(ka)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.log_search_progress = False

    status = solver.Solve(model)
    name = solver.StatusName(status)
    out = {
        "ka": ka,
        "kc": 26 - ka,
        "status": name,
        "wall_time": solver.WallTime(),
        "branches": solver.NumBranches(),
        "conflicts": solver.NumConflicts(),
    }
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        av = [solver.Value(x) for x in a]
        cv = [solver.Value(x) for x in c]
        out["a"] = av
        out["c"] = cv
        out["corr_1_12"] = [solver.Value(x) for x in corr]
        ok, why = verify_projection(av, cv)
        out["independent_projection_check"] = {"ok": ok, "detail": why}
        if not ok:
            print(json.dumps(out, sort_keys=True))
            return 3
    print(json.dumps(out, sort_keys=True))
    if status == cp_model.INFEASIBLE:
        return 0
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        return 0
    return 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ka", type=int, required=True)
    ap.add_argument("--seconds", type=float, default=900.0)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    return solve(args.ka, args.seconds, args.workers, args.seed)


if __name__ == "__main__":
    sys.exit(main())
