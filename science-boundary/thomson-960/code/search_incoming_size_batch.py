#!/usr/bin/env python3
"""Batched incoming neighboring-size propagation into N=960.

Previous size-beam campaigns started from the N=960 record and moved outward.
This search reverses the interface: start from public low-energy configurations
at nearby N and propagate each *into* N=960. Each source is tried with two
selection policies:

  energy  - ordinary Amore-Wales-style low-energy beam;
  motif   - prefer moves in sixfold bulk and descendants that preserve the
            source's non-sixfold defect-component organization / 7-7 pattern.

All independent source/policy paths run as single-threaded worker processes on
one Actions runner. BLAS thread limiting belongs in the workflow.
"""
from __future__ import annotations

import argparse, concurrent.futures as cf, json, os, pathlib
from collections import Counter
import numpy as np
from scipy.spatial import ConvexHull

import search_size_beam as sb
from analyze_twinned_motif import load_xyz
from search_learned_event_grammar import defect_signature

TARGET=960


def sig_compact(x):
    s=defect_signature(x)
    return {'coord':[[int(a),int(b)] for a,b in s['coord']],
            'components':[list(map(int,t)) for t in s['components']],
            'twins':int(s['twins'])}


def sig_distance(a,b):
    """Topology-weighted distance ignoring the changing sixfold population."""
    ca={int(k):int(v) for k,v in a['coord']}; cb={int(k):int(v) for k,v in b['coord']}
    degs=(set(ca)|set(cb))-{6}
    dcoord=sum(abs(ca.get(k,0)-cb.get(k,0)) for k in degs)
    A=Counter(tuple(t) for t in a['components']); B=Counter(tuple(t) for t in b['components'])
    dcomp=sum(abs(A[k]-B[k]) for k in set(A)|set(B))
    return 4*dcoord + 3*dcomp + 2*abs(a['twins']-b['twins'])


def topo(x):
    h=ConvexHull(x); n=len(x); nb=[set() for _ in range(n)]
    for tri in h.simplices:
        a,b,c=map(int,tri)
        for u,v in ((a,b),(b,c),(c,a)):
            nb[u].add(v); nb[v].add(u)
    z=np.array([len(q) for q in nb],int)
    return h,nb,z


def defect_distance(nb,z):
    inf=10**9; d=np.full(len(z),inf,int); q=list(map(int,np.flatnonzero(z!=6)))
    for v in q:d[v]=0
    head=0
    while head<len(q):
        u=q[head]; head+=1
        for v in nb[u]:
            if d[v]>d[u]+1:d[v]=d[u]+1;q.append(v)
    return d


def insert_sites_filtered(x, motif):
    h,nb,z=topo(x); dist=defect_distance(nb,z); sites=[]; vals=[]; facets=[]
    for tri in h.simplices:
        ids=list(map(int,tri))
        if motif and (not all(z[v]==6 for v in ids) or min(dist[v] for v in ids)<1):continue
        a,b,c=x[ids]; n=np.cross(b-a,c-a); nn=np.linalg.norm(n)
        if nn<1e-14:continue
        n/=nn
        if float(n@a)<0:n=-n
        sites.append(n);facets.append(ids)
    if not sites:return np.empty((0,3)),np.empty(0),[]
    y=np.asarray(sites); p=np.empty(len(y))
    for lo in range(0,len(y),300):
        q=y[lo:lo+300]; dots=np.clip(q@x.T,-1,1)
        p[lo:lo+len(q)]=np.sum(1/np.sqrt(np.maximum(2-2*dots,1e-15)),axis=1)
    return y,p,facets


def branch(state, move, count, motif, tag):
    E,x,hist=state; out=[]
    if move=='remove':
        h,nb,z=topo(x); dist=defect_distance(nb,z); c=sb.energy_contrib(x)
        if motif:
            allowed=np.array([i for i in range(len(x)) if z[i]==6 and dist[i]>=1],int)
        else: allowed=np.arange(len(x),dtype=int)
        if not len(allowed):return []
        ids=allowed[np.argsort(c[allowed])[-count:][::-1]]
        for rank,j in enumerate(ids):
            y=np.delete(x,int(j),axis=0); e,q,nit,ok=sb.stable_relax(y,1400); s=sig_compact(q)
            step={'move':'remove','rank':rank,'index':int(j),'pre_contribution':float(c[j]),'n':len(q),'energy':e,'signature':s}
            print(f'{tag} REM r={rank} n={len(q)} E={e:.12f} twins={s["twins"]} nit={nit}',flush=True)
            out.append((e,q,hist+[step]))
    else:
        sites,p,facets=insert_sites_filtered(x,motif)
        if not len(sites):return []
        ids=np.argsort(p)[:count]
        for rank,j in enumerate(ids):
            y=np.vstack([x,sites[int(j)]]); e,q,nit,ok=sb.stable_relax(y,1400); s=sig_compact(q)
            step={'move':'insert','rank':rank,'site':int(j),'facet':facets[int(j)],'pre_potential':float(p[int(j)]),'n':len(q),'energy':e,'signature':s}
            print(f'{tag} INS r={rank} n={len(q)} E={e:.12f} twins={s["twins"]} nit={nit}',flush=True)
            out.append((e,q,hist+[step]))
    return out


