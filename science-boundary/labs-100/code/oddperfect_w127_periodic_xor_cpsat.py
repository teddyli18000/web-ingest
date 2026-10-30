#!/usr/bin/env python3
"""Exact full-periodic XOR projection for the odd-perfect (20,0), W=127 branch.

This model is stronger than the order-25 ternary compression but still only a
necessary condition for a full LABS candidate: it enforces every periodic
constraint implied by W127, while omitting the negaperiodic/aperiodic lift.

Let A,B be the length-50 parity halves, with sums (20,0).  W127 forces
opposite even aperiodic correlations to agree and d_r=C_(2r)/2 to be 23 ones
and 26 twos.  Consequently

  PAF_A(r)+PAF_B(r) is 4 (23 shifts) or 8 (26 shifts), r != 0.

Odd-perfectness gives the periodic cross equation

  R_AB(r)+R_BA(r+1)=0, r in Z_50.

In negative-bit variables these are pure XOR-cardinality equations:

  combined within-half disagreements = 48 or 46,
  combined cross disagreements       = 50.

The optional ka shard fixes the number of i=0..24 with A_i=A_(i+25).
For W127, the B equality count is 26-ka.  Cyclic translation is a genuine
symmetry of this periodic projection, so A_0=+1 is safe; B -> -B is also a
symmetry (sum B=0), so B_0=+1 is fixed as well.

INFEASIBLE proves that no W127 LABS candidate can lie in that ka shard.
FEASIBLE is only a periodic projection survivor and must be lifted through the
NGP/aperiodic equations before it is a LABS candidate.
"""
from __future__ import annotations

import argparse
import json
import sys
from ortools.sat.python import cp_model

L = 50


def xor_var(model, x, y, name):
    d = model.NewBoolVar(name)
    model.AddBoolXOr([x, y, d.Not()])
    return d


def build(ka=None):
    if ka is not None and ka not in range(10, 25, 2):
        raise ValueError('ka must be one of 10,12,...,24')

    m = cp_model.CpModel()
    # 1 means sign -1.
    a = [m.NewBoolVar(f'a{i}') for i in range(L)]
    b = [m.NewBoolVar(f'b{i}') for i in range(L)]
    m.Add(sum(a) == 15)  # sum signs =20
    m.Add(sum(b) == 25)  # sum signs =0

    # Safe symmetries for the purely periodic projection.
    m.Add(a[0] == 0)     # common cyclic rotation; A has + entries
    m.Add(b[0] == 0)     # B -> -B after the rotation

    # Cache all pair XORs so each Boolean relation is encoded once.
    aa = {}
    bb = {}
    ab = {}
    for i in range(L):
        for j in range(L):
            if i < j:
                aa[i,j] = xor_var(m, a[i], a[j], f'aa_{i}_{j}')
                bb[i,j] = xor_var(m, b[i], b[j], f'bb_{i}_{j}')
            ab[i,j] = xor_var(m, a[i], b[j], f'ab_{i}_{j}')

    def same_xor(cache, i, j):
        if i == j:
            return 0
        if i > j:
            i,j = j,i
        return cache[i,j]

    hi = []
    for r in range(1, L):
        dis = []
        for i in range(L):
            j = (i + r) % L
            dis.append(same_xor(aa, i, j))
            dis.append(same_xor(bb, i, j))
        t = m.NewBoolVar(f'paf8_{r}')
        # PAF 4 -> disagreements 48; PAF 8 -> disagreements 46.
        m.Add(sum(dis) == 48 - 2*t)
        hi.append(t)

    # Periodic PAF symmetry is exact; sharing the flags strengthens propagation.
    for r in range(1, 25):
        m.Add(hi[r-1] == hi[50-r-1])
    # r=25 is self-opposite and W127 has d_25=1 -> PAF=4.
    m.Add(hi[24] == 0)
    m.Add(sum(hi) == 26)

    # H=A B* + x B A*=0: 100 cross products sum to zero, hence 50
    # sign disagreements at every cyclic shift r.
    for r in range(L):
        dis = []
        for i in range(L):
            dis.append(ab[i, (i+r) % L])
            # B_i versus A_(i+r+1) uses the same ab cache reversed.
            dis.append(ab[(i+r+1) % L, i])
        m.Add(sum(dis) == 50)

    if ka is not None:
        ae = []
        be = []
        for i in range(25):
            da = same_xor(aa, i, i+25)
            db = same_xor(bb, i, i+25)
            ea = m.NewBoolVar(f'aeq25_{i}')
            eb = m.NewBoolVar(f'beq25_{i}')
            m.Add(ea + da == 1)
            m.Add(eb + db == 1)
            ae.append(ea); be.append(eb)
        m.Add(sum(ae) == ka)
        m.Add(sum(be) == 26-ka)

    return m, a, b


def verify_periodic(av, bv):
    A = [1 if x == 0 else -1 for x in av]
    B = [1 if x == 0 else -1 for x in bv]
    if sum(A) != 20 or sum(B) != 0:
        return False, 'half sums'
    vals = []
    for r in range(1,50):
        p = sum(A[i]*A[(i+r)%50] + B[i]*B[(i+r)%50] for i in range(50))
        if p not in (4,8):
            return False, f'periodic PAF r={r} value={p}'
        vals.append(p)
    if vals.count(4) != 23 or vals.count(8) != 26:
        return False, 'periodic PAF multiplicities'
    for r in range(50):
        h = sum(A[i]*B[(i+r)%50] + B[i]*A[(i+r+1)%50] for i in range(50))
        if h != 0:
            return False, f'cross r={r} value={h}'
    return True, 'ok'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ka', type=int)
    ap.add_argument('--seconds', type=float, default=900)
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--seed', type=int, default=1)
    args = ap.parse_args()

    model,a,b = build(args.ka)
    err = model.Validate()
    if err:
        raise SystemExit('MODEL_INVALID '+err)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = args.seconds
    s.parameters.num_search_workers = args.workers
    s.parameters.random_seed = args.seed
    s.parameters.randomize_search = True
    s.parameters.cp_model_presolve = True
    s.parameters.symmetry_level = 2
    st = s.Solve(model)
    out = dict(ka=args.ka,status=s.StatusName(st),wall_time=s.WallTime(),
               branches=s.NumBranches(),conflicts=s.NumConflicts())
    if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        av=[s.Value(x) for x in a]; bv=[s.Value(x) for x in b]
        ok,detail=verify_periodic(av,bv)
        out.update(A=''.join('-' if x else '+' for x in av),
                   B=''.join('-' if x else '+' for x in bv),
                   independent_projection_check={'ok':ok,'detail':detail})
        print(json.dumps(out,sort_keys=True))
        if not ok: raise SystemExit('independent periodic check failed')
        return 0
    print(json.dumps(out,sort_keys=True))
    if st == cp_model.INFEASIBLE: return 0
    return 2

if __name__ == '__main__':
    sys.exit(main())
