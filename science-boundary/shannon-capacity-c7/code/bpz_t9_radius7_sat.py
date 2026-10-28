#!/usr/bin/env python3
"""Exact 7-owner / 8-addition exchange decision for the BPZ t=9 obstruction.

Let L be the canonical obstruction-free 366-set obtained by deleting 10665
from the published BPZ auxiliary X. For each allowed v outside L, S(v) is the
set of old L vertices confusable with v. A 7->8 improving exchange exists iff
there are at least eight pairwise nonconfusable outside vertices whose support
union has size at most seven.

This is encoded exactly with candidate variables x_v and owner variables y_i:
  x_v -> y_i for each i in S(v)
  sum y_i <= 7
  sum x_v >= 8
  at-most-one x_v in every a+{0,1}^5 clique of C7^5.
The 7^5 binary cubes cover every confusability edge, so the last constraints
are exactly the independent-set condition.
"""
import argparse, json, sys
from itertools import product
from pathlib import Path
from pysat.solvers import Minicard

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t9_obstruction_mis as mis
import bpz_t9_kamis as bridge

RADIUS=7
NEED=8


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('tan_root',type=Path)
    ap.add_argument('output',type=Path)
    ap.add_argument('status',type=Path)
    args=ap.parse_args()
    I,published_X,pairs,PH,PV,ring,digits,obstruction,lower=bridge.reconstruct(args.tan_root)
    if len(lower)!=366 or len(obstruction)!=1098:
        raise RuntimeError('instance drift')
    lower=list(lower); lower_set=set(lower)
    idx={v:i for i,v in enumerate(lower)}
    # Outside allowed candidates and exact owner supports.
    cand=[]; supports=[]
    for v in range(mis.U):
        if v in obstruction or v in lower_set: continue
        s=[i for i,u in enumerate(lower) if mis.conflict(v,u,digits)]
        if 1 <= len(s) <= RADIUS:
            cand.append(v); supports.append(s)
    xv={v:i+1 for i,v in enumerate(cand)}
    ybase=len(cand)+1
    y=lambda i:ybase+i
    solver=Minicard()
    implications=0
    for v,s in zip(cand,supports):
        z=xv[v]
        for i in s:
            solver.add_clause([-z,y(i)]); implications+=1
    solver.add_atmost([y(i) for i in range(len(lower))],RADIUS)
    # Exact conflict constraints via all 5D binary cubes.
    nontrivial=0; cube_lits=0; max_cube=0
    cset=set(cand)
    for a in range(mis.U):
        ad=digits[a]; lits=[]
        for bits in product((0,1),repeat=mis.D):
            v=mis.enc(tuple((ad[j]+bits[j])%mis.Q for j in range(mis.D)))
            if v in cset: lits.append(xv[v])
        if len(lits)>=2:
            solver.add_atmost(lits,1); nontrivial+=1; cube_lits+=len(lits); max_cube=max(max_cube,len(lits))
    # At least NEED selected candidates.
    solver.add_atmost([-xv[v] for v in cand],len(cand)-NEED)
    setup={'starting_size':len(lower),'obstruction_size':len(obstruction),'candidate_vertices':len(cand),'owner_variables':len(lower),'radius':RADIUS,'need_additions':NEED,'implication_clauses':implications,'nontrivial_cube_constraints':nontrivial,'cube_literal_total':cube_lits,'max_candidate_vertices_per_cube':max_cube}
    print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
    sat=solver.solve(); model=solver.get_model() if sat else None; solver.delete()
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if not sat:
        status={'candidate':False,'sat':False,'method':'bpz-t9-exact-radius7-exchange-sat','score':134753,'setup':setup}
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')
        print('UNSAT',json.dumps(status,sort_keys=True),flush=True); return
    pos={z for z in model if z>0}
    add=[v for v in cand if xv[v] in pos]
    owners=sorted({i for v,s in zip(cand,supports) if xv[v] in pos for i in s})
    # Keep exactly NEED additions; solver may choose more. Search a prefix that preserves
    # the owner-union bound, then form the corresponding independent set.
    add=add[:NEED]
    owners=sorted({i for v,s in zip(cand,supports) if v in set(add) for i in s})
    new=[v for i,v in enumerate(lower) if i not in set(owners)]+add
    if len(new)<367 or set(new)&obstruction or not mis.independent(new,digits):
        raise RuntimeError(f'SAT replay failed size={len(new)} owners={len(owners)}')
    X=new[:367]
    if len(X)!=367 or not mis.independent(X,digits): raise RuntimeError('367 truncation replay failed')
    points,xp=mis.build(I,X,pairs,PH,PV,ring)
    if len(points)!=mis.TARGET: raise RuntimeError(f'10D score drift {len(points)}')
    status={'candidate':True,'sat':True,'method':'bpz-t9-exact-radius7-exchange-sat','score':len(points),'removed_owners':owners,'added_auxiliary':add,'raw_repaired_auxiliary_size':len(new),'setup':setup,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n')
    args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')
    print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
