#!/usr/bin/env python3
"""Constructive cross-core six-tail repair for the 14-defect (4,6,36) near miss.

Enumerate every legal 30-core obtained by deleting six vertices that hit every
forbidden set at least twice. For each core, jointly regenerate six individually
legal tail neighborhoods; optimize the 15 tail-tail edges exactly at each move.
This is a search, not an exclusion. Recount any improvement independently.
"""
import argparse
import itertools
import json
import math
import random
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
from core30_six_tail_joint import legal_domains, features, clique_masks, count, comp

P = tuple(itertools.combinations(range(6), 2))
PI = {p:i for i,p in enumerate(P)}
TRI = tuple(itertools.combinations(range(6), 3))
QUAD = tuple(itertools.combinations(range(6), 4))
FIVE = tuple(itertools.combinations(range(6), 5))
FULL = (1<<30)-1
FEAT = features()

def rows_to_masks(rows):
    return [sum(1<<j for j,b in enumerate(r) if b=="1") for r in rows]

def defects(rows):
    a = rows_to_masks(rows)
    return clique_masks(a,4) + clique_masks(comp(a),6)

def possible_cores(rows):
    bad=defects(rows)
    return [sub for sub in itertools.combinations(range(36),6)
            if all((m&sum(1<<x for x in sub)).bit_count()>=2 for m in bad)]

def to_rows(core, domain, ids, bits):
    g=core[:]+[0]*6
    for t,index in enumerate(ids):
        m=domain[index]
        while m:
            b=m&-m;v=b.bit_length()-1;m^=b
            g[v]|=1<<(30+t);g[30+t]|=1<<v
    for k,(u,v) in enumerate(P):
        if bits>>k&1:g[30+u]|=1<<(30+v);g[30+v]|=1<<(30+u)
    return ["".join("1" if g[i]>>j&1 else "0" for j in range(36)) for i in range(36)]

def search_one(parent,part,rng,steps,best,outdir,core_id):
    keep=[i for i in range(36) if i not in part]
    core=[sum(1<<j for j,v in enumerate(keep) if parent[u][v]=="1") for u in keep]
    tails=[sum(1<<j for j,v in enumerate(keep) if parent[u][v]=="1") for u in part]
    domain=legal_domains(core)
    lookup={mask:i for i,mask in enumerate(domain)}
    ids=tuple(sorted(lookup[m] for m in tails))
    nbr=[]
    for i,x in enumerate(domain):
        nbr.append([j for _,j in sorted(((x^y).bit_count(),j)
                   for j,y in enumerate(domain) if i!=j)[:20]])
    cc=comp(core)
    @lru_cache(maxsize=250000)
    def pair(x,y):
        intersection=x&y
        k4=sum((core[i]&intersection).bit_count()
               for i in range(30) if intersection>>i&1)//2
        return count(cc,FULL&~(x|y),4),k4
    @lru_cache(maxsize=250000)
    def triple(x,y,z):
        return (x&y&z).bit_count(),count(cc,FULL&~(x|y|z),3)
    @lru_cache(maxsize=100000)
    def quad(x,y,z,w):
        return count(cc,FULL&~(x|y|z|w),2)
    def evaluate(indexes):
        masks=[domain[i] for i in indexes]
        pairs=[pair(*sorted((masks[u],masks[v]))) for u,v in P]
        base=sum(a for a,b in pairs)
        w=[b-a for a,b in pairs]
        for q in TRI:
            x,y,z=sorted(masks[i] for i in q)
            w.extend(triple(x,y,z))
        for q in QUAD:
            x=sorted(masks[i] for i in q)
            w.extend((1,quad(*x)))
        for q in FIVE:
            free=FULL
            for i in q:free &= ~masks[i]
            w.append(free.bit_count())
        w.append(1)
        scores=base+FEAT@np.asarray(w,dtype=np.int16)
        b=int(scores.argmin())
        return int(scores[b]),b

    value,bits=evaluate(ids)
    start=value
    pool=[(value,ids)]
    seen={ids}
    for step in range(steps):
        if step and step%420==0:
            value,ids=rng.choice(pool[:min(12,len(pool))])
            value,bits=evaluate(ids)
        proposal=list(ids)
        how_many=rng.choices([1,2,3,4,5,6],[22,20,26,18,10,4])[0]
        for t in rng.sample(range(6),how_many):
            z=rng.random()
            if z<0.80:proposal[t]=rng.choice(nbr[proposal[t]])
            elif z<0.92:proposal[t]=rng.randrange(len(domain))
            else:proposal[t]=rng.choice(pool[:min(12,len(pool))])[1][rng.randrange(6)]
        proposal=tuple(sorted(proposal))
        nextval,nextbits=evaluate(proposal)
        temperature=2.2+(step%420)/100
        if nextval<=value or rng.random()<math.exp((value-nextval)/temperature):
            ids,value,bits=proposal,nextval,nextbits
            if ids not in seen and value<=best+6:
                seen.add(ids);pool.append((value,ids))
                pool.sort(key=lambda x:x[0]);pool=pool[:28]
        if value<best:
            rows=to_rows(core,domain,ids,bits)
            a=rows_to_masks(rows)
            k4=count(a,(1<<36)-1,4)
            i6=count(comp(a),(1<<36)-1,6)
            assert k4+i6==value,(k4,i6,value)
            best=value
            (outdir/"best-36.json").write_text(json.dumps({"adjacency":rows})+"\n")
            print("IMPROVED",json.dumps({"core_index":core_id,"score":best,
                  "K4":k4,"I6":i6,"domain":len(domain),"step":step}),flush=True)
            if best==0:break
    return best,{"core_index":core_id,"tail_vertices":part,
                 "domain":len(domain),"initial_best":start,
                 "best_score":best,"steps":step+1}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seed",type=Path,required=True)
    p.add_argument("--outdir",type=Path,required=True)
    p.add_argument("--start",type=int,default=0)
    p.add_argument("--stop",type=int,default=46)
    p.add_argument("--steps",type=int,default=5000)
    p.add_argument("--rng",type=int,default=20261107)
    args=p.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    parent=json.loads(args.seed.read_text())["adjacency"]
    assert len(parent)==36 and len(defects(parent))==14
    cores=possible_cores(parent)
    assert len(cores)==46
    best=14
    records=[]
    rng=random.Random(args.rng)
    for i in range(args.start,args.stop):
        t=time.monotonic()
        best,record=search_one(parent,cores[i],rng,args.steps,best,args.outdir,i)
        records.append(record)
        print("CORE",i,"domain",record["domain"],
              "best",best,"seconds",round(time.monotonic()-t,2),flush=True)
        if best==0:break
    summary={"campaign":"cross-core-six-tail-constructive","cores_total":len(cores),
             "core_range":[args.start,args.stop],"rng":args.rng,"steps":args.steps,
             "best_defects":best,"records":records,"result":"witness" if best==0 else "no_witness"}
    (args.outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("SUMMARY",json.dumps({k:v for k,v in summary.items() if k!="records"}),flush=True)

if __name__=="__main__":main()
