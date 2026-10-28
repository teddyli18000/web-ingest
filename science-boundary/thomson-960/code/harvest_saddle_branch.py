#!/usr/bin/env python3
"""Harvest one relaxed minimum from a chosen saddle transverse branch."""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.spatial import ConvexHull, cKDTree

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import stable_relax_q
from search_saddle_transverse import load_refined

N=960


def coord_counts(x):
    h=ConvexHull(x); nb=[set() for _ in range(N)]
    for t in h.simplices:
        a,b,c=map(int,t); nb[a].update((b,c)); nb[b].update((a,c)); nb[c].update((a,b))
    z=np.array([len(s) for s in nb])
    return {str(k):int(np.sum(z==k)) for k in sorted(set(map(int,z)))}


def c3_z_rms(x):
    a=2*math.pi/3; c,s=math.cos(a),math.sin(a)
    M=np.array([[c,-s,0.],[s,c,0.],[0.,0.,1.]])
    tree=cKDTree(x); d,_=tree.query(x@M.T,k=1)
    return float(np.sqrt(np.mean(d*d))),float(np.max(d))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots'); ap.add_argument('refined_json')
    ap.add_argument('--mode',type=int,required=True); ap.add_argument('--sign',type=int,choices=[-1,1],required=True)
    ap.add_argument('--transverse-amp',type=float,required=True); ap.add_argument('--reaction-amp',type=float,default=0.0)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    root=pathlib.Path(args.few_shots); live_score,live_shot=sm.find_live(root)
    meta,x0,vecs,modes=load_refined(args.refined_json); q0=sm.xyz_to_vars(x0)
    Q=sm.rotation_basis(q0); reaction=vecs[:,0].copy(); transverse=vecs[:,args.mode].copy()
    reaction-=Q@(Q.T@reaction); transverse-=Q@(Q.T@transverse)
    reaction/=np.linalg.norm(reaction); transverse/=np.linalg.norm(transverse)
    transverse-=reaction*float(reaction@transverse); transverse/=np.linalg.norm(transverse); transverse*=args.sign
    y=np.sqrt(float(N))*(args.transverse_amp*transverse+args.reaction_amp*reaction)
    rms=float(np.linalg.norm(y)/math.sqrt(N)); qs=sp.exp_perturb(q0,y/np.linalg.norm(y),rms)
    start,_=sm.fg(qs); E,raw,x,nit,ok,msg=stable_relax_q(qs,2600)
    cc=coord_counts(x); crms,cmax=c3_z_rms(x)
    print(f'E={E:.12f} dlive={E-live_score:+.12g} start={start:.9f} nit={nit} ok={ok} coord={cc} c3z_rms={crms:.6g}',flush=True)
    out={'live_score':live_score,'live_shot':str(live_shot.relative_to(root)),'refined_json':str(args.refined_json),
         'saddle_energy':meta.get('final_energy'),'mode':args.mode,'eigenvalue':modes[args.mode]['eigenvalue'],'sign':args.sign,
         'transverse_amp':args.transverse_amp,'reaction_amp':args.reaction_amp,'start_energy':start,'energy':E,
         'raw_absolute_energy':raw,'delta_vs_live':E-live_score,'nit':nit,'success':ok,'message':msg,
         'coord_counts':cc,'c3_z_rms':crms,'c3_z_max':cmax,'points':x.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
