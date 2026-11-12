#!/usr/bin/env python3
"""Independent-parent constructive R(4,6,36) search over Exoo's 37 graphs.

For every valid n=35 parent: (1) optimize a *soft* one-vertex extension
(K4+I6, rather than impossible hard extension); (2) jointly mutate edges
of the ENTIRE 36-vertex graph with a delayed-acceptance conflict cascade;
(3) retain exact full-graph candidates and their source fingerprints.

This intentionally starts outside the previously exhausted 257--264-edge
12-defect local basin, whose four parents agree on 603 of the 630 edges.
"""
import argparse
import itertools
import json
import math
import random
import time
import urllib.request
from pathlib import Path

from compound_repair_search import Graph, select_actions

URL="https://users.cecs.anu.edu.au/~bdm/data/r46_35some.g6"


def decode_g6(line):
    n=ord(line[0])-63
    bits=(ord(ch)-63 >> shift & 1 for ch in line[1:]
          for shift in (5,4,3,2,1,0))
    g=[0]*n
    for j in range(1,n):
        for i in range(j):
            if next(bits):
                g[i]|=1<<j
                g[j]|=1<<i
    return g


def all_cliques(g,k):
    results=[]
    def rec(cand,vs):
        if len(vs)==k:
            results.append(vs)
            return
        while cand.bit_count()>=k-len(vs):
            bit=cand&-cand
            u=bit.bit_length()-1
            cand^=bit
            rec(cand&g[u],vs+(u,))
    rec((1<<len(g))-1,())
    return results


def valid35(g):
    n=len(g)
    comp=[((1<<n)-1)&~row&~(1<<i) for i,row in enumerate(g)]
    return not all_cliques(g,4) and not all_cliques(comp,6)


def parent35(raw):
    g=decode_g6(raw)
    if not valid35(g):
        n=len(g)
        g=[((1<<n)-1)&~row&~(1<<i) for i,row in enumerate(g)]
    assert len(g)==35 and valid35(g)
    return g


def score_extension(mask, tris, i5s):
    return sum((mask&m)==m for m in tris)+sum((mask&m)==0 for m in i5s)


def best_extension(parent,rng,rounds):
    n=35
    comp=[((1<<n)-1)&~row&~(1<<i) for i,row in enumerate(parent)]
    tris=[sum(1<<v for v in vs) for vs in all_cliques(parent,3)]
    i5s=[sum(1<<v for v in vs) for vs in all_cliques(comp,5)]
    clauses=[(m,0) for m in tris]+[(m,1) for m in i5s]
    inc=[[] for _ in range(n)]
    for idx,(mask,_) in enumerate(clauses):
        for i in range(n):
            if mask>>i&1:inc[i].append(idx)
    best_score=10**9
    best_mask=0
    current=0
    counts=[0]*len(clauses)
    cost=0
    period=1500
    for it in range(rounds):
        if it%period==0:
            current=0
            for v in rng.sample(range(n),rng.randrange(12,19)):
                current|=1<<v
            cost=0
            for k,(mask,kind) in enumerate(clauses):
                counts[k]=(mask&current).bit_count()
                if (kind==0 and counts[k]==3) or (kind==1 and counts[k]==0):
                    cost+=1
        if cost<best_score:
            best_score,best_mask=cost,current
        v=rng.randrange(n)
        was=bool(current>>v&1)
        degree=current.bit_count()
        if was and degree==9 or not was and degree==21:
            continue
        delta=0
        for k in inc[v]:
            kind=clauses[k][1]
            c=counts[k]
            if kind==0:
                if was and c==3:delta-=1
                elif not was and c==2:delta+=1
            else:
                if was and c==1:delta+=1
                elif not was and c==0:delta-=1
        temperature=0.35+2.75*(period-it%period)/period
        if delta<=0 or rng.random()<math.exp(-delta/temperature):
            current^=1<<v
            cost+=delta
            for k in inc[v]:
                counts[k]+=(-1 if was else 1)
    assert best_score==score_extension(best_mask,tris,i5s)
    return best_mask,best_score,{"triangles":len(tris),"independent5":len(i5s)}


def append_vertex(g,mask):
    rows=g[:]+[0]
    n=35
    for i in range(n):
        if mask>>i&1:
            rows[i]|=1<<n
            rows[n]|=1<<i
    return Graph(rows)


