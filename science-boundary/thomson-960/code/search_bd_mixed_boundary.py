#!/usr/bin/env python3
"""Adaptive mixed positive-mode search around the certified B<->D saddle.

Single-mode probes show that positive Hessian modes 1,2,6 already expose all
four low minima A/B/D/R.  This script searches their *joint* 3-D coefficient
space rather than extending one-dimensional mode grids.

Stage 1: Sobol space-filling samples in (m1,m2,m6), fully relaxed.
Stage 2: Delaunay tetrahedra whose vertices relax to multiple basins are refined
         at centroids and selected heterogeneous edge midpoints.
Stage 3: small +/- reaction-coordinate biases are evaluated at the most
         heterogeneous boundary points.
Stage 4: the two lowest unknown minima (if any) are second-hopped along their
         own lowest modes before the runner is released.

The goal is not dense enumeration. It is active refinement of basin junctions in
a reaction-coordinate subspace already known to be multi-basin.
"""
from __future__ import annotations

import argparse, concurrent.futures as cf, json, math, os, pathlib
from collections import Counter
import numpy as np
from scipy.spatial import Delaunay
from scipy.stats import qmc

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import stable_relax_q
from search_saddle_transverse import load_refined
from search_learned_event_grammar import defect_signature

N=960
KNOWN={'R':444368.3924061973,'A':444368.395686226,'B':444368.4029728614,'D':444368.4109930845}


def sig_key(sig):
    return (tuple(sig['coord']),tuple(sig['components']),int(sig['twins']))


def sig_json(sig):
    return {'coord':[list(t) for t in sig['coord']],
            'components':[list(t) for t in sig['components']],
            'twins':int(sig['twins'])}


def known_label(e,tol=5e-6):
    for k,v in KNOWN.items():
        if abs(e-v)<=tol:return k
    return None


def make_start(q0,basis,reaction,coeff,reaction_amp=0.0):
    y=np.zeros_like(reaction)
    for c,v in zip(coeff,basis): y += float(c)*v
    y += float(reaction_amp)*reaction
    yn=float(np.linalg.norm(y))
    if yn<1e-15:return q0.copy()
    # coeffs are physical RMS amplitudes; eigenvectors have Euclidean norm 1.
    y*=math.sqrt(N)
    yn=float(np.linalg.norm(y)); return sp.exp_perturb(q0,y/yn,yn/math.sqrt(N))


def eval_point(payload):
    coeff,ra,q0,basis,reaction,live,maxiter=payload
    qs=make_start(q0,basis,reaction,coeff,ra); es,_=sm.fg(qs)
    e,raw,x,nit,ok,msg=stable_relax_q(qs,maxiter)
    sig=defect_signature(x)
    return {'coeff':[float(c) for c in coeff],'reaction_amp':float(ra),
            'start_energy':float(es),'energy':float(e),'raw_energy':float(raw),
            'delta_vs_live':float(e-live),'nit':int(nit),'success':bool(ok),'message':msg,
            'known_label':known_label(e),'signature':sig_json(sig),'_sig':sig_key(sig),'_points':x}


def assign_labels(rows):
    reps=[]
    for r in sorted(rows,key=lambda z:z['energy']):
        if r['known_label']:
            r['_label']=r['known_label'];continue
        found=None
        for j,q in enumerate(reps):
            if abs(r['energy']-q['energy'])<2e-7 and r['_sig']==q['_sig']:
                found=j;break
        if found is None:
            reps.append(r);found=len(reps)-1
        r['_label']=f'N{found}'
    return reps


def unique_coeffs(points,tol=1e-10):
    out=[]
    for p in points:
        p=np.asarray(p,float)
        if any(np.linalg.norm(p-q)<tol for q in out):continue
        out.append(p)
    return out


