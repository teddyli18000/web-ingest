#!/usr/bin/env python3
"""Constructively minimize (K4 + I6) on 36-point rooted elite reconstructions.

All Ramsey clauses corresponding to a non-root 4-clique or independent
6-set are *soft* with unit weight; degree conditions are hard. The weighted
MaxSAT optimum is the exact number of forbidden sets, not a proxy score.
The unchanged 14-defect elite is an explicit feasible reference assignment.
"""
import argparse
import itertools
import json
import random
import time
from pathlib import Path
from pysat.formula import WCNF
from pysat.card import CardEnc, EncType
from pysat.examples.rc2 import RC2
from rooted_mutable_static import read, comp, count, witnesses

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--near14',type=Path,required=True)
    p.add_argument('--root',type=int,default=3)
    p.add_argument('--free-a',type=int,default=0)
    p.add_argument('--free-b',type=int,default=0)
    p.add_argument('--seed',type=int,default=1)
    p.add_argument('--outdir',type=Path,required=True)
    args=p.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    original=read(args.near14)
    n=len(original);full=(1<<n)-1
    assert n==36
    fours=witnesses(original,4)
    sixes=witnesses(comp(original),6)
    assert (len(fours),len(sixes))==(10,4)
    r=args.root
    A=[i for i in range(n) if original[r]>>i&1]
    B=[i for i in range(n) if i!=r and not original[r]>>i&1]
    if r==3:assert (len(A),len(B))==(13,22)
    rng=random.Random(args.seed)
    impact={}
    for v in fours+sixes:
        for e in itertools.combinations(v,2):
            impact[e]=impact.get(e,0)+1
    def sample(edges,take):
        if not take:return set()
        pool=sorted(((impact.get(e,0)*4 + rng.random()*6,e) for e in edges),
                    reverse=True)
        return {e for _,e in pool[:take]}
    va=sample(list(itertools.combinations(A,2)),args.free_a)
    vb=sample(list(itertools.combinations(B,2)),args.free_b)
    extra=va|vb
    edges=list(itertools.combinations(range(n),2))
    variable=[e for e in edges
              if (e[0] in A and e[1] in B or e[0] in B and e[1] in A
                  or e in extra)]
    idx={e:i+1 for i,e in enumerate(variable)}
    fixed={e:bool(original[e[0]]>>e[1]&1) for e in edges if e not in idx}
    top=len(idx)
    wcnf=WCNF()
    for v in range(n):
        fixed_degree=sum(1 for u in range(n) if u!=v and
             fixed.get((min(v,u),max(v,u)),False))
        var=[idx[(min(v,u),max(v,u))] for u in range(n) if u!=v
             and (min(v,u),max(v,u)) in idx]
        low=max(0,11-fixed_degree)
        high=min(len(var),17-fixed_degree)
        if low>len(var) or high<0:wcnf.append([])
        else:
            for fn,bound in ((CardEnc.atleast,low),(CardEnc.atmost,high)):
                encoding=fn(lits=var,bound=bound,top_id=top,
                            encoding=EncType.seqcounter)
                wcnf.extend(encoding.clauses)
                top=max(top,encoding.nv)
    soft=[0,0]
    violated_by_parent=0
    for k in (4,6):
        for q in itertools.combinations(range(n),k):
            lits=[]
            impossible=False
            for e in itertools.combinations(q,2):
                num=idx.get(e)
                if num is not None:
                    lits.append(-num if k==4 else num)
                elif fixed[e]!=(k==4):
                    impossible=True;break
            if impossible:continue
            assert lits
            wcnf.append(lits,weight=1)
            soft[0 if k==4 else 1]+=1
            if all((original[e[0]]>>e[1]&1)==(k==4)
                   for e in itertools.combinations(q,2)):
                violated_by_parent+=1
    assert violated_by_parent==14
    summary={'campaign':'rooted-elite-anytime-maxsat',
             'root':r,'A':len(A),'B':len(B),
             'free_A':args.free_a,'free_B':args.free_b,
             'cross_variables':len(A)*len(B),'all_variables':len(idx),
             'hard_clauses':len(wcnf.hard),'soft_K4':soft[0],
             'soft_I6':soft[1],'original_score':violated_by_parent,
             'status':'SEARCHING','seed':args.seed}
    path=args.outdir/'summary.json'
    path.write_text(json.dumps(summary,indent=2)+'\n')
    print('MAXSAT_READY',json.dumps(summary,sort_keys=True),flush=True)
    with RC2(wcnf,solver='g4',adapt=True) as rc2:
        model=rc2.compute()
        assert model is not None
        cost=rc2.cost
    positives={v for v in model if v>0}
    result=[0]*n
    for (u,v),e in fixed.items():
        if e:result[u]|=1<<v;result[v]|=1<<u
    for (u,v),num in idx.items():
        if num in positives:result[u]|=1<<v;result[v]|=1<<u
    k4=count(result,4,full)
    i6=count(comp(result),6,full)
    assert k4+i6==cost,(k4,i6,cost)
    summary.update(status='OPTIMUM_FOUND',best_score=cost,K4=k4,I6=i6,
                   elapsed_seconds=round(time.monotonic()-started,2))
    if cost<14:
        rows=[''.join('1' if result[i]>>j&1 else '0'
                      for j in range(n)) for i in range(n)]
        (args.outdir/'best-36.json').write_text(
            json.dumps({'adjacency':rows})+'\n')
        summary['certificate']='best-36.json'
    path.write_text(json.dumps(summary,indent=2)+'\n')
    print('SUMMARY',json.dumps(summary,sort_keys=True),flush=True)
if __name__=='__main__':
    main()
