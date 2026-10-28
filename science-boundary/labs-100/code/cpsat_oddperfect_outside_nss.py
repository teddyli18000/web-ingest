#!/usr/bin/env python3
"""Exact LABS-100 feasibility for E<=574, odd energy 50, outside near-skew.

Use parity halves A_i=s_{2i}, B_i=s_{2i+1}.  Odd-perfect implies a*b=0,
where a=sum A and b=sum B.  Reversal swaps the halves and global/alternating
sign changes normalize every solution to

    A_0=B_0=+1, b=0, a in {0,2,...,20}.

The bound |a|<=20 follows from Cauchy and even energy <=524.

The model directly enforces all 50 odd correlations to be +/-1, the 49 scaled
even correlations D_r=C_{2r}/2 with sum D_r^2<=131, exact correlation-sum
and z=i Fourier identities, and excludes both skew-99 endpoint orientations:
positions 1..99 skew and positions 0..98 skew.  The near-skew exclusion is
sound because the entire near-skew manifold is independently proved to have
minimum N=100 energy 578.
"""
from __future__ import annotations

import argparse
import time
from ortools.sat.python import cp_model

N = 50
FULL_N = 100


def exact(seq: str):
    x = [1 if c == "+" else -1 for c in seq]
    cs = [sum(x[i] * x[i+k] for i in range(FULL_N-k)) for k in range(1, FULL_N)]
    e = sum(c*c for c in cs)
    odd = sum(cs[k-1]*cs[k-1] for k in range(1, FULL_N, 2))
    a = sum(x[0::2]); b = sum(x[1::2])
    return e, odd, cs, a, b


def suffix_nearskew(seq: str) -> bool:
    s = [1 if c == "+" else -1 for c in seq]
    return all(s[p] * s[100-p] == (-1 if p & 1 else 1) for p in range(1, 50))


def prefix_nearskew(seq: str) -> bool:
    s = [1 if c == "+" else -1 for c in seq]
    return all(s[q] * s[98-q] == (-1 if (q+1) & 1 else 1) for q in range(0, 49))