def second_hop(seedrow,live,maxiter=1800):
    x=np.asarray(seedrow['_points'],float);q=sm.xyz_to_vars(x)
    H,raw,Q,calls=sm.build_hessian(q,3e-6,1e6)
    from scipy.sparse.linalg import eigsh
    vals,V=eigsh(H,k=6,which='SA',tol=1e-5,maxiter=900,ncv=32);o=np.argsort(vals);vals=vals[o];V=V[:,o]
    for j in range(V.shape[1]):V[:,j]-=Q@(Q.T@V[:,j]);V[:,j]/=np.linalg.norm(V[:,j])
    rows=[]
    for mode in range(4):
        for sign in (-1,1):
            for amp in (0.004,0.009,0.018,0.032):
                qs=sp.exp_perturb(q,sign*V[:,mode],amp)
                e,rawE,z,nit,ok,msg=stable_relax_q(qs,maxiter)
                sig=defect_signature(z)
                rows.append({'mode':mode,'sign':sign,'amp':amp,'energy':float(e),'delta_vs_live':float(e-live),
                             'known_label':known_label(e),'signature':sig_json(sig),'nit':nit,'success':ok,
                             'points':z.tolist() if e<live-2e-7 else None})
    return {'parent_energy':seedrow['energy'],'parent_label':seedrow['_label'],
            'eigenvalues':[float(v) for v in vals],'rows':rows,
            'best_energy':min(r['energy'] for r in rows)}


def clean(r,keep_points=False):
    z={k:v for k,v in r.items() if not k.startswith('_')}
    if keep_points and '_points' in r:z['points']=r['_points'].tolist()
    return z


