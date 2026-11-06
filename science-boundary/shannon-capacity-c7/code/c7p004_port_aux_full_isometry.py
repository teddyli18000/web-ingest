#!/usr/bin/env python3
"""Construct high-quality 367-word auxiliaries by *all* C7^5 signed permutations
and translations, targeting the actual parent port endpoint envelope.

Every candidate remains 367-independent by graph automorphism. For each parent,
score X by (# x with any confusable endpoint, total endpoint incidences),
subject to X disjoint from the candidate endpoint set itself. Unlike a fixed
port-oriented obstruction scan, all left/right endpoint choices remain open.
Top candidates feed directly into the 10D constructive fiber MILP.
"""
import argparse
import itertools
import json
import time
from pathlib import Path
import numpy as np

from c7p004_joint_fibers_construct import (
    DIG, NB, P, parent_codes, private_universe, legal,
)

U=7**5
SHIFTS=tuple(itertools.product((-1,1),repeat=5))
PERMS=tuple(itertools.permutations(range(5)))

def source_sets(family,bpz,parents,extras):
    raw=json.loads((bpz/"data/base_c7.json").read_text())
    F=json.loads((family/"data/family-f.json").read_text())
    src=parent_codes(parents)
    allsets=[("neutral14a",src["neutral14a"]),("neutral14b",src["neutral14b"])]
    allsets += [(f"F{i}",list(map(int,v))) for i,v in enumerate(F["states"])]
    allsets += [("I0",list(map(int,raw["I0"]))),("X",list(map(int,raw["X"])))]
    allsets += [(f"port12{i}",list(map(int,(extras/(f"port12{i}.ids")).read_text().split()))) for i in ("a","b")]
    assert len(allsets)==42
    return allsets

def array_from_ids(v):
    a=np.zeros((7,)*5,dtype=np.float64)
    a[tuple(np.asarray([DIG[x] for x in v],dtype=np.int8).T)]=1.0
    return a

def geometry(I):
    owners,E,_=private_universe(I)
    E=set(E)
    ambient={z for e in E for z in NB[e]}
    weights=np.zeros((7,)*5,dtype=np.float64)
    for e in E:
        for z in NB[e]:
            weights[DIG[z]]+=1
    return owners,E,array_from_ids(E),array_from_ids(ambient),weights

def scan_sources(parents,library,shard,shards,out):
    geo={p:geometry(I) for p,I in parents.items()}
    fft={p:(np.fft.fftn(E),np.fft.fftn(A),np.fft.fftn(W))
         for p,(_,_,E,A,W) in geo.items()}
    results={p:None for p in parents}
    start=time.monotonic()
    tested=0
    for i,(name,S) in enumerate(library):
        if i%shards!=shard:continue
        assert len(S)==367 and legal(S)
        digits=np.asarray([DIG[x] for x in S],dtype=np.int8)
        local={p:None for p in parents}
        for perm in PERMS:
            x=digits[:,perm]
            for sign in SHIFTS:
                y=(x*np.asarray(sign,dtype=np.int8))%7
                A=np.zeros((7,)*5,dtype=np.float64)
                A[tuple(y.T)]=1.0
                fs=np.conj(np.fft.fftn(A))
                for p in parents:
                    FE,FA,FW=fft[p]
                    excluded=np.rint(np.fft.ifftn(fs*FE).real).astype(np.int16)
                    act=np.rint(np.fft.ifftn(fs*FA).real).astype(np.int16)
                    inc=np.rint(np.fft.ifftn(fs*FW).real).astype(np.int16)
                    metric=1000*act.astype(np.int32)+inc
                    metric[excluded!=0]=np.iinfo(np.int32).max
                    arg=int(metric.argmin())
                    if metric.flat[arg]==np.iinfo(np.int32).max:continue
                    delta=tuple(map(int,np.unravel_index(arg,metric.shape)))
                    key=(int(act.flat[arg]),int(inc.flat[arg]))
                    if local[p] is None or key<local[p]["metric"]:
                        z=[sum(((int(y[j,k])+delta[k])%7)*P[k] for k in range(5))
                           for j in range(367)]
                        assert len(set(z))==367 and legal(z)
                        owners,E,_,ambient,weights=geo[p]
                        assert not set(z)&E
                        assert key==(sum(v in {sum(d[k]*P[k] for k in range(5))
                                         for d in np.argwhere(ambient)} for v in z),
                                     int(sum(weights[DIG[v]] for v in z))), (p,key)
                        local[p]={"metric":key,"aux_name":name,"perm":list(perm),
                                  "sign":list(sign),"delta":list(delta),"words":sorted(z)}
                tested+=1
        for p in parents:
            if local[p] is not None:
                if results[p] is None or local[p]["metric"]<results[p]["metric"]:
                    results[p]=local[p]
                    print("IMPROVED",json.dumps({"parent":p,"source":name,
                      "metric":local[p]["metric"]},sort_keys=True),flush=True)
        print("SOURCE",name,"elapsed",round(time.monotonic()-start,2),flush=True)
    out.mkdir(parents=True,exist_ok=True)
    report={"method":"constructive-auxiliary-full-5D-isometries",
            "shard":shard,"shards":shards,"iso_evaluations":tested,
            "sources_in_shard":sum(i%shards==shard for i in range(len(library))),
            "elapsed_seconds":time.monotonic()-start}
    for p,record in results.items():
        if record is None:continue
        (out/(p+".ids")).write_text("".join(f"{v}\n" for v in record["words"]))
        report[p]={k:v for k,v in record.items() if k!="words"}
    (out/"status.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("FINAL",json.dumps(report,sort_keys=True),flush=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("bpz",type=Path)
    ap.add_argument("family",type=Path)
    ap.add_argument("parents",type=Path)
    ap.add_argument("extras",type=Path)
    ap.add_argument("output",type=Path)
    ap.add_argument("--shard",type=int,required=True)
    ap.add_argument("--shards",type=int,default=9)
    args=ap.parse_args()
    src=parent_codes(args.parents)
    library=source_sets(args.family,args.bpz,args.parents,args.extras)
    scan_sources(src,library,args.shard,args.shards,args.output)

if __name__=="__main__":main()
