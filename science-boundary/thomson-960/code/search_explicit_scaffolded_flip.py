#!/usr/bin/env python3
"""Scaffold an explicit target-independent 23->24 Delaunay flip from e432."""
from __future__ import annotations
import argparse,json,pathlib
from collections import Counter

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed,stable_relax_q
from search_e564_defect_flip_parallel import topology,threshold,perturb,flipped
from search_e564_scaffolded_flip import fixed_relax


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--quad',required=True,help='u,v,a,b')
    ap.add_argument('--patterns',default='balanced,newdiag,olddiag')
    ap.add_argument('--multipliers',default='1.01,1.04,1.10,1.22,1.45,1.80')
    ap.add_argument('--fixed-maxiter',type=int,default=1800); ap.add_argument('--release-maxiter',type=int,default=2800)
    ap.add_argument('--live-score',type=float,required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    quad=tuple(int(z) for z in args.quad.split(','));
    if len(quad)!=4: raise ValueError('quad needs four indices')
    meta,x0=load_seed(args.seed_json); E0,_=sm.fg(sm.xyz_to_vars(x0)); fixed=list(quad)
    patterns=[s for s in args.patterns.split(',') if s]; mults=[float(s) for s in args.multipliers.split(',') if s]
    rows=[]; basins=[]; thrs={}
    for pat in patterns:
        t=threshold(x0,quad,pat); thrs[pat]=t
        print('THRESHOLD',quad,pat,t,flush=True)
        if t is None: continue
        for m in mults:
            start=perturb(x0,quad,t*m,pat); sd,_=topology(start); sc=Counter(sd.tolist())
            actually=flipped(start,quad); qstart=sm.xyz_to_vars(start); Estart,_=sm.fg(qstart)
            Ef,rawf,qf,xf,nitf,okf,msgf=fixed_relax(qstart,fixed,args.fixed_maxiter)
            df,_=topology(xf); fc=Counter(df.tolist())
            Er,rawr,xr,nitr,okr,msgr=stable_relax_q(qf,maxiter=args.release_maxiter)
            dr,_=topology(xr); rc=Counter(dr.tolist())
            row={'pattern':pat,'threshold':t,'multiplier':m,'initial_flipped':bool(actually),
                 'start_energy':float(Estart),'start_coord':{str(k):int(v) for k,v in sorted(sc.items())},
                 'fixed_energy':float(Ef),'fixed_coord':{str(k):int(v) for k,v in sorted(fc.items())},
                 'fixed_nit':nitf,'fixed_success':okf,'fixed_message':msgf,
                 'release_energy':float(Er),'delta_live':float(Er-args.live_score),
                 'release_coord':{str(k):int(v) for k,v in sorted(rc.items())},
                 'release_nit':nitr,'release_success':okr,'release_message':msgr}
            rows.append(row)
            print('DONE',pat,'m',m,'flip',actually,'start',f'{Estart:.9f}','fixed',f'{Ef:.12f}',row['fixed_coord'],
                  'release',f'{Er:.12f}','dLive',f'{Er-args.live_score:+.9g}',row['release_coord'],flush=True)
            if not any(abs(Er-b['energy'])<2e-6 and row['release_coord']==b['coord_counts'] for b in basins):
                basins.append({'energy':float(Er),'delta_live':float(Er-args.live_score),'coord_counts':row['release_coord'],
                               'pattern':pat,'multiplier':m,'points':xr.tolist()})
    basins.sort(key=lambda z:z['energy']); best=min((r['release_energy'] for r in rows),default=None)
    out={'seed_energy':float(E0),'quad':list(quad),'thresholds':thrs,'rows':rows,
         'lowest_distinct_release_basins':basins[:16],'best_release_energy':best,
         'best_delta_live':best-args.live_score if best is not None else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if basins and basins[0]['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(basins[0],separators=(',',':'))+'\n')

if __name__=='__main__': main()
