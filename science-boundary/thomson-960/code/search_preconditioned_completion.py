#!/usr/bin/env python3
"""Scaffold a 23->24 completion after distributed neutral Delaunay rewiring.

Along the natural e432->B/A/R event avalanche, the first three Delaunay flips
change the triangulation but keep coordination 35/902/23.  After those neutral
rewirings, two central flips become one-step 23->24 completions even though the
corresponding move is not a direct local completion of the original e432 scar.

Construct a pointwise geodesic prefix (default t=0.31), detect all vertices
whose incident Delaunay edges differ from e432, cross one requested completion
boundary, relax with prefix+quad vertices fixed, then free the completion quad
while retaining the neutral-prefix scaffold, and finally release all points.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import Counter
import numpy as np
from scipy.spatial import ConvexHull

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed,stable_relax_q
from search_e564_defect_flip_parallel import topology,threshold,perturb,flipped
from search_e564_scaffolded_flip import fixed_relax
from search_defect_core_transfer import log_field


def exp_vec(base,v):
    a=np.linalg.norm(v,axis=1); out=np.empty_like(base)
    small=a<1e-12; out[small]=base[small]+v[small]
    q=~small
    out[q]=np.cos(a[q])[:,None]*base[q]+(np.sin(a[q])/a[q])[:,None]*v[q]
    return out/np.linalg.norm(out,axis=1)[:,None]


def edge_set(x):
    h=ConvexHull(x); es=set()
    for tri in h.simplices:
        a,b,c=map(int,tri)
        es.add(tuple(sorted((a,b)))); es.add(tuple(sorted((a,c)))); es.add(tuple(sorted((b,c))))
    return es


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('source_json'); ap.add_argument('guide_json')
    ap.add_argument('--prefix-t',type=float,default=0.31)
    ap.add_argument('--quad',required=True,help='old_u,old_v,new_a,new_b')
    ap.add_argument('--patterns',default='balanced,newdiag,olddiag')
    ap.add_argument('--multipliers',default='1.01,1.05,1.12,1.25,1.50')
    ap.add_argument('--fixed-maxiter',type=int,default=1800)
    ap.add_argument('--prefix-release-maxiter',type=int,default=1800)
    ap.add_argument('--release-maxiter',type=int,default=3200)
    ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    _,S=load_seed(args.source_json); _,G=load_seed(args.guide_json)
    X=exp_vec(S,args.prefix_t*log_field(S,G))
    Es=edge_set(S); Ex=edge_set(X)
    changed=(Es-Ex)|(Ex-Es)
    prefix_support=sorted({v for e in changed for v in e})
    quad=tuple(int(z) for z in args.quad.split(','))
    if len(quad)!=4: raise ValueError('quad needs four indices')
    all_support=sorted(set(prefix_support)|set(quad))
    dx,_=topology(X); ccx=Counter(dx.tolist())
    print('PREFIX t',args.prefix_t,'energy',sm.fg(sm.xyz_to_vars(X))[0],
          'coord',dict(sorted(ccx.items())),'changed_edges',len(changed),
          'prefix_support',prefix_support,'quad',quad,flush=True)

    patterns=[z for z in args.patterns.split(',') if z]
    mults=[float(z) for z in args.multipliers.split(',') if z]
    rows=[]; basins=[]; thrs={}
    for pat in patterns:
        th=threshold(X,quad,pat); thrs[pat]=th
        print('THRESHOLD',pat,th,flush=True)
        if th is None: continue
        for m in mults:
            start=perturb(X,quad,th*m,pat); q0=sm.xyz_to_vars(start)
            ds,_=topology(start); ccs=Counter(ds.tolist()); Es0,_=sm.fg(q0)
            # Stage 1: preserve both neutral-prefix rewiring and completion quad.
            E1,raw1,q1,x1,n1,ok1,msg1=fixed_relax(q0,all_support,args.fixed_maxiter)
            d1,_=topology(x1); cc1=Counter(d1.tolist())
            # Stage 2: completion quad is released, while the distributed neutral prefix remains anchored.
            E2,raw2,q2,x2,n2,ok2,msg2=fixed_relax(q1,prefix_support,args.prefix_release_maxiter)
            d2,_=topology(x2); cc2=Counter(d2.tolist())
            # Stage 3: full release.
            E3,raw3,x3,n3,ok3,msg3=stable_relax_q(q2,maxiter=args.release_maxiter)
            d3,_=topology(x3); cc3=Counter(d3.tolist())
            row={'pattern':pat,'threshold':th,'multiplier':m,'initial_flipped':bool(flipped(start,quad)),
                 'start_energy':float(Es0),'start_coord':{str(k):int(v) for k,v in sorted(ccs.items())},
                 'fixed_all_energy':float(E1),'fixed_all_coord':{str(k):int(v) for k,v in sorted(cc1.items())},
                 'fixed_prefix_energy':float(E2),'fixed_prefix_coord':{str(k):int(v) for k,v in sorted(cc2.items())},
                 'release_energy':float(E3),'delta_live':float(E3-args.live_score),
                 'release_coord':{str(k):int(v) for k,v in sorted(cc3.items())},
                 'nit':[int(n1),int(n2),int(n3)],'success':[bool(ok1),bool(ok2),bool(ok3)],
                 'messages':[str(msg1),str(msg2),str(msg3)]}
            rows.append(row)
            print('DONE',pat,'m',m,'start',f'{Es0:.9f}',row['start_coord'],
                  'fixed-all',f'{E1:.12f}',row['fixed_all_coord'],
                  'fixed-prefix',f'{E2:.12f}',row['fixed_prefix_coord'],
                  'release',f'{E3:.12f}','dLive',f'{E3-args.live_score:+.9g}',row['release_coord'],flush=True)
            if not any(abs(E3-b['energy'])<2e-6 and row['release_coord']==b['coord_counts'] for b in basins):
                basins.append({'energy':float(E3),'delta_live':float(E3-args.live_score),
                               'coord_counts':row['release_coord'],'pattern':pat,'multiplier':m,
                               'points':x3.tolist()})
    basins.sort(key=lambda z:z['energy'])
    best=min((r['release_energy'] for r in rows),default=None)
    out={'prefix_t':args.prefix_t,'prefix_support':prefix_support,'prefix_changed_edges':[list(e) for e in sorted(changed)],
         'quad':list(quad),'thresholds':thrs,'rows':rows,'lowest_distinct_release_basins':basins[:16],
         'best_release_energy':best,'best_delta_live':best-args.live_score if best is not None else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if basins and basins[0]['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(basins[0],separators=(',',':'))+'\n')

if __name__=='__main__': main()
