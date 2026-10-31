#!/usr/bin/env python3
"""Exact/feasible CP-SAT search for a 368-set inside the union of public C7^5 367 sets.

Unlike the previous cardinality-network SAT, this model keeps the graph native:
1525 Bool variables, one x_u+x_v<=1 constraint per conflict edge, and a single
linear sum(x)>=368 constraint.  The 40 validated 367 seeds are supplied as
partial hints in separate repeated solves.  CP-SAT status INFEASIBLE proves the
union alpha is 367; FEASIBLE/OPTIMAL yields a 368 witness, independently replayed
and squared to a 135424-point C7^10 certificate.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

from ortools.sat.python import cp_model

TARGET=368
OFFSETS=tuple(itertools.product((-1,0,1),repeat=5))


def dec(v:int):
    d=[0]*5
    for i in range(4,-1,-1): d[i]=v%7; v//=7
    return d

def enc(d):
    v=0
    for x in d: v=7*v+x
    return v

def word5(v:int): return ''.join(map(str,dec(v)))

def independent(S):
    ss=set(S)
    if len(ss)!=len(S): return False
    for v in S:
        d=dec(v)
        for off in OFFSETS:
            if off==(0,0,0,0,0): continue
            w=enc(tuple((d[i]+off[i])%7 for i in range(5)))
            if w in ss and w>v: return False
    return True


def graph_from_corpus(path:Path):
    corpus=json.loads(path.read_text()); rows=corpus['sets']
    if not rows: raise RuntimeError('empty corpus')
    seed_sets=[]
    for r in rows:
        pts=tuple(sorted(map(int,r['points'])))
        if len(pts)!=367 or not independent(pts): raise RuntimeError(('bad seed',r.get('sources')))
        seed_sets.append(pts)
    universe=sorted(set().union(*(set(s) for s in seed_sets))); idx={v:i for i,v in enumerate(universe)}
    edges=[]
    for v in universe:
        i=idx[v]; d=dec(v)
        for off in OFFSETS:
            if off==(0,0,0,0,0): continue
            w=enc(tuple((d[k]+off[k])%7 for k in range(5)))
            j=idx.get(w)
            if j is not None and j>i: edges.append((i,j))
    if (len(universe),len(edges))!=(1525,13487):
        raise RuntimeError(('union graph drift',len(universe),len(edges)))
    return rows,seed_sets,universe,edges


def solve_once(universe,edges,hint,seconds,workers,seed,log=False):
    model=cp_model.CpModel(); x=[model.NewBoolVar(f'x{i}') for i in range(len(universe))]
    for a,b in edges: model.Add(x[a]+x[b]<=1)
    model.Add(sum(x)>=TARGET)
    if hint is not None:
        hs=set(hint)
        for i,v in enumerate(universe):
            if v in hs: model.AddHint(x[i],1)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=float(seconds)
    solver.parameters.num_search_workers=int(workers)
    solver.parameters.random_seed=int(seed)
    solver.parameters.cp_model_presolve=True
    solver.parameters.linearization_level=2
    solver.parameters.log_search_progress=bool(log)
    t=time.time(); st=solver.Solve(model); wall=time.time()-t
    status=solver.StatusName(st)
    chosen=[]
    if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        chosen=[universe[i] for i in range(len(universe)) if solver.Value(x[i])]
        if len(chosen)<TARGET or not independent(chosen): raise RuntimeError(('bad CP-SAT witness',len(chosen)))
    return {'status':status,'wall_seconds':wall,'conflicts':solver.NumConflicts(),'branches':solver.NumBranches(),'chosen':chosen}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('corpus',type=Path); ap.add_argument('output',type=Path); ap.add_argument('witness5',type=Path); ap.add_argument('certificate10',type=Path); ap.add_argument('--seconds',type=float,default=10800); ap.add_argument('--workers',type=int,default=4); ap.add_argument('--seed',type=int,default=1); a=ap.parse_args()
    rows,seeds,universe,edges=graph_from_corpus(a.corpus)
    # Use the first validated 367-set as a partial positive hint.  It is one short
    # of target but gives CP-SAT a very strong incumbent neighborhood.
    r=solve_once(universe,edges,seeds[0],a.seconds,a.workers,a.seed,True)
    out={'method':'public367-union-cpsat-target368','distinct_seed_sets':len(rows),'union_vertices':len(universe),'conflict_edges':len(edges),'target':TARGET,'solver_status':r['status'],'wall_seconds':r['wall_seconds'],'conflicts':r['conflicts'],'branches':r['branches'],'candidate_368':bool(r['chosen'])}
    if r['chosen']:
        chosen=sorted(r['chosen']); out['size5']=len(chosen); out['score10']=len(chosen)**2
        a.witness5.parent.mkdir(parents=True,exist_ok=True); a.witness5.write_text(json.dumps({'points':[word5(v) for v in chosen]},separators=(',',':'))+'\n')
        w=[word5(v) for v in chosen]; pts10=sorted(x+y for x in w for y in w)
        a.certificate10.parent.mkdir(parents=True,exist_ok=True); a.certificate10.write_text(json.dumps({'points':pts10},separators=(',',':'))+'\n')
    elif r['status']=='INFEASIBLE':
        out['exact_union_alpha']=367
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True))

if __name__=='__main__': main()