def keep(states, beam, source_sig, policy, tol=2e-7):
    rows=[]
    for s in states:
        sg=sig_compact(s[1]); sd=sig_distance(sg,source_sig)
        rows.append((sd,s[0],s,sg))
    rows.sort(key=(lambda t:(t[1],t[0])) if policy=='energy' else (lambda t:(t[0],t[1])))
    ans=[]
    for sd,E,s,sg in rows:
        if any(abs(E-q[0])<=tol and sig_compact(q[1])==sg for q in ans):continue
        ans.append(s)
        if len(ans)>=beam:break
    return ans


def run_one(payload):
    path,policy,live,branch_n,beam_n=payload
    x=load_xyz(path); n0=len(x); e0,x,nit,ok=sb.stable_relax(x,1000); source_sig=sig_compact(x)
    move='insert' if n0<TARGET else 'remove'; steps=abs(TARGET-n0); beam=[(e0,x,[])]
    print(f'START n={n0} policy={policy} E={e0:.12f} twins={source_sig["twins"]} steps={steps}',flush=True)
    for step in range(steps):
        cand=[]
        for bi,s in enumerate(beam):cand+=branch(s,move,branch_n,policy=='motif',f'N{n0}/{policy}/s{step+1}/b{bi}')
        if not cand:return {'source_n':n0,'policy':policy,'status':'no_candidates','source_energy':e0,'source_signature':source_sig}
        beam=keep(cand,beam_n,source_sig,policy)
        print(f'KEEP N{n0}/{policy} step={step+1} '+str([(len(s[1]),s[0],sig_compact(s[1])["twins"]) for s in beam]),flush=True)
    finals=sorted(beam,key=lambda s:s[0]); best=finals[0]; E,q,hist=best; sg=sig_compact(q)
    return {'source_n':n0,'policy':policy,'status':'ok','source_energy':e0,'source_signature':source_sig,
            'best_float_energy':E,'delta_vs_live':E-live,'best_signature':sg,'history':hist,
            'finals':[{'energy':s[0],'signature':sig_compact(s[1]),'history':s[2]} for s in finals],
            'best_points':q.tolist() if E<live-2e-7 else None}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('xyz_dir');ap.add_argument('few_shots')
    ap.add_argument('--workers',type=int,default=0);ap.add_argument('--branch',type=int,default=3);ap.add_argument('--beam',type=int,default=2);ap.add_argument('--out',required=True)
    args=ap.parse_args();workers=min(args.workers or (os.cpu_count() or 1),os.cpu_count() or 1,4)
    root=pathlib.Path(args.few_shots);live,_=sb.find_live(root); files=[]
    for p in sorted(pathlib.Path(args.xyz_dir).glob('*.xyz')):
        try:n=len(load_xyz(p))
        except Exception:continue
        if n!=TARGET:files.append((n,p))
    payload=[]
    for n,p in files:
        for policy in ('energy','motif'):payload.append((str(p),policy,live,args.branch,args.beam))
    print(f'CPUS={os.cpu_count()} workers={workers} parents={[n for n,_ in files]} tasks={len(payload)} live={live}',flush=True)
    rows=[]
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        futs=[ex.submit(run_one,p) for p in payload]
        for i,f in enumerate(cf.as_completed(futs),1):
            try:r=f.result()
            except Exception as e:r={'status':'error','error':repr(e)}
            rows.append(r);print('DONE',i,'/',len(futs),r.get('source_n'),r.get('policy'),r.get('status'),r.get('best_float_energy'),r.get('delta_vs_live'),flush=True)
    good=[r for r in rows if r.get('status')=='ok'];good.sort(key=lambda r:r['best_float_energy'])
    best=good[0] if good else None
    out={'live_score':live,'workers':workers,'branch':args.branch,'beam':args.beam,'parents':[n for n,_ in files],'results':rows,
         'best_float_energy':best['best_float_energy'] if best else None,'best_delta_vs_live':best['delta_vs_live'] if best else None,
         'best_source_n':best['source_n'] if best else None,'best_policy':best['policy'] if best else None,
         'best_points':best['best_points'] if best and best.get('best_points') is not None else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best:print(f'BEST N{best["source_n"]} {best["policy"]} E={best["best_float_energy"]:.12f} d={best["delta_vs_live"]:+.9g} twins={best["best_signature"]["twins"]}',flush=True)

if __name__=='__main__':main()
