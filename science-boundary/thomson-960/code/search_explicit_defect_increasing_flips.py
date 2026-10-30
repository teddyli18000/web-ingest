#!/usr/bin/env python3
"""Relax explicitly selected e432 23->24-dislocation bistellar flips.

Candidates are selected without reference to B: they are legal source-triangulation
flips whose combinatorial degree counts become exactly 36/900/24 and that lie near
the unique short 5-7-5 scar.  For each quad we locate the actual geometric Delaunay
boundary and test modest overshoots in balanced/newdiag/olddiag realizations.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import Counter

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed
from search_e564_defect_flip_parallel import threshold,relax_one,topology


def parse_quads(s):
    out=[]
    for item in s.split(';'):
        if not item.strip(): continue
        q=tuple(int(v) for v in item.split(','))
        if len(q)!=4: raise ValueError(item)
        out.append(q)
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json'); ap.add_argument('--quads',required=True)
    ap.add_argument('--patterns',default='balanced,newdiag,olddiag')
    ap.add_argument('--multipliers',default='1.01,1.04,1.10,1.22,1.40,1.70')
    ap.add_argument('--maxiter',type=int,default=3000); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x=load_seed(args.seed_json); E0,_=sm.fg(sm.xyz_to_vars(x))
    quads=parse_quads(args.quads); pats=[p for p in args.patterns.split(',') if p]; mults=[float(v) for v in args.multipliers.split(',') if v]
    rows=[]; saved=[]; best=(1e300,None)
    print('SEED',f'{E0:.12f}','coord',meta.get('coord_counts'),'QUADS',quads,flush=True)
    for q in quads:
        for p in pats:
            th=threshold(x,q,p); print('THRESH',q,p,th,flush=True)
            if th is None: continue
            for m in mults:
                r=relax_one((x,q,p,th,m,args.maxiter)); rows.append({k:v for k,v in r.items() if k!='points'})
                e=r['energy']; cc=r['coord']
                print('TRY',q,p,m,'E',f'{e:.12f}','dLive',f'{e-args.live_score:+.9g}','cc',cc,'nit',r['nit'],flush=True)
                if e<best[0]: best=(e,r['points'])
                if e<args.live_score+0.08 and all(abs(e-z['energy'])>2e-6 or cc!=z['coord'] for z in saved):
                    saved.append({'energy':e,'delta_live':e-args.live_score,'coord':cc,'quad':list(q),'pattern':p,'multiplier':m,'points':r['points']})
    saved.sort(key=lambda z:z['energy'])
    out={'seed_energy':float(E0),'live_score':args.live_score,'quads':[list(q) for q in quads],'rows':rows,
         'distinct_low_basins':saved[:30],'best_energy':float(best[0]),'best_delta_live':float(best[0]-args.live_score),
         'best_points':best[1] if best[1] is not None and best[0]<args.live_score-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if out['best_points'] is not None:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps({'energy':out['best_energy'],'points':out['best_points']},separators=(',',':'))+'\n')

if __name__=='__main__': main()
