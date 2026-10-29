#!/usr/bin/env python3
"""Use one Actions runner efficiently for the B-D / D-upward frontier.

The driver is intentionally staged so a scarce queued runner stays productive:
1. four proximal normal-plane B<->D string variants in parallel;
2. four previously untried D upward searches (modes 1/2, both signs) in parallel;
3. four continuations of the best string with trust penalties around the winner;
4. if the string is sufficiently close to a MEP, four index-1 refiners with
   different reaction damping, followed by negative-mode side validation.

All subprocesses are single-threaded at the BLAS/OpenMP level; parallelism is
across independent scientific tasks, capped by os.cpu_count().
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, json, math, os, pathlib, shlex, subprocess, sys


def run_logged(cmd, log, env):
    log=pathlib.Path(log); log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('w') as f:
        f.write('$ '+shlex.join(cmd)+'\n'); f.flush()
        p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,text=True,env=env)
    return {'cmd':cmd,'returncode':p.returncode,'log':str(log)}

def parallel(tasks, workers, env, label):
    out=[]
    with cf.ThreadPoolExecutor(max_workers=min(workers,len(tasks))) as ex:
        futs={ex.submit(run_logged,t['cmd'],t['log'],env):t for t in tasks}
        for fut in cf.as_completed(futs):
            t=futs[fut]; r=fut.result(); r['tag']=t['tag']; r['out']=t['out']
            print(f'{label} {t["tag"]}: rc={r["returncode"]}',flush=True); out.append(r)
    return out

def load_ok(rows):
    ans=[]
    for r in rows:
        p=pathlib.Path(r['out'])
        if r['returncode']==0 and p.exists():
            try: ans.append((r,json.loads(p.read_text())))
            except Exception: pass
    return ans

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots'); ap.add_argument('bd_resume'); ap.add_argument('--outdir',required=True)
    ap.add_argument('--workers',type=int,default=0); ap.add_argument('--mep-target',type=float,default=2e-4)
    args=ap.parse_args(); outdir=pathlib.Path(args.outdir); outdir.mkdir(parents=True,exist_ok=True)
    code=pathlib.Path(__file__).resolve().parent; repo=code.parent
    B=repo/'data/basin-b-010566.json'; D=repo/'data/basin-d-018586.json'
    env=os.environ.copy()
    for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'): env[k]='1'
    ncpu=os.cpu_count() or 2; workers=min(ncpu,args.workers or ncpu); print(f'runner_cpus={ncpu} workers={workers}',flush=True)
    summary={'runner_cpus':ncpu,'workers':workers,'stages':{}}

    # Stage 1: broad proximal trust sweep.
    s1=[]
    for p in (5.0,15.0,40.0,120.0):
        tag=f'p{p:g}'; out=outdir/f'prox1-{tag}.json'
        s1.append({'tag':tag,'out':str(out),'log':str(outdir/f'prox1-{tag}.log'),
                   'cmd':[sys.executable,str(code/'string_prox_normal.py'),str(B),str(D),args.bd_resume,
                          '--outer','10','--parallel-penalty','400000','--prox-penalty',str(p),
                          '--image-maxiter','90','--perp-tol','2e-5','--out',str(out)]})
    r1=parallel(s1,workers,env,'PROX1'); ok1=load_ok(r1)
    if not ok1: raise SystemExit('all proximal stage-1 variants failed')
    for r,d in ok1:
        r.update(maxperp=d['max_path_perpendicular_gradient_rms'],maxE=max(d['path_energies']),converged=d['string_converged'])
        print(f'PROX1_RESULT {r["tag"]} maxperp={r["maxperp"]:.6g} maxE={r["maxE"]:.12f}',flush=True)
    summary['stages']['prox1']=r1

    # Stage 2: independent D upward interfaces not covered by the earlier mode-0 run.
    s2=[]
    for mode in (1,2):
        for sign in (-1,1):
            tag=f'm{mode}-s{sign:+d}'; out=outdir/f'd-up-{tag}.json'
            s2.append({'tag':tag,'out':str(out),'log':str(outdir/f'd-up-{tag}.log'),
                       'cmd':[sys.executable,str(code/'upward_index1_eigenfollow.py'),str(D),
                              '--mode',str(mode),'--sign',str(sign),'--escape-amp','0.0015','--steps','90',
                              '--k','10','--curv-floor','0.25','--residual-scale','0.02',
                              '--max-step-rms','0.00015','--max-energy-rise','0.12','--out',str(out)]})
    r2=parallel(s2,workers,env,'DUP'); ok2=load_ok(r2)
    for r,d in ok2:
        r.update(final_energy=d['final_energy'],grad=d['final_gradient_rms'],index=d['negative_internal_modes_below_-1e-3'],status=d['status'])
        print(f'DUP_RESULT {r["tag"]} E={r["final_energy"]:.12f} grad={r["grad"]:.4g} index={r["index"]}',flush=True)
    summary['stages']['d_up']=r2

    # Stage 3: continue the best path with a local trust-penalty sweep.
    best_r,best_d=min(ok1,key=lambda rd:rd[1]['max_path_perpendicular_gradient_rms'])
    best_path=best_r['out']; winner=float(best_r['tag'][1:])
    vals=sorted(set(max(0.5,min(300.0,winner*f)) for f in (0.25,0.55,1.0,2.2)))
    s3=[]
    for p in vals:
        tag=f'p{p:g}'; out=outdir/f'prox2-{tag}.json'
        s3.append({'tag':tag,'out':str(out),'log':str(outdir/f'prox2-{tag}.log'),
                   'cmd':[sys.executable,str(code/'string_prox_normal.py'),str(B),str(D),best_path,
                          '--outer','18','--parallel-penalty','400000','--prox-penalty',str(p),
                          '--image-maxiter','110','--perp-tol','2e-5','--out',str(out)]})
    r3=parallel(s3,workers,env,'PROX2'); ok3=load_ok(r3)
    if not ok3: raise SystemExit('all proximal stage-2 variants failed')
    for r,d in ok3:
        r.update(maxperp=d['max_path_perpendicular_gradient_rms'],maxE=max(d['path_energies']),converged=d['string_converged'])
        print(f'PROX2_RESULT {r["tag"]} maxperp={r["maxperp"]:.6g} maxE={r["maxE"]:.12f}',flush=True)
    summary['stages']['prox2']=r3
    br,bd=min(ok3,key=lambda rd:rd[1]['max_path_perpendicular_gradient_rms']); best2=br['out']; mp=bd['max_path_perpendicular_gradient_rms']
    summary['best_string']={'path':best2,'maxperp':mp,'max_energy':max(bd['path_energies']),'max_index':bd['max_image_index']}

    # Stage 4: only refine when transverse string force is low enough to justify a saddle seed.
    refiners=[]; ok4=[]
    if mp <= args.mep_target:
        for damp in (0.20,0.35,0.50,0.70):
            tag=f'd{damp:g}'; out=outdir/f'refine-{tag}.json'
            refiners.append({'tag':tag,'out':str(out),'log':str(outdir/f'refine-{tag}.log'),
                             'cmd':[sys.executable,str(code/'refine_tracked_index1.py'),best2,
                                    '--outer','16','--k','10','--perp-maxiter','700','--reaction-damping',str(damp),
                                    '--max-reaction-rms','0.000025','--grad-tol','2e-5','--out',str(out)]})
        r4=parallel(refiners,workers,env,'REFINE'); ok4=load_ok(r4)
        for r,d in ok4:
            r.update(final_energy=d['final_energy'],grad=d['final_gradient_rms'],index=d['negative_internal_modes_below_-1e-3'],status=d['status'])
            print(f'REFINE_RESULT {r["tag"]} E={r["final_energy"]:.12f} grad={r["grad"]:.4g} index={r["index"]}',flush=True)
        summary['stages']['refine']=r4
    else:
        print(f'SKIP_REFINE maxperp={mp:.6g} > target={args.mep_target:.6g}',flush=True)
        summary['stages']['refine']=[]

    # Stage 5: certify sides of the cleanest index-1 result, if any.
    cert=[]
    candidates=[(r,d) for r,d in ok4 if int(d.get('negative_internal_modes_below_-1e-3',-1))==1]
    candidates.sort(key=lambda rd:float(rd[1].get('final_gradient_rms',1e9)))
    for j,(r,d) in enumerate(candidates[:2]):
        out=outdir/f'validate-{j}.json'; tag=f'v{j}'
        cert.append({'tag':tag,'out':str(out),'log':str(outdir/f'validate-{j}.log'),
                     'cmd':[sys.executable,str(code/'validate_index1_seed.py'),args.few_shots,r['out'],
                            '--amps','0.00005,0.0001,0.0002','--out',str(out)]})
    if cert:
        rv=parallel(cert,min(workers,len(cert)),env,'VALIDATE'); summary['stages']['validate']=rv
    else: summary['stages']['validate']=[]

    (outdir/'batch-summary.json').write_text(json.dumps(summary,indent=2)+'\n')

if __name__=='__main__': main()
