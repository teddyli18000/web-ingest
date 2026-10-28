#!/usr/bin/env python3
"""Near-neighbor 2-opt probe for p010; exact TSPLIB integer gain verification."""
import argparse
import importlib.util
import json
import math
import pathlib
import sys
import time
from functools import lru_cache

import numpy as np
from scipy.spatial import cKDTree

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--report',required=True)
    p.add_argument('--k',type=int,default=32)
    p.add_argument('--max-passes',type=int,default=4)
    args=p.parse_args()
    root=pathlib.Path(__file__).resolve()
    upstream=pathlib.Path(__import__('os').environ['FEWSHOTS_ROOT'])
    modpath=upstream/'problems/p010-mona-lisa-tsp/verify/verify.py'
    spec=importlib.util.spec_from_file_location('p010_verify',modpath)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    tour=np.asarray(json.loads(pathlib.Path(args.input).read_text())['tour'],dtype=np.int32)-1
    assert len(tour)==100000 and len(np.unique(tour))==100000
    xs,ys=mod.coordinates()
    xy=np.column_stack((xs,ys)).astype(np.int32)
    start=time.time()
    neighbors=cKDTree(xy).query(xy,k=args.k+1,workers=-1)[1][:,1:].astype(np.int32)
    @lru_cache(maxsize=2500000)
    def d(a,b):
        dx=int(xs[a])-int(xs[b]);dy=int(ys[a])-int(ys[b])
        return mod.euc_2d(dx,dy)
    def length(t):
        return sum(d(int(t[i]),int(t[(i+1)%len(t)])) for i in range(len(t)))
    initial=length(tour)
    passes=[]
    for iteration in range(args.max_passes):
        position=np.empty(len(tour),dtype=np.int32);position[tour]=np.arange(len(tour))
        nxt=np.roll(tour,-1)
        base=np.fromiter((d(int(a),int(b)) for a,b in zip(tour,nxt)),dtype=np.int32,count=len(tour))
        # For each oriented baseline edge (a,b), candidate c near a, edge (c,d).
        # Standard reversal replaces (a,b),(c,d) with (a,c),(b,d), c edge forward in tour.
        chosen=None
        scanned=0
        for i in range(len(tour)):
            a=int(tour[i]);b=int(nxt[i])
            for c0 in neighbors[a]:
                c=int(c0);j=int(position[c])
                if i==j or (i+1)%len(tour)==j or (j+1)%len(tour)==i: continue
                # No wrap-around reversal: require i < j, and i+1 < j.
                if j<=i+1: continue
                dd=int(nxt[j]);scanned+=1
                gain=int(base[i])+int(base[j])-d(a,c)-d(b,dd)
                if gain>0 and (chosen is None or gain>chosen[0]):
                    chosen=(gain,i,j)
        if chosen is None:
            passes.append({'iteration':iteration,'scanned_pairs':scanned,'best_gain':0})
            break
        gain,i,j=chosen
        tour[i+1:j+1]=tour[i+1:j+1][::-1]
        newlength=length(tour)
        assert newlength==initial-sum(x['best_gain'] for x in passes)-gain
        passes.append({'iteration':iteration,'scanned_pairs':scanned,'best_gain':gain,'new_length':newlength})
    final=length(tour)
    output={'tour':(tour+1).tolist()}
    pathlib.Path(args.output).write_text(json.dumps(output,separators=(',',':')))
    verdict=mod.verify_dir(pathlib.Path(args.output).parent,mod.load_config())
    # verify_dir expects certificate.json; make independent check against direct data as well
    score=mod.tour_length(output['tour'])
    assert score==final
    report={'baseline':initial,'final':final,'passes':passes,'k':args.k,'elapsed_seconds':round(time.time()-start,2),'verifier_direct_score':score}
    pathlib.Path(args.report).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
    assert initial==5757191
if __name__=='__main__':main()
