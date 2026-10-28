#!/usr/bin/env python3
"""Harvest distinct low-energy stationary points from exact C3 orbit space.

This deliberately preserves C3 during optimization and does NOT release the
result in full space.  The discovery that C is an index-2 full-space stationary
state shows why this distinction matters: a constrained C3 minimum can be a
useful higher-index portal whose unstable manifold exposes symmetry-broken
minima.

The search reuses the deterministic low-order global C3 perturbations from
`search_c3_smooth.py`, but retains one representative geometry for every
distinct constrained stationary energy below a requested cutoff.  The output is
intended for a second stage (`diagnose_seed_modes.py` / CHiSD downward search),
not as a claim that these are full-space minima.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np

import search_c3_smooth as c3


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots')
    ap.add_argument('--seed',type=int,required=True); ap.add_argument('--trials',type=int,default=20)
    ap.add_argument('--cutoff-delta',type=float,default=0.5)
    ap.add_argument('--cluster-tol',type=float,default=2e-7); ap.add_argument('--out',required=True)
    args=ap.parse_args(); root=pathlib.Path(args.few_shots)
    live_score,shot=c3.find_live(root); points=c3.load_cert(shot/'certificate.json')
    reps=c3.c3_representatives(points); v0=c3.xyz_to_vars(reps); base=c3.polish(v0,1200)
    rng=np.random.default_rng(args.seed); scales=np.geomspace(0.008,0.25,11)
    portals=[]; rows=[]
    # Include the constrained live state explicitly, but mark it as the reference.
    xbase,_,_=c3.vars_to_full(base.x)
    portals.append({'energy':float(base.fun),'delta_vs_live':float(base.fun)-live_score,
                    'hits':[{'trial':'reference','scale':0.0}],'points':xbase.tolist()})
    print(f'live={live_score:.10f} constrained_reference={base.fun:.12f}',flush=True)
    for t in range(args.trials):
        scale=float(scales[t%len(scales)]*math.exp(rng.normal(0.0,0.18)))
        start=c3.perturb(base.x,rng,scale); start_e,_=c3.fg(start); res=c3.polish(start,900); E=float(res.fun)
        pid=None
        if E<=live_score+args.cutoff_delta:
            for i,p in enumerate(portals):
                if abs(E-p['energy'])<args.cluster_tol: pid=i; break
            if pid is None:
                x,_,_=c3.vars_to_full(res.x); pid=len(portals)
                portals.append({'energy':E,'delta_vs_live':E-live_score,'hits':[],'points':x.tolist()})
            portals[pid]['hits'].append({'trial':t,'scale':scale})
        rows.append({'trial':t,'scale':scale,'start_energy':float(start_e),'energy':E,
                     'delta_vs_live':E-live_score,'portal_id':pid,'nit':int(res.nit),'success':bool(res.success)})
        print(f'trial={t:02d} scale={scale:.5f} start={start_e:.9f} E={E:.12f} '
              f'dlive={E-live_score:+.7g} portal={pid} nit={res.nit}',flush=True)
    portals.sort(key=lambda p:p['energy'])
    for rank,p in enumerate(portals): p['energy_rank']=rank
    print('PORTALS',[(p['energy_rank'],p['energy'],p['delta_vs_live'],len(p['hits'])) for p in portals],flush=True)
    out={'seed':args.seed,'trials':args.trials,'live_score':live_score,
         'live_shot':str(shot.relative_to(root)),'cutoff_delta':args.cutoff_delta,
         'cluster_tol':args.cluster_tol,'rows':rows,'portals':portals}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
