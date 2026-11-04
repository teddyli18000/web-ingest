#!/usr/bin/env python3
"""Exact two-adjacent-layer block reoptimization for C7^5, source-pinned.

For adjacent layers s,s+1 of coordinate axis k, all other five layers are
frozen. A projection q in C7^4 is allowed in layer s iff it is not confusable
with any projection of the fixed layer s-1; similarly s+1 requires avoiding
the fixed layer s+2. Since s and s+1 are adjacent, the *entire* new pair must
project to an independent set in C7^4. Consequently their joint optimum is
exactly an MIS on the union of these two allowed 4D projection pools.

Replacing a pair can change >100 words in a single score-preserving move, so
this is not a small exchange radius search. Each MILP result is replayed
independently against the original five-dimensional graph.
"""
from __future__ import annotations
import argparse, itertools, json, random, time
from pathlib import Path
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

P5=(1,7,49,343,2401)
P4=(1,7,49,343)
N4=7**4
OFFSETS=list(itertools.product((-1,0,1),repeat=4))

def digits5(v):
    return tuple((v//p)%7 for p in P5)

def code5(d):
    return sum(x*p for x,p in zip(d,P5))

def conf5(a,b):
    return all(((a//p)-(b//p))%7 in (0,1,6) for p in P5)

def independent(S):
    L=sorted(S)
    return len(S)==len(L) and all(not conf5(a,b) for i,a in enumerate(L) for b in L[i+1:])

def proj(v,axis):
    d=digits5(v)
    return sum(d[k]*7**j for j,k in enumerate(i for i in range(5) if i!=axis))

def lift(q,axis,layer):
    d4=tuple((q//p)%7 for p in P4)
    d=[];j=0
    for i in range(5):
        if i==axis:d.append(layer)
        else:d.append(d4[j]);j+=1
    return code5(d)

def neighbors4(q):
    d=tuple((q//p)%7 for p in P4)
    return tuple(sum(((a+z)%7)*p for a,z,p in zip(d,o,P4)) for o in OFFSETS)

NEIGH4=tuple(neighbors4(q) for q in range(N4))

def solve_pair(S,axis,s,rng,seconds):
    t=(s+1)%7
    group=[set() for _ in range(7)]
    for v in S:group[digits5(v)[axis]].add(proj(v,axis))
    oldpair=group[s]|group[t]
    assert len(oldpair)==len(group[s])+len(group[t])
    fA=set().union(*(NEIGH4[q] for q in group[(s-1)%7]))
    fB=set().union(*(NEIGH4[q] for q in group[(t+1)%7]))
    allowA=set(range(N4))-fA
    allowB=set(range(N4))-fB
    Q=sorted(allowA|allowB)
    idx={q:i for i,q in enumerate(Q)}
    n=len(Q)
    rows=[];cols=[];vals=[];e=0
    for i,q in enumerate(Q):
        for v in NEIGH4[q]:
            j=idx.get(v)
            if j is not None and j>i:
                rows.extend((e,e));cols.extend((i,j));vals.extend((1,1));e+=1
    A=coo_matrix((np.array(vals,float),(rows,cols)),shape=(e,n)).tocsr()
    # |Q|<=2401, so 10000 dominates all tie-breaking contributions.
    c=np.array([-10000+(2 if q in oldpair else 0)+rng.randrange(2) for q in Q],float)
    opt=milp(c,integrality=np.ones(n),bounds=Bounds(np.zeros(n),np.ones(n)),
             constraints=LinearConstraint(A,-np.inf,np.ones(e)),
             options={'time_limit':seconds,'mip_rel_gap':0})
    result={'axis':axis,'pair':s,'old_pair_size':len(oldpair),'pool':n,
            'conflict_edges':e,'solver_status':int(opt.status),
            'mip_gap':float(opt.mip_gap) if opt.mip_gap is not None else None,
            'new_pair_size':None,'accepted':False}
    if opt.x is None:return S,result
    chosen={q for i,q in enumerate(Q) if opt.x[i]>.5}
    assert all(not(v in chosen and v!=q) for q in chosen for v in NEIGH4[q])
    if len(chosen)<len(oldpair):
        result['new_pair_size']=len(chosen)
        return S,result
    newset=set()
    for q in chosen:
        if q in allowA and q in allowB:
            # Alternate arbitrary legal layer placements to diversify global basins.
            if q in group[s] and rng.random()<.4: lab=s
            elif q in group[t] and rng.random()<.4: lab=t
            else:lab=(s,t)[rng.randrange(2)]
        elif q in allowA:lab=s
        else:lab=t
        newset.add(lift(q,axis,lab))
    oldset={v for v in S if digits5(v)[axis] in (s,t)}
    cand=(S-oldset)|newset
    assert len(cand)==len(S)-len(oldset)+len(chosen)
    assert independent(cand),('invalid five-dimensional block recombination',axis,s)
    result.update(new_pair_size=len(chosen),accepted=True,new_score=len(cand),
                  symmetric_difference=len(S^cand))
    return cand,result

def dump_certificate(S,out):
    if len(S)<368:return False
    words=sorted(''.join(map(str,digits5(v))) for v in sorted(S)[:368])
    words10=sorted(a+b for a in words for b in words)
    assert len(words10)==135424 and len(set(words10))==135424
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'points':words10},separators=(',',':'))+'\n')
    return True

def main():
    p=argparse.ArgumentParser()
    p.add_argument('input',type=Path);p.add_argument('status',type=Path)
    p.add_argument('certificate',type=Path)
    p.add_argument('--seed-name',choices=['I0','X'],default='I0')
    p.add_argument('--sweeps',type=int,default=2)
    p.add_argument('--seconds',type=float,default=5.)
    p.add_argument('--random-seed',type=int,default=20261104)
    a=p.parse_args()
    raw=json.loads(a.input.read_text())
    S=set(map(int,raw[a.seed_name]))
    assert len(S)==367 and independent(S)
    rng=random.Random(a.random_seed+('I0','X').index(a.seed_name)*10000)
    rows=[];best=S.copy();seen=set()
    start=time.monotonic()
    for sweep in range(a.sweeps):
        order=list(itertools.product(range(5),range(7)))
        rng.shuffle(order)
        for axis,s in order:
            S,res=solve_pair(S,axis,s,rng,a.seconds)
            rows.append(res)
            seen.add(tuple(sorted(S)))
            if len(S)>len(best):best=S.copy()
            print(json.dumps({'sweep':sweep,**res,'best':len(best)},sort_keys=True),flush=True)
            if len(best)>=368:break
        if len(best)>=368:break
    have=dump_certificate(best,a.certificate)
    result={'method':'full-pair-4d-MIS-coordinate-repair','source':'BPZ/Tandon base_c7.json',
            'seed':a.seed_name,'sweeps_requested':a.sweeps,'seconds_per_milp':a.seconds,
            'milp_count':len(rows),'optimal_milps':sum(x['solver_status']==0 for x in rows),
            'timeout_milps':sum(x['solver_status']==1 for x in rows),
            'neutral_accepted':sum(x['accepted'] and x['new_score']==367 for x in rows),
            'best_size':len(best),'candidate_368':have,'distinct_states':len(seen),
            'elapsed_seconds':time.monotonic()-start,'rows':rows,
            'best_points5':sorted(best)}
    a.status.parent.mkdir(parents=True,exist_ok=True)
    a.status.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('FINAL',json.dumps({k:v for k,v in result.items() if k not in ('rows','best_points5')},sort_keys=True),flush=True)

if __name__=='__main__':main()
