#!/usr/bin/env python3
"""Compare topological defect motifs across Thomson minima."""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import ConvexHull
import search_topology_morph as tm


def load(path):
    d=json.loads(pathlib.Path(path).read_text())
    p=d.get('points') if isinstance(d,dict) else d
    if p is None or len(p)!=tm.N: raise ValueError(path)
    x=np.asarray(p,float); x/=np.linalg.norm(x,axis=1)[:,None]
    return x


def graph_info(x):
    hull=ConvexHull(x)
    adj=[set() for _ in range(len(x))]
    for tri in hull.simplices:
        a,b,c=map(int,tri)
        adj[a].update((b,c)); adj[b].update((a,c)); adj[c].update((a,b))
    deg=np.array([len(s) for s in adj],int)
    defects=np.flatnonzero(deg!=6)
    dset=set(map(int,defects)); comps=[]; seen=set()
    for s in defects:
        s=int(s)
        if s in seen: continue
        stack=[s]; seen.add(s); comp=[]
        while stack:
            u=stack.pop(); comp.append(u)
            for v in adj[u]:
                if v in dset and v not in seen:
                    seen.add(v); stack.append(v)
        comps.append(comp)
    rows=[]
    for comp in comps:
        vals=deg[comp]
        rows.append({'size':len(comp),'n5':int(np.sum(vals==5)),'n7':int(np.sum(vals==7)),
                     'degrees':[int(v) for v in sorted(vals)]})
    rows.sort(key=lambda z:(-z['size'],-z['n7'],-z['n5']))
    return deg,adj,rows


def match_defects(A,B,seed,starts):
    rng=np.random.default_rng(seed)
    rms,R,Ar=tm.icp(A,B,rng,starts=starts,iters=18)
    da,_,_=graph_info(A); db,_,_=graph_info(B)
    out={'particle_nn_rms':float(rms)}
    for typ in (5,7):
        ia=np.flatnonzero(da==typ); ib=np.flatnonzero(db==typ)
        if len(ia) and len(ib):
            cost=np.maximum(0.0,2-2*np.clip(Ar[ia]@B[ib].T,-1,1))
            ra,rb=linear_sum_assignment(cost); dist=np.sqrt(cost[ra,rb])
            matched_a=ia[ra]; matched_b=ib[rb]
            ua=sorted(set(map(int,ia))-set(map(int,matched_a)))
            ub=sorted(set(map(int,ib))-set(map(int,matched_b)))
            out[str(typ)]={'source_count':len(ia),'target_count':len(ib),
                           'match_rms':float(np.sqrt(np.mean(dist*dist))),
                           'match_max':float(np.max(dist)),
                           'unmatched_source':[Ar[i].tolist() for i in ua],
                           'unmatched_target':[B[i].tolist() for i in ub]}
        else:
            out[str(typ)]={'source_count':len(ia),'target_count':len(ib),'match_rms':None,
                           'match_max':None,'unmatched_source':[],'unmatched_target':[]}
    return out


def summary(x):
    deg,adj,comps=graph_info(x); uniq,cnt=np.unique(deg,return_counts=True)
    return {'energy':float(tm.raw_energy(x)),
            'coord_counts':{str(int(k)):int(v) for k,v in zip(uniq,cnt)},
            'defect_components':comps,'n_defect_components':len(comps)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--state',action='append',required=True,help='name=path')
    ap.add_argument('--pair',action='append',default=[],help='source,target')
    ap.add_argument('--seed',type=int,default=20261030); ap.add_argument('--starts',type=int,default=24)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    states={}
    for spec in args.state:
        name,path=spec.split('=',1); states[name]=load(path)
    result={'states':{k:summary(v) for k,v in states.items()},'pairs':{}}
    for j,spec in enumerate(args.pair):
        a,b=spec.split(',',1); z=match_defects(states[a],states[b],args.seed+j,args.starts)
        result['pairs'][f'{a}->{b}']=z
        print(a,'->',b,'particle_rms',z['particle_nn_rms'],
              '5rms',z['5']['match_rms'],'7rms',z['7']['match_rms'],
              'unmatched5',len(z['5']['unmatched_source']),len(z['5']['unmatched_target']),
              'unmatched7',len(z['7']['unmatched_source']),len(z['7']['unmatched_target']),flush=True)
    for n,s in result['states'].items():
        print('STATE',n,s['energy'],s['coord_counts'],'components',s['defect_components'][:12],flush=True)
    pathlib.Path(args.out).write_text(json.dumps(result,separators=(',',':'))+'\n')


if __name__=='__main__': main()