def bit_at(A, B, i: int):
    return A[i//2] if i % 2 == 0 else B[i//2]


def xor_var(model: cp_model.CpModel, x, y, name: str):
    z = model.NewBoolVar(name)
    model.AddBoolXOr([x, y, z.Not()])  # z == x xor y
    return z


def square_table(model: cp_model.CpModel, v, lo: int, hi: int, cap: int, name: str):
    q = model.NewIntVar(0, cap, name)
    model.AddAllowedAssignments([v, q], [(x, x*x) for x in range(lo, hi+1) if x*x <= cap])
    return q


def add_not_nearskew(model: cp_model.CpModel, A, B):
    # Suffix positions 1..99 skew: s_p*s_{100-p}=(-1)^p.
    suffix_viol = []
    for p in range(1, 50):
        z = xor_var(model, bit_at(A,B,p), bit_at(A,B,100-p), f"ns_s_{p}")
        # required xor is 1 for odd p, 0 for even p; literal below means violation.
        suffix_viol.append(z.Not() if p & 1 else z)
    model.AddBoolOr(suffix_viol)

    # Prefix positions 0..98 skew (the reversal of the suffix orientation):
    # s_q*s_{98-q}=(-1)^(q+1), q=0..48.
    prefix_viol = []
    for q in range(0, 49):
        z = xor_var(model, bit_at(A,B,q), bit_at(A,B,98-q), f"ns_p_{q}")
        required_xor = 1 if q % 2 == 0 else 0
        prefix_viol.append(z.Not() if required_xor else z)
    model.AddBoolOr(prefix_viol)


def build(asum: int, target: int):
    if asum not in range(0, 21, 2):
        raise ValueError("canonical asum must be one of 0,2,...,20")
    if target > 574:
        raise ValueError("this target model is calibrated for E<=574")

    model = cp_model.CpModel()
    A = [model.NewBoolVar(f"A{i}") for i in range(N)] # 0 => +1, 1 => -1
    B = [model.NewBoolVar(f"B{i}") for i in range(N)]
    model.Add(A[0] == 0)
    model.Add(B[0] == 0)
    model.Add(50 - 2*sum(A) == asum)
    model.Add(50 - 2*sum(B) == 0)

    # Odd correlations C_{2r+1}, r=0..49.  Each is +/-1.
    odd_pos = []
    for r in range(50):
        terms = []
        # A_t B_{t+r}, t=0..49-r.
        for t in range(0, 50-r):
            terms.append(xor_var(model, A[t], B[t+r], f"oA_{r}_{t}"))
        # B_t A_{t+r+1}, t=0..48-r.
        for t in range(0, 49-r):
            terms.append(xor_var(model, B[t], A[t+r+1], f"oB_{r}_{t}"))
        L = 99 - 2*r
        pos = model.NewBoolVar(f"odd_pos_{r}")  # 1 => +1
        # correlation L-2*m = +1 for pos=1, -1 for pos=0.
        model.Add(sum(terms) == (L+1)//2 - pos)
        odd_pos.append(pos)

    # Explicit opposite-lag consequence C_k+C_{100-k}=0 for odd-perfect.
    for r in range(25):
        model.Add(odd_pos[r] + odd_pos[49-r] == 1)

    # Even correlations scaled by two: D_r=C_{2r}/2.
    qcap = (target - 50)//4
    dvars = []
    qvars = []
    for r in range(1, 50):
        za = [xor_var(model, A[t], A[t+r], f"eA_{r}_{t}") for t in range(50-r)]
        zb = [xor_var(model, B[t], B[t+r], f"eB_{r}_{t}") for t in range(50-r)]
        d = model.NewIntVar(-(50-r), 50-r, f"d_{r}")
        model.Add(d == (50-r) - sum(za) - sum(zb))
        q = square_table(model, d, -(50-r), 50-r, qcap, f"q_{r}")
        dvars.append(d); qvars.append(q)
    model.Add(sum(qvars) <= qcap)

    # Exact sum of even correlations / 2.
    model.Add(sum(dvars) == (asum*asum - 100)//4)

    # z=i identity.  q_j are sums of signs in residue classes mod 4.
    qsum = []
    for j in range(4):
        bits = [bit_at(A,B,i) for i in range(j,100,4)]
        v = model.NewIntVar(-25,25,f"res_{j}")
        model.Add(v == 25 - 2*sum(bits))
        qsum.append(v)
    u = model.NewIntVar(-50,50,"u")
    v = model.NewIntVar(-50,50,"v")
    model.Add(u == qsum[0]-qsum[2])
    model.Add(v == qsum[1]-qsum[3])
    u2 = square_table(model,u,-50,50,2500,"u2")
    v2 = square_table(model,v,-50,50,2500,"v2")
    altD = sum((1 if r%2==0 else -1)*dvars[r-1] for r in range(1,50))
    model.Add(u2 + v2 == 100 + 4*altD)

    add_not_nearskew(model,A,B)
    return model,A,B


def reconstruct(solver, A, B):
    out=[]
    for i in range(50):
        out.append("-" if solver.Value(A[i]) else "+")
        out.append("-" if solver.Value(B[i]) else "+")
    return "".join(out)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--asum",type=int,required=True)
    ap.add_argument("--target",type=int,default=574)
    ap.add_argument("--seconds",type=float,default=120)
    ap.add_argument("--workers",type=int,default=4)
    ap.add_argument("--seed",type=int,default=1)
    args=ap.parse_args()
    model,A,B=build(args.asum,args.target)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=args.seconds
    solver.parameters.num_search_workers=args.workers
    solver.parameters.random_seed=args.seed
    solver.parameters.randomize_search=True
    solver.parameters.cp_model_presolve=True
    solver.parameters.symmetry_level=2
    t0=time.time(); status=solver.Solve(model); wall=time.time()-t0
    print("STATUS",f"asum={args.asum}",solver.StatusName(status),f"wall={wall:.3f}",f"branches={solver.NumBranches()}",f"conflicts={solver.NumConflicts()}")
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        print("NO_CERTIFICATE")
        return
    seq=reconstruct(solver,A,B)
    e,o,cs,a,b=exact(seq)
    print("FOUND",f"energy={e}",f"odd={o}",f"even={e-o}",f"asum={a}",f"bsum={b}",f"suffix_nss={suffix_nearskew(seq)}",f"prefix_nss={prefix_nearskew(seq)}",f"seq={seq}")
    if e>args.target or o!=50 or a!=args.asum or b!=0 or suffix_nearskew(seq) or prefix_nearskew(seq):
        raise SystemExit("independent validation failed")

if __name__=="__main__":
    main()
