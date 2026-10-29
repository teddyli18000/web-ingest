#!/usr/bin/env python3
"""Active mixed-mode search around the certified B<->D saddle junction.

Local probes show that the positive Hessian modes (1,2,6) already reach all four
known low minima: mode1 exposes A/B, mode2 exposes D, and mode6 exposes R/B.
This script treats coefficients in that three-dimensional transverse subspace as
a reaction-coordinate space rather than enumerating one eigenmode at a time.

Workflow inside one runner:
  1. Sobol + physically meaningful anchor samples in (c1,c2,c6);
  2. full unconstrained relaxation in parallel;
  3. Delaunay tessellation of coefficient space;
  4. iterative centroid sampling only in heterogeneous simplices whose vertices
     relax to different basins, strongly prioritizing 3/4-basin junctions;
  5. evaluate +/- small reaction-mode biases around the most heterogeneous
     remaining boundary centroids;
  6. if a new minimum is found, automatically second-hop its lowest modes.

The goal is to expose nonlinear mixed transverse exits that cannot appear in a
single-mode scan.  Any credible below-record endpoint preserves full points for
exact-verifier follow-up.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, json, math, os, pathlib, shlex, subprocess, sys
import numpy as np
from scipy.spatial import Delaunay
from scipy.stats import qmc

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import stable_relax_q
from search_saddle_transverse import load_refined
from search_learned_event_grammar import worker

N=960
KNOWN={'R':444368.3924061973,'A':444368.395686226,'B':444368.4029728614,'D':444368.4109930845}

def label_known(e,tol=5e-6):
    for k,v in KNOWN.items():
        if abs(e-v)<=tol:return k
    return None

def sigkey(r):
    return (tuple(tuple(x) for x in r['coord']),tuple(tuple(x) for x in r['components']),int(r['twin_count']))

def assign_labels(rows):
    labels=[]; clusters=[]
    for r in rows:
        k=label_known(r['energy'])
        if k is None:
            sk=sigkey(r); hit=None
            for j,(e,s) in enumerate(clusters):
                if s==sk and abs(r['energy']-e)<2e-7:hit=f'U{j:03d}';break
            if hit is None:
                clusters.append((r['energy'],sk));hit=f'U{len(clusters)-1:03d}'
            k=hit
        labels.append(k)
    return labels,clusters

def normalize(X,lo,hi):return (X-lo)/(hi-lo)

def build_start(q0,basis,reaction,c,ra=0.0):
    y=math.sqrt(N)*(sum(float(c[j])*basis[:,j] for j in range(3))+float(ra)*reaction)
    yn=float(np.linalg.norm(y))
    if yn<1e-16:return sm.vars_to_xyz(q0)[0]
    q=sp.exp_perturb(q0,y/yn,yn/math.sqrt(N));return sm.vars_to_xyz(q)[0]

def relax_coeffs(coeffs,q0,basis,reaction,ra,few,live,workers,maxiter,prefix):
    payload=[]
    for i,c in enumerate(coeffs):
        start=build_start(q0,basis,reaction,c,ra)
        payload.append((f'{prefix}-{i:04d}',start,live,maxiter))
    out=[]
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        for c,r in zip(coeffs,ex.map(worker,payload,chunksize=1)):
            rr=dict(r);rr['coeff']=[float(x) for x in c];rr['reaction_bias']=float(ra);out.append(rr)
            print(f'{prefix} c={np.asarray(c).round(5).tolist()} r={ra:+.2g} E={r["energy"]:.12f} '
                  f'd={r["delta_vs_live"]:+.9g} twins={r["twin_count"]}',flush=True)
    return out

def boundary_candidates(rows,labels,lo,hi,nmax,seen,round_no):
    X=np.asarray([r['coeff'] for r in rows if abs(r.get('reaction_bias',0.0))<1e-15],float)
    idx=[i for i,r in enumerate(rows) if abs(r.get('reaction_bias',0.0))<1e-15]
    if len(X)<5:return []
    Z=normalize(X,lo,hi)
    try:tri=Delaunay(Z,qhull_options='QJ Qbb Qc')
    except Exception as e:print('Delaunay failed',e,flush=True);return []
    cand=[]
    for sx in tri.simplices:
        gi=[idx[int(j)] for j in sx]; labs={labels[i] for i in gi}
        if len(labs)<2:continue
        pts=Z[sx];cent=np.mean(pts,axis=0);c=lo+cent*(hi-lo);key=tuple(np.round(c,10))
        if key in seen:continue
        low=min(rows[i]['energy'] for i in gi);unknown=sum(x.startswith('U') for x in labs)
        diam=max(float(np.linalg.norm(pts[a]-pts[b])) for a in range(4) for b in range(a))
        # Multi-basin junctions dominate score. Low energy and unknown labels are
        # secondary. This intentionally differs from uniform boundary bisection.
        score=40*len(labs)+12*unknown-220*(low-KNOWN['R'])-1.0*diam
        cand.append((score,c,{'labels':sorted(labs),'vertices':gi,'min_energy':low,'diameter':diam,'round':round_no}))
    cand.sort(key=lambda x:x[0],reverse=True);chosen=[]
    for item in cand:
        _,c,_=item;z=normalize(c,lo,hi)
        if any(np.linalg.norm(z-normalize(q[1],lo,hi))<0.022 for q in chosen):continue
        chosen.append(item)
        if len(chosen)>=nmax:break
    return chosen

def run_logged(cmd,log,env):
    with open(log,'w') as f:
        f.write('$ '+shlex.join(cmd)+'\n');f.flush();p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,text=True,env=env)
    return p.returncode

def main():
    ap=argparse.ArgumentParser();ap.add_argument('few_shots');ap.add_argument('refined_json');ap.add_argument('--outdir',required=True)
    ap.add_argument('--modes',default='1,2,6');ap.add_argument('--lo',default='-0.025,-0.025,-0.040');ap.add_argument('--hi',default='0.025,0.025,0.025')
    ap.add_argument('--initial',type=int,default=64);ap.add_argument('--rounds',type=int,default=4);ap.add_argument('--per-round',type=int,default=36)
    ap.add_argument('--reaction-probes',type=int,default=24);ap.add_argument('--reaction-bias',type=float,default=0.00018)
    ap.add_argument('--workers',type=int,default=0);ap.add_argument('--maxiter',type=int,default=2200);args=ap.parse_args()
    outdir=pathlib.Path(args.outdir);outdir.mkdir(parents=True,exist_ok=True);root=pathlib.Path(args.few_shots)
    live,live_dir=sm.find_live(root);meta,x0,vecs,modes=load_refined(args.refined_json);q0=sm.xyz_to_vars(x0)
    mids=[int(x) for x in args.modes.split(',') if x]
    if len(mids)!=3:raise ValueError('exactly three positive modes required')
    Q=sm.rotation_basis(q0);reaction=vecs[:,0].copy();reaction-=Q@(Q.T@reaction);reaction/=np.linalg.norm(reaction)
    B=[]
    for m in mids:
        v=vecs[:,m].copy();v-=Q@(Q.T@v);v-=reaction*float(reaction@v);v/=np.linalg.norm(v);B.append(v)
    basis=np.column_stack(B);basis,_=np.linalg.qr(basis)
    lo=np.array([float(x) for x in args.lo.split(',')]);hi=np.array([float(x) for x in args.hi.split(',')])
    ncpu=os.cpu_count() or 2;workers=max(1,min(args.workers or ncpu,ncpu,4));print(f'cpus={ncpu} workers={workers} modes={mids}',flush=True)
    print('eigenvalues',[modes[m]['eigenvalue'] for m in mids],flush=True)

    sob=qmc.Sobol(3,scramble=True,seed=960126);m=int(math.ceil(math.log2(args.initial)));U=sob.random_base2(m)[:args.initial]
    coeff=[lo+u*(hi-lo) for u in U]
    # Anchors include the locally diagnosed axes and the finite R window on -mode6.
    anchors=[np.zeros(3)]
    for j in range(3):
        for a in (-0.012,0.012):
            c=np.zeros(3);c[j]=a;anchors.append(c)
    for a in (-0.008,-0.0095,-0.017,-0.026,-0.0295):anchors.append(np.array([0.,0.,a]))
    seen=set();init=[]
    for c in coeff+anchors:
        if np.all(c>=lo) and np.all(c<=hi):
            k=tuple(np.round(c,12))
            if k not in seen:seen.add(k);init.append(np.asarray(c,float))
    rows=relax_coeffs(init,q0,basis,reaction,0.0,args.few_shots,live,workers,args.maxiter,'seed')
    provenance=[{'coeff':r['coeff'],'kind':'seed'} for r in rows]
    for rd in range(args.rounds):
        labels,_=assign_labels(rows);sc={tuple(np.round(r['coeff'],10)) for r in rows if abs(r.get('reaction_bias',0))<1e-15}
        cand=boundary_candidates(rows,labels,lo,hi,args.per_round,sc,rd)
        if not cand:break
        print(f'ROUND {rd} n={len(cand)} top={cand[0][2]}',flush=True)
        C=[x[1] for x in cand];new=relax_coeffs(C,q0,basis,reaction,0.0,args.few_shots,live,workers,args.maxiter,f'r{rd}')
        rows.extend(new)
        for r,item in zip(new,cand):provenance.append({'coeff':r['coeff'],'kind':'junction-centroid','meta':item[2],'score':item[0]})
        if min(r['energy'] for r in new)<live-2e-7:break
    # Final heterogeneous centroids, now probed on both reaction sides.
    labels,_=assign_labels(rows);cand=boundary_candidates(rows,labels,lo,hi,args.reaction_probes,set(),99)
    if cand:
        C=[x[1] for x in cand]
        for rb in (-args.reaction_bias,args.reaction_bias):
            new=relax_coeffs(C,q0,basis,reaction,rb,args.few_shots,live,workers,args.maxiter,f'react{rb:+g}')
            rows.extend(new)
            for r,item in zip(new,cand):provenance.append({'coeff':r['coeff'],'kind':'reaction-side','reaction_bias':rb,'meta':item[2],'score':item[0]})
    labels,clusters=assign_labels(rows)
    for r,l in zip(rows,labels):r['basin_label']=l
    # Inventory and distinct representatives.
    inv={};reps=[]
    for r in rows:
        z=inv.setdefault(r['basin_label'],{'count':0,'best_energy':float('inf'),'best_coeff':None,'best_reaction_bias':None,'signature':None})
        z['count']+=1
        if r['energy']<z['best_energy']:
            z.update(best_energy=r['energy'],best_coeff=r['coeff'],best_reaction_bias=r['reaction_bias'],signature={'coord':r['coord'],'components':r['components'],'twin_count':r['twin_count']})
        sk=sigkey(r)
        if not any(abs(r['energy']-q['energy'])<2e-7 and sk==q['_sig'] for q in reps):
            q=dict(r);q['_sig']=sk;reps.append(q)
    reps.sort(key=lambda r:r['energy']);newreps=[r for r in reps if r['basin_label'].startswith('U')]
    print('BASINS',json.dumps(inv,sort_keys=True),flush=True)
    # Automatic second-hop from two lowest new basins.
    env=os.environ.copy()
    for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):env[k]='1'
    tasks=[]
    for j,r in enumerate(newreps[:2]):
        seed=outdir/f'new-seed-{j}.json';seed.write_text(json.dumps({'energy':r['energy'],'points':r['points']},separators=(',',':'))+'\n')
        for m in range(4):
            for s in (-1,1):
                tag=f'n{j}-m{m}-s{s:+d}';o=outdir/f'second-{tag}.json';log=outdir/f'second-{tag}.log'
                cmd=[sys.executable,str(pathlib.Path(__file__).resolve().parent/'search_from_seed_modes.py'),args.few_shots,str(seed),'--mode',str(m),'--sign',str(s),
                     '--amps','0.003,0.006,0.010,0.016,0.024,0.036','--out',str(o)]
                tasks.append((tag,o,log,cmd))
    second=[]
    if tasks:
        with cf.ThreadPoolExecutor(max_workers=workers) as ex:
            fut={ex.submit(run_logged,c,l,env):(t,o,l) for t,o,l,c in tasks}
            for f in cf.as_completed(fut):
                t,o,l=fut[f];rc=f.result();z={'tag':t,'returncode':rc,'out':str(o),'log':str(l)}
                if rc==0 and o.exists():
                    d=json.loads(o.read_text());z.update(best_energy=d['best_float_energy'],best_delta=d['best_delta_vs_live_score'])
                    print('SECOND',t,z['best_energy'],z['best_delta'],flush=True)
                second.append(z)
    best=min(rows,key=lambda r:r['energy']);top=[]
    for r in reps[:10]:
        top.append({k:v for k,v in r.items() if k!='_sig'})
    compact=[{k:v for k,v in r.items() if k!='points'} for r in rows]
    out={'live_score':live,'live_shot':str(live_dir.relative_to(root)),'modes':mids,'mode_eigenvalues':[modes[m]['eigenvalue'] for m in mids],
         'lo':lo.tolist(),'hi':hi.tolist(),'evaluations':len(rows),'rows':compact,'provenance':provenance,'basin_inventory':inv,
         'new_basin_count':len(newreps),'top_representatives':top,'second_hop':second,'best_energy':best['energy'],'best_delta_vs_live':best['delta_vs_live'],
         'best_points':best['points'] if best['energy']<live-2e-7 else None}
    (outdir/'bd-junction-active.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
    print(f'BEST {best["energy"]:.12f} d={best["delta_vs_live"]:+.12g} label={best["basin_label"]}',flush=True)
if __name__=='__main__':main()
