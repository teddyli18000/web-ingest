#!/usr/bin/env python3
"""Parallel multimode basin search from a saved N=960 Thomson minimum.

Compute the low physical-tangent Hessian spectrum once, then relax a Cartesian
product of mode/sign/amplitude perturbations in separate worker processes.  This
is intended for a single multi-core Actions runner: BLAS threading should be
limited externally so independent relaxations consume the available cores
without nested oversubscription.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, json, math, pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import load_seed, stable_relax_q


def relax_one(task):
    q0, direction, mode, sign, amp, maxiter = task
    qs = sp.exp_perturb(q0, direction * sign, amp)
    e, raw, x, nit, ok, msg = stable_relax_q(qs, maxiter=maxiter)
    return {
        'mode': int(mode), 'sign': int(sign), 'amp': float(amp),
        'energy': float(e), 'raw_energy': float(raw), 'nit': int(nit),
        'success': bool(ok), 'message': str(msg), 'points': x.tolist(),
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots'); ap.add_argument('seed_json')
    ap.add_argument('--modes',default='0,1,2,3,4,5')
    ap.add_argument('--amps',default='0.003,0.006,0.012,0.022,0.038,0.060')
    ap.add_argument('--k',type=int,default=12); ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--workers',type=int,default=4); ap.add_argument('--maxiter',type=int,default=1800)
    ap.add_argument('--keep-basins',type=int,default=12); ap.add_argument('--out',required=True)
    args=ap.parse_args()

    root=pathlib.Path(args.few_shots)
    live_score,live_shot=sm.find_live(root)
    meta,x0=load_seed(args.seed_json); q0=sm.xyz_to_vars(x0)
    e0,g0=sm.fg(q0)
    modes=[int(x) for x in args.modes.split(',') if x]
    amps=[float(x) for x in args.amps.split(',') if x]
    k=max(args.k,max(modes)+1)
    H,raw,Qrot,calls=sm.build_hessian(q0,args.fd_step,1e6)
    rng=np.random.default_rng(564539)
    v0=rng.normal(size=len(q0)); v0-=Qrot@(Qrot.T@v0)
    vals,V=eigsh(H,k=k,which='SA',tol=2e-5,maxiter=700,ncv=max(40,3*k),v0=v0)
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    dirs={}
    for m in modes:
        d=V[:,m].copy(); d-=Qrot@(Qrot.T@d); d/=np.linalg.norm(d); dirs[m]=d
    grms=float(np.linalg.norm(g0/sm.physical_scale(q0))/math.sqrt(len(q0)))
    print(f'seedE={e0:.12f} live={live_score:.10f} grad={grms:.4g} workers={args.workers}',flush=True)
    print('lambdas',vals[:k].tolist(),flush=True)

    tasks=[(q0,dirs[m],m,s,a,args.maxiter) for m in modes for s in (-1,1) for a in amps]
    rows=[]
    with cf.ProcessPoolExecutor(max_workers=max(1,args.workers)) as ex:
        futs={ex.submit(relax_one,t):t[2:5] for t in tasks}
        for fut in cf.as_completed(futs):
            m,s,a=futs[fut]
            try:
                r=fut.result(); rows.append(r)
                print(f"DONE m={m} s={s:+d} a={a:.4g} E={r['energy']:.12f} dLive={r['energy']-live_score:+.9g} nit={r['nit']}",flush=True)
            except Exception as exc:
                print(f'FAIL m={m} s={s:+d} a={a:.4g}: {exc}',flush=True)
                rows.append({'mode':m,'sign':s,'amp':a,'error':repr(exc)})

    good=[r for r in rows if 'energy' in r]
    good.sort(key=lambda r:r['energy'])
    basins=[]
    for r in good:
        if any(abs(r['energy']-b['energy'])<2e-6 for b in basins):
            continue
        basins.append({k:r[k] for k in ('mode','sign','amp','energy','raw_energy','nit','success','message','points')})
        if len(basins)>=args.keep_basins: break
    compact=[]
    for r in rows:
        compact.append({k:v for k,v in r.items() if k!='points'})
    best=good[0]['energy'] if good else float('inf')
    print(f'BEST {best:.12f} delta_live={best-live_score:+.9g} distinct_saved={len(basins)}',flush=True)
    out={
        'seed_json':str(args.seed_json),'seed_energy':float(e0),'seed_gradient_rms':grms,
        'live_score':float(live_score),'live_shot':str(live_shot.relative_to(root)),
        'modes':modes,'amps':amps,'workers':args.workers,'eigenvalues':[float(v) for v in vals],
        'hessian_gradient_calls':calls['n'],'rows':compact,'lowest_distinct_basins':basins,
        'best_energy':float(best),'best_delta_vs_live':float(best-live_score),
    }
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
