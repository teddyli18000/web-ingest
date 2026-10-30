#!/usr/bin/env python3
"""Split the unresolved e432->B reaction residual into plastic core and elastic field.

The e432->B physical reaction has only ~30.8% of its squared norm in the first
48 Hessian modes; the residual beyond those modes alone is sufficient to cross
into B.  This search therefore decomposes that residual by graph distance from
e432's unique short 5-7-5 scar, while retaining the captured first-48 component
as a third independently scaled coordinate.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np

import diagnose_soft_modes as sm
import search_soft_pair as sp
import search_topology_morph as tm
from search_from_seed_modes import stable_relax_q
from analyze_reaction_mode_overlap import load,reaction_physical
from search_reaction_spectral_band import modes
from search_scar_core_elastic_split import graph,short_component,shell_mask

N=960


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('source_json'); ap.add_argument('target_json')
    ap.add_argument('--shell',type=int,default=3); ap.add_argument('--decay',type=float,default=1.0)
    ap.add_argument('--k',type=int,default=48); ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--core-scales',default='0.35,0.5,0.65,0.8,0.95,1.15')
    ap.add_argument('--far-scales',default='0.35,0.5,0.65,0.8,0.95,1.15')
    ap.add_argument('--captured-scales',default='0,0.35,0.7,1.0')
    ap.add_argument('--maxiter',type=int,default=3400); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    if args.k<48: raise ValueError('k must be >=48')

    S=load(args.source_json); T=load(args.target_json)
    q,y,Q0=reaction_physical(S,T)
    vals,V,Q,hcalls=modes(q,args.k,args.fd_step)
    c=V.T@y; captured=V@c; residual=y-captured

    adj,deg=graph(S); core_vertices=short_component(adj,deg)
    w,dist=shell_mask(adj,core_vertices,args.shell,args.decay)
    w2=np.repeat(w,2)
    rcore=residual*w2; rfar=residual*(1.0-w2)
    # Spatial masking can reintroduce rigid rotation components; remove them
    # before forming search directions.
    for z in (rcore,rfar,captured):
        z-=Q@(Q.T@z)

    yn=float(np.linalg.norm(y))
    def power(z): return float(np.dot(z,z)/(yn*yn))
    print('SOURCE',tm.raw_energy(S),tm.coord_counts(S),'TARGET',tm.raw_energy(T),tm.coord_counts(T),flush=True)
    print('SHELL',args.shell,'DECAY',args.decay,'ACTIVE',len(dist),'CORE',core_vertices,flush=True)
    print('POWERS captured48',power(captured),'residual_core',power(rcore),'residual_far',power(rfar),
          'residual_total',float(np.dot(residual,residual)/(yn*yn)),flush=True)

    cs=[float(z) for z in args.core_scales.split(',') if z]
    fs=[float(z) for z in args.far_scales.split(',') if z]
    hs=[float(z) for z in args.captured_scales.split(',') if z]
    rows=[]; saved=[]
    for a in cs:
        for b in fs:
            for h in hs:
                z=a*rcore+b*rfar+h*captured
                z-=Q@(Q.T@z)
                native=float(np.linalg.norm(z)/math.sqrt(N))
                if native<1e-12: continue
                qs=sp.exp_perturb(q,z,native)
                start,_=sm.fg(qs)
                e,raw,x,nit,ok,msg=stable_relax_q(qs,maxiter=args.maxiter)
                cc=tm.coord_counts(x)
                row={'shell':args.shell,'decay':args.decay,'core_scale':a,'far_scale':b,'captured_scale':h,
                     'native_rms':native,'start_energy':float(start),'energy':float(e),
                     'delta_live':float(e-args.live_score),'coord_counts':cc,'nit':nit,'success':ok,'message':msg}
                rows.append(row)
                print('TRY a',a,'b',b,'h',h,'amp',f'{native:.7g}','E',f'{e:.12f}',
                      'dLive',f'{e-args.live_score:+.9g}','cc',cc,'nit',nit,flush=True)
                if e<args.live_score+0.15 and all(abs(e-s['energy'])>2e-6 or cc!=s['coord_counts'] for s in saved):
                    saved.append({'energy':float(e),'delta_live':float(e-args.live_score),'coord_counts':cc,
                                  'shell':args.shell,'decay':args.decay,'core_scale':a,'far_scale':b,
                                  'captured_scale':h,'points':x.tolist()})
    saved.sort(key=lambda z:z['energy']); best=min(rows,key=lambda z:z['energy'])
    out={'source_energy':float(tm.raw_energy(S)),'target_energy':float(tm.raw_energy(T)),
         'live_score':args.live_score,'shell':args.shell,'decay':args.decay,'active_vertices':len(dist),
         'core_vertices':core_vertices,'captured48_power':power(captured),'residual_core_power':power(rcore),
         'residual_far_power':power(rfar),'residual_total_power':float(np.dot(residual,residual)/(yn*yn)),
         'eigenvalues':[float(v) for v in vals],'hessian_gradient_calls':hcalls,'rows':rows,
         'distinct_low_basins':saved[:30],'best_energy':best['energy'],'best_delta_live':best['delta_live']}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if saved and saved[0]['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(saved[0],separators=(',',':'))+'\n')

if __name__=='__main__': main()
