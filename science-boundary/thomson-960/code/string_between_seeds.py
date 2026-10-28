#!/usr/bin/env python3
"""Spherical minimum-energy string between two frozen N=960 Thomson states.

Endpoints are JSON files containing a 960x3 `points` array with meaningful
pointwise correspondence. Interior images evolve only under the component of
the energy gradient perpendicular to the current path tangent, followed by
arc-length reparameterization. This is the string-method condition for a
minimum-energy path; monitoring raw step size alone is not a convergence
criterion.

A previous output can be continued with `--resume-json`; its saved `path_points`
are used directly, avoiding loss of thousands of relaxation iterations. The
final path, local tangent geometry, maximum perpendicular-gradient RMS and all
image coordinates are persisted. Endpoint collapse is recorded as data rather
than raised as an exception.
"""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np
import string_record_neighbor as sr


def load_seed(path):
    d=json.loads(pathlib.Path(path).read_text()); p=d.get('points') if isinstance(d,dict) else d
    if p is None or len(p)!=960: raise ValueError(f'{path}: expected 960 points')
    x=np.asarray(p,float); return x/np.linalg.norm(x,axis=1)[:,None],d


def load_resume(path,L,R):
    d=json.loads(pathlib.Path(path).read_text()); pts=d.get('path_points')
    if not pts or len(pts)<3: raise ValueError('resume JSON must contain >=3 path_points')
    images=[np.asarray(x,float) for x in pts]
    images=[x/np.linalg.norm(x,axis=1)[:,None] for x in images]
    if any(x.shape!=(960,3) for x in images): raise ValueError('resume path image shape mismatch')
    # Lock endpoints to current durable inputs; the interior labeling remains the
    # same because resume is only valid for the same endpoint pair.
    images[0]=L.copy(); images[-1]=R.copy()
    return images,d


def path_diagnostics(images):
    vals=[]; perps=[]; grads=[]
    for x in images:
        E,g=sr.energy_grad(x); vals.append(E); grads.append(g)
    for i in range(1,len(images)-1):
        tau=sr.path_tangent(images,i)
        gp=grads[i]-float(np.sum(grads[i]*tau))*tau
        perps.append(float(np.sqrt(np.mean(np.sum(gp*gp,axis=1)))))
    return vals,perps,grads


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('left_json'); ap.add_argument('right_json')
    ap.add_argument('--images',type=int,default=7); ap.add_argument('--iterations',type=int,default=180)
    ap.add_argument('--eta',type=float,default=2.5e-4); ap.add_argument('--max-step',type=float,default=7e-4)
    ap.add_argument('--perp-tol',type=float,default=0.0,help='stop when max interior perpendicular-gradient RMS is below this')
    ap.add_argument('--climb-iterations',type=int,default=120)
    ap.add_argument('--resume-json',default=None,help='continue from prior output containing path_points')
    ap.add_argument('--out',required=True); args=ap.parse_args()
    L,Lmeta=load_seed(args.left_json); R,Rmeta=load_seed(args.right_json)
    resume_meta=None
    if args.resume_json:
        images,resume_meta=load_resume(args.resume_json,L,R); args.images=len(images)
        print(f'resuming {len(images)} images from {args.resume_json}; prior_perp={resume_meta.get("max_path_perpendicular_gradient_rms")}',flush=True)
    else:
        images=sr.interpolate_endpoints(L,R,args.images)
    hist=[]; converged=False; performed=0
    for it in range(args.iterations):
        vals,perps,grads=path_diagnostics(images)
        maxstep=0.0; new=[images[0]]
        for i in range(1,len(images)-1):
            tau=sr.path_tangent(images,i)
            gp=grads[i]-float(np.sum(grads[i]*tau))*tau
            y,s=sr.capped_descent(images[i],gp,args.eta,args.max_step); new.append(y); maxstep=max(maxstep,s)
        new.append(images[-1]); images,total=sr.reparameterize(new); performed=it+1
        if it%10==0 or it==args.iterations-1:
            vals2,perps2,_=path_diagnostics(images); imax=int(np.argmax(vals2)); barrier=max(vals2)-min(vals2[0],vals2[-1])
            maxperp=max(perps2) if perps2 else 0.0
            print(f'iter={it} maxE={max(vals2):.12f} imax={imax} barrier={barrier:.9g} arc={total:.6g} step={maxstep:.3e} perp={maxperp:.6g}',flush=True)
            hist.append({'iteration':it,'energies':vals2,'max_index':imax,'arc':total,'max_step':maxstep,
                         'perpendicular_gradient_rms':perps2,'max_perpendicular_gradient_rms':maxperp})
            if args.perp_tol>0 and it>=20 and maxperp<args.perp_tol:
                converged=True; break

    vals,perps,_=path_diagnostics(images); imax=int(np.argmax(vals)); collapsed=imax in (0,len(images)-1)
    probe=imax if not collapsed else (1 if imax==0 else len(images)-2)
    saddle=images[probe].copy(); climb=[]
    if collapsed:
        print(f'endpoint-collapsed maximum at {imax}; retaining interior probe {probe}',flush=True)
    else:
        for it in range(args.climb_iterations):
            E,g=sr.energy_grad(saddle); tmp=images.copy(); tmp[probe]=saddle; tau=sr.path_tangent(tmp,probe)
            saddle,s=sr.climb_step(saddle,g,tau,args.eta,args.max_step*0.7)
            grms=float(np.sqrt(np.mean(np.sum(g*g,axis=1))))
            gperp=g-float(np.sum(g*tau))*tau; prms=float(np.sqrt(np.mean(np.sum(gperp*gperp,axis=1))))
            if it%10==0 or it==args.climb_iterations-1:
                print(f'climb={it} E={E:.12f} grad_rms={grms:.6g} perp={prms:.6g} step={s:.3e}',flush=True)
                climb.append({'iteration':it,'energy':E,'grad_rms':grms,'perpendicular_grad_rms':prms,'step':s})

    Es,gs=sr.energy_grad(saddle); grms=float(np.sqrt(np.mean(np.sum(gs*gs,axis=1))))
    tmp=images.copy(); tmp[probe]=saddle; tau=sr.path_tangent(tmp,probe)
    gp=gs-float(np.sum(gs*tau))*tau; prms=float(np.sqrt(np.mean(np.sum(gp*gp,axis=1))))
    out={'left_json':str(args.left_json),'right_json':str(args.right_json),'resume_json':str(args.resume_json) if args.resume_json else None,
         'prior_performed_iterations':int(resume_meta.get('performed_iterations',0)) if resume_meta else 0,
         'left_energy':sr.energy_grad(L)[0],'right_energy':sr.energy_grad(R)[0],
         'images':args.images,'requested_iterations':args.iterations,'performed_iterations':performed,
         'perp_tol':args.perp_tol,'string_converged':converged,'path_energies':vals,
         'path_perpendicular_gradient_rms':perps,'max_path_perpendicular_gradient_rms':max(perps) if perps else 0.0,
         'path_points':[x.tolist() for x in images],
         'max_image_index':imax,'endpoint_collapsed':collapsed,'probe_index':probe,'history':hist,
         'climbing_energy':Es,'climbing_gradient_rms':grms,'climbing_perpendicular_gradient_rms':prms,
         'climb_history':climb,'saddle_points':saddle.tolist(),
         'left_neighbor_points':images[probe-1].tolist(),'right_neighbor_points':images[probe+1].tolist(),
         'path_tangent_cartesian':tau.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
