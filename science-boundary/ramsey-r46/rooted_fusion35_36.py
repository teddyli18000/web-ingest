#!/usr/bin/env python3
"""Construction-first rooted A/B gluing of two (4,6,35) parents.

A = N(root) (triangle-free, no independent 6), B = non-N(root)
(K4-free, no independent 5). The 36-vertex experiment takes A at root
degree d in one Exoo parent, B at root degree d-1 in another, and solves
ALL A--B edges at once, with the root and both interiors fixed. This
avoids unrelated random halves that violate the root's exact constraints.
A hidden-answer n=35 control uses A and B of one actual parent.
"""
import argparse
import itertools
import json
import random
import threading
import time
import urllib.request
from pathlib import Path
from pysat.solvers import Glucose4
from pysat.card import CardEnc, EncType

SOURCE="https://users.cecs.anu.edu.au/~bdm/data/r46_35some.g6"
def decode(code):
    n=ord(code[0])-63
    bs=(ord(c)-63>>s&1 for c in code[1:] for s in (5,4,3,2,1,0))
    a=[0]*n
    for j in range(1,n):
        for i in range(j):
            if next(bs):
                a[i]|=1<<j;a[j]|=1<<i
    return a
def complement(a):
    mask=(1<<len(a))-1
    return [mask&~r&~(1<<i) for i,r in enumerate(a)]
def count(a,c,k):
    if not k:return 1
    z=0
    while c.bit_count()>=k:
        bit=c&-c;i=bit.bit_length()-1;c^=bit
        z+=count(a,c&a[i],k-1)
    return z
def legal(g):
    m=(1<<len(g))-1
    return not count(g,m,4) and not count(complement(g),m,6)
def induced(g,vs):
    return [sum(1<<j for j,v in enumerate(vs) if g[u]>>v&1) for u in vs]
def catalog():
    raw=urllib.request.urlopen(SOURCE,timeout=45).read().decode('ascii')
    graphs=[]
    for line in raw.splitlines():
        g=decode(line)
        assert len(g)==35
        if not legal(g):g=complement(g)
        assert legal(g)
        graphs.append(g)
    assert len(graphs)==37
    return graphs
def sample_structure(args,rng):
    gs=catalog()
    if args.mode=="control35":
        g=gs[rng.randrange(37)]
        roots=[i for i in range(35) if g[i].bit_count()==args.degree]
        if not roots:
            # Deterministically pick another published graph with the desired degree.
            matches=[(pi,i) for pi,q in enumerate(gs) for i in range(35)
                     if q[i].bit_count()==args.degree]
            pi,root=rng.choice(matches)
            g=gs[pi]
        else:
            root=rng.choice(roots);pi=gs.index(g)
        A=[i for i in range(35) if g[root]>>i&1]
        B=[i for i in range(35) if i!=root and not g[root]>>i&1]
        return induced(g,A),induced(g,B),{"A_parent":pi,"B_parent":pi,
                                       "A_root":root,"B_root":root}
    roots_a=[(pi,i) for pi,g in enumerate(gs) for i in range(35)
             if g[i].bit_count()==args.degree]
    roots_b=[(pi,i) for pi,g in enumerate(gs) for i in range(35)
             if g[i].bit_count()==args.degree-1]
    ia,va=rng.choice(roots_a)
    matches=[z for z in roots_b if z[0]!=ia]
    ib,vb=rng.choice(matches)
    ga,gb=gs[ia],gs[ib]
    A=[i for i in range(35) if ga[va]>>i&1]
    B=[i for i in range(35) if i!=vb and not gb[vb]>>i&1]
    assert len(A)==args.degree and len(B)==35-args.degree
    return induced(ga,A),induced(gb,B),{"A_parent":ia,"B_parent":ib,
                                      "A_root":va,"B_root":vb}

