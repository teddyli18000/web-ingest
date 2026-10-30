#!/usr/bin/env python3
"""Compose the e432-B saddle interface with the known A->live direction.

The refined e432<->B saddle has a broad transverse fan whose positive modes
repeatedly quench to A.  We therefore stop treating those modes independently.
Instead, in the physical tangent space at the e432-B saddle, form the exact
(log-map) displacements to labeled A and to the current live record R.  The
line y(t)=y_A+t*(y_R-y_A) passes through the A direction at t=0 and the R
direction at t=1; t>1 continues the same collective coordinate beyond R.
Small independent radial scalings probe nearby basin-boundary sheets.
"""
from __future__ import annotations
import argparse,json,pathlib,math
import numpy as np

import diagnose_soft_modes as sm
import search_soft_pair as sp
import search_topology_morph as tm
from analyze_reaction_mode_overlap import load,reaction_physical
from search_from_seed_modes import stable_relax_q

N=960


def kabsch_labeled(X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Rotate labeled row-vectors X to Y without permutation."""
    U,s,Vt=np.linalg.svd(X.T@Y)
    R=U@Vt
    if np.linalg.det(R)<0:
        U[:,-1]*=-1
        R=U@Vt
    Z=X@R
    return Z/np.linalg.norm(Z,axis=1)[:,None]


def load_saddle(path):
    d=json.loads(pathlib.Path(path).read_text())
    S=np.asarray(d['saddle_points'],float)
    S/=np.linalg.norm(S,axis=1)[:,None]
    return d,S


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots'); ap.add_argument('refined_json'); ap.add_argument('A_json'); ap.add_argument('live_json')
    ap.add_argument('--ts',default='0.45,0.65,0.8,0.9,1.0,1.08,1.18,1.32,1.5,1.75,2.0,2.4')
    ap.add_argument('--scales',default='0.88,0.96,1.0,1.04,1.12')
    ap.add_argument('--maxiter',type=int,default=3000); ap.add_argument('--out',required=True)
    args=ap.parse_args()

    root=pathlib.Path(args.few_shots); live_score,live_shot=sm.find_live(root)
    meta,S=load_saddle(args.refined_json)
    A=kabsch_labeled(load(args.A_json),S); R=kabsch_labeled(load(args.live_json),S)
    q,yA,Q=reaction_physical(S,A); q2,yR,Q2=reaction_physical(S,R)
    if np.linalg.norm(q-q2)>1e-10: raise RuntimeError('inconsistent saddle variables')
    d=yR-yA
    # All three vectors already have rigid rotations removed by reaction_physical;
    # clean once more after differencing.
    d-=Q@(Q.T@d); yA-=Q@(Q.T@yA); yR-=Q@(Q.T@yR)
    rmsA=float(np.linalg.norm(yA)/math.sqrt(N)); rmsR=float(np.linalg.norm(yR)/math.sqrt(N)); rmsd=float(np.linalg.norm(d)/math.sqrt(N))
    cosAR=float(yA@yR/(np.linalg.norm(yA)*np.linalg.norm(yR)))
    print('SADDLE',meta.get('final_energy'),'grad',meta.get('final_gradient_rms'),'A_RMS',rmsA,'R_RMS',rmsR,'D_RMS',rmsd,'COS_AR',cosAR,flush=True)

    ts=[float(v) for v in args.ts.split(',') if v]; scales=[float(v) for v in args.scales.split(',') if v]
    rows=[]; saved=[]; best=(1e300,None)
    for t in ts:
        base=yA+t*d
        for s in scales:
            y=s*base; y-=Q@(Q.T@y)
            yn=float(np.linalg.norm(y)); amp=yn/math.sqrt(N)
            qs=sp.exp_perturb(q,y/yn,amp); es,_=sm.fg(qs)
            e,raw,x,nit,ok,msg=stable_relax_q(qs,args.maxiter); cc=tm.coord_counts(x)
            row={'t':t,'scale':s,'combined_rms_amp':amp,'start_energy':float(es),'energy':float(e),
                 'delta_vs_live':float(e-live_score),'coord_counts':cc,'nit':nit,'success':ok,'message':msg}
            rows.append(row)
            print('TRY t',t,'s',s,'rms',f'{amp:.7g}','start',f'{es:.9f}','E',f'{e:.12f}',
                  'dLive',f'{e-live_score:+.9g}','cc',cc,'nit',nit,flush=True)
            if e<best[0]: best=(e,x.copy())
            if e<live_score+0.06 and all(abs(e-z['energy'])>2e-6 or cc!=z['coord_counts'] for z in saved):
                saved.append({'energy':float(e),'delta_vs_live':float(e-live_score),'coord_counts':cc,
                              't':t,'scale':s,'points':x.tolist()})
    saved.sort(key=lambda z:z['energy'])
    out={'live_score':live_score,'live_shot':str(live_shot.relative_to(root)),'saddle_energy':meta.get('final_energy'),
         'saddle_gradient_rms':meta.get('final_gradient_rms'),'A_rms':rmsA,'R_rms':rmsR,'A_to_R_delta_rms':rmsd,
         'cos_A_R':cosAR,'rows':rows,'distinct_low_basins':saved[:30],'best_energy':float(best[0]),
         'best_delta_vs_live':float(best[0]-live_score),'best_points':best[1].tolist() if best[1] is not None and best[0]<live_score-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best[1] is not None and best[0]<live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps({'energy':float(best[0]),'points':best[1].tolist()},separators=(',',':'))+'\n')

if __name__=='__main__': main()
