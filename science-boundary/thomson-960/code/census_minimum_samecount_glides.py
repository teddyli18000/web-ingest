#!/usr/bin/env python3
"""Census soft same-count Delaunay glide interfaces around an arbitrary minimum.

Enumerates every legal one-flip move that preserves the coordination-count
multiset, ranks by exact balanced crossing threshold, then for the softest N
moves crosses just beyond the boundary, globally adapts with the four quad
vertices fixed, and finally fully releases.  Designed to seed dynamic scar-walk
search from minima other than the live record (notably A).
"""
from __future__ import annotations
import argparse,json,pathlib,collections,math

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed,stable_relax_q
from search_e564_defect_flip_parallel import topology,threshold,perturb
from search_e564_scaffolded_flip import fixed_relax


def edge(a,b): return (min(int(a),int(b)),max(int(a),int(b)))

def counts(x):
    d,_=topology(x); c=collections.Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}

def legal_rows(x):
    deg,ef=topology(x); edges=set(ef); base=collections.Counter(deg.tolist()); rows=[]
    for (u,v),opp in ef.items():
        if len(opp)!=2: continue
        a,b=opp; add=edge(a,b); delete=edge(u,v)
        if add in edges: continue
        nd=deg.copy(); nd[u]-=1; nd[v]-=1; nd[a]+=1; nd[b]+=1
        if collections.Counter(nd.tolist())!=base: continue
        q=(int(u),int(v),int(a),int(b)); t=threshold(x,q,'balanced')
        if t is None or not math.isfinite(t): continue
        rows.append({'quad':q,'delete':delete,'add':add,'threshold':float(t)})
    rows.sort(key=lambda r:(r['threshold'],r['quad']))
    return rows

def classify(e,live):
    refs={'R':live,'A':444368.3956862258,'B':444368.4029728613,'D':444368.41099308443,'e432':444368.4322496275}
    n,err=min(((n,abs(e-v)) for n,v in refs.items()),key=lambda z:z[1])
    return n if err<2e-6 else 'novel'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json'); ap.add_argument('--tag',default='seed')
    ap.add_argument('--top',type=int,default=15); ap.add_argument('--multiplier',type=float,default=1.003)
    ap.add_argument('--fixed-maxiter',type=int,default=1600); ap.add_argument('--release-maxiter',type=int,default=3200)
    ap.add_argument('--live-score',type=float,required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x=load_seed(args.seed_json); E0,_=sm.fg(sm.xyz_to_vars(x)); cc0=counts(x)
    rows=legal_rows(x); print('SEED',args.tag,f'{E0:.12f}','cc',cc0,'LEGAL',len(rows),flush=True)
    tested=[]
    for rank,r in enumerate(rows[:args.top]):
        q=r['quad']; t=r['threshold']; xs=perturb(x,q,t*args.multiplier,'balanced')
        try:
            Ef,raw,qf,xf,nit,ok,msg=fixed_relax(sm.xyz_to_vars(xs),sorted(set(q)),args.fixed_maxiter)
            Er,rawr,xr,nr,okr,msgr=stable_relax_q(qf,maxiter=args.release_maxiter)
            rec=dict(r); rec.update({'rank':rank,'fixed_energy':float(Ef),'fixed_delta_live':float(Ef-args.live_score),
                'fixed_coord':counts(xf),'fixed_success':bool(ok),'fixed_nit':int(nit),
                'free_energy':float(Er),'free_delta_live':float(Er-args.live_score),'free_coord':counts(xr),
                'free_class':classify(Er,args.live_score),'free_success':bool(okr),'free_nit':int(nr),'free_points':xr.tolist()})
            tested.append(rec)
            print('MOVE',rank,'t',f'{t:.9g}','del',r['delete'],'add',r['add'],
                  'fix',f'{Ef:.12f}','free',rec['free_class'],f'{Er:.12f}','dLive',f'{Er-args.live_score:+.9g}',flush=True)
        except Exception as exc:
            print('FAIL',rank,q,repr(exc),flush=True)
    # Save coordinates only for distinct free basins; keep compact metadata for all tested rows.
    seen=[]; endpoints=[]
    for r in sorted(tested,key=lambda z:z['free_energy']):
        e=r['free_energy']; cc=r['free_coord']
        if any(abs(e-ee)<2e-7 and cc==ccc for ee,ccc in seen): continue
        seen.append((e,cc)); endpoints.append({k:v for k,v in r.items() if k!='free_points'} | {'points':r['free_points']})
    compact=[{k:v for k,v in r.items() if k!='free_points'} for r in tested]
    best=min((r['free_energy'] for r in tested),default=float('inf'))
    out={'tag':args.tag,'seed_energy':float(E0),'seed_coord':cc0,'legal_count':len(rows),
         'soft_legal':[{**r,'quad':list(r['quad']),'delete':list(r['delete']),'add':list(r['add'])} for r in rows[:max(args.top,30)]],
         'tested':compact,'distinct_endpoints':endpoints,'best_free_energy':best,'best_delta_live':best-args.live_score}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH').write_text('candidate below live; inspect distinct_endpoints\n')

if __name__=='__main__': main()
