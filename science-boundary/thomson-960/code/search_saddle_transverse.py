#!/usr/bin/env python3
"""Search transverse exits from a refined first-order Thomson saddle.

A minimum-mode scan around R or A can only see basin exits from a minimum.  A
first-order saddle exposes a different local interface.  This script perturbs a
refined R<->A saddle along low *positive* Hessian modes, optionally with a small
push along the negative reaction mode, then fully relaxes without symmetry using
the stable termwise energy-difference objective.

Amplitude arguments are physical RMS angular displacements in radians, matching
the minimum-mode scans used elsewhere in this topic.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import numpy as np

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import stable_relax_q

N=960


def load_refined(path):
    d=json.loads(pathlib.Path(path).read_text())
    x=np.asarray(d['saddle_points'],dtype=float)
    x/=np.linalg.norm(x,axis=1)[:,None]
    vecs=np.asarray(d['eigenvectors_physical'],dtype=float).T
    modes=d['final_modes']
    if vecs.shape[0] != 2*N:
        raise ValueError(f'expected {2*N} physical tangent rows, got {vecs.shape}')
    return d,x,vecs,modes


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots')
    ap.add_argument('refined_json')
    ap.add_argument('--transverse-mode',type=int,required=True,
                    help='mode index in final_modes; 0 should be the negative reaction mode')
    ap.add_argument('--sign',type=int,choices=[-1,1],required=True)
    ap.add_argument('--transverse-amps',default='0.0015,0.003,0.006,0.010')
    ap.add_argument('--reaction-amps',default='-0.001,0,0.001')
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    root=pathlib.Path(args.few_shots)
    live_score,live_shot=sm.find_live(root)
    meta,x0,vecs,modes=load_refined(args.refined_json)
    q0=sm.xyz_to_vars(x0)
    if len(modes)<2 or args.transverse_mode>=len(modes):
        raise ValueError('transverse mode unavailable')
    if modes[0]['eigenvalue'] >= 0:
        raise ValueError('mode 0 is not a negative reaction mode')
    if modes[args.transverse_mode]['eigenvalue'] <= 0:
        raise ValueError('requested transverse mode is not positive')

    Qrot=sm.rotation_basis(q0)
    reaction=vecs[:,0].copy(); transverse=vecs[:,args.transverse_mode].copy()
    reaction-=Qrot@(Qrot.T@reaction); transverse-=Qrot@(Qrot.T@transverse)
    reaction/=np.linalg.norm(reaction); transverse/=np.linalg.norm(transverse)
    transverse-=reaction*float(reaction@transverse); transverse/=np.linalg.norm(transverse)
    transverse*=args.sign

    e0,_=sm.fg(q0)
    tamps=[float(v) for v in args.transverse_amps.split(',') if v]
    ramps=[float(v) for v in args.reaction_amps.split(',') if v]
    rows=[]; best_e=1e300; best_x=None
    print(f'saddle={e0:.12f} grad_rms={meta.get("final_gradient_rms")} '
          f'tmode={args.transverse_mode} lambda={modes[args.transverse_mode]["eigenvalue"]:.9g} sign={args.sign}',flush=True)
    for ta in tamps:
        for ra in ramps:
            # Unit Hessian eigenvectors have Euclidean physical-tangent norm 1.
            # Multiply by sqrt(N) so ta/ra themselves denote RMS radians.
            y=np.sqrt(float(N))*(ta*transverse + ra*reaction)
            yn=float(np.linalg.norm(y))
            if yn==0: continue
            direction=y/yn
            rms_amp=yn/np.sqrt(float(N))
            qs=sp.exp_perturb(q0,direction,rms_amp)
            es,_=sm.fg(qs)
            e,raw,x,nit,ok,msg=stable_relax_q(qs,2200)
            row={'transverse_amp':ta,'reaction_amp':ra,'combined_rms_amp':rms_amp,
                 'start_energy':es,'energy':e,'raw_absolute_energy':raw,
                 'delta_vs_live':e-live_score,'nit':nit,'success':ok,'message':msg}
            rows.append(row)
            print(f't={ta:.5g} r={ra:+.5g} rms={rms_amp:.4g} start={es:.9f} '
                  f'min={e:.12f} dlive={e-live_score:+.9g} nit={nit} ok={ok}',flush=True)
            if e<best_e:
                best_e=e; best_x=x.copy()

    out={'live_score':live_score,'live_shot':str(live_shot.relative_to(root)),
         'refined_json':str(args.refined_json),'saddle_energy':e0,
         'saddle_gradient_rms':meta.get('final_gradient_rms'),
         'negative_modes':meta.get('negative_internal_modes_below_-1e-3'),
         'reaction_eigenvalue':modes[0]['eigenvalue'],
         'transverse_mode':args.transverse_mode,
         'transverse_eigenvalue':modes[args.transverse_mode]['eigenvalue'],
         'sign':args.sign,'rows':rows,'best_float_energy':best_e,
         'best_delta_vs_live':best_e-live_score,
         'best_points':best_x.tolist() if best_x is not None and best_e < live_score-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__':
    main()
