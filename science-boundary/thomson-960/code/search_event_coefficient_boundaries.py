#!/usr/bin/env python3
"""Active search of the relaxed-basin map in learned event-coefficient space.

Coordinates are the three finite-amplitude lowering fields learned from actual
N=960 minima: A->R, B->A, and D->B, all rigidly aligned and parallel-transported
to the live record R.  For a coefficient vector c=(c_AR,c_BA,c_DB), the start is

    X(c) = Exp_R(c_AR f_AR + c_BA f_BA + c_DB f_DB).

The expensive oracle is not the Coulomb energy but *full relaxation* of X(c).
That oracle maps broad coefficient regions to discrete basins.  We therefore do
not refine a surrogate of the raw PES.  Instead:
  1. make a Sobol space-filling design in a bounded coefficient box;
  2. fully relax all points in parallel;
  3. Delaunay-tessellate coefficient space and identify simplices whose vertices
     relax to different basins;
  4. evaluate centroids of the most informative heterogeneous simplices;
  5. repeat, concentrating relaxations on basin boundaries / junctions.

Basin identity uses energy plus the full defect-component signature, with known
R/A/B/D energy anchors recognized explicitly.  Any credible below-record result
keeps its full points for exact-verifier follow-up.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import math
import os
import pathlib

import numpy as np
from scipy.spatial import Delaunay
from scipy.stats import qmc

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed
from search_learned_event_grammar import (
    cert_xyz, align_to_ref, logmap, expmap, parallel_transport, defect_signature,
    worker,
)

KNOWN = {
    'R': 444368.3924061973,
    'A': 444368.395686226,
    'B': 444368.4029728614,
    'D': 444368.4109930845,
}


def coeff_start(R, fields, c):
    v = c[0]*fields[0] + c[1]*fields[1] + c[2]*fields[2]
    return expmap(R, v)


def canonical_signature(r):
    return (tuple(tuple(x) for x in r['coord']),
            tuple(tuple(x) for x in r['components']), int(r['twin_count']))


def assign_labels(rows, tol_known=5e-6, tol_cluster=2e-7):
    """Assign deterministic relaxed-basin labels to evaluated coefficient points."""
    labels=[]; clusters=[]
    for r in rows:
        e=float(r['energy']); sig=canonical_signature(r)
        hit=None
        for name,ek in KNOWN.items():
            if abs(e-ek) <= tol_known:
                hit=name; break
        if hit is None:
            for j,(ej,sj) in enumerate(clusters):
                if sig==sj and abs(e-ej)<=tol_cluster:
                    hit=f'U{j:03d}'; break
        if hit is None:
            clusters.append((e,sig)); hit=f'U{len(clusters)-1:03d}'
        labels.append(hit)
    return labels, clusters


def normalized(X, lo, hi):
    return (X-lo)/(hi-lo)


def row_public(r):
    return {k:v for k,v in r.items() if k!='points'}


def relax_batch(coeffs, R, fields, live_score, workers, maxiter, prefix):
    payload=[]
    for i,c in enumerate(coeffs):
        start=coeff_start(R,fields,c)
        payload.append((f'{prefix}-{i:04d}',start,live_score,maxiter))
    out=[]
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        for c,r in zip(coeffs, ex.map(worker,payload,chunksize=1)):
            rr=dict(r); rr['coeff']=[float(x) for x in c]
            out.append(rr)
            print(f'{prefix} c={np.asarray(c).round(5).tolist()} E={r["energy"]:.12f} '
                  f'd={r["delta_vs_live"]:+.9g} twins={r["twin_count"]}', flush=True)
    return out


def candidate_centroids(rows, labels, lo, hi, nmax, seen, round_no):
    X=np.asarray([r['coeff'] for r in rows],float); Z=normalized(X,lo,hi)
    if len(X)<5:return []
    try: tri=Delaunay(Z, qhull_options='QJ Qbb Qc')
    except Exception as e:
        print(f'Delaunay failed: {e}',flush=True); return []
    cand=[]
    for simplex in tri.simplices:
        labs=[labels[i] for i in simplex]; distinct=set(labs)
        if len(distinct)<2:continue
        pts=Z[simplex]; centroid=np.mean(pts,axis=0)
        c=lo+centroid*(hi-lo)
        key=tuple(np.round(c,10))
        if key in seen:continue
        energies=[rows[i]['energy'] for i in simplex]
        unknown=sum(1 for q in distinct if q.startswith('U'))
        diameter=max(float(np.linalg.norm(pts[a]-pts[b])) for a in range(4) for b in range(a))
        # Prefer 3/4-basin junctions, then unknown-basin interfaces, then low
        # energy boundaries.  A small diameter bonus prevents repeatedly picking
        # enormous uninformative hull simplices.
        diversity=len(distinct)
        low=min(energies)
        score=(20.0*diversity + 8.0*unknown - 200.0*(low-KNOWN['R']) - 1.5*diameter)
        cand.append((score,c,{'labels':sorted(distinct),'min_energy':low,'diameter':diameter,
                              'simplex':[int(i) for i in simplex],'round':round_no}))
    cand.sort(key=lambda t:t[0],reverse=True)
    chosen=[]
    for score,c,meta in cand:
        z=normalized(np.asarray(c),lo,hi)
        if any(np.linalg.norm(z-normalized(np.asarray(q[0]),lo,hi))<0.025 for q in chosen):continue
        chosen.append((c,meta,score))
        if len(chosen)>=nmax:break
    return chosen


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots')
    ap.add_argument('--a',required=True); ap.add_argument('--b',required=True); ap.add_argument('--d',required=True)
    ap.add_argument('--outdir',required=True); ap.add_argument('--workers',type=int,default=0)
    ap.add_argument('--initial',type=int,default=64); ap.add_argument('--rounds',type=int,default=4)
    ap.add_argument('--per-round',type=int,default=40); ap.add_argument('--maxiter',type=int,default=2200)
    ap.add_argument('--lo',default='-0.75,-1.25,-1.0'); ap.add_argument('--hi',default='2.5,1.5,1.25')
    args=ap.parse_args(); outdir=pathlib.Path(args.outdir);outdir.mkdir(parents=True,exist_ok=True)
    root=pathlib.Path(args.few_shots); live_score,live_dir=sm.find_live(root); R=cert_xyz(live_dir/'certificate.json')
    _,A0=load_seed(args.a);_,B0=load_seed(args.b);_,D0=load_seed(args.d)
    A,_,ar=align_to_ref(A0,R); B,_,br=align_to_ref(B0,R); D,_,dr=align_to_ref(D0,R)
    fields=[parallel_transport(A,R,logmap(A,R)),
            parallel_transport(B,R,logmap(B,A)),
            parallel_transport(D,R,logmap(D,B))]
    lo=np.array([float(x) for x in args.lo.split(',')]); hi=np.array([float(x) for x in args.hi.split(',')])
    if not (len(lo)==len(hi)==3 and np.all(hi>lo)):raise ValueError('need 3D lo/hi with hi>lo')
    ncpu=os.cpu_count() or 2; workers=max(1,min(args.workers or ncpu,ncpu,4))
    print(f'cpus={ncpu} workers={workers} live={live_score:.12f} align={ar,br,dr}',flush=True)
    print('field_rms',[float(np.sqrt(np.mean(np.sum(v*v,axis=1)))) for v in fields],flush=True)

    sob=qmc.Sobol(d=3,scramble=True,seed=9602026)
    m=int(math.ceil(math.log2(max(1,args.initial)))); U=sob.random_base2(m)[:args.initial]
    coeffs=[lo+u*(hi-lo) for u in U]
    # Always include the origin and physically interpretable axis anchors.
    anchors=[np.zeros(3),np.array([0.5,0,0]),np.array([1,0,0]),np.array([1.5,0,0]),
             np.array([0,0.5,0]),np.array([0,1,0]),np.array([0,0,0.5]),np.array([0,0,1]),
             np.array([1,0.5,0]),np.array([1,0.5,0.25])]
    for c in anchors:
        if np.all(c>=lo) and np.all(c<=hi):coeffs.append(c)
    # exact coefficient dedup
    uniq=[]; seen=set()
    for c in coeffs:
        k=tuple(np.round(c,12))
        if k not in seen:seen.add(k);uniq.append(np.asarray(c,float))
    rows=relax_batch(uniq,R,fields,live_score,workers,args.maxiter,'seed')
    provenance=[{'coeff':r['coeff'],'kind':'seed'} for r in rows]

    for rd in range(args.rounds):
        labels,clusters=assign_labels(rows)
        seen_coeff={tuple(np.round(np.asarray(r['coeff']),10)) for r in rows}
        cand=candidate_centroids(rows,labels,lo,hi,args.per_round,seen_coeff,rd)
        if not cand:
            print(f'round={rd} no heterogeneous simplices left',flush=True); break
        C=[x[0] for x in cand]
        print(f'round={rd} candidates={len(C)} best_meta={cand[0][1]} score={cand[0][2]:.3g}',flush=True)
        new=relax_batch(C,R,fields,live_score,workers,args.maxiter,f'r{rd}')
        for r,(_,meta,score) in zip(new,cand):
            provenance.append({'coeff':r['coeff'],'kind':'boundary-centroid','round':rd,'source':meta,'score':score})
        rows.extend(new)
        if min(r['energy'] for r in new) < live_score-2e-7:
            print('credible floating below-record result; stopping adaptive rounds for verification',flush=True);break

    labels,clusters=assign_labels(rows)
    for r,l in zip(rows,labels):r['basin_label']=l
    order=np.argsort([r['energy'] for r in rows]); best=rows[int(order[0])]
    # Basin inventory.
    inv={}
    for r in rows:
        q=inv.setdefault(r['basin_label'],{'count':0,'best_energy':float('inf'),'best_coeff':None,'signature':None})
        q['count']+=1
        if r['energy']<q['best_energy']:
            q['best_energy']=r['energy'];q['best_coeff']=r['coeff'];q['signature']={'coord':r['coord'],'components':r['components'],'twin_count':r['twin_count']}
    # Keep full coordinates for the eight lowest distinct relaxed energies.
    top=[]; used=[]
    for i in order:
        r=rows[int(i)]
        if any(abs(r['energy']-e)<2e-7 for e in used):continue
        used.append(r['energy']); top.append({'name':r['name'],'basin_label':r['basin_label'],'energy':r['energy'],
             'coeff':r['coeff'],'coord':r['coord'],'components':r['components'],'twin_count':r['twin_count'],'points':r['points']})
        if len(top)>=8:break
    compact=[row_public(r) for r in rows]
    out={'live_score':live_score,'live_shot':str(live_dir.relative_to(root)),'lo':lo.tolist(),'hi':hi.tolist(),
         'alignment_rms':{'A':ar,'B':br,'D':dr},'evaluations':len(rows),'rows':compact,'provenance':provenance,
         'basin_inventory':inv,'top_states':top,'best_name':best['name'],'best_energy':best['energy'],
         'best_delta_vs_live':best['delta_vs_live'],'best_coeff':best['coeff'],
         'best_points':best['points'] if best['energy']<live_score-2e-7 else None}
    (outdir/'active-event-boundaries.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
    print('BASINS',json.dumps(inv,sort_keys=True),flush=True)
    print(f'BEST {best["name"]} {best["energy"]:.12f} d={best["delta_vs_live"]:+.12g} c={best["coeff"]}',flush=True)

if __name__=='__main__':main()
