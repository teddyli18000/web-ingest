#!/usr/bin/env python3
"""Remove one full 12-point tetrahedral orbit from the historical N=972 twin family.

N=972 -> 960 is exactly 12 particles, matching a generic orbit of the proper
tetrahedral rotation group T.  The historical 972 CCD minimum is T_h symmetric
and belongs to the twinned-defect family.  Rather than greedy one-at-a-time
removal (which can destroy both symmetry and topology), recover the proper T
rotation group directly from the point cloud, enumerate its point orbits, screen
12-point bulk orbits away from the 5/7 defect core, remove one entire orbit, and
fully release the resulting N=960 child.

This defines a finite, symmetry/topology-preserving search space not covered by
ordinary neighboring-size propagation.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.optimize import differential_evolution, minimize
from scipy.spatial import cKDTree, ConvexHull
from scipy.spatial.transform import Rotation
import search_size_beam as sb
from analyze_twinned_motif import load_xyz

PI=math.pi

def axis_from_angles(v):
    th,ph=v; return np.array([math.sin(th)*math.cos(ph),math.sin(th)*math.sin(ph),math.cos(th)])
def rot_axis(n,ang): return Rotation.from_rotvec(ang*np.asarray(n,float)/np.linalg.norm(n)).as_matrix()
def symmetry_objective(v,x,tree,ang):
    n=axis_from_angles(v); R=rot_axis(n,ang); d,_=tree.query(x@R.T,k=1)
    # RMS plus a small max-error term makes the exact symmetry basin easier to locate.
    return float(np.sqrt(np.mean(d*d))+0.15*np.max(d))
def recover_axis(x,ang,seed):
    tree=cKDTree(x); rng=np.random.default_rng(seed)
    # Differential evolution is robust on the two angular variables.  Polish the
    # best few random/DE seeds with Nelder-Mead because the nearest-neighbor
    # objective is only piecewise smooth.
    res=differential_evolution(lambda v:symmetry_objective(v,x,tree,ang),[(0,PI),(-PI,PI)],seed=seed,popsize=18,maxiter=45,tol=1e-9,polish=False,workers=1)
    seeds=[res.x]
    for _ in range(10):
        n=rng.normal(size=3);n/=np.linalg.norm(n);seeds.append([math.acos(np.clip(n[2],-1,1)),math.atan2(n[1],n[0])])
    best=None
    for s in seeds:
        r=minimize(lambda v:symmetry_objective(v,x,tree,ang),s,method='Nelder-Mead',options={'maxiter':1200,'xatol':1e-12,'fatol':1e-13})
        item=(float(r.fun),axis_from_angles(r.x))
        if best is None or item[0]<best[0]:best=item
    return best

def mat_close(A,B,tol=3e-6): return float(np.linalg.norm(A-B))<tol
def ortho(M):
    U,S,Vt=np.linalg.svd(M); R=U@Vt
    if np.linalg.det(R)<0:U[:,-1]*=-1;R=U@Vt
    return R

def group_closure(generators):
    G=[np.eye(3)]; changed=True
    while changed:
        changed=False
        for A in list(G):
            for B in generators:
                for C in (A@B,B@A):
                    C=ortho(C)
                    if not any(mat_close(C,Q) for Q in G):G.append(C);changed=True
                    if len(G)>24:raise RuntimeError(f'group closure too large: {len(G)}')
    return G

def validate_group(x,G,tol=2e-5):
    tree=cKDTree(x); perms=[]; worst=0.0
    for R in G:
        d,p=tree.query(x@R.T,k=1); worst=max(worst,float(np.max(d)))
        if len(np.unique(p))!=len(x):raise RuntimeError('symmetry map not bijective')
        perms.append(np.asarray(p,int))
    if worst>tol:raise RuntimeError(f'group validation worst {worst}')
    return perms,worst

def graph(x):
    h=ConvexHull(x);nb=[set() for _ in range(len(x))];edges=set()
    for tri in h.simplices:
        a,b,c=map(int,tri)
        for u,v in ((a,b),(b,c),(c,a)):
            if u>v:u,v=v,u
            edges.add((u,v));nb[u].add(v);nb[v].add(u)
    z=np.array([len(s) for s in nb],int);return nb,edges,z
def core_distance(nb,z):
    n=len(z);dist=np.full(n,10**9,int);front=list(map(int,np.flatnonzero(z!=6)))
    for v in front:dist[v]=0
    q=list(front);head=0
    while head<len(q):
        u=q[head];head+=1
        for v in nb[u]:
            if dist[v]>dist[u]+1:dist[v]=dist[u]+1;q.append(v)
    return dist
def e77_count(x):
    nb,edges,z=graph(x);return int(sum(1 for a,b in edges if z[a]==7 and z[b]==7)),{str(k):int(np.sum(z==k)) for k in sorted(set(map(int,z)))}
def raw_energy(x):
    d=np.clip(x@x.T,-1,1);r2=np.maximum(2-2*d,1e-300);np.fill_diagonal(r2,np.inf)
    iu=np.triu_indices(len(x),1);return float(np.sum(np.asarray((1/np.sqrt(r2))[iu],np.longdouble),dtype=np.longdouble))
def build_orbits(perms,n):
    unseen=set(range(n));out=[]
    while unseen:
        i=min(unseen);orb=sorted(set(int(p[i]) for p in perms));out.append(orb);unseen-=set(orb)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('xyz');ap.add_argument('few_shots');ap.add_argument('--core-distance',type=int,default=2)
    ap.add_argument('--screen',type=int,default=18);ap.add_argument('--relax',type=int,default=10);ap.add_argument('--seed',type=int,default=97212);ap.add_argument('--out',required=True);args=ap.parse_args()
    x=load_xyz(args.xyz)
    if len(x)!=972:raise ValueError(f'expected 972, got {len(x)}')
    s2,n2=recover_axis(x,PI,args.seed);s3,n3=recover_axis(x,2*PI/3,args.seed+1)
    R2=rot_axis(n2,PI);R3=rot_axis(n3,2*PI/3);G=group_closure([R2,R3])
    # If an arbitrary recovered C2/C3 pair generated too large a group due to a
    # mismatched numerical axis, try the inverse C3 sense before failing.
    if len(G)!=12:
        G=group_closure([R2,rot_axis(n3,-2*PI/3)])
    if len(G)!=12:raise RuntimeError(f'expected proper T group order 12, got {len(G)}')
    perms,worst=validate_group(x,G);orbits=build_orbits(perms,len(x));nb,edges,z=graph(x);dist=core_distance(nb,z)
    parent_e77,parent_coord=e77_count(x);live,_=sb.find_live(pathlib.Path(args.few_shots))
    print(f'axes scores C2={s2:.3e} C3={s3:.3e} dot={float(n2@n3):+.6g} group={len(G)} worst={worst:.3e} orbits={[len(o) for o in orbits[:12]]}... parent_e77={parent_e77} coord={parent_coord}',flush=True)
    cand=[]
    for oi,o in enumerate(orbits):
        if len(o)!=12:continue
        mind=int(np.min(dist[o]));all6=bool(np.all(z[o]==6))
        if not all6 or mind<args.core_distance:continue
        y=np.delete(x,np.asarray(o,int),axis=0);e=raw_energy(y);pre_e77,pre_coord=e77_count(y)
        cand.append({'orbit_index':oi,'orbit':o,'min_core_distance':mind,'raw_energy':e,'pre_relax_e77':pre_e77,'pre_relax_coord':pre_coord})
    cand.sort(key=lambda q:q['raw_energy']);print(f'eligible_12_orbits={len(cand)}',flush=True)
    rows=[];best=None
    for rank,c in enumerate(cand[:args.screen]):
        print(f'SCREEN rank={rank} orbit={c["orbit_index"]} raw={c["raw_energy"]:.9f} core={c["min_core_distance"]} e77={c["pre_relax_e77"]}',flush=True)
        if rank>=args.relax:continue
        y=np.delete(x,np.asarray(c['orbit'],int),axis=0);E,q,nit,ok=sb.stable_relax(y,1800);ne77,coord=e77_count(q)
        row={**c,'rank':rank,'relaxed_energy':E,'delta_vs_live':E-live,'post_relax_e77':ne77,'post_relax_coord':coord,'nit':nit,'success':ok}
        rows.append(row);print(f'RELAX rank={rank} E={E:.12f} dlive={E-live:+.9g} e77={ne77} coord={coord} nit={nit} ok={ok}',flush=True)
        if best is None or E<best[0]:best=(E,q,row)
    if best is None:raise RuntimeError('no eligible orbit relaxed')
    E,q,brow=best;out={'live_score':live,'axis2':n2.tolist(),'axis3':n3.tolist(),'axis2_score':s2,'axis3_score':s3,'group_order':len(G),'group_validation_max':worst,'parent_e77':parent_e77,'parent_coord':parent_coord,'orbit_size_hist':{str(k):sum(1 for o in orbits if len(o)==k) for k in sorted(set(map(len,orbits)))},'eligible_orbits':cand,'relaxed_rows':rows,'best_float_energy':E,'best_delta_vs_live':E-live,'best_row':brow,'best_points':q.tolist() if E<live-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
