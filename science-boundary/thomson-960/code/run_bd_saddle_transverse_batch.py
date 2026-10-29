#!/usr/bin/env python3
"""Expand the certified B<->D saddle interface on one CPU-saturated runner.

Stage 1 scans positive saddle modes 1..8, both signs, over transverse amplitudes
and small reaction-coordinate biases.  Each task keeps representatives of every
distinct relaxed basin it encounters, not only its lowest-energy endpoint.
Known R/A/B/D energies are recognized explicitly; new low basins retain full
coordinates and Delaunay defect signatures.

Stage 2 automatically takes the two lowest new minima (if any) and launches
minimum-centered modes 0..3, both signs, in parallel before releasing the runner.
This mirrors the successful A<->B transverse search that discovered D, while
avoiding another Actions queue round-trip after a discovery.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, json, math, os, pathlib, shlex, subprocess, sys
import numpy as np

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import stable_relax_q
from search_saddle_transverse import load_refined
from search_learned_event_grammar import defect_signature

N=960
KNOWN={'R':444368.3924061973,'A':444368.395686226,'B':444368.4029728614,'D':444368.4109930845}


def known_label(e,tol=5e-6):
    for k,v in KNOWN.items():
        if abs(e-v)<=tol:return k
    return None


def scan_worker(payload):
    few_shots,refined_json,mode,sign,tamps,ramps,maxiter=payload
    root=pathlib.Path(few_shots); live_score,live_shot=sm.find_live(root)
    meta,x0,vecs,modes=load_refined(refined_json); q0=sm.xyz_to_vars(x0)
    Q=sm.rotation_basis(q0); reaction=vecs[:,0].copy(); transverse=vecs[:,mode].copy()
    reaction-=Q@(Q.T@reaction); transverse-=Q@(Q.T@transverse)
    reaction/=np.linalg.norm(reaction); transverse/=np.linalg.norm(transverse)
    transverse-=reaction*float(reaction@transverse); transverse/=np.linalg.norm(transverse); transverse*=sign
    rows=[]; reps=[]
    for ta in tamps:
        for ra in ramps:
            y=math.sqrt(N)*(ta*transverse+ra*reaction); yn=float(np.linalg.norm(y))
            if yn==0:continue
            qs=sp.exp_perturb(q0,y/yn,yn/math.sqrt(N)); es,_=sm.fg(qs)
            e,raw,x,nit,ok,msg=stable_relax_q(qs,maxiter)
            sig=defect_signature(x); row={'transverse_amp':ta,'reaction_amp':ra,'start_energy':es,'energy':e,
                'raw_absolute_energy':raw,'delta_vs_live':e-live_score,'nit':nit,'success':ok,'message':msg,
                'known_label':known_label(e),'twin_count':sig['twins'],
                'coord':[list(t) for t in sig['coord']],'components':[list(t) for t in sig['components']]}
            rows.append(row)
            sk=(tuple(sig['coord']),tuple(sig['components']),sig['twins'])
            if not any(abs(e-r['energy'])<2e-7 and sk==r['_sig'] for r in reps):
                reps.append({'energy':e,'transverse_amp':ta,'reaction_amp':ra,'known_label':known_label(e),
                    'twin_count':sig['twins'],'coord':[list(t) for t in sig['coord']],
                    'components':[list(t) for t in sig['components']],'points':x.tolist(),'_sig':sk})
    for r in reps:r.pop('_sig',None)
    return {'mode':mode,'sign':sign,'eigenvalue':modes[mode]['eigenvalue'],'rows':rows,'representatives':reps}


def run_logged(cmd,log,env):
    with open(log,'w') as f:
        f.write('$ '+shlex.join(cmd)+'\n');f.flush()
        p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,text=True,env=env)
    return p.returncode


def main():
    ap=argparse.ArgumentParser();ap.add_argument('few_shots');ap.add_argument('refined_json');ap.add_argument('--outdir',required=True)
    ap.add_argument('--modes',default='1,2,3,4,5,6,7,8');ap.add_argument('--transverse-amps',default='0.002,0.004,0.007,0.011,0.017,0.026,0.040')
    ap.add_argument('--reaction-amps',default='-0.00015,0,0.00015');ap.add_argument('--workers',type=int,default=0);ap.add_argument('--maxiter',type=int,default=2200)
    args=ap.parse_args();outdir=pathlib.Path(args.outdir);outdir.mkdir(parents=True,exist_ok=True)
    modes=[int(x) for x in args.modes.split(',') if x];tamps=[float(x) for x in args.transverse_amps.split(',') if x];ramps=[float(x) for x in args.reaction_amps.split(',') if x]
    ncpu=os.cpu_count() or 2;workers=max(1,min(args.workers or ncpu,ncpu,4));print(f'cpus={ncpu} workers={workers} tasks={2*len(modes)}',flush=True)
    payload=[(args.few_shots,args.refined_json,m,s,tamps,ramps,args.maxiter) for m in modes for s in (-1,1)]
    scans=[]
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        for res in ex.map(scan_worker,payload,chunksize=1):
            scans.append(res);best=min(r['energy'] for r in res['rows'])
            labs=sorted(set(r['known_label'] or 'NEW' for r in res['rows']))
            print(f'SCAN m={res["mode"]} s={res["sign"]:+d} lambda={res["eigenvalue"]:.6g} best={best:.12f} basins={labs}',flush=True)
    # Merge basin representatives globally.
    reps=[]
    for s in scans:
        for r in s['representatives']:
            sk=(tuple(tuple(x) for x in r['coord']),tuple(tuple(x) for x in r['components']),r['twin_count'])
            if any(abs(r['energy']-q['energy'])<2e-7 and sk==q['_sig'] for q in reps):continue
            z=dict(r);z['_sig']=sk;z['source_mode']=s['mode'];z['source_sign']=s['sign'];reps.append(z)
    reps.sort(key=lambda r:r['energy'])
    print('REPRESENTATIVES',[(r['known_label'] or 'NEW',r['energy'],r['source_mode'],r['source_sign'],r['transverse_amp'],r['reaction_amp'],r['twin_count']) for r in reps],flush=True)
    new=[r for r in reps if r['known_label'] is None]
    # Stage 2: second-hop low-mode scans from the two lowest new minima.
    env=os.environ.copy()
    for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):env[k]='1'
    second=[]
    for j,r in enumerate(new[:2]):
        seed=outdir/f'new-seed-{j}.json';seed.write_text(json.dumps({'energy':r['energy'],'points':r['points']},separators=(',',':'))+'\n')
        for mode in range(4):
            for sign in (-1,1):
                tag=f'n{j}-m{mode}-s{sign:+d}';out=outdir/f'second-{tag}.json';log=outdir/f'second-{tag}.log'
                cmd=[sys.executable,str(pathlib.Path(__file__).resolve().parent/'search_from_seed_modes.py'),args.few_shots,str(seed),
                     '--mode',str(mode),'--sign',str(sign),'--amps','0.003,0.006,0.010,0.016,0.024,0.036','--out',str(out)]
                second.append({'tag':tag,'out':str(out),'log':str(log),'cmd':cmd})
    second_results=[]
    if second:
        with cf.ThreadPoolExecutor(max_workers=workers) as ex:
            futs={ex.submit(run_logged,t['cmd'],t['log'],env):t for t in second}
            for fut in cf.as_completed(futs):
                t=futs[fut];rc=fut.result();row={'tag':t['tag'],'returncode':rc,'out':t['out'],'log':t['log']}
                if rc==0 and pathlib.Path(t['out']).exists():
                    d=json.loads(pathlib.Path(t['out']).read_text());row.update(best_energy=d['best_float_energy'],best_delta=d['best_delta_vs_live_score'])
                    print(f'SECOND {t["tag"]} E={row["best_energy"]:.12f} d={row["best_delta"]:+.9g}',flush=True)
                second_results.append(row)
    # Compact stage1 rows; keep full coordinates only for top distinct reps.
    top=[]
    for r in reps[:10]:
        z={k:v for k,v in r.items() if k!='_sig'};top.append(z)
    compact_scans=[]
    for s in scans:
        compact_scans.append({k:v for k,v in s.items() if k!='representatives'})
    best=min((r['energy'] for r in reps),default=float('inf'));live=sm.find_live(pathlib.Path(args.few_shots))[0]
    out={'refined_json':args.refined_json,'live_score':live,'scans':compact_scans,'top_representatives':top,
         'new_basin_count':len(new),'second_hop':second_results,'best_energy':best,'best_delta_vs_live':best-live,
         'best_points':reps[0]['points'] if reps and reps[0]['energy']<live-2e-7 else None}
    (outdir/'bd-transverse-batch.json').write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__':main()
