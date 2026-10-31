#!/usr/bin/env python3
"""Edge-track the fixed-occupancy A/H sheets of the N961 auxiliary landscape.

At q886=q960=q380=2/3 (all other charges one, total charge exactly 960),
continuations from the A960 and H380 deletion vertices reach distinct weighted
local minima.  This script treats those two minima as endpoints of a genuine
fixed-parameter bistable landscape:

1. rigidly align labelled A/H center geometries;
2. find a great-circle interpolation interval whose independently weighted-
   relaxed endpoints fall into different A/H sheets;
3. bisect that geometric basin boundary using full weighted relaxation;
4. start from the boundary interpolation and run small-step Riemannian weighted
   gradient descent, which shadows the stable manifold of an intervening edge
   state before roundoff eventually selects one basin;
5. save the minimum-gradient geometry and project it to ordinary unit-charge
   N=960 by deleting each distinguished label.

This mirrors the successful fixed-N edge-tracking method used elsewhere in the
topic, but the objective here is the enlarged constant-total fractional-charge
landscape rather than the ordinary Thomson objective.
"""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np

import search_size_beam as sbeam
from search_n972_mobile_fractional_homotopy import stable_weighted_relax
from search_n961_occupancy_exchange import sig_json
from search_n961_three_occupancy_simplex import LABELS,classify
from search_n961_simplex_sheet_crossing import kabsch_align,sphere_interp


def weighted_cart_energy_grad(x: np.ndarray, q: np.ndarray):
    dots=np.clip(x@x.T,-1.0,1.0)
    r2=np.maximum(2.0-2.0*dots,1e-300)
    np.fill_diagonal(r2,np.inf)
    inv=1.0/np.sqrt(r2)
    qq=np.multiply.outer(q,q)
    W=qq*inv/r2
    np.fill_diagonal(W,0.0)
    E=float(np.sum(np.triu(qq*inv,1)))
    g=W@x-np.sum(W,axis=1)[:,None]*x
    return E,g


def capped_descent(x,g,eta,max_step):
    step=-eta*g
    # g is already tangent up to roundoff.
    step-=np.sum(step*x,axis=1)[:,None]*x
    n=np.linalg.norm(step,axis=1)
    scale=np.ones_like(n); mask=n>max_step; scale[mask]=max_step/n[mask]
    step*=scale[:,None]
    a=np.linalg.norm(step,axis=1)
    y=np.empty_like(x)
    small=a<1e-14
    y[small]=x[small]
    y[~small]=np.cos(a[~small])[:,None]*x[~small] + np.sin(a[~small])[:,None]*(step[~small]/a[~small,None])
    y/=np.linalg.norm(y,axis=1)[:,None]
    return y


def project_n960(x,di,live,maxiter):
    e,y,nit,ok=sbeam.stable_relax(np.delete(x,int(di),axis=0),maxiter)
    return {'delete_index':int(di),'energy':float(e),'delta_live':float(e-live),
            'class':classify(e,live),'signature':sig_json(y),'nit':int(nit),'success':bool(ok)}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('a_result'); ap.add_argument('h_result')
    ap.add_argument('--coarse',type=int,default=12); ap.add_argument('--bisect',type=int,default=22)
    ap.add_argument('--relax-maxiter',type=int,default=2400); ap.add_argument('--flow-steps',type=int,default=7000)
    ap.add_argument('--eta',type=float,default=.00035); ap.add_argument('--max-step',type=float,default=.00010)
    ap.add_argument('--project-maxiter',type=int,default=3800); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    da=json.load(open(args.a_result)); dh=json.load(open(args.h_result))
    xa=np.asarray(da['center_points'],float); xh=np.asarray(dh['center_points'],float)
    xh,align_rms,align_max=kabsch_align(xa,xh)
    ea=float(da['center_weighted_energy']); eh=float(dh['center_weighted_energy'])
    q=np.ones(961,float); q[list(LABELS)]=2/3
    if abs(float(np.sum(q))-960)>1e-10: raise RuntimeError(np.sum(q))

    def relax_class(t):
        x0=sphere_interp(xa,xh,float(t))
        e,x,nit,ok,msg,grms=stable_weighted_relax(x0,q,args.relax_maxiter)
        lab='A-sheet' if abs(e-ea)<abs(e-eh) else 'H-sheet'
        return lab,float(e),x,int(nit),bool(ok),float(grms)

    coarse=[]
    prev=None; bracket=None
    for t in np.linspace(0,1,args.coarse+1):
        lab,e,x,nit,ok,gr=relax_class(float(t)); coarse.append({'t':float(t),'class':lab,'energy':e,'grms':gr,'nit':nit,'success':ok})
        print('COARSE',f'{t:.8f}',lab,f'{e:.12f}',f'grms={gr:.3g}',flush=True)
        if prev is not None and prev[1]!=lab and bracket is None: bracket=(prev[0],float(t),prev[1],lab)
        prev=(float(t),lab)
    if bracket is None: raise RuntimeError('no A/H basin switch on aligned interpolation')
    lo,hi,llo,lhi=bracket
    bisection=[]
    for it in range(args.bisect):
        mid=.5*(lo+hi); lab,e,x,nit,ok,gr=relax_class(mid)
        bisection.append({'iteration':it,'t':mid,'class':lab,'energy':e,'grms':gr,'nit':nit,'success':ok})
        print('BISECT',it,f'{mid:.12f}',lab,f'{e:.12f}',flush=True)
        if lab==llo: lo=mid
        else: hi=mid
    tb=.5*(lo+hi); x=sphere_interp(xa,xh,tb)

    best={'gradient_rms':1e300}; flow=[]; rising=0
    for it in range(args.flow_steps+1):
        E,g=weighted_cart_energy_grad(x,q)
        gr=float(np.sqrt(np.mean(np.sum(g*g,axis=1))))
        if gr<best['gradient_rms']:
            best={'iteration':it,'weighted_energy':float(E),'gradient_rms':gr,'points':x.copy()}; rising=0
        elif best['gradient_rms']<2e-3 and gr>best['gradient_rms']*4: rising+=1
        if it%25==0 or it==args.flow_steps:
            print('FLOW',it,f'E={E:.12f}',f'grad={gr:.7g}',f"best={best['gradient_rms']:.7g}@{best['iteration']}",flush=True)
            flow.append({'iteration':it,'weighted_energy':float(E),'gradient_rms':gr,'best_gradient_rms':best['gradient_rms']})
        if rising>=20:
            print('STOP clear departure from edge state',flush=True); break
        if it==args.flow_steps: break
        x=capped_descent(x,g,args.eta,args.max_step)

    bx=best.pop('points')
    projections=[]
    for di in LABELS:
        p=project_n960(bx,di,args.live_score,args.project_maxiter); projections.append(p)
        print('PROJECT',di,p['class'],f"{p['energy']:.12f}",f"d={p['delta_live']:+.9g}",flush=True)
    bestp=min(projections,key=lambda z:z['energy'])
    out={'live_score':float(args.live_score),'center_A_energy':ea,'center_H_energy':eh,
         'alignment_rms':align_rms,'alignment_max':align_max,'coarse':coarse,
         'boundary_bracket':[lo,hi],'boundary_t':tb,'bisection':bisection,'flow':flow,'best':best,
         'edge_points':bx.tolist(),'projections':projections,'best_projection':bestp}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if bestp['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH.json').write_text(json.dumps(bestp,separators=(',',':'))+'\n')

if __name__=='__main__': main()
