#!/usr/bin/env python3
"""Construction-first exact rooted reconstruction with mutable interiors.

From the verified 14-defect 36-vertex near miss, fix the edges incident to
a valid root, retain most of the induced A=N(root), B=non-N(root) interiors,
and jointly synthesize ALL A--B edges plus selected A/B internal edges.
Encode every Ramsey clause statically, not lazy model-based separators.
All satisfiable results require an independent exact K4/I6 recount.
"""
import argparse
import itertools
import json
import random
import threading
import time
from pathlib import Path
from pysat.solvers import Glucose4
from pysat.card import CardEnc, EncType

def comp(a):
    mask=(1<<len(a))-1
    return [mask&~r&~(1<<i) for i,r in enumerate(a)]

def count(a,k,cand):
    if k==0:return 1
    total=0
    while cand.bit_count()>=k:
        bit=cand&-cand;v=bit.bit_length()-1;cand^=bit
        total+=count(a,k-1,cand&a[v])
    return total

def witnesses(a,k):
    out=[]
    def rec(c,vs):
        if len(vs)==k:
            out.append(vs)
            return
        while c.bit_count()>=k-len(vs):
            bit=c&-c;v=bit.bit_length()-1;c^=bit
            rec(c&a[v],vs+(v,))
    rec((1<<len(a))-1,())
    return out

def read(path):
    rows=json.loads(path.read_text())["adjacency"]
    n=len(rows)
    assert all(len(r)==n and r[i]=='0' for i,r in enumerate(rows))
    assert all(rows[i][j]==rows[j][i] for i in range(n) for j in range(n))
    return [sum(1<<j for j,c in enumerate(r) if c=='1') for r in rows]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--near14',type=Path,required=True)
    p.add_argument('--root',type=int,default=3)
    p.add_argument('--free-a',type=int,default=6)
    p.add_argument('--free-b',type=int,default=16)
    p.add_argument('--seed',type=int,default=1)
    p.add_argument('--seconds',type=int,default=180)
    p.add_argument('--outdir',type=Path,required=True)
    args=p.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    start=time.monotonic()
    g=read(args.near14)
    assert len(g)==36
    full=(1<<36)-1
    four=witnesses(g,4)
    six=witnesses(comp(g),6)
    assert (len(four),len(six))==(10,4)
    root=args.root
    A=[i for i in range(36) if g[root]>>i&1]
    B=[i for i in range(36) if i!=root and not g[root]>>i&1]
    assert len(A)==13 and len(B)==22 and root==3
    # The full near miss has 14 defects, all crossing this cut.
    assert all(any(u in A for u in q) and any(v in B for v in q)
               for q in four+six)
    rng=random.Random(args.seed)
    score={}
    for q in four+six:
        for e in itertools.combinations(q,2):
            score[e]=score.get(e,0)+1
    ea=[tuple(sorted(q)) for q in itertools.combinations(A,2)]
    eb=[tuple(sorted(q)) for q in itertools.combinations(B,2)]
    def rank(edges,number):
        # Mix damage-based priority with exploration of alternative structures.
        w=[(score.get(e,0)*4+rng.random()*6,e) for e in edges]
        w.sort(reverse=True)
        return set(e for _,e in w[:number])
    free_inside=rank(ea,args.free_a)|rank(eb,args.free_b)
    variable_pairs=[e for e in itertools.combinations(range(36),2)
                    if (e[0] in A and e[1] in B or e[0] in B and e[1] in A
                        or e in free_inside)]
    vid={e:i+1 for i,e in enumerate(variable_pairs)}
    fixed={(u,v):bool(g[u]>>v&1)
           for u,v in itertools.combinations(range(36),2) if (u,v) not in vid}
    assert len(vid)==len(A)*len(B)+args.free_a+args.free_b
    print('CONFIG',json.dumps({'A':A,'B':B,'free_inside':len(free_inside),
                               'vars':len(vid),'root':root}),flush=True)
    nclauses=0
    t0=time.monotonic()
    with Glucose4() as solver:
        top=len(vid)
        for vertex in range(36):
            deg_fixed=sum(int(fixed.get((min(vertex,u),max(vertex,u)),False))
                          for u in range(36) if u!=vertex)
            incident=[vid[(min(vertex,u),max(vertex,u))]
                      for u in range(36) if u!=vertex
                      and (min(vertex,u),max(vertex,u)) in vid]
            lo=max(0,11-deg_fixed)
            hi=min(len(incident),17-deg_fixed)
            if lo>len(incident) or hi<0:
                solver.add_clause([])
                break
            for method,bound in ((CardEnc.atleast,lo),(CardEnc.atmost,hi)):
                cnf=method(lits=incident,bound=bound,top_id=top,
                           encoding=EncType.seqcounter)
                solver.append_formula(cnf.clauses)
                top=max(top,cnf.nv)
        print('DEGREE_READY',round(time.monotonic()-t0,2),flush=True)
        for k in (4,6):
            for q in itertools.combinations(range(36),k):
                literals=[]
                killed=False
                for e in itertools.combinations(q,2):
                    v=vid.get(e)
                    if v is not None:
                        literals.append(-v if k==4 else v)
                    elif fixed[e]!=(k==4):
                        killed=True
                        break
                if killed:continue
                solver.add_clause(literals)
                nclauses+=1
        print('CNF_READY',json.dumps({'ramsey_clauses':nclauses,
             'vars':top,'generation_seconds':round(time.monotonic()-t0,2)}),
             flush=True)
        timer=threading.Timer(args.seconds,solver.interrupt)
        timer.start()
        sat=solver.solve_limited(expect_interrupt=True)
        timer.cancel()
        summary={'campaign':'rooted-elite-mutable-interiors-static-cnf',
                 'root':root,'A':len(A),'B':len(B),
                 'free_A':args.free_a,'free_B':args.free_b,
                 'free_inside':len(free_inside),'variables':len(vid),
                 'ramsey_clauses':nclauses,'seed':args.seed,
                 'status':'SAT' if sat is True else
                          ('UNSAT_THIS_FREE_SET' if sat is False else 'UNKNOWN'),
                 'elapsed_seconds':round(time.monotonic()-start,2)}
        if sat is True:
            pos=set(x for x in solver.get_model() if x>0)
            result=[0]*36
            for (u,v),bit in fixed.items():
                if bit:
                    result[u]|=1<<v;result[v]|=1<<u
            for (u,v),num in vid.items():
                if num in pos:
                    result[u]|=1<<v;result[v]|=1<<u
            n4=count(result,4,full)
            n6=count(comp(result),6,full)
            assert n4==n6==0,(n4,n6)
            rows=[''.join('1' if result[i]>>j&1 else '0'
                          for j in range(36)) for i in range(36)]
            (args.outdir/'certificate.json').write_text(
                json.dumps({'adjacency':rows})+'\n')
            summary['edges']=sum(m.bit_count() for m in result)//2
        (args.outdir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print('SUMMARY',json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__':
    main()