def main():
    ap=argparse.ArgumentParser();ap.add_argument('few_shots');ap.add_argument('refined_json');ap.add_argument('--out',required=True)
    ap.add_argument('--workers',type=int,default=1);ap.add_argument('--base',type=int,default=32)
    ap.add_argument('--scale',type=float,default=0.032);ap.add_argument('--radius-cap',type=float,default=0.050)
    ap.add_argument('--adaptive',type=int,default=20);ap.add_argument('--reaction-points',type=int,default=8)
    ap.add_argument('--reaction-amp',type=float,default=0.00015);ap.add_argument('--maxiter',type=int,default=1800)
    ap.add_argument('--seed',type=int,default=12606);args=ap.parse_args()
    workers=max(1,int(args.workers));root=pathlib.Path(args.few_shots);live,shot=sm.find_live(root)
    meta,x0,vecs,modes=load_refined(args.refined_json);q0=sm.xyz_to_vars(x0);Q=sm.rotation_basis(q0)
    reaction=vecs[:,0].copy();reaction-=Q@(Q.T@reaction);reaction/=np.linalg.norm(reaction)
    mids=(1,2,6);basis=[]
    for m in mids:
        v=vecs[:,m].copy();v-=Q@(Q.T@v);v-=reaction*float(reaction@v)
        for u in basis:v-=u*float(u@v)
        v/=np.linalg.norm(v);basis.append(v)
    print(f'live={live:.10f} workers={workers} modes={mids} lambdas={[modes[m]["eigenvalue"] for m in mids]}',flush=True)

    # Axial anchors plus Sobol interior samples.
    pts=[np.zeros(3)]
    for j in range(3):
        for a in (0.008,0.016,0.028,0.040):
            for s in (-1,1):
                p=np.zeros(3);p[j]=s*a;pts.append(p)
    sob=qmc.Sobol(d=3,scramble=True,seed=args.seed);u=sob.random_base2(int(math.ceil(math.log2(max(2,args.base)))))[:args.base]
    for p in (2*u-1)*args.scale:
        n=np.linalg.norm(p)
        if n>args.radius_cap:p=p*(args.radius_cap/n)
        pts.append(p)
    pts=unique_coeffs(pts)
    rows=[]
    def run_batch(points,ra=0.0):
        payload=[(p,ra,q0,basis,reaction,live,args.maxiter) for p in points]
        out=[]
        if workers==1:
            for i,p in enumerate(payload,1):
                r=eval_point(p);out.append(r);print(f'EVAL {i}/{len(payload)} c={np.round(r["coeff"],5).tolist()} ra={ra:+.1e} E={r["energy"]:.12f} known={r["known_label"]}',flush=True)
        else:
            with cf.ProcessPoolExecutor(max_workers=workers) as ex:
                for i,r in enumerate(ex.map(eval_point,payload,chunksize=1),1):
                    out.append(r);print(f'EVAL {i}/{len(payload)} c={np.round(r["coeff"],5).tolist()} ra={ra:+.1e} E={r["energy"]:.12f} known={r["known_label"]}',flush=True)
        return out
    rows+=run_batch(pts)
    reps=assign_labels(rows)

    # Delaunay adaptive refinement. Rank heterogeneous tetrahedra by number of
    # labels, then smaller diameter to focus on junctions rather than huge cells.
    X=np.array([r['coeff'] for r in rows if abs(r['reaction_amp'])<1e-16]); labs=[r['_label'] for r in rows if abs(r['reaction_amp'])<1e-16]
    tri=Delaunay(X,qhull_options='QJ');cand=[]
    for simplex in tri.simplices:
        ls={labs[int(i)] for i in simplex}
        if len(ls)<2:continue
        P=X[simplex];diam=max(np.linalg.norm(P[a]-P[b]) for a in range(4) for b in range(a))
        cen=np.mean(P,axis=0);cand.append((-len(ls),diam,cen,simplex,ls))
    cand.sort(key=lambda t:(t[0],t[1]))
    adapt=[]
    for _,diam,cen,simplex,ls in cand:
        adapt.append(cen)
        P=X[simplex]
        # one shortest heterogeneous edge midpoint from this simplex
        edges=[]
        for a in range(4):
            for b in range(a):
                ia,ib=int(simplex[a]),int(simplex[b])
                if labs[ia]!=labs[ib]:edges.append((np.linalg.norm(X[ia]-X[ib]),0.5*(X[ia]+X[ib])))
        if edges: adapt.append(min(edges,key=lambda t:t[0])[1])
        if len(unique_coeffs(adapt))>=args.adaptive:break
    adapt=unique_coeffs(adapt)[:args.adaptive]
    if adapt:
        print(f'ADAPT points={len(adapt)} hetero_simplices={len(cand)}',flush=True)
        rows+=run_batch(adapt);reps=assign_labels(rows)

    # Select zero-bias points nearest to heterogeneous neighbors for reaction bias.
    zero=[r for r in rows if abs(r['reaction_amp'])<1e-16]
    scores=[]
    for i,r in enumerate(zero):
        p=np.array(r['coeff']);neigh=sorted((np.linalg.norm(p-np.array(q['coeff'])),j) for j,q in enumerate(zero) if j!=i)[:6]
        nl={zero[j]['_label'] for _,j in neigh};nl.add(r['_label'])
        if len(nl)>=2:scores.append((-len(nl),neigh[0][0] if neigh else 9,i))
    scores.sort();picked=[]
    for _,_,i in scores:
        p=np.array(zero[i]['coeff'])
        if any(np.linalg.norm(p-q)<0.003 for q in picked):continue
        picked.append(p)
        if len(picked)>=args.reaction_points:break
    for ra in (-args.reaction_amp,args.reaction_amp):
        if picked:rows+=run_batch(picked,ra)
    reps=assign_labels(rows)

    # Unknown basin representatives sorted by energy; second-hop the two lowest
    # reasonably low ones. High basins are saved but not expanded automatically.
    unknown=[r for r in reps if not r.get('known_label')];unknown.sort(key=lambda r:r['energy'])
    second=[]
    for r in unknown[:2]:
        if r['energy']<=live+0.20:
            print(f'SECOND parent={r["_label"]} E={r["energy"]:.12f}',flush=True)
            second.append(second_hop(r,live,args.maxiter))

    allrows=sorted(rows,key=lambda r:r['energy']);best=allrows[0]
    # Retain coordinates for the lowest distinct unknown reps, and always for a candidate.
    top_unknown=[clean(r,keep_points=True) for r in unknown[:8]]
    out={'live_score':live,'live_shot':str(shot.relative_to(root)),'parent_saddle_energy':meta.get('final_energy'),
         'basis_modes':list(mids),'basis_eigenvalues':[modes[m]['eigenvalue'] for m in mids],
         'workers':workers,'base_count':len(pts),'adaptive_count':len(adapt),'reaction_boundary_count':len(picked),
         'evaluations':len(rows),'known_counts':dict(Counter(r['_label'] for r in rows if r['_label'] in KNOWN)),
         'unknown_basin_count':len(unknown),'top_unknown':top_unknown,'second_hop':second,
         'best_energy':best['energy'],'best_delta_vs_live':best['energy']-live,
         'best_label':best['_label'],'best_points':best['_points'].tolist() if best['energy']<live-2e-7 else None,
         'rows':[clean(r,keep_points=False) | {'basin_label':r['_label']} for r in rows]}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    print(f'FINAL evals={len(rows)} unknown={len(unknown)} best={best["energy"]:.12f} d={best["energy"]-live:+.9g} label={best["_label"]}',flush=True)
    print('TOP_UNKNOWN',[(r['_label'],r['energy'],r['coeff'],r['reaction_amp'],r['signature']['twins']) for r in unknown[:8]],flush=True)

if __name__=='__main__':main()
