#!/usr/bin/env python3
"""Accelerate a spherical Thomson string by proximal normal-plane L-BFGS sweeps.

This continues a saved path from string_between_seeds.py.  Each outer sweep
freezes the current path tangents, approximately minimizes each interior image
in the hyperplane normal to its tangent with a proximal trust penalty, then
reparameterizes the path by RMS geodesic arc length.  Re-anchoring the proximal
term after every sweep gives a stable implicit-like alternative to thousands of
small explicit perpendicular-gradient steps.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.optimize import minimize

import diagnose_soft_modes as sm
import string_record_neighbor as sr
from string_between_seeds import load_seed, load_resume, path_diagnostics

N=960

def wrap_phi(d): return (d+math.pi)%(2*math.pi)-math.pi

def tangent_to_physical(q,tau_cart):
    x,dth,dph=sm.vars_to_xyz(q); st=np.maximum(np.linalg.norm(dph,axis=1),1e-8); eph=dph/st[:,None]
    m=np.column_stack([np.sum(tau_cart*dth,axis=1),np.sum(tau_cart*eph,axis=1)]).ravel()
    Q=sm.rotation_basis(q); m-=Q@(Q.T@m); n=np.linalg.norm(m)
    if n<1e-14: raise RuntimeError('degenerate path tangent')
    return m/n

def relax_image(xref,tau_cart,parallel_penalty,prox_penalty,maxiter):
    q0=sm.xyz_to_vars(xref); n=N; tri=np.triu_indices(n,1)
    x0,_,_=sm.vars_to_xyz(q0); dots=np.clip(x0@x0.T,-1,1); r2=np.maximum(2-2*dots,1e-300); np.fill_diagonal(r2,np.inf)
    inv0=1/np.sqrt(r2); ref=np.asarray(inv0[tri],dtype=np.longdouble); ref_abs=float(np.sum(inv0[tri],dtype=np.float64))
    a0=q0.reshape(-1,2); sin0=np.maximum(np.sin(a0[:,0]),1e-6); mode=tangent_to_physical(q0,tau_cart).reshape(-1,2)
    def disp(q):
        a=q.reshape(-1,2); dth=a[:,0]-a0[:,0]; dph=wrap_phi(a[:,1]-a0[:,1]); return np.column_stack([dth,sin0*dph])
    def obj(q):
        x,dth,dph=sm.vars_to_xyz(q); dots=np.clip(x@x.T,-1,1); r2=np.maximum(2-2*dots,1e-300); np.fill_diagonal(r2,np.inf)
        inv=1/np.sqrt(r2); delta=float(np.sum(np.asarray(inv[tri],dtype=np.longdouble)-ref,dtype=np.longdouble))
        w=inv/r2; np.fill_diagonal(w,0); gc=w@x-np.sum(w,axis=1)[:,None]*x
        gq=np.column_stack([np.sum(gc*dth,axis=1),np.sum(gc*dph,axis=1)])
        y=disp(q); c=float(np.sum(y*mode)); p2=float(np.sum(y*y))
        gp=np.empty_like(gq); gp[:,0]=parallel_penalty*c*mode[:,0]+prox_penalty*y[:,0]
        gp[:,1]=(parallel_penalty*c*mode[:,1]+prox_penalty*y[:,1])*sin0
        return delta+0.5*parallel_penalty*c*c+0.5*prox_penalty*p2,(gq+gp).ravel()
    bounds=[(1e-8,math.pi-1e-8),(None,None)]*n
    res=minimize(obj,q0,jac=True,method='L-BFGS-B',bounds=bounds,
                 options={'maxiter':maxiter,'gtol':2e-9,'ftol':1e-15,'maxls':60,'maxcor':30})
    x=sm.vars_to_xyz(res.x)[0]; x/=np.linalg.norm(x,axis=1)[:,None]
    return x,int(res.nit),bool(res.success),str(res.message)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('left_json'); ap.add_argument('right_json'); ap.add_argument('resume_json')
    ap.add_argument('--outer',type=int,default=20); ap.add_argument('--parallel-penalty',type=float,default=4e5)
    ap.add_argument('--prox-penalty',type=float,default=40.0); ap.add_argument('--image-maxiter',type=int,default=80)
    ap.add_argument('--perp-tol',type=float,default=2e-5); ap.add_argument('--out',required=True); args=ap.parse_args()
    L,_=load_seed(args.left_json); R,_=load_seed(args.right_json); images,meta=load_resume(args.resume_json,L,R)
    hist=[]; converged=False
    for outer in range(args.outer):
        vals,perps,grads=path_diagnostics(images); old=images; new=[old[0]]; stats=[]
        for i in range(1,len(old)-1):
            tau=sr.path_tangent(old,i); y,nit,ok,msg=relax_image(old[i],tau,args.parallel_penalty,args.prox_penalty,args.image_maxiter)
            new.append(y); stats.append({'image':i,'nit':nit,'success':ok,'message':msg})
        new.append(old[-1]); images,arc=sr.reparameterize(new); vals2,perps2,_=path_diagnostics(images)
        mp=max(perps2) if perps2 else 0.0; imax=int(np.argmax(vals2))
        print(f'outer={outer} maxE={max(vals2):.12f} imax={imax} arc={arc:.7g} maxperp={mp:.6g}',flush=True)
        hist.append({'outer':outer,'energies':vals2,'perpendicular_gradient_rms':perps2,'max_perpendicular_gradient_rms':mp,'arc':arc,'image_stats':stats})
        if mp<args.perp_tol: converged=True; break
    vals,perps,_=path_diagnostics(images); imax=int(np.argmax(vals)); probe=imax if imax not in (0,len(images)-1) else (1 if imax==0 else len(images)-2)
    out={'left_json':args.left_json,'right_json':args.right_json,'resume_json':args.resume_json,
         'outer_requested':args.outer,'outer_performed':len(hist),'parallel_penalty':args.parallel_penalty,'prox_penalty':args.prox_penalty,
         'perp_tol':args.perp_tol,'string_converged':converged,'path_energies':vals,'path_perpendicular_gradient_rms':perps,
         'max_path_perpendicular_gradient_rms':max(perps) if perps else 0.0,'max_image_index':imax,'probe_index':probe,
         'history':hist,'path_points':[x.tolist() for x in images],'saddle_points':images[probe].tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
