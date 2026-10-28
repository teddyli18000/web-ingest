#!/usr/bin/env python3
"""Map the unstable manifold of a C3-symmetric index-2 Thomson stationary point.

The lowest Hessian pair is canonicalized under the +120 degree C3 action, then
a full 120-degree oriented phase fundamental domain is sampled.  Do not reduce
to 60 degrees unless an independent reflection symmetry has been established:
C3 alone identifies theta modulo 120 degrees, while theta and theta+180 degrees
can differ already through cubic invariants. Each perturbed point is fully
relaxed without symmetry using the stable termwise pair-energy-difference
objective. Endpoints are clustered by energy and one representative geometry per
energy class is retained.

C is reconstructed by floating relaxation and is C3 only to a few 1e-7 in xyz.
For group mapping we therefore validate a one-to-one nearest-neighbor
permutation with a conservative 2e-6 tolerance, then explicitly report both the
point-map error and the eigenspace representation residual.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.sparse.linalg import eigsh
from scipy.spatial import ConvexHull, cKDTree

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import load_seed, stable_relax_q

N=960
PI=math.pi


def coord_counts(x):
    h=ConvexHull(x); nb=[set() for _ in range(N)]
    for t in h.simplices:
        a,b,c=map(int,t); nb[a].update((b,c)); nb[b].update((a,c)); nb[c].update((a,b))
    z=np.array([len(s) for s in nb]); return {str(k):int(np.sum(z==k)) for k in sorted(set(map(int,z)))}


def c3_mapping_near(q,tol=2e-6):
    x,_,_=sp.tangent_bases(q); xr,R=sp.rz(x,2*PI/3); tree=cKDTree(x)
    dist,dest=tree.query(xr,k=1); err=float(np.max(dist))
    if len(np.unique(dest))!=len(x): raise RuntimeError('C3 map is not a permutation')
    if err>tol: raise RuntimeError(f'C3 point mapping failed maxdist={err} tol={tol}')
    return dest,R,err


def canonicalize_pair_near(V,q):
    x,_,_=sp.tangent_bases(q); order=np.lexsort((x[:,2],x[:,1],x[:,0]))
    best=None
    for idx in order[:64]:
        for comp in (0,1):
            r=np.zeros(V.shape[0]); r[2*idx+comp]=1.0; p=V@(V.T@r); n=float(np.linalg.norm(p))
            key=(n,-int(idx),-comp)
            if best is None or key>best[0]: best=(key,p,r,int(idx),comp)
    _,p,r,anchor_idx,anchor_comp=best
    if np.linalg.norm(p)<1e-8: raise RuntimeError('deterministic anchor has negligible pair projection')
    v0=p/np.linalg.norm(p)
    if float(v0@r)<0: v0=-v0
    mapping=c3_mapping_near(q); Tv0=sp.transform_c3(v0,q,mapping)
    v1=Tv0+0.5*v0; v1-=v0*float(v0@v1); v1/=np.linalg.norm(v1)
    if float(Tv0@v1)<0: v1=-v1
    W=np.column_stack([v0,v1])
    TW=np.column_stack([sp.transform_c3(W[:,j],q,mapping) for j in range(2)])
    M=W.T@TW; resid=float(np.linalg.norm(TW-W@M))
    return W,M,resid,anchor_idx,anchor_comp,mapping[2]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots'); ap.add_argument('seed_json')
    ap.add_argument('--phases',default=','.join(str(v) for v in range(0,120,5)))
    ap.add_argument('--amps',default='0.0015,0.003,0.006,0.012')
    ap.add_argument('--fd-step',type=float,default=3e-6); ap.add_argument('--out',required=True); args=ap.parse_args()
    root=pathlib.Path(args.few_shots); live_score,live_shot=sm.find_live(root); seed_meta,x0=load_seed(pathlib.Path(args.seed_json))
    q0=sm.xyz_to_vars(x0); E0,g0=sm.fg(q0); H,raw,Q,calls=sm.build_hessian(q0,args.fd_step,1e6)
    rng=np.random.default_rng(9607001); v0=rng.normal(size=len(q0)); v0-=Q@(Q.T@v0); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=6,which='SA',tol=1e-5,maxiter=800,ncv=40,v0=v0); o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    pair=V[:,:2].copy(); pair-=Q@(Q.T@pair); pair,_=np.linalg.qr(pair)
    pair,M,resid,anchor_i,anchor_c,maperr=canonicalize_pair_near(pair,q0)
    if vals[1]>=-1e-3: raise RuntimeError(f'lowest pair is not unstable: {vals[:3]}')
    print(f'seedE={E0:.12f} live={live_score:.10f} lambdas={vals[0]:.9g},{vals[1]:.9g},{vals[2]:.9g}',flush=True)
    print(f'C3 pair M={M.tolist()} subspace_res={resid:.3e} maperr={maperr:.3e} anchor={anchor_i}/{anchor_c}',flush=True)
    phases=[float(s) for s in args.phases.split(',') if s]; amps=[float(s) for s in args.amps.split(',') if s]
    rows=[]; basins=[]
    for ph in phases:
        a=math.radians(ph); direction=math.cos(a)*pair[:,0]+math.sin(a)*pair[:,1]; direction/=np.linalg.norm(direction)
        for amp in amps:
            qs=sp.exp_perturb(q0,direction,amp); start,_=sm.fg(qs); E,rawE,x,nit,ok,msg=stable_relax_q(qs,2400)
            bid=None
            for i,b in enumerate(basins):
                if abs(E-b['energy'])<2e-7: bid=i; break
            if bid is None:
                bid=len(basins); basins.append({'energy':E,'delta_vs_live':E-live_score,'coord_counts':coord_counts(x),
                                                'hits':[],'representative_points':x.tolist()})
            basins[bid]['hits'].append({'phase_deg':ph,'amp':amp})
            rows.append({'phase_deg':ph,'amp':amp,'start_energy':start,'energy':E,'delta_vs_live':E-live_score,
                         'basin_id':bid,'nit':nit,'success':ok,'message':msg})
            print(f'phase={ph:5.1f} amp={amp:.4g} start={start:.9f} E={E:.12f} dlive={E-live_score:+.9g} basin={bid} nit={nit}',flush=True)
    basins.sort(key=lambda b:b['energy'])
    for rank,b in enumerate(basins): b['energy_rank']=rank
    best=min(b['energy'] for b in basins)
    print('BASINS',[(b['energy_rank'],b['energy'],b['delta_vs_live'],len(b['hits']),b['coord_counts']) for b in basins],flush=True)
    out={'seed_json':str(args.seed_json),'seed_energy':E0,'seed_gradient_rms':float(np.sqrt(np.mean((g0/sm.physical_scale(q0))**2))),
         'live_score':live_score,'live_shot':str(live_shot.relative_to(root)),'phase_domain_degrees':[min(phases),max(phases)],
         'eigenvalues':[float(v) for v in vals],'c3_pair_matrix':M.tolist(),'c3_subspace_residual':resid,'c3_mapping_max_error':maperr,
         'canonical_anchor_point':anchor_i,'canonical_anchor_component':anchor_c,'rows':rows,'basins':basins,
         'best_float_energy':best,'best_delta_vs_live':best-live_score,'gradient_calls_for_modes':calls['n']}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
