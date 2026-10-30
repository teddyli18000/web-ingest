#!/usr/bin/env python3
"""Exhaustive T-orbit N=972 -> 960 transfer with full-space portal release.

The historical N=972 Thomson minimum is T_h symmetric and differs from N=960 by
exactly one generic 12-point orbit of the proper tetrahedral rotation group T.
This search avoids greedy one-particle deletion: recover an exact T group by
aligning SciPy's canonical tetrahedral group to numerically recovered C2/C3
axes, enumerate every 12-point orbit, remove each orbit, and fully relax all
children in parallel on one Actions runner.

Distinct low children are then classified by the full 1920-dimensional physical
tangent Hessian.  Any symmetry-constrained index>0 child is released along its
lowest negative modes, again within the same runner lifetime.  Scientific
acceptance remains the official p007 threshold; this code only produces float
candidates for the verifier pipeline.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import math
import os
import pathlib
from typing import Any

import numpy as np
from scipy.sparse.linalg import eigsh
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

import diagnose_soft_modes as sm
import search_soft_pair as sp
import search_size_beam as sb
from analyze_twinned_motif import load_xyz
from search_972_twin_orbit_removal import recover_axis, graph, core_distance, raw_energy
from search_learned_event_grammar import defect_signature, sig_key

N0=972
NT=960
PI=math.pi
_PARENT: np.ndarray | None = None


def exact_t_group_from_axes(x: np.ndarray, n2: np.ndarray, n3: np.ndarray):
    """Align canonical proper-T to recovered C2/C3 axis lines.

    For a tetrahedral group every C2 axis has |dot|=1/sqrt(3) with every C3
    axis.  The independently recovered numerical axes are projected onto that
    exact relation before conjugating SciPy's canonical T group.  Sign choices
    are tried explicitly and the point-cloud self-mapping with smallest maximum
    error is retained.
    """
    e2=np.array([1.0,0.0,0.0])
    e3=np.array([1.0,1.0,1.0])/math.sqrt(3.0)
    c=1.0/math.sqrt(3.0)
    s2=e2
    s3=e3-c*s2; s3/=np.linalg.norm(s3)
    s4=np.cross(s2,s3)
    S=np.column_stack([s2,s3,s4])
    G0=Rotation.create_group('T').as_matrix()
    tree=cKDTree(x)
    best=None
    for a2 in (n2,-n2):
        a2=a2/np.linalg.norm(a2)
        for a3raw in (n3,-n3):
            a3raw=a3raw/np.linalg.norm(a3raw)
            # Choose the axis-line orientation compatible with +1/sqrt(3).
            if float(a2@a3raw)<0: a3raw=-a3raw
            u=a3raw-float(a2@a3raw)*a2
            nu=np.linalg.norm(u)
            if nu<1e-8: continue
            u/=nu
            a3=c*a2+math.sqrt(2.0/3.0)*u
            t2=a2
            t3=a3-c*t2; t3/=np.linalg.norm(t3)
            t4=np.cross(t2,t3)
            T=np.column_stack([t2,t3,t4])
            A=T@S.T
            group=[A@R@A.T for R in G0]
            perms=[]; worst=0.0; rms=[]; ok=True
            for R in group:
                d,p=tree.query(x@R.T,k=1)
                if len(np.unique(p))!=len(x): ok=False; break
                perms.append(np.asarray(p,int)); worst=max(worst,float(np.max(d)))
                rms.append(float(np.sqrt(np.mean(d*d))))
            if not ok: continue
            item=(worst,float(max(rms)),group,perms,A,a2,a3)
            if best is None or item[:2]<best[:2]: best=item
    if best is None: raise RuntimeError('could not align a bijective tetrahedral group')
    worst,rms,group,perms,A,a2,a3=best
    if worst>2e-3:
        raise RuntimeError(f'T-group point-cloud validation too poor: max={worst:.3e}, rms={rms:.3e}')
    return group,perms,worst,rms,A,a2,a3


def build_orbits(perms: list[np.ndarray], n: int):
    unseen=set(range(n)); out=[]
    while unseen:
        i=min(unseen)
        orb=sorted(set(int(p[i]) for p in perms))
        # Close under all mappings in case numerical nearest-neighbour mappings
        # need more than one application to expose the whole orbit.
        cur=set(orb); changed=True
        while changed:
            changed=False
            for j in list(cur):
                for p in perms:
                    k=int(p[j])
                    if k not in cur: cur.add(k); changed=True
        orb=sorted(cur); out.append(orb); unseen-=cur
    return out


def sig_json(sig):
    return {'coord':[[int(a),int(b)] for a,b in sig['coord']],
            'components':[list(map(int,t)) for t in sig['components']],
            'twin_count':int(sig['twins']),
            'e77':[list(map(int,t)) for t in sig['e77']]}


def relax_orbit(payload):
    global _PARENT
    oi,orbit,live,pre=payload
    if _PARENT is None: raise RuntimeError('parent not initialized')
    y=np.delete(_PARENT,np.asarray(orbit,int),axis=0)
    E,q,nit,ok=sb.stable_relax(y,1800)
    sig=defect_signature(q)
    return {'orbit_index':int(oi),'orbit':list(map(int,orbit)),**pre,
            'energy':float(E),'delta_vs_live':float(E-live),'nit':int(nit),'success':bool(ok),
            'signature':sig_json(sig),'_sigkey':sig_key(sig),'_points':q}


def classify_child(payload):
    rank,row,k,fd=payload
    x=np.asarray(row['_points'],float); q=sm.xyz_to_vars(x)
    E,gq=sm.fg(q); gy=gq/sm.physical_scale(q); grms=float(np.linalg.norm(gy)/math.sqrt(len(gy)))
    H,raw,Q,calls=sm.build_hessian(q,fd,1e6)
    vals,V=eigsh(H,k=k,which='SA',tol=1e-5,maxiter=1000,ncv=max(50,4*k))
    vals=np.sort(vals); neg=int(np.sum(vals<-1e-3))
    return {'rank':rank,'orbit_index':row['orbit_index'],'energy':float(E),'gradient_rms':grms,
            'negative_modes_among_k':neg,'lowest_eigenvalues':[float(v) for v in vals],
            'hessian_gradient_calls':int(calls['n']),'signature':row['signature'],'_points':x}


def release_portal(payload):
    rank,crow,live,fd=payload
    x=np.asarray(crow['_points'],float); q=sm.xyz_to_vars(x)
    H,raw,Q,calls=sm.build_hessian(q,fd,1e6)
    k=max(10,min(18,crow['negative_modes_among_k']+6))
    vals,V=eigsh(H,k=k,which='SA',tol=1e-5,maxiter=1000,ncv=max(50,4*k))
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    for j in range(V.shape[1]):
        V[:,j]-=Q@(Q.T@V[:,j]); V[:,j]/=np.linalg.norm(V[:,j])
    negids=[j for j,v in enumerate(vals) if v<-1e-3][:4]
    rows=[]
    for j in negids:
        for sign in (-1,1):
            for amp in (0.0006,0.0018,0.0045):
                qs=sp.exp_perturb(q,sign*V[:,j],amp)
                # search_size_beam relaxation works in xyz and uses stable
                # long-double termwise energy differences.
                xs=sm.vars_to_xyz(qs)[0]
                E,z,nit,ok=sb.stable_relax(xs,2200)
                sig=defect_signature(z)
                rows.append({'mode':int(j),'sign':int(sign),'amp':amp,'energy':float(E),
                             'delta_vs_live':float(E-live),'nit':int(nit),'success':bool(ok),
                             'signature':sig_json(sig),'points':z.tolist() if E<live-2e-7 else None})
    return {'rank':rank,'parent_energy':crow['energy'],'parent_neg':crow['negative_modes_among_k'],
            'parent_lows':crow['lowest_eigenvalues'],'release_rows':rows}


def dedup_low(rows,limit=16,tol=2e-7):
    keep=[]
    for r in sorted(rows,key=lambda z:z['energy']):
        key=r['_sigkey']
        if any(abs(r['energy']-q['energy'])<=tol and key==q['_sigkey'] for q in keep): continue
        keep.append(r)
        if len(keep)>=limit: break
    return keep


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('xyz972'); ap.add_argument('few_shots')
    ap.add_argument('--workers',type=int,default=0); ap.add_argument('--classify',type=int,default=16)
    ap.add_argument('--hessian-k',type=int,default=12); ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--seed',type=int,default=97212); ap.add_argument('--out',required=True); args=ap.parse_args()
    workers=args.workers or max(1,min(os.cpu_count() or 1,4))
    root=pathlib.Path(args.few_shots); live,_=sb.find_live(root)
    x=load_xyz(args.xyz972)
    if len(x)!=N0: raise ValueError(f'expected {N0}, got {len(x)}')
    # Recover one C2 and one C3 line, then enforce the exact tetrahedral relation.
    s2,n2=recover_axis(x,PI,args.seed); s3,n3=recover_axis(x,2*PI/3,args.seed+1)
    group,perms,worst,rms,A,a2,a3=exact_t_group_from_axes(x,n2,n3)
    orbits=build_orbits(perms,len(x)); hist={str(k):sum(len(o)==k for o in orbits) for k in sorted(set(map(len,orbits)))}
    nb,edges,z=graph(x); dist=core_distance(nb,z)
    generic=[(i,o) for i,o in enumerate(orbits) if len(o)==12]
    print(f'CPUS={os.cpu_count()} workers={workers} axis_scores={s2:.3e}/{s3:.3e} group=12 validate={worst:.3e}/{rms:.3e} orbit_hist={hist} generic={len(generic)}',flush=True)
    global _PARENT; _PARENT=x
    payload=[]
    for oi,o in generic:
        y=np.delete(x,np.asarray(o,int),axis=0)
        pre_sig=defect_signature(y)
        pre={'all_six':bool(np.all(z[o]==6)),'min_core_distance':int(np.min(dist[o])),
             'raw_energy':raw_energy(y),'pre_signature':sig_json(pre_sig)}
        payload.append((oi,o,live,pre))
    rows=[]
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        futs=[ex.submit(relax_orbit,p) for p in payload]
        for n,f in enumerate(cf.as_completed(futs),1):
            r=f.result(); rows.append(r)
            print(f'RELAX {n}/{len(futs)} orbit={r["orbit_index"]} E={r["energy"]:.12f} d={r["delta_vs_live"]:+.7g} twins={r["signature"]["twin_count"]} all6={r["all_six"]} core={r["min_core_distance"]}',flush=True)
    low=dedup_low(rows,args.classify)
    print('LOW',[(r['orbit_index'],r['energy'],r['signature']['twin_count']) for r in low],flush=True)
    classes=[]
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        futs=[ex.submit(classify_child,(rank,r,args.hessian_k,args.fd_step)) for rank,r in enumerate(low)]
        for f in cf.as_completed(futs):
            c=f.result(); classes.append(c)
            print(f'CLASS rank={c["rank"]} E={c["energy"]:.12f} grad={c["gradient_rms"]:.3g} neg={c["negative_modes_among_k"]} lows={c["lowest_eigenvalues"][:5]}',flush=True)
    classes.sort(key=lambda c:c['rank'])
    portals=[c for c in classes if c['negative_modes_among_k']>0][:workers]
    releases=[]
    if portals:
        print(f'PORTALS {[(c["rank"],c["energy"],c["negative_modes_among_k"]) for c in portals]}',flush=True)
        with cf.ProcessPoolExecutor(max_workers=min(workers,len(portals))) as ex:
            futs=[ex.submit(release_portal,(c['rank'],c,live,args.fd_step)) for c in portals]
            for f in cf.as_completed(futs):
                rr=f.result(); releases.append(rr)
                best=min((r['energy'] for r in rr['release_rows']),default=float('inf'))
                print(f'RELEASE rank={rr["rank"]} best={best:.12f} d={best-live:+.7g}',flush=True)
    # Global best over direct children and portal releases.
    best_direct=min(rows,key=lambda r:r['energy']); best_E=best_direct['energy']; best_pts=best_direct['_points']
    best_source=f'orbit-{best_direct["orbit_index"]}'
    for rr in releases:
        for r in rr['release_rows']:
            if r['energy']<best_E:
                best_E=r['energy']; best_source=f'portal-r{rr["rank"]}-m{r["mode"]}-s{r["sign"]}-a{r["amp"]}'
                best_pts=np.asarray(r['points'],float) if r['points'] is not None else None
    def clean_row(r):
        return {k:v for k,v in r.items() if not k.startswith('_')}
    out={'live_score':live,'parent_n':N0,'target_n':NT,'workers':workers,'axis2_score':s2,'axis3_score':s3,
         'group_validation_max':worst,'group_validation_rms_max':rms,'orbit_size_hist':hist,
         'generic_orbit_count':len(generic),'all_relaxed':[clean_row(r) for r in sorted(rows,key=lambda q:q['energy'])],
         'classified':[clean_row(c) for c in classes],'portal_releases':releases,
         'best_float_energy':best_E,'best_delta_vs_live':best_E-live,'best_source':best_source,
         'best_points':best_pts.tolist() if best_pts is not None and best_E<live-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    print(f'BEST {best_E:.12f} delta={best_E-live:+.9g} source={best_source}',flush=True)

if __name__=='__main__': main()
