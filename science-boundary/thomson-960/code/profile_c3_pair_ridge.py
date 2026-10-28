#!/usr/bin/env python3
"""Profile a C3-doublet Landau ridge after minimizing all orthogonal directions.

For the index-2 state C, the two unstable Hessian modes give a physically
meaningful 2-D reaction coordinate.  Rather than tracking individual Hessian
eigenvectors as they cross, hold the two canonical pair coordinates fixed at
(rho,theta), minimize the remaining 1918-dimensional complement, and measure
the *unpenalized* radial/angular gradient components.

Along the C3 Landau ridge the angular gradient is symmetry-small.  A zero of the
radial component after complement relaxation is therefore a direct candidate
for the B<->D index-1 descendant.  The best sampled/bracket-refined point is
classified by an independent full-space Hessian.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.optimize import minimize
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import load_seed
from search_seed_c3_negative_pair import canonicalize_pair_near

N=960; PI=math.pi


def low_pair(q,fd):
    H,raw,Q,calls=sm.build_hessian(q,fd,1e6)
    rng=np.random.default_rng(9601516); v0=rng.normal(size=len(q)); v0-=Q@(Q.T@v0); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=6,which='SA',tol=1e-5,maxiter=800,ncv=40,v0=v0); o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    pair=V[:,:2].copy(); pair-=Q@(Q.T@pair); pair,_=np.linalg.qr(pair)
    pair,M,resid,ai,ac,maperr=canonicalize_pair_near(pair,q)
    return vals,pair,Q,calls['n'],M,resid,maperr


def wrap_phi(d): return (d+math.pi)%(2*math.pi)-math.pi


def constrained_at(q0,pair,phase,amp,penalty,maxiter):
    n=N; a0=q0.reshape(-1,2); sin0=np.maximum(np.sin(a0[:,0]),1e-6)
    tri=np.triu_indices(n,1); _,inv0,_=geom_grad(q0); ref=np.asarray(inv0[tri],np.longdouble); E0=float(np.sum(inv0[tri],dtype=np.float64))
    rho=amp*math.sqrt(N); target=np.array([rho*math.cos(phase),rho*math.sin(phase)])
    # Start from the exact geodesic pair displacement.
    direction=math.cos(phase)*pair[:,0]+math.sin(phase)*pair[:,1]; direction/=np.linalg.norm(direction)
    qstart=sp.exp_perturb(q0,direction,amp)
    def disp(q):
        a=q.reshape(-1,2); dth=a[:,0]-a0[:,0]; dph=wrap_phi(a[:,1]-a0[:,1])
        y=np.column_stack([dth,sin0*dph]).ravel(); return y
    def obj(q):
        _,inv,gq=geom_grad(q); delta=float(np.sum(np.asarray(inv[tri],np.longdouble)-ref,dtype=np.longdouble))
        y=disp(q); cs=pair.T@y-target
        # d c_j / d theta = pair(theta), d c_j / d phi = pair(phi)*sin(theta0)
        gp=np.zeros_like(gq).reshape(-1,2)
        for j in range(2):
            m=pair[:,j].reshape(-1,2); gp[:,0]+=penalty*cs[j]*m[:,0]; gp[:,1]+=penalty*cs[j]*m[:,1]*sin0
        return delta+0.5*penalty*float(cs@cs), gq+gp.ravel()
    bounds=[(1e-8,PI-1e-8),(None,None)]*n
    r=minimize(obj,qstart,jac=True,method='L-BFGS-B',bounds=bounds,options={'maxiter':maxiter,'gtol':5e-10,'ftol':1e-15,'maxls':70,'maxcor':40})
    _,inv,gq=geom_grad(r.x); E=E0+float(np.sum(np.asarray(inv[tri],np.longdouble)-ref,dtype=np.longdouble))
    y=disp(r.x); cs=pair.T@y-target
    gphys=gq/sm.physical_scale(r.x); Q=sm.rotation_basis(r.x); gphys-=Q@(Q.T@gphys)
    # Compare gradients with the C-centered canonical pair; adequate at rho~1e-2 total norm.
    gr=float(gphys@(math.cos(phase)*pair[:,0]+math.sin(phase)*pair[:,1]))
    gt=float(gphys@(-math.sin(phase)*pair[:,0]+math.cos(phase)*pair[:,1]))
    gres=gphys-pair@(pair.T@gphys)
    return {'amp':amp,'rho':rho,'energy':E,'radial_gradient':gr,'angular_gradient':gt,
            'complement_gradient_rms':float(np.linalg.norm(gres)/math.sqrt(2*N)),
            'full_gradient_rms':float(np.linalg.norm(gphys)/math.sqrt(2*N)),
            'constraint_residual':[float(v) for v in cs],'nit':int(r.nit),'success':bool(r.success),'message':str(r.message)},r.x


def geom_grad(q):
    x,dth,dph=sm.vars_to_xyz(q); dots=np.clip(x@x.T,-1,1); r2=np.maximum(2-2*dots,1e-300); np.fill_diagonal(r2,np.inf)
    inv=1/np.sqrt(r2); w=inv/r2; np.fill_diagonal(w,0); ga=w@x
    gt=np.sum(ga*dth,axis=1); gp=np.sum(ga*dph,axis=1)
    return x,inv,np.column_stack([gt,gp]).ravel()


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json'); ap.add_argument('--phase-deg',type=float,default=14.8795)
    ap.add_argument('--amps',default='0.00035,0.00040,0.00045,0.00050,0.00055,0.00060,0.00065')
    ap.add_argument('--penalty',type=float,default=2e7); ap.add_argument('--maxiter',type=int,default=700)
    ap.add_argument('--fd-step',type=float,default=3e-6); ap.add_argument('--bisect',type=int,default=4); ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x=load_seed(pathlib.Path(args.seed_json)); q0=sm.xyz_to_vars(x); E0,_=sm.fg(q0)
    vals,pair,Q,calls,M,resid,maperr=low_pair(q0,args.fd_step); phase=math.radians(args.phase_deg)
    rows=[]; qs=[]
    for amp in [float(z) for z in args.amps.split(',') if z]:
        row,q=constrained_at(q0,pair,phase,amp,args.penalty,args.maxiter); rows.append(row); qs.append(q)
        print(f'a={amp:.7f} E={row["energy"]:.12f} gr={row["radial_gradient"]:+.5g} gt={row["angular_gradient"]:+.5g} '
              f'gperp={row["complement_gradient_rms"]:.3g} c={row["constraint_residual"]}',flush=True)
    # Find the tightest radial-gradient sign bracket and bisect in amplitude.
    order=np.argsort([r['amp'] for r in rows]); bracket=None
    for ia,ib in zip(order[:-1],order[1:]):
        if rows[ia]['radial_gradient']*rows[ib]['radial_gradient']<=0:
            bracket=[rows[ia]['amp'],rows[ib]['amp'],rows[ia]['radial_gradient'],rows[ib]['radial_gradient']]; break
    if bracket:
        lo,hi,glo,ghi=bracket
        for _ in range(args.bisect):
            mid=0.5*(lo+hi); row,q=constrained_at(q0,pair,phase,mid,args.penalty,args.maxiter); rows.append(row); qs.append(q)
            print(f'bisect a={mid:.9f} E={row["energy"]:.12f} gr={row["radial_gradient"]:+.5g} gt={row["angular_gradient"]:+.5g}',flush=True)
            gm=row['radial_gradient']
            if glo*gm<=0: hi,ghi=mid,gm
            else: lo,glo=mid,gm
    best=min(range(len(rows)),key=lambda i:abs(rows[i]['radial_gradient'])+abs(rows[i]['angular_gradient'])+10*rows[i]['complement_gradient_rms'])
    qbest=qs[best]; E,gq=sm.fg(qbest); g=gq/sm.physical_scale(qbest); grms=float(np.linalg.norm(g)/math.sqrt(2*N))
    H,raw,Qb,c=sm.build_hessian(qbest,args.fd_step,1e6); eig,V=eigsh(H,k=12,which='SA',tol=1e-5,maxiter=900,ncv=40); eig=np.sort(eig); neg=int(np.sum(eig<-1e-3))
    print(f'BEST a={rows[best]["amp"]:.9f} E={E:.12f} grad={grms:.6g} neg={neg} eigs={eig[:6].tolist()}',flush=True)
    out={'seed_json':str(args.seed_json),'parent_energy':E0,'parent_eigenvalues':[float(v) for v in vals],
         'phase_deg':args.phase_deg,'c3_pair_matrix':M.tolist(),'c3_subspace_residual':resid,'c3_mapping_max_error':maperr,
         'penalty':args.penalty,'rows':rows,'best_row_index':best,'best_energy':float(E),'best_gradient_rms':grms,
         'negative_internal_modes_below_-1e-3':neg,'best_eigenvalues':[float(v) for v in eig],
         'points':sm.vars_to_xyz(qbest)[0].tolist(),'saddle_points':sm.vars_to_xyz(qbest)[0].tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
if __name__=='__main__': main()
