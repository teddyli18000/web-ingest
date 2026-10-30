#!/usr/bin/env python3
"""Search a two-mode transverse plane around a refined Thomson index-1 saddle.

This is used when two distinct positive modes of the same saddle independently
reach the same low basin.  Rather than extending either one-dimensional scan,
we vary both modes jointly, with a small independent reaction-coordinate bias,
and fully relax every trial.  The goal is to expose basin boundaries that are
invisible on either axis alone.
"""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np

import diagnose_soft_modes as sm
import search_soft_pair as sp
import search_topology_morph as tm
from search_from_seed_modes import stable_relax_q
from search_saddle_transverse import load_refined

N=960


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots'); ap.add_argument('refined_json')
    ap.add_argument('--mode-a',type=int,default=1); ap.add_argument('--mode-b',type=int,default=5)
    ap.add_argument('--sign-a',type=int,choices=[-1,1],required=True)
    ap.add_argument('--sign-b',type=int,choices=[-1,1],required=True)
    ap.add_argument('--amps-a',default='0.006,0.010,0.015')
    ap.add_argument('--amps-b',default='0.004,0.0065,0.010')
    ap.add_argument('--reaction-amps',default='-0.0012,0,0.0012')
    ap.add_argument('--maxiter',type=int,default=2600); ap.add_argument('--out',required=True)
    args=ap.parse_args()

    root=pathlib.Path(args.few_shots); live_score,live_shot=sm.find_live(root)
    meta,x0,vecs,modes=load_refined(args.refined_json); q0=sm.xyz_to_vars(x0)
    if modes[0]['eigenvalue']>=0: raise ValueError('mode0 is not reaction mode')
    for j in (args.mode_a,args.mode_b):
        if j>=len(modes) or modes[j]['eigenvalue']<=0: raise ValueError(f'mode {j} unavailable/nonpositive')

    Q=sm.rotation_basis(q0)
    r=vecs[:,0].copy(); a=vecs[:,args.mode_a].copy(); b=vecs[:,args.mode_b].copy()
    basis=[]
    for z in (r,a,b):
        z-=Q@(Q.T@z)
        for u in basis: z-=u*float(u@z)
        z/=np.linalg.norm(z); basis.append(z)
    r,a,b=basis
    a*=args.sign_a; b*=args.sign_b
    e0,_=sm.fg(q0)
    aa=[float(v) for v in args.amps_a.split(',') if v]
    bb=[float(v) for v in args.amps_b.split(',') if v]
    rr=[float(v) for v in args.reaction_amps.split(',') if v]
    rows=[]; saved=[]; best=(1e300,None)
    print('SADDLE',f'{e0:.12f}','grad',meta.get('final_gradient_rms'),'modes',args.mode_a,args.mode_b,
          'lambdas',modes[args.mode_a]['eigenvalue'],modes[args.mode_b]['eigenvalue'],
          'signs',args.sign_a,args.sign_b,flush=True)
    for xa in aa:
        for xb in bb:
            for xr in rr:
                y=np.sqrt(float(N))*(xa*a+xb*b+xr*r)
                yn=float(np.linalg.norm(y)); direction=y/yn; rms=yn/np.sqrt(float(N))
                qs=sp.exp_perturb(q0,direction,rms); es,_=sm.fg(qs)
                e,raw,x,nit,ok,msg=stable_relax_q(qs,args.maxiter); cc=tm.coord_counts(x)
                row={'amp_a':xa,'amp_b':xb,'reaction_amp':xr,'combined_rms_amp':rms,
                     'start_energy':float(es),'energy':float(e),'delta_vs_live':float(e-live_score),
                     'coord_counts':cc,'nit':nit,'success':ok,'message':msg}
                rows.append(row)
                print('TRY a',xa,'b',xb,'r',xr,'rms',f'{rms:.6g}','start',f'{es:.9f}',
                      'E',f'{e:.12f}','dLive',f'{e-live_score:+.9g}','cc',cc,'nit',nit,flush=True)
                if e<best[0]: best=(e,x.copy())
                if e<live_score+0.06 and all(abs(e-s['energy'])>2e-6 or cc!=s['coord_counts'] for s in saved):
                    saved.append({'energy':float(e),'delta_vs_live':float(e-live_score),'coord_counts':cc,
                                  'amp_a':xa,'amp_b':xb,'reaction_amp':xr,'points':x.tolist()})
    saved.sort(key=lambda z:z['energy'])
    out={'live_score':live_score,'live_shot':str(live_shot.relative_to(root)),'saddle_energy':float(e0),
         'saddle_gradient_rms':meta.get('final_gradient_rms'),'mode_a':args.mode_a,'mode_b':args.mode_b,
         'mode_a_eigenvalue':modes[args.mode_a]['eigenvalue'],'mode_b_eigenvalue':modes[args.mode_b]['eigenvalue'],
         'sign_a':args.sign_a,'sign_b':args.sign_b,'rows':rows,'distinct_low_basins':saved,
         'best_energy':float(best[0]),'best_delta_vs_live':float(best[0]-live_score),
         'best_points':best[1].tolist() if best[1] is not None and best[0]<live_score-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best[1] is not None and best[0]<live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps({'energy':float(best[0]),'points':best[1].tolist()},separators=(',',':'))+'\n')

if __name__=='__main__': main()
