#!/usr/bin/env python3
"""Minimum-energy string between the A/H weighted N=961 simplex sheets.

The charges are fixed at q886=q960=q380=2/3 and one elsewhere, so total
charge is exactly 960.  The two endpoint geometries are distinct local minima
of the same weighted objective at identical auxiliary parameters.  We align
the labelled H endpoint onto A, evolve a geodesic string by the gradient
component perpendicular to the path, then apply a bounded climbing-image
refinement.  The output is a transition-state seed, not a record candidate.
"""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np

import string_record_neighbor as sr
from edge_track_n961_simplex_sheets import weighted_cart_energy_grad
from search_n961_simplex_sheet_crossing import kabsch_align
from search_n961_three_occupancy_simplex import LABELS


def load_center(path):
    d=json.loads(pathlib.Path(path).read_text())
    x=np.asarray(d['center_points'],float)
    x/=np.linalg.norm(x,axis=1)[:,None]
    return d,x


def diagnostics(images,charges):
    es=[]; gs=[]; perps=[]
    for x in images:
        e,g=weighted_cart_energy_grad(x,charges); es.append(float(e)); gs.append(g)
    for i in range(1,len(images)-1):
        tau=sr.path_tangent(images,i)
        gp=gs[i]-float(np.sum(gs[i]*tau))*tau
        perps.append(float(np.sqrt(np.mean(np.sum(gp*gp,axis=1)))))
    return es,gs,perps


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('a_result'); ap.add_argument('h_result')
    ap.add_argument('--images',type=int,default=11); ap.add_argument('--iterations',type=int,default=260)
    ap.add_argument('--eta',type=float,default=2.5e-4); ap.add_argument('--max-step',type=float,default=1.2e-4)
    ap.add_argument('--climb-iterations',type=int,default=180); ap.add_argument('--out',required=True)
    args=ap.parse_args()
    da,A=load_center(args.a_result); dh,H=load_center(args.h_result)
    if A.shape!=(961,3) or H.shape!=(961,3): raise ValueError((A.shape,H.shape))
    H,align_rms,align_max=kabsch_align(A,H)
    charges=np.ones(961,float); charges[list(LABELS)]=2/3
    if abs(float(np.sum(charges))-960)>1e-10: raise RuntimeError(np.sum(charges))

    images=sr.interpolate_endpoints(A,H,args.images); hist=[]
    for it in range(args.iterations):
        es,gs,perps=diagnostics(images,charges); new=[images[0]]; maxstep=0.0
        for i in range(1,len(images)-1):
            tau=sr.path_tangent(images,i)
            gp=gs[i]-float(np.sum(gs[i]*tau))*tau
            y,s=sr.capped_descent(images[i],gp,args.eta,args.max_step)
            new.append(y); maxstep=max(maxstep,float(s))
        new.append(images[-1]); images,arc=sr.reparameterize(new)
        if it%10==0 or it==args.iterations-1:
            e2,_,p2=diagnostics(images,charges); imax=int(np.argmax(e2)); maxp=max(p2) if p2 else 0.0
            print('STRING',it,'maxE',f'{max(e2):.12f}','imax',imax,'arc',f'{arc:.7g}',
                  'step',f'{maxstep:.3e}','perp',f'{maxp:.7g}',flush=True)
            hist.append({'iteration':it,'energies':e2,'max_index':imax,'arc':float(arc),
                         'max_step':maxstep,'max_perpendicular_gradient_rms':maxp})

    es,_,perps=diagnostics(images,charges); imax=int(np.argmax(es))
    if imax in (0,len(images)-1): raise RuntimeError(f'string maximum collapsed to endpoint {imax}')
    saddle=images[imax].copy(); climb=[]
    for it in range(args.climb_iterations):
        e,g=weighted_cart_energy_grad(saddle,charges)
        tmp=list(images); tmp[imax]=saddle; tau=sr.path_tangent(tmp,imax)
        saddle,s=sr.climb_step(saddle,g,tau,args.eta,args.max_step*0.7)
        gr=float(np.sqrt(np.mean(np.sum(g*g,axis=1))))
        gp=g-float(np.sum(g*tau))*tau; pr=float(np.sqrt(np.mean(np.sum(gp*gp,axis=1))))
        if it%10==0 or it==args.climb_iterations-1:
            print('CLIMB',it,'E',f'{e:.12f}','grad',f'{gr:.7g}','perp',f'{pr:.7g}','step',f'{s:.3e}',flush=True)
            climb.append({'iteration':it,'energy':float(e),'gradient_rms':gr,
                          'perpendicular_gradient_rms':pr,'step':float(s)})
    ef,gf=weighted_cart_energy_grad(saddle,charges)
    grf=float(np.sqrt(np.mean(np.sum(gf*gf,axis=1))))
    tmp=list(images); tmp[imax]=saddle; tau=sr.path_tangent(tmp,imax)
    gpf=gf-float(np.sum(gf*tau))*tau
    prf=float(np.sqrt(np.mean(np.sum(gpf*gpf,axis=1))))
    out={'charges_labels':list(LABELS),'fractional_charge':2/3,'total_charge':float(np.sum(charges)),
         'center_A_energy':float(da['center_weighted_energy']),'center_H_energy':float(dh['center_weighted_energy']),
         'alignment_rms':align_rms,'alignment_max':align_max,'images':args.images,'iterations':args.iterations,
         'history':hist,'path_energies':es,'path_perpendicular_gradient_rms':perps,'max_image_index':imax,
         'path_points':[x.tolist() for x in images],'climb_history':climb,'climbing_energy':float(ef),
         'climbing_gradient_rms':grf,'climbing_perpendicular_gradient_rms':prf,
         'saddle_points':saddle.tolist(),'edge_points':saddle.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
