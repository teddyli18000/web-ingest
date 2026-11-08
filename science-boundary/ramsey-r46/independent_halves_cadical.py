#!/usr/bin/env python3
"""Constructive Ramsey 35/36 cross-cut SAT with independent fixed halves.

Positive control: hide *all* cross edges of a known valid 35-point graph.
Target: concatenate independently sampled valid 18-point induced subgraphs
from Exoo's 35-point catalogue and synthesize all 324 cross edges at once.
No exclusion claim is made on UNSAT or timeout for these fixed halves.
"""
import argparse
import itertools
import json
import random
import threading
import time
import urllib.request
from pathlib import Path
from pysat.solvers import Cadical195

G6_URL="https://users.cecs.anu.edu.au/~bdm/data/r46_35some.g6"

def decode(code):
    n=ord(code[0])-63
    bs=(ord(c)-63 >> b & 1 for c in code[1:] for b in (5,4,3,2,1,0))
    a=[0]*n
    for j in range(1,n):
        for i in range(j):
            if next(bs):
                a[i]|=1<<j
                a[j]|=1<<i
    return a

def comp(a):
    full=(1<<len(a))-1
    return [full&~x&~(1<<i) for i,x in enumerate(a)]

def count(a,c,k):
    if not k:return 1
    z=0
    while c.bit_count()>=k:
        b=c&-c;v=b.bit_length()-1;c^=b
        z+=count(a,c&a[v],k-1)
    return z

def valid(a):
    c=(1<<len(a))-1
    return count(a,c,4)==0 and count(comp(a),c,6)==0

def induced(a,vs):
    return [sum(1<<j for j,u in enumerate(vs) if a[v]>>u&1) for v in vs]

def parents():
    data=urllib.request.urlopen(G6_URL,timeout=45).read().decode("ascii")
    graphs=[]
    for code in data.splitlines():
        a=decode(code)
        if not valid(a):
            a=comp(a)
        assert len(a)==35 and valid(a)
        graphs.append(a)
    assert len(graphs)==37
    return graphs

def graph(mode, rng, baseline):
    if mode=="control35":
        a=[sum(1<<j for j,c in enumerate(r) if c=="1") for r in baseline]
        assert len(a)==35 and valid(a)
        perm=list(range(35));rng.shuffle(perm)
        l=induced(a,perm[:17]);r=induced(a,perm[17:])
        chosen={"kind":"known35-hidden-cross-edges","split":[17,18]}
    elif mode=="fusion35":
        base=parents()
        i,j=rng.sample(range(len(base)),2)
        l=induced(base[i],rng.sample(range(35),17))
        r=induced(base[j],rng.sample(range(35),18))
        chosen={"kind":"two-independent-17-plus-18-vertex-cores",
                "published_parent_indices":[i,j]}
    elif mode=="overlap36":
        base=parents()
        i=rng.randrange(len(base))
        perm=list(range(35))
        rng.shuffle(perm)
        left_vertices=perm[:18]
        right_vertices=[perm[0]]+perm[18:]
        l=induced(base[i],left_vertices)
        r=induced(base[i],right_vertices)
        chosen={"kind":"same-parent-overlap-one-vertex-recombination",
                "published_parent_index":i,
                "duplicated_original_vertex":perm[0]}
    elif mode=="fusion36":
        base=parents()
        i,j=rng.sample(range(len(base)),2)
        l=induced(base[i],rng.sample(range(35),18))
        r=induced(base[j],rng.sample(range(35),18))
        chosen={"kind":"two-independent-18-vertex-cores","published_parent_indices":[i,j]}
    else:
        raise ValueError(mode)
    n1,n2=len(l),len(r)
    a=[l[i] for i in range(n1)]+[r[i]<<n1 for i in range(n2)]
    assert valid(l) and valid(r)
    return a,n1,chosen

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("control35","fusion35","fusion36","overlap36"),required=True)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--rng",type=int,default=20261107)
    p.add_argument("--timeout",type=int,default=120)
    p.add_argument("--outdir",type=Path,required=True)
    args=p.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    rand=random.Random(args.rng)
    b=json.loads(args.baseline.read_text())["adjacency"]
    a,n1,source=graph(args.mode,rand,b)
    n=len(a)
    var=[(i,j) for i in range(n1) for j in range(n1,n)]
    ids={e:k+1 for k,e in enumerate(var)}
    fixed={(i,j):(a[i]>>j&1) for i in range(n)
           for j in range(i+1,n) if (i,j) not in ids}
    t0=time.monotonic()
    clausecount={4:0,6:0}
    with Cadical195() as solver:
        for k in (4,6):
            for vs in itertools.combinations(range(n),k):
                edge_pairs=itertools.combinations(vs,2)
                clause=[]
                killed=False
                for e in edge_pairs:
                    if e in fixed:
                        if fixed[e] != (k==4):
                            killed=True
                            break
                    else:
                        clause.append(-ids[e] if k==4 else ids[e])
                if killed:continue
                assert clause
                solver.add_clause(clause)
                clausecount[k]+=1
        timer=threading.Timer(args.timeout,solver.interrupt)
        timer.start()
        solved=solver.solve_limited(expect_interrupt=True)
        timer.cancel()
        result={"campaign":"independent-core-cross-cut-sat",
                "mode":args.mode,"rng":args.rng,"source":source,
                "vertices":n,"cross_edge_variables":len(var),
                "clauses":clausecount,
                "solve_status":"SAT" if solved is True else
                 ("UNSAT_THIS_PAIR" if solved is False else "UNKNOWN_OR_TIMEOUT"),
                "elapsed_seconds":round(time.monotonic()-t0,3)}
        if solved is True:
            model={abs(z):z>0 for z in solver.get_model()}
            candidate=a[:]
            for (u,v),i in ids.items():
                if model[i]:
                    candidate[u]|=1<<v
                    candidate[v]|=1<<u
            assert valid(candidate)
            out=["".join("1" if candidate[i]>>j&1 else "0"
                         for j in range(n)) for i in range(n)]
            path=args.outdir/("candidate%d.json"%n)
            path.write_text(json.dumps({"adjacency":out})+"\n")
            result["candidate"]=str(path)
            result["edges"]=sum(x.bit_count() for x in candidate)//2
        (args.outdir/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