def clique_subsets(g,k,red):
    if k==0:return [()]
    adj=g if red else complement(g)
    out=[]
    def rec(cand,partial):
        if len(partial)==k:
            out.append(partial)
            return
        left=k-len(partial)
        while cand.bit_count()>=left:
            bit=cand&-cand;i=bit.bit_length()-1;cand^=bit
            rec(cand&adj[i],partial+(i,))
    rec((1<<len(g))-1,())
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["control35","fusion36"],required=True)
    ap.add_argument("--degree",type=int,default=14)
    ap.add_argument("--seed",type=int,required=True)
    ap.add_argument("--seconds",type=int,default=300)
    ap.add_argument("--outdir",type=Path,required=True)
    args=ap.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    start=time.monotonic()
    rng=random.Random(args.seed)
    A,B,orig=sample_structure(args,rng)
    na,nb=len(A),len(B);n=1+na+nb
    assert n==(35 if args.mode=="control35" else 36)
    assert legal(A) and legal(B)
    assert count(A,(1<<na)-1,3)==0
    assert count(complement(B),(1<<nb)-1,5)==0
    vars={(i,j):1+i*nb+j for i in range(na) for j in range(nb)}
    base=na*nb
    counters={"K4":0,"I6":0,"degree_clauses":0}
    with Glucose4() as s:
        top=base
        degree_min=n-25
        for i in range(na):
            row=[vars[i,j] for j in range(nb)]
            base_deg=A[i].bit_count()+1
            lo=max(0,degree_min-base_deg)
            hi=min(nb,17-base_deg)
            for kind,bnd in ((CardEnc.atleast,lo),(CardEnc.atmost,hi)):
                cnf=kind(lits=row,bound=bnd,top_id=top,encoding=EncType.seqcounter)
                s.append_formula(cnf.clauses);top=max(top,cnf.nv)
                counters["degree_clauses"]+=len(cnf.clauses)
        for j in range(nb):
            col=[vars[i,j] for i in range(na)]
            deg=B[j].bit_count()
            lo=max(0,degree_min-deg)
            hi=min(na,17-deg)
            for kind,bnd in ((CardEnc.atleast,lo),(CardEnc.atmost,hi)):
                cnf=kind(lits=col,bound=bnd,top_id=top,encoding=EncType.seqcounter)
                s.append_formula(cnf.clauses);top=max(top,cnf.nv)
                counters["degree_clauses"]+=len(cnf.clauses)
        for k in (4,6):
            for a in range(1,k):
                b=k-a
                if a>na or b>nb:continue
                asets=clique_subsets(A,a,red=(k==4))
                bsets=clique_subsets(B,b,red=(k==4))
                for av in asets:
                    for bv in bsets:
                        lits=[vars[i,j]*(1 if k==6 else -1)
                              for i in av for j in bv]
                        s.add_clause(lits)
                        counters["K4" if k==4 else "I6"]+=1
        # A and B internally satisfy all required root-aware Ramsey restrictions.
        deadline=threading.Timer(args.seconds,s.interrupt)
        deadline.start()
        sat=s.solve_limited(expect_interrupt=True)
        deadline.cancel()
        result={"mode":args.mode,"degree":args.degree,
                "seed":args.seed,"source":orig,"n":n,"A":na,"B":nb,
                "cross_variables":base,"clauses":counters,
                "status":"SAT" if sat is True else
                ("FIXED_PAIR_UNSAT" if sat is False else "UNKNOWN"),
                "elapsed_seconds":round(time.monotonic()-start,3)}
        if sat is True:
            sol=set(q for q in s.get_model() if q>0)
            g=[0]*n
            for i in range(na):
                g[0]|=1<<(1+i);g[1+i]|=1
                for j in range(na):
                    if A[i]>>j&1:g[1+i]|=1<<(1+j)
            for i in range(nb):
                for j in range(nb):
                    if B[i]>>j&1:g[1+na+i]|=1<<(1+na+j)
            for (i,j),q in vars.items():
                if q in sol:
                    g[1+i]|=1<<(1+na+j)
                    g[1+na+j]|=1<<(1+i)
            assert legal(g)
            rows=["".join('1' if g[i]>>j&1 else '0' for j in range(n))
                  for i in range(n)]
            (args.outdir/f"candidate{n}.json").write_text(
                json.dumps({"adjacency":rows})+"\n")
            result["edges"]=sum(x.bit_count() for x in g)//2
    (args.outdir/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print("SUMMARY",json.dumps(result,sort_keys=True),flush=True)
if __name__=="__main__":
    main()
