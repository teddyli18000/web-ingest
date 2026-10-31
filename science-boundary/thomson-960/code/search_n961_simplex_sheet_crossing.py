#!/usr/bin/env python3
"""Probe the fixed-occupancy geometric boundary between N961 simplex sheets.

Inputs are result.json files from the constant-total three-occupancy continuation
at the common center q886=q960=q380=2/3.  The R886 and A960 branches merge onto
the same A-like weighted minimum at the center, while the H380 branch remains a
distinct weighted minimum.  This script rigidly aligns labelled center states,
constructs per-particle great-circle interpolants at fixed charges, independently
relaxes each interpolated start under the same weighted objective, and projects
each relaxed state to genuine unit-charge N=960 by deleting 886, 960, or 380.

The purpose is to locate the A-sheet/H-sheet basin boundary at fixed auxiliary
parameters and check whether interpolation exposes any third weighted sheet or
new N960 projection.  It is not a continuation in occupancy space.
"""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np

import search_size_beam as sbeam
from search_n972_mobile_fractional_homotopy import stable_weighted_relax
from search_n961_occupancy_exchange import sig_json
from search_n961_three_occupancy_simplex import classify, LABELS


def kabsch_align(ref: np.ndarray, x: np.ndarray):
    H=x.T@ref
    U,_,Vt=np.linalg.svd(H)
    R=U@Vt
    if np.linalg.det(R)<0:
        U[:,-1]*=-1.0; R=U@Vt
    y=x@R
    d=np.linalg.norm(y-ref,axis=1)
    return y,float(np.sqrt(np.mean(d*d))),float(np.max(d))


def sphere_interp(a: np.ndarray, b: np.ndarray, t: float):
    c=np.clip(np.sum(a*b,axis=1),-1.0,1.0)
    ang=np.arccos(c)
    s=np.sin(ang)
    out=np.empty_like(a)
    good=s>1e-10
    out[good]=(np.sin((1-t)*ang[good])/s[good])[:,None]*a[good] + (np.sin(t*ang[good])/s[good])[:,None]*b[good]
    out[~good]=(1-t)*a[~good]+t*b[~good]
    out/=np.linalg.norm(out,axis=1)[:,None]
    return out


def project(x,di,live,maxiter):
    e,y,nit,ok=sbeam.stable_relax(np.delete(x,int(di),axis=0),maxiter)
    return {'delete_index':int(di),'energy':float(e),'delta_live':float(e-live),
            'class':classify(e,live),'signature':sig_json(y),'nit':int(nit),'success':bool(ok)}


def classify_weighted(e,ea,eh,tol=2e-5):
    da=abs(float(e)-float(ea)); dh=abs(float(e)-float(eh))
    if da<tol and da<dh: return 'A-sheet'
    if dh<tol and dh<da: return 'H-sheet'
    return 'other-sheet'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('a_result'); ap.add_argument('h_result')
    ap.add_argument('--ts',default='0,.08,.16,.24,.32,.4,.46,.48,.5,.52,.54,.6,.68,.76,.84,.92,1')
    ap.add_argument('--weighted-maxiter',type=int,default=2600)
    ap.add_argument('--project-maxiter',type=int,default=3800)
    ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    da=json.load(open(args.a_result)); dh=json.load(open(args.h_result))
    xa=np.asarray(da['center_points'],float); xh=np.asarray(dh['center_points'],float)
    if xa.shape!=(961,3) or xh.shape!=(961,3): raise ValueError((xa.shape,xh.shape))
    xh,align_rms,align_max=kabsch_align(xa,xh)
    qa=np.ones(961,float); qa[list(LABELS)]=2/3
    if abs(np.sum(qa)-960)>1e-10: raise RuntimeError(np.sum(qa))
    ea=float(da['center_weighted_energy']); eh=float(dh['center_weighted_energy'])
    ts=[float(z) for z in args.ts.split(',') if z.strip()]
    rows=[]
    for t in ts:
        x0=sphere_interp(xa,xh,t)
        ew,x,nit,ok,msg,grms=stable_weighted_relax(x0,qa,args.weighted_maxiter)
        pa=[]
        for di in LABELS: pa.append(project(x,di,args.live_score,args.project_maxiter))
        wr=classify_weighted(ew,ea,eh)
        rr={'t':t,'weighted_energy':float(ew),'weighted_class':wr,'weighted_grms':float(grms),
            'weighted_nit':int(nit),'weighted_success':bool(ok),'weighted_message':str(msg),
            'projections':pa}
        rows.append(rr)
        print('T',t,wr,f'Ew={ew:.12f}',f'grms={grms:.3g}',
              'P',[(p['delete_index'],p['class'],round(p['delta_live'],9)) for p in pa],flush=True)
    # detect adjacent class switches along interpolation parameter
    switches=[]
    for a,b in zip(rows,rows[1:]):
        if a['weighted_class']!=b['weighted_class']:
            switches.append({'lo_t':a['t'],'lo_class':a['weighted_class'],'hi_t':b['t'],'hi_class':b['weighted_class']})
    best=min((p for r in rows for p in r['projections']),key=lambda p:p['energy'])
    out={'live_score':float(args.live_score),'center_A_energy':ea,'center_H_energy':eh,
         'center_energy_gap_H_minus_A':eh-ea,'center_alignment_rms':align_rms,'center_alignment_max':align_max,
         'ts':ts,'rows':rows,'switches':switches,'best_projection':best}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH.json').write_text(json.dumps(best,separators=(',',':'))+'\n')

if __name__=='__main__': main()
