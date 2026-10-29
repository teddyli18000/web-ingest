#!/usr/bin/env python3
"""Search beyond the N=960 record using learned finite-amplitude defect events.

The low-energy sequence D -> B -> A -> R supplies three *nonlinear secant
fields* learned from actual relaxed configurations, rather than infinitesimal
Hessian eigenvectors.  After rigidly aligning the saved states to the live C3
record, each pointwise spherical log field is parallel-transported to R.  C3
copies are generated with the record's exact 120-degree point permutation.

Stage 1 explores extrapolation through R using:
  - single learned lowering fields;
  - sequential/simultaneous C3-copy compositions;
  - cross-edge secant combinations and first/second finite differences.
Every start receives full unconstrained stable long-double-difference L-BFGS.

Stage 2 takes the best distinct non-record minima from Stage 1 and applies a
small event palette again, allowing a learned event grammar to leave the known
R/A/B/D chain without another Actions queue round trip.

One Actions runner is saturated with independent single-threaded worker
processes.  Endpoints are classified by spherical Delaunay defect-component
signature; any floating candidate below live_score-2e-7 persists its points for
immediate exact-verifier follow-up.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import math
import os
import pathlib
from dataclasses import dataclass

import numpy as np
from scipy.spatial import ConvexHull, cKDTree

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed, stable_relax_q

N=960
TWOPI=2*math.pi


def cert_xyz(path: pathlib.Path) -> np.ndarray:
    d=json.loads(path.read_text())
    x=np.array([[a/q,b/q,c/q] for a,b,c,q in d['points']],float)
    return x/np.linalg.norm(x,axis=1)[:,None]


def align_to_ref(x,ref):
    """Proper Kabsch rotation for row-vector coordinates with fixed labels."""
    H=x.T@ref; U,s,Vt=np.linalg.svd(H); Q=U@Vt
    if np.linalg.det(Q)<0:
        U[:,-1]*=-1; Q=U@Vt
    y=x@Q
    rms=float(np.sqrt(np.mean(np.sum((y-ref)**2,axis=1))))
    return y,Q,rms


def logmap(p,q):
    d=np.clip(np.sum(p*q,axis=1),-1,1); th=np.arccos(d)
    w=q-d[:,None]*p; nw=np.linalg.norm(w,axis=1); v=np.zeros_like(p); m=nw>1e-14
    v[m]=w[m]*(th[m]/nw[m])[:,None]
    return v


def expmap(p,v):
    a=np.linalg.norm(v,axis=1); q=np.empty_like(p); m=a>1e-14
    q[~m]=p[~m]
    q[m]=np.cos(a[m,None])*p[m]+np.sin(a[m,None])*v[m]/a[m,None]
    return q/np.linalg.norm(q,axis=1)[:,None]


def parallel_transport(p,q,v):
    """Exact shortest-geodesic parallel transport on S^2, pointwise."""
    den=1.0+np.sum(p*q,axis=1); den=np.maximum(den,1e-10)
    c=np.sum(v*q,axis=1)/den
    z=v-c[:,None]*(p+q)
    z-=np.sum(z*q,axis=1)[:,None]*q
    return z


def field_rms(v): return float(np.sqrt(np.mean(np.sum(v*v,axis=1))))


def c3_permutation(ref):
    a=TWOPI/3; c,s=math.cos(a),math.sin(a)
    M=np.array([[c,-s,0.],[s,c,0.],[0.,0.,1.]])
    rot=ref@M.T; tree=cKDTree(ref); d,p=tree.query(rot,k=1)
    if len(set(map(int,p)))!=N or float(np.max(d))>2e-6:
        raise RuntimeError(f'could not recover C3 permutation: unique={len(set(map(int,p)))} max={np.max(d)}')
    return M,np.asarray(p,int),float(np.sqrt(np.mean(d*d))),float(np.max(d))


def copy_field(v,M,perm,k):
    if k%3==0:return v.copy()
    out=v.copy(); cur=np.arange(N)
    R=np.eye(3)
    for _ in range(k%3):
        R=M@R; cur=perm[cur]
    out2=np.zeros_like(v); out2[cur]=v@R.T
    return out2


def apply_sim(base,terms):
    v=np.zeros_like(base)
    for field,coef in terms:v+=coef*field
    return expmap(base,v)


def apply_seq(base,ref,terms):
    x=base.copy()
    for field,coef in terms:
        vt=parallel_transport(ref,x,coef*field)
        x=expmap(x,vt)
    return x


def defect_signature(x):
    h=ConvexHull(x); nb=[set() for _ in range(N)]; edges=set()
    for tri in h.simplices:
        a,b,c=map(int,tri)
        for u,v in ((a,b),(b,c),(c,a)):
            if u>v:u,v=v,u
            edges.add((u,v)); nb[u].add(v); nb[v].add(u)
    z=np.array([len(s) for s in nb],int)
    defects=set(np.flatnonzero(z!=6)); adj={v:set() for v in defects}
    for a,b in edges:
        if a in defects and b in defects:adj[a].add(b);adj[b].add(a)
    comps=[]; unseen=set(defects)
    while unseen:
        r=unseen.pop(); comp={r}; st=[r]
        while st:
            u=st.pop()
            for v in adj[u]:
                if v in unseen:unseen.remove(v);comp.add(v);st.append(v)
        verts=sorted(comp); c5=sum(z[v]==5 for v in verts); c7=sum(z[v]==7 for v in verts)
        e77=sum(1 for a,b in edges if a in comp and b in comp and z[a]==7 and z[b]==7)
        comps.append((len(verts),int(c5),int(c7),int(e77)))
    comps.sort()
    e77all=sorted((a,b) for a,b in edges if z[a]==7 and z[b]==7)
    coord=tuple((int(k),int(np.sum(z==k))) for k in sorted(set(map(int,z))))
    return {'coord':coord,'components':tuple(comps),'twins':len(e77all),'e77':e77all}


def sig_key(sig):
    return (sig['coord'],sig['components'],sig['twins'])


def worker(payload):
    name,start,live_score,maxiter=payload
    q=sm.xyz_to_vars(start); es,_=sm.fg(q)
    e,raw,x,nit,ok,msg=stable_relax_q(q,maxiter)
    sig=defect_signature(x)
    return {'name':name,'start_energy':float(es),'energy':float(e),'raw_absolute_energy':float(raw),
            'delta_vs_live':float(e-live_score),'nit':nit,'success':ok,'message':msg,
            'coord':[[a,b] for a,b in sig['coord']],
            'components':[list(t) for t in sig['components']], 'twin_count':sig['twins'],
            'e77':[list(t) for t in sig['e77']], 'points':x.tolist()}


def generate_stage1(R,fields):
    specs=[]
    def add(name,x):specs.append((name,x))
    scales=(0.35,0.55,0.75,0.95,1.15,1.40,1.75)
    # Single-copy extrapolations. C3 images are symmetry-equivalent at exact R,
    # so only copy 0 is needed here.
    for key in ('AR','BA','DB'):
        for s in scales:add(f'{key}-single-{s:g}',apply_sim(R,[(fields[key][0],s)]))
    # Same-event C3 compositions: pair breaks C3, triple restores it.
    for key in ('AR','BA','DB'):
        for s in (0.40,0.60,0.80,1.00,1.20):
            add(f'{key}-pair-sim-{s:g}',apply_sim(R,[(fields[key][0],s),(fields[key][1],s)]))
            add(f'{key}-pair-seq-{s:g}',apply_seq(R,R,[(fields[key][0],s),(fields[key][1],s)]))
        for s in (0.35,0.55,0.75,0.95):
            add(f'{key}-triple-sim-{s:g}',apply_sim(R,[(fields[key][k],s) for k in range(3)]))
            add(f'{key}-triple-seq-{s:g}',apply_seq(R,R,[(fields[key][k],s) for k in range(3)]))
    # Cross-edge lowering directions and finite-difference extrapolation of the
    # sequence D->B->A->R.  Fields have their native finite amplitudes.
    fAR,fBA,fDB=fields['AR'][0],fields['BA'][0],fields['DB'][0]
    combos={
      'AR+BA':[(fAR,1),(fBA,0.6)],
      'AR+DB':[(fAR,1),(fDB,0.5)],
      'AR+BA+DB':[(fAR,1),(fBA,0.5),(fDB,0.3)],
      'trend1':[(fAR,1.5),(fBA,-0.5)],
      'trend2':[(fAR,2.0),(fBA,-1.0)],
      'curvature1':[(fAR,1.5),(fBA,-0.75),(fDB,0.25)],
      'curvature2':[(fAR,2.0),(fBA,-1.5),(fDB,0.5)],
    }
    for nm,terms in combos.items():
        for s in (0.55,0.80,1.00,1.25):
            add(f'cross-{nm}-{s:g}',apply_sim(R,[(v,s*c) for v,c in terms]))
    # Mixed C3 copies of the strongest near-record AR field.
    for a,b in ((1.0,-0.5),(1.0,0.5),(1.0,1.0),(1.25,-0.75),(1.25,0.5)):
        for s in (0.6,0.9,1.2):
            add(f'AR-mix01-{a:g}-{b:g}-{s:g}',apply_sim(R,[(fields['AR'][0],s*a),(fields['AR'][1],s*b)]))
    return specs


def generate_stage2(base,ref,fields,parent_name):
    specs=[]
    palette=[
      ('AR0',[(fields['AR'][0],0.55)]),('AR0x',[(fields['AR'][0],1.0)]),
      ('AR01',[(fields['AR'][0],0.55),(fields['AR'][1],0.55)]),
      ('BA0',[(fields['BA'][0],0.55)]),('DB0',[(fields['DB'][0],0.45)]),
      ('trend',[(fields['AR'][0],0.9),(fields['BA'][0],-0.3)]),
    ]
    for nm,terms in palette:
        specs.append((f'{parent_name}-hop-{nm}',apply_seq(base,ref,terms)))
    return specs


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots'); ap.add_argument('--a',required=True); ap.add_argument('--b',required=True); ap.add_argument('--d',required=True)
    ap.add_argument('--outdir',required=True); ap.add_argument('--workers',type=int,default=0)
    ap.add_argument('--stage1-maxiter',type=int,default=2200); ap.add_argument('--stage2-maxiter',type=int,default=2400)
    args=ap.parse_args(); root=pathlib.Path(args.few_shots); outdir=pathlib.Path(args.outdir);outdir.mkdir(parents=True,exist_ok=True)
    live_score,live_dir=sm.find_live(root); R=cert_xyz(live_dir/'certificate.json')
    _,A=load_seed(args.a);_,B=load_seed(args.b);_,D=load_seed(args.d)
    aligned={}; alignmeta={}
    for nm,x in [('A',A),('B',B),('D',D)]:
        y,Q,r=align_to_ref(x,R);aligned[nm]=y;alignmeta[nm]=r
    A,B,D=aligned['A'],aligned['B'],aligned['D']
    M,perm,c3rms,c3max=c3_permutation(R)
    # Native lowering events, transported to R so they form a common tangent basis.
    native={
      'AR':parallel_transport(A,R,logmap(A,R)),
      'BA':parallel_transport(B,R,logmap(B,A)),
      'DB':parallel_transport(D,R,logmap(D,B)),
    }
    fields={k:[copy_field(v,M,perm,j) for j in range(3)] for k,v in native.items()}
    names=list(native); gram=np.array([[np.sum(native[a]*native[b])/N for b in names] for a in names])
    R_sig=defect_signature(R)
    print('LIVE',live_score,'coord',R_sig['coord'],'twins',R_sig['twins'],'components',R_sig['components'],flush=True)
    print('align_rms',alignmeta,'c3_rms',c3rms,'c3_max',c3max,flush=True)
    print('field_rms',{k:field_rms(v) for k,v in native.items()},flush=True)
    print('field_gram',gram.tolist(),flush=True)
    ncpu=os.cpu_count() or 2; workers=max(1,min(args.workers or ncpu,ncpu,4)); print('cpus',ncpu,'workers',workers,flush=True)

    stage1=generate_stage1(R,fields)
    payload=[(nm,x,live_score,args.stage1_maxiter) for nm,x in stage1]
    rows=[]
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        for r in ex.map(worker,payload,chunksize=1):
            rows.append(r); print(f'S1 {r["name"]} E={r["energy"]:.12f} d={r["delta_vs_live"]:+.9g} twins={r["twin_count"]} coord={r["coord"]}',flush=True)
    # Deduplicate relaxed endpoints by energy plus coarse defect signature; keep
    # R-like numerical returns separate only if energy differs materially.
    rows.sort(key=lambda r:r['energy']); distinct=[]
    for r in rows:
        key=(tuple(map(tuple,r['coord'])),tuple(map(tuple,r['components'])),r['twin_count'])
        if any(abs(r['energy']-q['energy'])<2e-7 and key==q['_key'] for q in distinct):continue
        rr=dict(r);rr['_key']=key;distinct.append(rr)
    print('STAGE1_DISTINCT',[(q['name'],q['energy'],q['delta_vs_live'],q['twin_count']) for q in distinct[:12]],flush=True)

    # Second hop from the best distinct endpoints that are not simple R returns.
    parents=[]
    for q in distinct:
        if abs(q['energy']-live_score)<5e-6:continue
        parents.append(q)
        if len(parents)>=4:break
    s2=[]
    for q in parents:
        base=np.asarray(q['points'],float); s2.extend(generate_stage2(base,R,fields,q['name']))
    rows2=[]
    if s2:
        with cf.ProcessPoolExecutor(max_workers=workers) as ex:
            for r in ex.map(worker,[(nm,x,live_score,args.stage2_maxiter) for nm,x in s2],chunksize=1):
                rows2.append(r); print(f'S2 {r["name"]} E={r["energy"]:.12f} d={r["delta_vs_live"]:+.9g} twins={r["twin_count"]}',flush=True)
    allrows=rows+rows2; allrows.sort(key=lambda r:r['energy']); best=allrows[0]
    # Keep full points only for a credible near/below-record endpoint or top few
    # distinct states; strip the rest to keep artifact size reasonable.
    best_points=best['points'] if best['energy']<live_score-2e-7 else None
    compact=[]
    for r in allrows:
        z={k:v for k,v in r.items() if k!='points'};compact.append(z)
    top_states=[]
    seen=[]
    for r in allrows:
        if any(abs(r['energy']-e)<2e-7 for e in seen):continue
        seen.append(r['energy']);top_states.append({'name':r['name'],'energy':r['energy'],'points':r['points'],'twin_count':r['twin_count'],'coord':r['coord'],'components':r['components']})
        if len(top_states)>=8:break
    out={'live_score':live_score,'live_shot':str(live_dir.relative_to(root)),'live_signature':{'coord':[list(t) for t in R_sig['coord']],
         'components':[list(t) for t in R_sig['components']],'twin_count':R_sig['twins'],'e77':[list(t) for t in R_sig['e77']]},
         'alignment_rms':alignmeta,'c3_rms':c3rms,'c3_max':c3max,'field_names':names,
         'field_rms':{k:field_rms(v) for k,v in native.items()},'field_gram_per_point':gram.tolist(),
         'stage1_count':len(rows),'stage2_count':len(rows2),'rows':compact,'top_states':top_states,
         'best_energy':best['energy'],'best_delta_vs_live':best['delta_vs_live'],'best_name':best['name'],'best_points':best_points}
    (outdir/'event-grammar.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
    print(f'BEST {best["name"]} E={best["energy"]:.12f} d={best["delta_vs_live"]:+.12g}',flush=True)

if __name__=='__main__':main()
