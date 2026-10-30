#!/usr/bin/env python3
"""Compose C3-equivalent nonlinear e564 -> e553 rearrangement events."""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree
import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed, stable_relax_q
TWOPI=2*math.pi

def rz(x,a):
    c,s=math.cos(a),math.sin(a); R=np.array([[c,-s,0.0],[s,c,0.0],[0.0,0.0,1.0]])
    return x@R.T,R

def kabsch(P,Q):
    U,S,Vt=np.linalg.svd(P.T@Q); R=U@Vt
    if np.linalg.det(R)<0: U[:,-1]*=-1; R=U@Vt
    return R

def sphere_log(x,y):
    dot=np.clip(np.sum(x*y,axis=1),-1.0,1.0); a=np.arccos(dot)
    t=y-dot[:,None]*x; n=np.linalg.norm(t,axis=1); out=np.zeros_like(x); ok=n>1e-14
    out[ok]=t[ok]*(a[ok]/n[ok])[:,None]; return out

def sphere_exp(x,v):
    a=np.linalg.norm(v,axis=1); y=np.empty_like(x); small=a<1e-14; y[small]=x[small]; ok=~small
    y[ok]=np.cos(a[ok])[:,None]*x[ok]+np.sin(a[ok])[:,None]*(v[ok]/a[ok,None])
    y/=np.linalg.norm(y,axis=1)[:,None]; return y

def c3_perm(x,a):
    xr,R=rz(x,a); tree=cKDTree(x); dist,idx=tree.query(xr)
    if len(set(map(int,idx)))!=len(x) or float(np.max(dist))>1e-6:
        cost=np.maximum(0.0,2-2*np.clip(xr@x.T,-1,1)); rows,cols=linear_sum_assignment(cost)
        assert np.array_equal(rows,np.arange(len(x))); idx=cols; dist=np.sqrt(cost[rows,cols])
    if float(np.max(dist))>1e-5: raise RuntimeError(f'C3 mapping error {np.max(dist)}')
    return np.asarray(idx,dtype=int),R,float(np.sqrt(np.mean(dist*dist))),float(np.max(dist))

def rotate_event(v,perm,R):
    out=np.zeros_like(v); out[perm]=v@R.T; return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('e564_json'); ap.add_argument('e553_json')
    ap.add_argument('--coeffs',required=True); ap.add_argument('--scales',default='0.6,0.8,1.0,1.2,1.5')
    ap.add_argument('--maxiter',type=int,default=2400); ap.add_argument('--out',required=True); args=ap.parse_args()
    m0,x0=load_seed(args.e564_json); m1,x1=load_seed(args.e553_json)
    Rfit=kabsch(x1,x0); x1a=x1@Rfit; base=sphere_log(x0,x1a)
    rms=float(np.sqrt(np.mean(np.sum(base*base,axis=1)))); mx=float(np.max(np.linalg.norm(base,axis=1)))
    p1,R1,r1,m1err=c3_perm(x0,TWOPI/3); p2,R2,r2,m2err=c3_perm(x0,2*TWOPI/3)
    events=[base,rotate_event(base,p1,R1),rotate_event(base,p2,R2)]
    coeff=np.array([float(s) for s in args.coeffs.split(',')],dtype=float)
    if len(coeff)!=3: raise ValueError('need 3 coeffs')
    scales=[float(s) for s in args.scales.split(',') if s]; combo=sum(c*v for c,v in zip(coeff,events))
    crms=float(np.sqrt(np.mean(np.sum(combo*combo,axis=1))))
    print(f'event_rms={rms:.7g} max={mx:.7g} maps={r1:.3g}/{r2:.3g} coeff={coeff.tolist()} combo_rms={crms:.7g}',flush=True)
    rows=[]; basins=[]
    for s in scales:
        start=sphere_exp(x0,s*combo); qs=sm.xyz_to_vars(start); Es,_=sm.fg(qs)
        e,raw,z,nit,ok,msg=stable_relax_q(qs,maxiter=args.maxiter)
        row={'scale':s,'start_energy':Es,'energy':e,'raw_energy':raw,'nit':nit,'success':ok,'message':msg}; rows.append(row)
        print(f's={s:.3g} start={Es:.9f} E={e:.12f}',flush=True)
        if not any(abs(e-b['energy'])<2e-6 for b in basins):
            b=dict(row); b['points']=z.tolist(); basins.append(b); basins.sort(key=lambda z:z['energy']); basins=basins[:10]
    out={'e564_energy':float(m0.get('energy',m0.get('full_energy',float('nan')))),'e553_energy':float(m1.get('energy',m1.get('release_energy',float('nan')))),
         'coeffs':coeff.tolist(),'scales':scales,'single_event_rms':rms,'single_event_max':mx,
         'c3_map_rms':[r1,r2],'c3_map_max':[m1err,m2err],'combo_rms':crms,
         'rows':rows,'lowest_distinct_basins':basins,'best_energy':min(r['energy'] for r in rows)}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
if __name__=='__main__': main()
