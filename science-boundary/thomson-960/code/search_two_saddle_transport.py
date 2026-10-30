#!/usr/bin/env python3
"""Compose two known Thomson transition interfaces by tangent-field transport.

At A, the incoming e432/B->A interface direction is nearly orthogonal to the
known A->R direction.  This script parallel-transports that incoming physical
field along the short A->(R-A saddle) geodesic, removes rigid rotations and the
certified R-A reaction mode, then scans this transported field transversely to
the certified R-A saddle.  This tests for a fourth basin near the junction of
the e432-B-A and A-R transition networks without truncating the incoming field
to low Hessian modes.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np

import diagnose_soft_modes as sm
import search_soft_pair as sp
import search_topology_morph as tm
from search_from_seed_modes import stable_relax_q

N=960


def load_points(path,key='points'):
    d=json.loads(pathlib.Path(path).read_text())
    p=d.get(key) if isinstance(d,dict) else d
    if p is None: raise ValueError(f'missing {key} in {path}')
    x=np.asarray(p,float); return x/np.linalg.norm(x,axis=1)[:,None]


def kabsch_rotation(X,Y):
    U,s,Vt=np.linalg.svd(X.T@Y); R=U@Vt
    if np.linalg.det(R)<0:
        U[:,-1]*=-1; R=U@Vt
    return R


def log_field(X,Y):
    c=np.clip(np.sum(X*Y,axis=1),-1.0,1.0); a=np.arccos(c); sa=np.sin(a)
    v=np.zeros_like(X); good=sa>1e-12
    v[good]=(a[good]/sa[good])[:,None]*(Y[good]-c[good,None]*X[good])
    bad=~good
    if np.any(bad):
        z=Y[bad]-X[bad]; z-=np.sum(z*X[bad],axis=1)[:,None]*X[bad]; v[bad]=z
    return v


def field_to_y(X,V):
    q=sm.xyz_to_vars(X); x,dth,dph=sm.vars_to_xyz(q)
    sinth=np.maximum(np.sin(q.reshape(-1,2)[:,0]),1e-10); ephi=dph/sinth[:,None]
    y=np.column_stack([np.sum(V*dth,axis=1),np.sum(V*ephi,axis=1)]).ravel()
    return q,y,dth,ephi


def y_to_field(y,dth,ephi):
    z=y.reshape(-1,2)
    return z[:,0,None]*dth+z[:,1,None]*ephi


def parallel_transport(X,Y,V):
    # Exact shortest-geodesic parallel transport on the unit sphere:
    # V_y = V_x - ((V_x dot Y)/(1+X dot Y)) (X+Y), pointwise.
    den=1.0+np.sum(X*Y,axis=1)
    if np.min(den)<1e-8: raise ValueError('near-antipodal transport encountered')
    a=np.sum(V*Y,axis=1)/den
    W=V-a[:,None]*(X+Y)
    W-=np.sum(W*Y,axis=1)[:,None]*Y
    return W


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots'); ap.add_argument('ra_saddle_json'); ap.add_argument('eb_saddle_json'); ap.add_argument('A_json')
    ap.add_argument('--sign',type=int,choices=[-1,1],required=True)
    ap.add_argument('--transverse-amps',default='0.001,0.0025,0.0045,0.007,0.0105,0.015,0.022')
    ap.add_argument('--reaction-amps',default='-0.0015,0,0.0015')
    ap.add_argument('--maxiter',type=int,default=3000); ap.add_argument('--out',required=True)
    args=ap.parse_args()

    root=pathlib.Path(args.few_shots); live_score,live_shot=sm.find_live(root)
    dra=json.loads(pathlib.Path(args.ra_saddle_json).read_text()); deb=json.loads(pathlib.Path(args.eb_saddle_json).read_text())
    Sra=np.asarray(dra['saddle_points'],float); Sra/=np.linalg.norm(Sra,axis=1)[:,None]
    Seb=np.asarray(deb['saddle_points'],float); Seb/=np.linalg.norm(Seb,axis=1)[:,None]
    A=load_points(args.A_json)

    # A and e432-B saddle have meaningful common labels.  Rotate them together
    # into the certified R-A saddle frame, preserving their relative field.
    Rot=kabsch_rotation(A,Sra); A2=A@Rot; Seb2=Seb@Rot
    A2/=np.linalg.norm(A2,axis=1)[:,None]; Seb2/=np.linalg.norm(Seb2,axis=1)[:,None]

    # Incoming interface field at A, with rigid rotation removed before transport.
    VA=log_field(A2,Seb2)
    qA,yA,dthA,ephiA=field_to_y(A2,VA); QA=sm.rotation_basis(qA); yA-=QA@(QA.T@yA)
    VA=y_to_field(yA,dthA,ephiA)
    W=parallel_transport(A2,Sra,VA)

    q0,yT,dth0,ephi0=field_to_y(Sra,W); Q0=sm.rotation_basis(q0); yT-=Q0@(Q0.T@yT)
    reaction=np.asarray(dra['eigenvectors_physical'][0],float).copy(); reaction-=Q0@(Q0.T@reaction); reaction/=np.linalg.norm(reaction)
    yT-=reaction*float(reaction@yT); yT-=Q0@(Q0.T@yT); yT/=np.linalg.norm(yT); yT*=args.sign
    print('RA_SADDLE',dra['final_energy'],'grad',dra['final_gradient_rms'],'lambda0',dra['final_modes'][0]['eigenvalue'],flush=True)
    print('TRANSPORT sign',args.sign,'A_to_RA_rms',float(np.sqrt(np.mean(np.sum(log_field(A2,Sra)**2,axis=1)))),
          'incoming_A_rms',float(np.linalg.norm(yA)/math.sqrt(N)),'reaction_overlap_removed',float(reaction@yT),flush=True)

    ta=[float(v) for v in args.transverse_amps.split(',') if v]; ra=[float(v) for v in args.reaction_amps.split(',') if v]
    rows=[]; saved=[]; best=(1e300,None)
    for t in ta:
        for r in ra:
            y=math.sqrt(N)*(t*yT+r*reaction); y-=Q0@(Q0.T@y)
            yn=float(np.linalg.norm(y)); amp=yn/math.sqrt(N); qs=sp.exp_perturb(q0,y/yn,amp)
            es,_=sm.fg(qs); e,raw,x,nit,ok,msg=stable_relax_q(qs,args.maxiter); cc=tm.coord_counts(x)
            row={'transverse_amp':t,'reaction_amp':r,'combined_rms_amp':amp,'start_energy':float(es),'energy':float(e),
                 'delta_vs_live':float(e-live_score),'coord_counts':cc,'nit':nit,'success':ok,'message':msg}
            rows.append(row)
            print('TRY t',t,'r',r,'start',f'{es:.9f}','E',f'{e:.12f}','dLive',f'{e-live_score:+.9g}','cc',cc,'nit',nit,flush=True)
            if e<best[0]: best=(e,x.copy())
            if e<live_score+0.06 and all(abs(e-z['energy'])>2e-6 or cc!=z['coord_counts'] for z in saved):
                saved.append({'energy':float(e),'delta_vs_live':float(e-live_score),'coord_counts':cc,'transverse_amp':t,'reaction_amp':r,'points':x.tolist()})
    saved.sort(key=lambda z:z['energy'])
    out={'live_score':live_score,'live_shot':str(live_shot.relative_to(root)),'ra_saddle_energy':dra['final_energy'],
         'ra_saddle_gradient_rms':dra['final_gradient_rms'],'sign':args.sign,'rows':rows,'distinct_low_basins':saved,
         'best_energy':float(best[0]),'best_delta_vs_live':float(best[0]-live_score),
         'best_points':best[1].tolist() if best[1] is not None and best[0]<live_score-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if out['best_points'] is not None:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps({'energy':out['best_energy'],'points':out['best_points']},separators=(',',':'))+'\n')

if __name__=='__main__': main()
