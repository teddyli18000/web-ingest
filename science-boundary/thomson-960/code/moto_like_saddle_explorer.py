#!/usr/bin/env python3
"""MOTO-inspired local saddle explorer for Thomson N=960.

This is intentionally not another relax-random-kicks search.  It targets diverse
transition states around a known minimum, following the 2026 MOTO principles:

  * generate diverse feasible tangent perturbations,
  * estimate the two lowest physical-tangent curvatures by HVP/eigsh,
  * prefer large minimum-mode spectral gaps and index-1-like starts,
  * minimum-mode-follow selected starts toward first-order saddles,
  * descend both sides of the final negative mode to certify connectivity.

The implementation reuses the sphere-manifold/HVP machinery already validated in
this topic.  Candidate generation uses random combinations of the seed's first
`basis_k` internal modes, so the search changes from individual eigenvector scans
to a screened population in their nonlinear span.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import stable_relax_q
from refine_saddle_eigenfollow import lowest_modes, step_eigenfollow

N=960


def load_seed(root:pathlib.Path, seed_json:str|None):
    if seed_json:
        d=json.loads(pathlib.Path(seed_json).read_text())
        pts=d.get('points') or d.get('saddle_points')
        if pts is None: raise ValueError('seed JSON needs points')
        x=np.asarray(pts,float); x/=np.linalg.norm(x,axis=1)[:,None]
        return x, {'source':seed_json}
    score,shot=sm.find_live(root)
    x=sm.load_cert(shot/'certificate.json')
    return x, {'source':str(shot.relative_to(root)),'live_score':score}


def seed_modes(q,k,fd=3e-6):
    H,raw,Qrot,calls=sm.build_hessian(q,fd,1e6)
    vals,V=eigsh(H,k=k,which='SA',tol=2e-5,maxiter=900,ncv=max(48,4*k))
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    # Remove any tiny rotation contamination.
    for j in range(V.shape[1]):
        V[:,j]-=Qrot@(Qrot.T@V[:,j]); V[:,j]/=np.linalg.norm(V[:,j])
    return vals,V,Qrot,calls['n']


def min_pair_distance(x):
    d=x@x.T
    np.fill_diagonal(d,-2.0)
    return float(np.sqrt(max(0.0,2.0-2.0*np.max(d))))


def curvature2(q,seed):
    H,raw,Qrot,calls=sm.build_hessian(q,3e-6,1e6)
    rng=np.random.default_rng(seed)
    v0=rng.normal(size=len(q)); v0-=Qrot@(Qrot.T@v0)
    vals,V=eigsh(H,k=3,which='SA',tol=4e-5,maxiter=650,ncv=32,v0=v0)
    vals=np.sort(vals)
    return [float(v) for v in vals], calls['n']


def choose_population(rows,count):
    # First prioritize clean index-1 starts with a large lambda2-lambda1 gap.
    # Then fill by maximin diversity among coefficient vectors, with gap as tie-break.
    eligible=[r for r in rows if r['feasible']]
    if not eligible: return []
    eligible.sort(key=lambda r:(
        0 if (r['lambdas'][0] < -0.05 and r['lambdas'][1] > 0.05) else 1,
        -r['spectral_gap'], r['start_energy']))
    selected=[]
    pool=eligible.copy()
    while pool and len(selected)<count:
        if not selected:
            pick=pool[0]
        else:
            for r in pool:
                c=np.asarray(r['coefficients'])
                r['_div']=min(float(np.linalg.norm(c-np.asarray(s['coefficients']))) for s in selected)
                r['_utility']=r['_div']*(1.0+0.05*max(r['spectral_gap'],0.0))
            pick=max(pool,key=lambda r:r['_utility'])
        selected.append(pick); pool.remove(pick)
    for r in selected:
        r.pop('_div',None); r.pop('_utility',None)
    return selected


def mmf(q,cycles,steps,eta,max_rms):
    hist=[]; total_h=0; prev=None
    for cyc in range(cycles):
        vals,V,rows,h=lowest_modes(q,4,3e-6,1e6,4e-5); total_h+=h
        mode=V[:,0].copy()
        if prev is not None and float(mode@prev)<0: mode=-mode
        prev=mode.copy()
        last=None
        for _ in range(steps):
            q,E,grms,srms,gpar=step_eigenfollow(q,mode,eta,max_rms)
            last=(E,grms,gpar)
        hist.append({'cycle':cyc,'lambdas':[float(v) for v in vals],
                     'end_energy':last[0],'end_grad_rms':last[1],
                     'end_gradient_parallel':last[2]})
    vals,V,rows,h=lowest_modes(q,8,3e-6,1e6,2e-5); total_h+=h
    E,gq=sm.fg(q); gp=gq/sm.physical_scale(q)
    grms=float(np.linalg.norm(gp)/math.sqrt(2*N))
    return q,float(E),grms,vals,V,rows,hist,total_h


def certify(root,q,V,live_score,amp):
    out=[]
    mode=V[:,0].copy(); mode/=np.linalg.norm(mode)
    for sign in (-1,1):
        qs=sp.exp_perturb(q,mode*sign,amp)
        e,raw,x,nit,ok,msg=stable_relax_q(qs,2200)
        out.append({'sign':sign,'energy':e,'delta_vs_live':e-live_score,
                    'nit':nit,'success':ok,'points':x.tolist()})
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots')
    ap.add_argument('--seed-json')
    ap.add_argument('--seed',type=int,default=20261028)
    ap.add_argument('--population',type=int,default=8)
    ap.add_argument('--select',type=int,default=2)
    ap.add_argument('--basis-k',type=int,default=12)
    ap.add_argument('--scales',default='0.006,0.010,0.016,0.024')
    ap.add_argument('--mmf-cycles',type=int,default=6)
    ap.add_argument('--mmf-steps',type=int,default=55)
    ap.add_argument('--mmf-eta',type=float,default=0.00025)
    ap.add_argument('--mmf-max-rms',type=float,default=0.000012)
    ap.add_argument('--certify-amp',type=float,default=0.002)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    root=pathlib.Path(args.few_shots)
    live_score,live_shot=sm.find_live(root)
    x0,meta=load_seed(root,args.seed_json); q0=sm.xyz_to_vars(x0)
    e0,_=sm.fg(q0); dmin0=min_pair_distance(x0)
    vals0,V0,Qrot,h0=seed_modes(q0,args.basis_k)
    rng=np.random.default_rng(args.seed)
    scales=[float(v) for v in args.scales.split(',') if v]
    rows=[]
    print(f'seed={meta["source"]} E={e0:.12f} dmin={dmin0:.6g} basis={vals0[:6].tolist()}',flush=True)

    for i in range(args.population):
        c=rng.normal(size=args.basis_k)
        # Encourage genuinely mixed directions; normalize coefficients then vary scale.
        c/=np.linalg.norm(c)
        scale=scales[i%len(scales)]*math.exp(float(rng.normal(0.0,0.12)))
        direction=V0@c; direction-=Qrot@(Qrot.T@direction); direction/=np.linalg.norm(direction)
        qs=sp.exp_perturb(q0,direction,scale)
        xs=sm.vars_to_xyz(qs)[0]; es,_=sm.fg(qs); dmin=min_pair_distance(xs)
        lams,h=curvature2(qs,args.seed+1000+i)
        gap=lams[1]-lams[0]
        feasible=dmin > 0.72*dmin0
        row={'candidate':i,'scale':scale,'start_energy':float(es),
             'delta_seed':float(es-e0),'min_pair_distance':dmin,
             'feasible':bool(feasible),'lambdas':lams,'spectral_gap':float(gap),
             'coefficients':c.tolist(),'points':xs.tolist(),'hessian_gradient_calls':h}
        rows.append(row)
        print(f'cand={i} scale={scale:.5g} dE={es-e0:+.6g} dmin={dmin:.5g} '
              f'lambda={lams[:2]} gap={gap:.5g} feasible={feasible}',flush=True)

    selected=choose_population(rows,args.select)
    results=[]
    for rank,r in enumerate(selected):
        q=sm.xyz_to_vars(np.asarray(r['points'],float))
        q,E,grms,vals,V,mrows,hist,hcalls=mmf(q,args.mmf_cycles,args.mmf_steps,args.mmf_eta,args.mmf_max_rms)
        neg=int(np.sum(vals < -1e-3))
        print(f'selected={r["candidate"]} rank={rank} MMF E={E:.12f} grad={grms:.5g} '
              f'neg={neg} lambdas={[float(v) for v in vals[:4]]}',flush=True)
        cert=[]
        if neg==1:
            cert=certify(root,q,V,live_score,args.certify_amp)
            print('  endpoints='+','.join(f'{z["energy"]:.12f}' for z in cert),flush=True)
        results.append({'selected_candidate':r['candidate'],'start':{k:v for k,v in r.items() if k!='points'},
                        'saddle_energy':E,'saddle_gradient_rms':grms,
                        'negative_modes':neg,'final_modes':mrows,'mmf_history':hist,
                        'hessian_gradient_calls':hcalls,'saddle_points':sm.vars_to_xyz(q)[0].tolist(),
                        'certified_endpoints':cert})

    best=min((z['energy'] for r in results for z in r['certified_endpoints']),default=1e300)
    out={'seed':args.seed,'source':meta,'live_score':live_score,
         'live_shot':str(live_shot.relative_to(root)),'seed_energy':e0,
         'seed_min_pair_distance':dmin0,'seed_basis_eigenvalues':[float(v) for v in vals0],
         'screen':[ {k:v for k,v in r.items() if k!='points'} for r in rows],
         'selected_ids':[r['candidate'] for r in selected],'results':results,
         'best_certified_endpoint_energy':best,
         'best_delta_vs_live':best-live_score if best<1e299 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
