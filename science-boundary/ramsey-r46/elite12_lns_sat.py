#!/usr/bin/env python3
"""Construction-first SAT search for <=11 exact (4,6) defects near elite12."""
import argparse
import itertools
import json
import threading
import time
from pathlib import Path
from pysat.card import CardEnc, EncType
from pysat.solvers import Glucose4

N=36
PAIRS=list(itertools.combinations(range(N),2))
FULL=(1<<N)-1

def score(a):
    def count(g,c,k):
        if k==0:return 1
        z=0
        while c.bit_count()>=k:
            b=c&-c;v=b.bit_length()-1;c^=b
            z+=count(g,c&g[v],k-1)
        return z
    comp=[FULL&~x&~(1<<i) for i,x in enumerate(a)]
    return count(a,FULL,4),count(comp,FULL,6)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--elite',type=Path,required=True)
    p.add_argument('--vertices',type=int,nargs='+',required=True)
    p.add_argument('--target',type=int,default=11)
    p.add_argument('--seconds',type=int,default=180)
    p.add_argument('--outdir',type=Path,required=True)
    args=p.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    start=time.monotonic()
    rows=json.loads(args.elite.read_text())['adjacency']
    assert len(rows)==N and all(len(r)==N for r in rows)
    graph=[sum(1<<j for j,c in enumerate(row) if c=='1') for row in rows]
    assert score(graph)==(12,0)
    free=set(args.vertices)
    changing=[pair for pair in PAIRS if pair[0] in free or pair[1] in free]
    var={pair:i+1 for i,pair in enumerate(changing)}
    fixed={pair:bool(graph[pair[0]]>>pair[1]&1) for pair in PAIRS if pair not in var}
    counter={'K4':0,'I6':0,'fixed_bad':0,'hard_degree':0}
    with Glucose4() as solver:
        top=len(var)
        for vertex in range(N):
            base=sum(int(value) for e,value in fixed.items() if vertex in e)
            inc=[idx for e,idx in var.items() if vertex in e]
            lo=max(0,11-base)
            hi=min(len(inc),17-base)
            if lo>len(inc) or hi<0:
                solver.add_clause([])
                continue
            for fn,bnd in ((CardEnc.atleast,lo),(CardEnc.atmost,hi)):
                clauses=fn(lits=inc,bound=bnd,top_id=top,encoding=EncType.seqcounter)
                solver.append_formula(clauses.clauses)
                top=max(top,clauses.nv)
                counter['hard_degree']+=len(clauses.clauses)
        penalty=[]
        for k in (4,6):
            for subset in itertools.combinations(range(N),k):
                lits=[]
                killed=False
                for e in itertools.combinations(subset,2):
                    idx=var.get(e)
                    if idx is not None:
                        lits.append(-idx if k==4 else idx)
                    elif fixed[e]!=(k==4):
                        killed=True
                        break
                if killed:continue
                if not lits:
                    counter['fixed_bad']+=1
                    continue
                top+=1
                penalty.append(top)
                solver.add_clause(lits+[top])
                counter['K4' if k==4 else 'I6']+=1
        limit=args.target-counter['fixed_bad']
        if limit<0:solver.add_clause([])
        else:
            clauses=CardEnc.atmost(lits=penalty,bound=limit,top_id=top,encoding=EncType.seqcounter)
            solver.append_formula(clauses.clauses)
            top=max(top,clauses.nv)
        print('MODEL_READY',json.dumps({'free_vertices':sorted(free),'variables':len(var),'counter':counter,
             'penalties':len(penalty),'limit':limit,'top':top,'elapsed':round(time.monotonic()-start,2)}),flush=True)
        timer=threading.Timer(args.seconds,solver.interrupt)
        timer.start()
        sat=solver.solve_limited(expect_interrupt=True)
        timer.cancel()
        result={'campaign':'elite12-threshold-lns-sat','free_vertices':sorted(free),
                'target':args.target,'model_vars':len(var),'penalty_vars':len(penalty),
                'counter':counter,'status':'SAT' if sat is True else ('UNSAT_THIS_NEIGHBORHOOD' if sat is False else 'UNKNOWN'),
                'seconds':round(time.monotonic()-start,2)}
        if sat is True:
            pos=set(q for q in solver.get_model() if q>0)
            new=[0]*N
            for (a,b),value in fixed.items():
                if value:new[a]|=1<<b;new[b]|=1<<a
            for (a,b),q in var.items():
                if q in pos:new[a]|=1<<b;new[b]|=1<<a
            k4,i6=score(new)
            assert k4+i6<=args.target,(k4,i6)
            result.update(K4=k4,I6=i6,defects=k4+i6)
            out=[''.join('1' if new[i]>>j&1 else '0' for j in range(N)) for i in range(N)]
            (args.outdir/'candidate36.json').write_text(json.dumps({'adjacency':out},indent=1)+'\n')
        (args.outdir/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
        print('SUMMARY',json.dumps(result,sort_keys=True),flush=True)
if __name__=='__main__':main()
