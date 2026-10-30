#!/usr/bin/env python3
"""Defect-core-aware transfer between two Thomson minima."""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import ConvexHull
import search_topology_morph as tm


def load(path):
    d=json.loads(pathlib.Path(path).read_text()); p=d.get('points') if isinstance(d,dict) else d
    if p is None or len(p)!=tm.N: raise ValueError('expected 960 points')
    x=np.asarray(p,float); return x/np.linalg.norm(x,axis=1)[:,None]


def degrees(x):
    h=ConvexHull(x); adj=[set() for _ in range(len(x))]
    for tri in h.simplices:
        a,b,c=map(int,tri)
        adj[a].update((b,c)); adj[b].update((a,c)); adj[c].update((a,b))
    return np.array([len(s) for s in adj],int)


def align(source,target,seed,starts):
    rng=np.random.default_rng(seed)
    rms,R,sa=tm.icp(source,target,rng,starts=starts,iters=18)
    cost=np.maximum(0.0,2-2*np.clip(target@sa.T,-1,1))
    ia,ib=linear_sum_assignment(cost)
    if not np.array_equal(ia,np.arange(tm.N)): raise RuntimeError('assignment rows')
    return sa[ib],ib,float(rms),float(np.sqrt(np.mean(cost[ia,ib])))


def unmatched_target_cores(sm,source_deg,target,target_deg):
    groups={}
    for typ in (5,7):
        ia=np.flatnonzero(source_deg==typ); ib=np.flatnonzero(target_deg==typ)
        if len(ia)>len(ib): raise ValueError('target must have at least as many defects of each type')
        cost=np.maximum(0.0,2-2*np.clip(sm[ia]@target[ib].T,-1,1))
        ra,rb=linear_sum_assignment(cost)
        used=set(map(int,ib[rb])); groups[typ]=np.array(sorted(set(map(int,ib))-used),int)
    fives=groups[5]; sevens=groups[7]
    if len(fives)!=len(sevens): raise RuntimeError('unmatched 5/7 counts differ')
    cost=np.maximum(0.0,2-2*np.clip(target[sevens]@target[fives].T,-1,1))
    rs,rf=linear_sum_assignment(cost); cores=[]
    for a,b in zip(rs,rf):
        i7=int(sevens[a]); i5=int(fives[b]); c=target[i7]+target[i5]; c/=np.linalg.norm(c)
        cores.append({'i5':i5,'i7':i7,'center':c})
    return cores


def log_field(base,goal):
    c=np.clip(np.sum(base*goal,axis=1),-1.0,1.0); th=np.arccos(c); s=np.sin(th)
    v=np.zeros_like(base); good=s>1e-10
    v[good]=(th[good]/s[good])[:,None]*(goal[good]-c[good,None]*base[good])
    bad=~good
    if np.any(bad):
        z=goal[bad]-base[bad]; z-=np.sum(z*base[bad],axis=1)[:,None]*base[bad]; v[bad]=z
    return v


def exp_field(base,v,alpha,w):
    z=v*(alpha*w)[:,None]; a=np.linalg.norm(z,axis=1); out=np.empty_like(base)
    small=a<1e-12; out[small]=base[small]+z[small]
    q=~small; out[q]=np.cos(a[q])[:,None]*base[q]+(np.sin(a[q])/a[q])[:,None]*z[q]
    return out/np.linalg.norm(out,axis=1)[:,None]


def weights(base,centers,radius):
    if not centers: return np.zeros(len(base))
    C=np.stack(centers); ang=np.arccos(np.clip(base@C.T,-1,1)); d=np.min(ang,axis=1)
    return np.exp(-(d/radius)**4)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('source_json'); ap.add_argument('target_json')
    ap.add_argument('--seed',type=int,required=True); ap.add_argument('--starts',type=int,default=24)
    ap.add_argument('--radii',default='0.10,0.16,0.24'); ap.add_argument('--alphas',default='0.35,0.70,1.05,1.40')
    ap.add_argument('--maxiter',type=int,default=2800); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()

    source=load(args.source_json); target=load(args.target_json); ds=degrees(source); dt=degrees(target)
    sm,perm,rms,mrms=align(source,target,args.seed,args.starts); ds=ds[perm]
    cores=unmatched_target_cores(sm,ds,target,dt)
    print('ALIGN',rms,mrms,'source',tm.raw_energy(sm),'target',tm.raw_energy(target),'cores',len(cores),flush=True)
    for j,c in enumerate(cores): print('CORE',j,'i5',c['i5'],'i7',c['i7'],'center',c['center'].tolist(),flush=True)
    subsets=[([j],f'core{j}') for j in range(len(cores))]
    if cores: subsets.append((list(range(len(cores))),'all'))
    radii=[float(z) for z in args.radii.split(',') if z]; alphas=[float(z) for z in args.alphas.split(',') if z]
    rows=[]; saved=[]

    def attempt(label,base,goal,centers,r,a):
        v=log_field(base,goal); w=weights(base,centers,r); x=exp_field(base,v,a,w)
        start=tm.raw_energy(x); e,y,nit,ok=tm.relax(x,maxiter=args.maxiter); cc=tm.coord_counts(y)
        row={'label':label,'radius':r,'alpha':a,'start_energy':start,'energy':e,
             'delta_live':e-args.live_score,'coord_counts':cc,'nit':nit,'success':ok,
             'weight_mean':float(np.mean(w)),'weight_max':float(np.max(w))}
        rows.append(row); print(label,'r',r,'a',a,'E',f'{e:.12f}','dLive',f'{e-args.live_score:+.9g}','cc',cc,flush=True)
        if e < args.live_score+0.35 and all(abs(e-z['energy'])>2e-6 or cc!=z['coord_counts'] for z in saved):
            saved.append({'energy':e,'delta_live':e-args.live_score,'coord_counts':cc,'label':label,
                          'radius':r,'alpha':a,'points':y.tolist()})

    for ids,name in subsets:
        centers=[cores[j]['center'] for j in ids]
        for r in radii:
            for a in alphas:
                attempt(f'forward:{name}',sm,target,centers,r,a)
                attempt(f'reverse:{name}',target,sm,centers,r,a)

    saved.sort(key=lambda z:z['energy']); best=min(rows,key=lambda z:z['energy'])
    out={'seed':args.seed,'source_energy':tm.raw_energy(sm),'target_energy':tm.raw_energy(target),
         'source_coord':tm.coord_counts(sm),'target_coord':tm.coord_counts(target),
         'particle_nn_rms':rms,'assignment_rms':mrms,
         'cores':[{'i5':c['i5'],'i7':c['i7'],'center':c['center'].tolist()} for c in cores],
         'rows':rows,'distinct_low_basins':saved[:24],
         'best_energy':best['energy'],'best_delta_live':best['delta_live'],'best_label':best['label']}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if saved and saved[0]['energy'] < args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(saved[0],separators=(',',':'))+'\n')


if __name__=='__main__': main()
