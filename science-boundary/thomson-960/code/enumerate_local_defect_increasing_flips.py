#!/usr/bin/env python3
"""Enumerate local Delaunay flips that raise e432 from 23 to 24 dislocations.

No target minimum is supplied.  We inspect the source triangulation, identify the
unique short 5-7-5 scar, and enumerate every legal bistellar flip whose *degree
count after the combinatorial flip* is exactly 36/900/24.  Candidates are ranked
by graph distance from that short scar and by the geometric threshold needed to
cross the corresponding Delaunay boundary.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import Counter,deque
import numpy as np

from search_from_seed_modes import load_seed
from search_e564_defect_flip_parallel import topology,threshold
from search_scar_core_elastic_split import graph,short_component

TARGET={5:36,6:900,7:24}


def distance_to_core(adj,core):
    d={int(v):0 for v in core}; q=deque(core)
    while q:
        u=q.popleft()
        for v in adj[u]:
            if v not in d:
                d[v]=d[u]+1; q.append(v)
    return d


def increasing_flips(x):
    deg,ef=topology(x); edges=set(ef); out=[]
    base=Counter(deg.tolist())
    for (u,v),opp in ef.items():
        if len(opp)!=2: continue
        a,b=opp; ne=(min(a,b),max(a,b))
        if ne in edges: continue
        nd=deg.copy(); nd[u]-=1; nd[v]-=1; nd[a]+=1; nd[b]+=1
        cc=Counter(nd.tolist())
        if cc.get(5,0)==36 and cc.get(6,0)==900 and cc.get(7,0)==24 and sum(cc.values())==len(x):
            # Exclude any unexpected 4/8 etc even if 5/6/7 counts happen to match.
            if any(k not in (5,6,7) and val for k,val in cc.items()): continue
            out.append((int(u),int(v),int(a),int(b)))
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--max-shell',type=int,default=4); ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x=load_seed(args.seed_json)
    adj,deg=graph(x); core=short_component(adj,deg); dist=distance_to_core(adj,core)
    flips=increasing_flips(x); rows=[]
    for q in flips:
        ds=[dist[int(i)] for i in q]; shell=min(ds); maxd=max(ds)
        th={p:threshold(x,q,p) for p in ('balanced','newdiag','olddiag')}
        rows.append({'quad':list(q),'min_core_distance':int(shell),'max_core_distance':int(maxd),
                     'degrees_before':[int(deg[i]) for i in q],'thresholds':th})
    rows.sort(key=lambda r:(r['min_core_distance'],min((v for v in r['thresholds'].values() if v is not None),default=99),r['max_core_distance']))
    local=[r for r in rows if r['min_core_distance']<=args.max_shell]
    print('CORE',core,'degrees',[int(deg[i]) for i in core],'TOTAL_TARGET_FLIPS',len(rows),'LOCAL',len(local),flush=True)
    for i,r in enumerate(local[:80]): print('CAND',i,r,flush=True)
    pathlib.Path(args.out).write_text(json.dumps({'seed':args.seed_json,'core':core,'core_degrees':[int(deg[i]) for i in core],
        'total_target_flips':len(rows),'max_shell':args.max_shell,'local_flips':local,'all_flips':rows},separators=(',',':'))+'\n')

if __name__=='__main__': main()
