#!/usr/bin/env python3
"""Fractional cube-clique cover for the strongest BPZ t=9 obstruction.

An independent set in C7^5 contains at most one point from every binary cube
`a + {0,1}^5`.  Therefore any nonnegative weighted collection of such cubes
that covers each allowed vertex to weight at least one is a rigorous upper
bound on alpha(C7^5 \ D).

This script reconstructs exactly the same 1098-point obstruction as
`bpz_t9_obstruction_mis.py`, solves the sparse covering LP over all 16807 cubes,
then converts the floating solution into an integer-unit cover and verifies
coverage using integer arithmetic.  If total_units < 367 * denominator, the
certificate proves alpha(C7^5 \ D) <= 366 and rules out a 134770 construction
for this specific obstruction without any SAT timeout ambiguity.
"""
import argparse, json, math, sys
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

import bpz_t9_obstruction_mis as mis


def reconstruct(root):
    sys.path.insert(0, str(root.resolve()))
    from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text())
    I=set(map(int,raw['I0']));X=set(map(int,raw['X']));ring=Ring(mis.D)
    digits=tuple(ring.decode(v) for v in range(mis.U))
    for a,b in mis.I_SWAPS:I.remove(a);I.add(b)
    pairs=list(mis.PRIVATE_PAIRS)
    PH=[q if s else a for (a,q),s in zip(pairs,mis.ORIENTATION)]
    PV=[a if s else q for (a,q),s in zip(pairs,mis.ORIENTATION)]
    obs=ring.nbhd(set(PH)) & ring.nbhd(set(PV))
    hits=sorted(X & obs)
    if len(obs)!=1098 or hits!=[10665]:raise RuntimeError(f'obstruction drift {len(obs)} {hits}')
    return ring,digits,obs


def incidence(digits, allowed):
    row_of={v:i for i,v in enumerate(allowed)}
    rows=[];cols=[]
    cube_allowed=[]
    for a in range(mis.U):
        vals=[]
        for v in mis.cube(digits[a]):
            i=row_of.get(v)
            if i is not None:
                rows.append(i);cols.append(a);vals.append(v)
        cube_allowed.append(vals)
    data=np.ones(len(rows),dtype=np.float64)
    A=coo_matrix((data,(rows,cols)),shape=(len(allowed),mis.U)).tocsr()
    return A,cube_allowed,row_of


def integerize(x, cube_allowed, row_of, denominator):
    # Upward rounding cannot hurt coverage; verify with integer arithmetic anyway.
    units=[max(0,int(math.ceil(float(v)*denominator-1e-9))) for v in x]
    cov=[0]*len(row_of)
    for a,u in enumerate(units):
        if not u:continue
        for v in cube_allowed[a]:cov[row_of[v]]+=u
    repairs=0
    # Numerical LP tolerances can leave a row below D after aggressive rounding
    # near zero. Repair deterministically by adding deficit to the first cube
    # containing that vertex; this preserves rigorous validity.
    for v,i in row_of.items():
        if cov[i]>=denominator:continue
        deficit=denominator-cov[i]
        # v belongs to 32 binary cubes. Find the first explicitly stored one.
        chosen=None
        for a,vals in enumerate(cube_allowed):
            if v in vals:
                chosen=a;break
        if chosen is None:raise RuntimeError('allowed vertex belongs to no cube')
        units[chosen]+=deficit;repairs+=deficit
        for z in cube_allowed[chosen]:cov[row_of[z]]+=deficit
    minimum=min(cov)
    if minimum<denominator:raise RuntimeError('integer cover verification failed')
    return units,sum(units),minimum,repairs


def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    ring,digits,obs=reconstruct(args.tan_root)
    allowed=[v for v in range(mis.U) if v not in obs]
    A,cube_allowed,row_of=incidence(digits,allowed)
    print('SETUP',json.dumps({'allowed':len(allowed),'obstruction':len(obs),'cubes':mis.U,'incidences':int(A.nnz)},sort_keys=True),flush=True)
    res=linprog(c=np.ones(mis.U),A_ub=-A,b_ub=-np.ones(len(allowed)),bounds=(0,None),method='highs',options={'presolve':True})
    if not res.success:raise RuntimeError(f'LP failed: {res.message}')
    lp=float(res.fun);print('LP',lp,flush=True)
    certs=[];best=None
    for den in (10_000,1_000_000,100_000_000):
        units,total,minimum,repairs=integerize(res.x,cube_allowed,row_of,den)
        rec={'denominator':den,'total_units':total,'total_weight':total/den,'minimum_coverage_units':minimum,'repair_units':repairs,'proves_alpha_le_366':total<367*den,'nonzero_cubes':sum(u>0 for u in units)}
        certs.append(rec);print('CERT',json.dumps(rec,sort_keys=True),flush=True)
        if best is None or rec['total_weight']<best[0]:best=(rec['total_weight'],den,units,rec)
        if rec['proves_alpha_le_366']:break
    _,den,units,rec=best
    status={'method':'bpz-t9-obstruction-fractional-binary-cube-cover','obstruction_size':len(obs),'allowed_vertices':len(allowed),'lp_optimum':lp,'certificates':certs,'best_certificate':rec,'conclusion':'alpha<=366' if rec['proves_alpha_le_366'] else 'no-366-upper-bound-from-rounded-LP'}
    out={'status':status,'denominator':den,'cube_units':[[i,u] for i,u in enumerate(units) if u]}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(out,separators=(',',':'))+'\n')
    print(json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
