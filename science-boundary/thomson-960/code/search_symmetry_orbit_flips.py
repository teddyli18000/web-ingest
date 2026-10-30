#!/usr/bin/env python3
"""Cross all symmetry copies of a same-count Delaunay glide together.

For a C3 Thomson minimum a single dislocation glide breaks C3, while the three
symmetry-related copies applied coherently preserve C3 and may avoid the elastic
restoring force that heals an isolated glide.  This script crosses a list of
pairwise-disjoint Delaunay quads with a shared amplitude/pattern, relaxes with
all involved vertices fixed, then releases the full system.
"""
from __future__ import annotations
import argparse,json,pathlib,math
from collections import Counter
import numpy as np

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed,stable_relax_q
from search_e564_defect_flip_parallel import topology,tangent_to,flipped
from search_e564_scaffolded_flip import fixed_relax


def parse_quads(s):
    out=[]
    for part in s.split(';'):
        q=tuple(int(z) for z in part.split(','))
        if len(q)!=4: raise ValueError('each quad must have u,v,a,b')
        out.append(q)
    return out


def perturb_multi(x,quads,amp,pattern):
    y=x.copy(); orig=x
    touched=set()
    for u,v,a,b in quads:
        moves=[]
        if pattern in ('balanced','newdiag'): moves += [(a,b,+1),(b,a,+1)]
        if pattern in ('balanced','olddiag'): moves += [(u,v,-1),(v,u,-1)]
        for i,j,sg in moves:
            if i in touched: raise ValueError('quads must have disjoint moved vertices')
            touched.add(i)
            p=orig[i]; t=sg*tangent_to(p,orig[j])
            y[i]=math.cos(amp)*p+math.sin(amp)*t
            y[i]/=np.linalg.norm(y[i])
    return y


def all_flipped(x,quads):
    return all(flipped(x,q) for q in quads)


def threshold_multi(x,quads,pattern):
    hi=0.004
    while hi<=0.08 and not all_flipped(perturb_multi(x,quads,hi,pattern),quads): hi*=1.35
    if hi>0.08: return None
    lo=0.0
    for _ in range(22):
        mid=(lo+hi)/2
        if all_flipped(perturb_multi(x,quads,mid,pattern),quads): hi=mid
        else: lo=mid
    return hi


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json'); ap.add_argument('--quads',required=True)
    ap.add_argument('--patterns',default='balanced,newdiag,olddiag')
    ap.add_argument('--multipliers',default='1.003,1.01,1.03,1.08,1.18,1.35')
    ap.add_argument('--fixed-maxiter',type=int,default=1800); ap.add_argument('--release-maxiter',type=int,default=3400)
    ap.add_argument('--live-score',type=float,required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x0=load_seed(args.seed_json); quads=parse_quads(args.quads)
    fixed=sorted({i for q in quads for i in q})
    E0,_=sm.fg(sm.xyz_to_vars(x0)); rows=[]; basins=[]; thrs={}
    for pat in [z for z in args.patterns.split(',') if z]:
        th=threshold_multi(x0,quads,pat); thrs[pat]=th
        print('THRESHOLD',pat,th,'quads',quads,flush=True)
        if th is None: continue
        for m in [float(z) for z in args.multipliers.split(',') if z]:
            start=perturb_multi(x0,quads,th*m,pat); q0=sm.xyz_to_vars(start)
            ds,_=topology(start); ccs=Counter(ds.tolist()); Estart,_=sm.fg(q0)
            Ef,rawf,qf,xf,nf,okf,msgf=fixed_relax(q0,fixed,args.fixed_maxiter)
            df,_=topology(xf); ccf=Counter(df.tolist())
            Er,rawr,xr,nr,okr,msgr=stable_relax_q(qf,maxiter=args.release_maxiter)
            dr,_=topology(xr); ccr=Counter(dr.tolist())
            row={'pattern':pat,'threshold':th,'multiplier':m,'all_initial_flipped':bool(all_flipped(start,quads)),
                 'start_energy':float(Estart),'start_coord':{str(k):int(v) for k,v in sorted(ccs.items())},
                 'fixed_energy':float(Ef),'fixed_coord':{str(k):int(v) for k,v in sorted(ccf.items())},
                 'release_energy':float(Er),'delta_live':float(Er-args.live_score),
                 'release_coord':{str(k):int(v) for k,v in sorted(ccr.items())},
                 'fixed_nit':int(nf),'release_nit':int(nr),'success':[bool(okf),bool(okr)],'messages':[str(msgf),str(msgr)]}
            rows.append(row)
            print('DONE',pat,'m',m,'start',f'{Estart:.9f}',row['start_coord'],
                  'fixed',f'{Ef:.12f}',row['fixed_coord'],'release',f'{Er:.12f}',
                  'dLive',f'{Er-args.live_score:+.9g}',row['release_coord'],flush=True)
            if not any(abs(Er-b['energy'])<2e-6 and row['release_coord']==b['coord_counts'] for b in basins):
                basins.append({'energy':float(Er),'delta_live':float(Er-args.live_score),'coord_counts':row['release_coord'],
                               'pattern':pat,'multiplier':m,'points':xr.tolist()})
    basins.sort(key=lambda z:z['energy']); best=min((r['release_energy'] for r in rows),default=None)
    pathlib.Path(args.out).write_text(json.dumps({'seed_energy':float(E0),'quads':[list(q) for q in quads],
        'thresholds':thrs,'rows':rows,'lowest_distinct_release_basins':basins[:16],
        'best_release_energy':best,'best_delta_live':best-args.live_score if best is not None else None},separators=(',',':'))+'\n')
    if basins and basins[0]['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(basins[0],separators=(',',':'))+'\n')

if __name__=='__main__': main()
