#!/usr/bin/env python3
"""Enumerate legal Delaunay flips preserving a seed's 5/6/7 coordination counts.

Useful for mapping the immediate topological neighborhood of a low-energy
Thomson minimum.  Candidates are ranked by the exact balanced perturbation
threshold needed to cross the Delaunay boundary.  Equal thresholds expose
symmetry-related flip orbits when the seed is symmetric.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import Counter

from search_from_seed_modes import load_seed
from search_e564_defect_flip_parallel import topology,threshold


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json'); ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x=load_seed(args.seed_json); deg,ef=topology(x); edges=set(ef); base=Counter(deg.tolist())
    rows=[]
    for (u,v),opp in ef.items():
        if len(opp)!=2: continue
        a,b=opp; ne=(min(a,b),max(a,b))
        if ne in edges: continue
        nd=deg.copy(); nd[u]-=1; nd[v]-=1; nd[a]+=1; nd[b]+=1
        cc=Counter(nd.tolist())
        if cc!=base: continue
        q=(int(u),int(v),int(a),int(b)); t=threshold(x,q,'balanced')
        if t is None: continue
        rows.append({'quad':list(q),'threshold':float(t),'degrees_before':[int(deg[i]) for i in q]})
    rows.sort(key=lambda r:(r['threshold'],r['quad']))
    # Group by a tolerance safely below separations seen between unrelated soft orbits.
    groups=[]
    for r in rows:
        if not groups or abs(r['threshold']-groups[-1]['threshold'])>=1e-7:
            groups.append({'threshold':r['threshold'],'members':[r]})
        else: groups[-1]['members'].append(r)
    print('BASE',dict(sorted(base.items())),'FLIPS',len(rows),'ORBITS',len(groups),flush=True)
    for i,g in enumerate(groups):
        print('ORBIT',i,'threshold',g['threshold'],'size',len(g['members']),'rep',g['members'][0],flush=True)
    pathlib.Path(args.out).write_text(json.dumps({'seed':args.seed_json,'base_coord':{str(k):int(v) for k,v in sorted(base.items())},
        'rows':rows,'threshold_groups':groups},separators=(',',':'))+'\n')

if __name__=='__main__': main()
