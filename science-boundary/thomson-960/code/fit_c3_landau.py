#!/usr/bin/env python3
"""Fit the local C3 Landau potential on a two-dimensional unstable doublet.

For a C3-symmetric stationary state whose lowest two Hessian modes form the
nontrivial real C3 irrep, symmetry forces the leading angular anisotropy to have
period 120 degrees.  In the physical tangent-plane polar coordinates
rho = sqrt(N) * RMS and theta in the canonicalized doublet basis, fit

  Delta E(rho,theta) = c2 rho^2
                     + rho^3 [c3 cos(3 theta) + s3 sin(3 theta)]
                     + c4 rho^4
                     + rho^6 [c6 cos(6 theta) + s6 sin(6 theta)] + ...

We fit each sampled radius independently in theta first, then report the scaled
cubic coefficient and the phase of the C3 ridge/valley.  The radius-averaged
isotropic residual above the Hessian quadratic term estimates c4.  This is a
local model only; its purpose is to select principled downward-search directions
and amplitudes, not to extrapolate globally.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import load_seed
from search_seed_c3_negative_pair import canonicalize_pair_near

N=960


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--rms-amps',default='0.0002,0.0003,0.0004')
    ap.add_argument('--phase-step-deg',type=float,default=5.0)
    ap.add_argument('--fd-step',type=float,default=3e-6); ap.add_argument('--out',required=True)
    args=ap.parse_args(); meta,x=load_seed(pathlib.Path(args.seed_json)); q=sm.xyz_to_vars(x)
    E0,gq=sm.fg(q); H,raw,Q,calls=sm.build_hessian(q,args.fd_step,1e6)
    rng=np.random.default_rng(9603003); v0=rng.normal(size=len(q)); v0-=Q@(Q.T@v0); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=6,which='SA',tol=1e-5,maxiter=800,ncv=40,v0=v0); o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    pair=V[:,:2].copy(); pair-=Q@(Q.T@pair); pair,_=np.linalg.qr(pair)
    pair,M,resid,ai,ac,maperr=canonicalize_pair_near(pair,q)
    phases=np.arange(0.0,120.0-1e-12,args.phase_step_deg)
    th=np.deg2rad(phases)
    X=np.column_stack([np.ones(len(phases)),np.cos(3*th),np.sin(3*th),np.cos(6*th),np.sin(6*th)])
    rows=[]; radius_fits=[]; c4_est=[]
    lam_mean=float(np.mean(vals[:2])); c2=0.5*lam_mean
    for amp in [float(z) for z in args.rms_amps.split(',') if z]:
        rho=amp*math.sqrt(N); de=[]
        for ph,t in zip(phases,th):
            direction=math.cos(t)*pair[:,0]+math.sin(t)*pair[:,1]; direction/=np.linalg.norm(direction)
            E,_=sm.fg(sp.exp_perturb(q,direction,amp)); d=float(E-E0); de.append(d)
            rows.append({'rms_amp':amp,'rho':rho,'phase_deg':float(ph),'delta_energy':d})
        de=np.asarray(de); coef=np.linalg.lstsq(X,de,rcond=None)[0]
        A3,B3=float(coef[1]),float(coef[2]); amp3=math.hypot(A3,B3); phi=math.atan2(B3,A3)
        ridge=(phi/3.0)%(2*math.pi/3); valley=((phi+math.pi)/3.0)%(2*math.pi/3)
        cubic_scaled=amp3/(rho**3)
        mean=float(coef[0]); quartic=(mean-c2*rho*rho)/(rho**4); c4_est.append(quartic)
        radius_fits.append({'rms_amp':amp,'rho':rho,'mean_delta':mean,'cos3':A3,'sin3':B3,
                            'harmonic3_amplitude':amp3,'cubic_scaled':cubic_scaled,
                            'cos6':float(coef[3]),'sin6':float(coef[4]),
                            'ridge_phase_deg':math.degrees(ridge),'valley_phase_deg':math.degrees(valley),
                            'quartic_isotropic_estimate':quartic,'min_delta':float(np.min(de)),'max_delta':float(np.max(de))})
        print(f'amp={amp:.6g} rho={rho:.6g} mean={mean:+.9g} c3/rho3={cubic_scaled:.6g} '
              f'c4={quartic:.6g} ridge={math.degrees(ridge):.4f} valley={math.degrees(valley):.4f}',flush=True)
    cubic=float(np.median([r['cubic_scaled'] for r in radius_fits])); c4=float(np.median(c4_est))
    ridge=float(np.median([r['ridge_phase_deg'] for r in radius_fits])); valley=(ridge+60.0)%120.0
    # Reduced quartic stationary radii on angular extrema: dV/drho=0.
    predictions=[]
    a=-lam_mean
    for sign,label,ang in [(1.0,'ridge',ridge),(-1.0,'valley',valley)]:
        roots=np.roots([4*c4,3*cubic*sign,-a])
        pos=sorted(float(z.real) for z in roots if abs(z.imag)<1e-8 and z.real>0)
        for rho in pos:
            dE=-0.5*a*rho*rho + cubic*sign*rho**3 + c4*rho**4
            predictions.append({'kind':label,'phase_deg':ang,'rho':rho,'rms_amp':rho/math.sqrt(N),'delta_energy':dE})
    out={'seed_json':str(args.seed_json),'energy':E0,'physical_gradient_rms':float(np.sqrt(np.mean((gq/sm.physical_scale(q))**2))),
         'eigenvalues':[float(v) for v in vals],'lambda_pair_mean':lam_mean,'quadratic_coefficient':c2,
         'c3_pair_matrix':M.tolist(),'c3_subspace_residual':resid,'c3_mapping_max_error':maperr,
         'canonical_anchor_point':ai,'canonical_anchor_component':ac,'radius_fits':radius_fits,
         'median_cubic_scaled':cubic,'median_quartic_isotropic':c4,'ridge_phase_deg':ridge,'valley_phase_deg':valley,
         'quartic_stationary_predictions':predictions,'rows':rows,'hessian_gradient_calls':calls['n']}
    print('predictions',predictions,flush=True); pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__': main()