def repaired_graph(initial,rng,seconds,steps):
    start=time.monotonic()
    best=initial.copy()
    current=initial.copy()
    elites=[initial.copy()]
    count=0
    while count<steps and time.monotonic()-start<seconds:
        count+=1
        if count%450==0:
            current=rng.choice(elites[:min(8,len(elites))]).copy()
        state=current.copy()
        w4=state.witnesses(False)
        w6=state.witnesses(True)
        kind=4 if rng.random()<(len(w4)/(len(w4)+len(w6))) else 6
        source=w4 if kind==4 else w6
        if not source:continue
        moves=select_actions(state,kind,source,rng)
        if not moves:continue
        m=moves[rng.randrange(min(4,len(moves)))]
        state.flip(*m[2],m[3])
        tabu=[m[2]]
        for depth in range(rng.randrange(5,15)):
            options=[]
            for k,ws in ((4,state.witnesses(False)),(6,state.witnesses(True))):
                if ws:
                    options.extend(select_actions(state,k,ws,rng,tabu[-2:])[:12])
            if not options:break
            options.sort(key=lambda x:(x[0],x[1],rng.random()))
            choice=options[rng.randrange(min(5,len(options)))]
            state.flip(*choice[2],choice[3])
            tabu.append(choice[2])
            if state.objective()<best.objective():
                assert state.totals()==(state.c4,state.c6)
                best=state.copy()
                elites.append(best.copy())
                elites.sort(key=lambda g:g.objective())
                elites=elites[:10]
                if best.objective()==0:
                    return best,count
        if state.objective()<best.objective():
            assert state.totals()==(state.c4,state.c6)
            best=state.copy()
        temperature=0.65+2.7*(1-(count%500)/500)
        if state.objective()<=current.objective() or \
                rng.random()<math.exp(min(0,(current.objective()-state.objective())/temperature)):
            current=state
        if state.objective()<=best.objective()+2 and \
                all(state.a!=g.a for g in elites):
            elites.append(state.copy())
            elites.sort(key=lambda g:g.objective())
            elites=elites[:10]
    return best,count


def verify_graph(g):
    # Independent from the cached incremental counts.
    n=36
    full=(1<<n)-1
    comp=[full&~row&~(1<<i) for i,row in enumerate(g.a)]
    k4=len(all_cliques(g.a,4))
    i6=len(all_cliques(comp,6))
    assert (k4,i6)==(g.c4,g.c6)
    return k4,i6


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--start",type=int,default=0)
    p.add_argument("--end",type=int,default=37)
    p.add_argument("--seed",type=int,default=20261112)
    p.add_argument("--ext-rounds",type=int,default=350000)
    p.add_argument("--repair-seconds",type=int,default=35)
    p.add_argument("--repair-steps",type=int,default=5000)
    p.add_argument("--g6",type=Path)
    p.add_argument("--outdir",type=Path,required=True)
    args=p.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    if args.g6:codes=args.g6.read_text().splitlines()
    else:codes=urllib.request.urlopen(URL,timeout=45).read().decode("ascii").splitlines()
    assert len(codes)==37
    summaries=[]
    overall=100000
    for idx in range(args.start,args.end):
        t=time.monotonic()
        rng=random.Random(args.seed+idx*1289)
        g=parent35(codes[idx])
        mask,score,fingerprint=best_extension(g,rng,args.ext_rounds)
        init=append_vertex(g,mask)
        assert init.objective()==score
        best,steps=repaired_graph(init,rng,args.repair_seconds,args.repair_steps)
        k4,i6=verify_graph(best)
        result={"parent_index":idx,"parent_fingerprint":fingerprint,
                "initial_extension_score":score,"extension_degree":mask.bit_count(),
                "final_K4":k4,"final_I6":i6,"final_defects":k4+i6,
                "final_edges":sum(x.bit_count() for x in best.a)//2,
                "repair_steps":steps,
                "seconds":round(time.monotonic()-t,2)}
        summaries.append(result)
        if k4+i6<overall:
            overall=k4+i6
            (args.outdir/"best36.json").write_text(json.dumps({
                "adjacency":best.encode()},indent=2)+"\n")
        (args.outdir/f"parent{idx:02d}-best.json").write_text(json.dumps({
            "adjacency":best.encode()},indent=2)+"\n")
        (args.outdir/"summary.json").write_text(json.dumps({
            "campaign":"independent-35-parent-extension-plus-coordinated-repair",
            "parent_range":[args.start,args.end],"best_defects":overall,
            "parent_results":summaries},indent=2)+"\n")
        print("PARENT",json.dumps(result,sort_keys=True),flush=True)
        if k4+i6==0:break
    print("SUMMARY",json.dumps({"range":[args.start,args.end],
        "best_defects":overall,"processed":len(summaries)}),flush=True)


if __name__=="__main__":
    main()
