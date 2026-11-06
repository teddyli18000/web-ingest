#!/usr/bin/env python3
"""Search lower Thomson N960 energies via Riesz-exponent landscape homotopy.

Change the interaction law, not merely the coordinates. Starting from distinct
near-record N960 minima, move the SAME 960 particles through a Riesz r^-s
landscape at s != 1 (soft logarithmic-like and hard packing-like potentials),
relax there, apply coupled scar motion while the energy barriers are different,
and adiabatically return to physical s=1. Every genuine final s=1 structure
is fully Coulomb-polished, with sub-record coordinates preserved.

A control uses the same coordinate perturbation at physical s=1 directly.
The power-law energy and analytic sphere gradient are independently checked
by centered finite differences and cross-tested against the existing Coulomb
engine at s=1. All stage energies are trial-relative compensated sums to avoid
catastrophic cancellation at high N.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib

import numpy as np
from numba import njit
from scipy.optimize import minimize

import search_hamiltonian_scar_braid as hb
import search_size_beam as sb

RECORD=444368.3924061973


@njit(cache=True)
def pair_power_terms(q,s):
    n=q.size//2
    x=np.empty((n,3),np.float64)
    for i in range(n):
        th=q[2*i];ph=q[2*i+1]
        st=math.sin(th)
        x[i,0]=st*math.cos(ph)
        x[i,1]=st*math.sin(ph)
        x[i,2]=math.cos(th)
    inv=np.empty(n*(n-1)//2,np.float64)
    k=0
    for i in range(n):
        for j in range(i+1,n):
            d2=0.0
            for a in range(3):
                t=x[i,a]-x[j,a]
                d2+=t*t
            inv[k]=math.pow(max(d2,1e-20),-s/2.)
            k+=1
    return inv


@njit(cache=True)
def power_relative_fg(q,ref,s):
    n=q.size//2
    x=np.empty((n,3),np.float64)
    dt=np.empty((n,3),np.float64)
    dp=np.empty((n,3),np.float64)
    for i in range(n):
        th=q[2*i];ph=q[2*i+1]
        st=math.sin(th);ct=math.cos(th)
        cp=math.cos(ph);sp=math.sin(ph)
        x[i,0]=st*cp;x[i,1]=st*sp;x[i,2]=ct
        dt[i,0]=ct*cp;dt[i,1]=ct*sp;dt[i,2]=-st
        dp[i,0]=-st*sp;dp[i,1]=st*cp;dp[i,2]=0.0
    force=np.zeros((n,3),np.float64)
    delta=0.0
    comp=0.0
    k=0
    for i in range(n):
        for j in range(i+1,n):
            d2=0.0
            for a in range(3):
                diff=x[i,a]-x[j,a]
                d2+=diff*diff
            d2=max(d2,1e-20)
            inv=math.pow(d2,-s/2.)
            tmp=(inv-ref[k])-comp
            acc=delta+tmp
            comp=(acc-delta)-tmp
            delta=acc
            w=s*inv/d2
            for a in range(3):
                force[i,a]+=w*x[j,a]
                force[j,a]+=w*x[i,a]
            k+=1
    g=np.empty(q.size,np.float64)
    for i in range(n):
        g[2*i]=force[i,0]*dt[i,0]+force[i,1]*dt[i,1]+force[i,2]*dt[i,2]
        g[2*i+1]=force[i,0]*dp[i,0]+force[i,1]*dp[i,1]+force[i,2]*dp[i,2]
    return delta,g


def selftest(x):
    q=sb.xyz_to_vars(x)
    ref=pair_power_terms(q,1.)
    ref2=hb.pair_inverse(q)
    assert np.max(np.abs(ref-ref2))<1e-11
    test_rng=np.random.default_rng(921)
    for s in (0.25,1.,2.6):
        terms=pair_power_terms(q,s)
        e,g=power_relative_fg(q,terms,s)
        assert abs(e)<1e-7
        for j in test_rng.choice(q.size,size=8,replace=False):
            h=2e-6
            p=q.copy();m=q.copy();p[j]+=h;m[j]-=h
            fp=power_relative_fg(p,terms,s)[0]
            fm=power_relative_fg(m,terms,s)[0]
            df=(fp-fm)/(2*h)
            if abs(df-g[j])>1e-4*(1+abs(df)):
                raise RuntimeError((s,j,df,g[j]))
    return float(math.fsum(ref.tolist()))


def power_polish(x,s,maxiter):
    q0=sb.xyz_to_vars(x)
    ref=pair_power_terms(q0,float(s))
    e0=float(math.fsum(ref.tolist()))
    def fg(q):
        return power_relative_fg(q,ref,float(s))
    r=minimize(fg,q0,jac=True,method='L-BFGS-B',
               bounds=[(1e-8,math.pi-1e-8),(None,None)]*len(x),
               options={'maxiter':maxiter,'gtol':2e-8,'ftol':1e-15,
                        'maxls':60,'maxcor':30})
    de,g=fg(r.x)
    theta=r.x[0::2]
    rms=float(np.sqrt(np.mean(g[0::2]**2+
        (g[1::2]/np.maximum(np.sin(theta),1e-7))**2)))
    return e0+de,sb.vars_to_xyz(r.x)[0],int(r.nit),bool(r.success),rms


def read_seeds(fewshots,elite_json):
    record,shot=sb.find_live(fewshots)
    assert abs(record-RECORD)<1e-7
    seeds=[('R',sb.load_cert(shot/'certificate.json')),
           ('D2',sb.load_cert(fewshots/'problems/p007-thomson-problem/shots/Abreto/thomson960-d2-ga/certificate.json'))]
    elite=json.loads(elite_json.read_text())
    for i,p in enumerate(elite['minima'][:4]):
        seeds.append((f'W{i}',np.asarray(p['points'],float)))
    return seeds


def physical_quench(x,maxiter):
    E,y,nit,ok,grms=hb.polish(x,maxiter)
    if grms>3e-4:
        E,y,nmore,ok2,grms=hb.polish(y,maxiter+450)
        nit+=nmore
    return E,y,nit,grms


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots',type=pathlib.Path)
    ap.add_argument('--elite-json',type=pathlib.Path,required=True)
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--cycles',type=int,default=190)
    ap.add_argument('--maxiter',type=int,default=600)
    ap.add_argument('--out',type=pathlib.Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    seeds=read_seeds(args.few_shots,args.elite_json)
    E0=selftest(seeds[0][1])
    assert abs(E0-RECORD)<3e-6
    pool=[]
    for tag,x in seeds:
        E,y,nit,grad=physical_quench(x,1500)
        print('SEED',tag,f'{E:.12f}','grad',grad,flush=True)
        if all(abs(E-z['energy'])>4e-7 for z in pool):
            pool.append({'energy':E,'points':y.copy(),'tag':tag})
    pool.sort(key=lambda x:x['energy'])
    print('POWER_TEST',E0,'PARENTS',[(z['tag'],z['energy']) for z in pool],flush=True)
    best=RECORD
    hits=0
    rows=[]
    target_exponents=[.18,.35,.55,.78,1.27,1.7,2.4,3.4]
    stage_count={.18:3,.35:3,.55:2,.78:2,1.27:2,1.7:2,2.4:3,3.4:3}
    for t in range(args.cycles):
        # Favor high-quality donors but choose other defect patterns regularly.
        if t%7==0:parent=pool[0]
        else:
            weights=np.exp(-np.arange(len(pool))/4.)
            weights/=weights.sum()
            parent=pool[int(rng.choice(len(pool),p=weights))]
        x=parent['points'].copy()
        exponent=float(rng.choice(target_exponents))
        ctrl=(t%6==0)
        intermediate=[]
        if not ctrl:
            steps=stage_count[exponent]
            for j in range(1,steps+1):
                s=1+(exponent-1)*j/steps
                e,x,nit,ok,gr=power_polish(x,s,args.maxiter)
                intermediate.append({'s':float(s),'energy':float(e),'gradient':gr,'nit':nit})
        centers,_,_=hb.scar_centers(x)
        kind=str(rng.choice(['vortices','dipole','braid','randomcap'],
                            p=[.35,.25,.25,.15]))
        move=float(np.exp(rng.uniform(math.log(.014),math.log(.15))))
        pert=hb.transport(x,rng,centers,move,kind)
        md=hb.min_spacing(pert);contract=0
        while md<.038 and contract<6:
            pert=.5*(x+pert)
            pert/=np.linalg.norm(pert,axis=1)[:,None]
            md=hb.min_spacing(pert);contract+=1
        if md<.038:
            rows.append({'trial':t,'skipped':'collision','exponent':exponent,'kind':kind})
            continue
        x=pert
        if not ctrl:
            ep,x,nit,ok,gr=power_polish(x,exponent,args.maxiter)
            intermediate.append({'s':exponent,'energy':float(ep),'gradient':gr,'nit':nit})
            steps=stage_count[exponent]
            for j in range(steps-1,0,-1):
                s=1+(exponent-1)*j/steps
                e,x,nit,ok,gr=power_polish(x,s,args.maxiter)
                intermediate.append({'s':float(s),'energy':float(e),'gradient':gr,'nit':nit})
        E,Y,nit,grad=physical_quench(x,maxiter=args.maxiter+350)
        new=E<RECORD+.5 and all(abs(E-z['energy'])>3e-6 for z in pool)
        if new:
            pool.append({'energy':E,'points':Y.copy(),'tag':f'{t}-{exponent}-{kind}'})
            pool.sort(key=lambda z:z['energy'])
            if len(pool)>20:pool.pop()
            print('NEW',t,'s',exponent,'kind',kind,'E',f'{E:.12f}',
                  'deltaR',f'{E-RECORD:+.9f}',flush=True)
        if E<best-2e-7:
            best=E
            print('BEST',t,'E',f'{E:.12f}','deltaR',f'{E-RECORD:+.9f}',flush=True)
        if E<RECORD-2e-7:
            path=args.out/f'CANDIDATE-{args.seed}-{t}.json'
            path.write_text(json.dumps({'points':Y.tolist(),'energy':E,'seed':args.seed,
                'trial':t,'target_exponent':exponent,'kind':kind,'gradient_rms':grad})+'\n')
            hits+=1
            print('CANDIDATE',str(path),f'{E:.12f}',flush=True)
        rows.append({'trial':t,'parent':parent['tag'],'parent_energy':parent['energy'],
                     'exponent':exponent,'control_at_s1':bool(ctrl),
                     'kind':kind,'amp':move,'contract':contract,
                     'energy':E,'delta_record':E-RECORD,'new_basin':new,'grad_rms':grad,
                     'intermediate':intermediate})
        if t%10==0:
            print('CYCLE',t,'s',exponent,'control',ctrl,
                  'E',f'{E:.12f}','deltaR',f'{E-RECORD:+.8f}',
                  'pool',len(pool),'best',f'{best:.12f}',flush=True)
        if t%10==0 or t==args.cycles-1:
            out={'seed':args.seed,'cycles_done':t+1,'target_cycles':args.cycles,
                 'best_energy':best,'delta_record':best-RECORD,
                 'subrecord_candidates':hits,'pool':[
                    {'energy':z['energy'],'tag':z['tag'],'points':z['points'].tolist()}
                    for z in pool[:14]],'rows':rows}
            (args.out/'result.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
    print('FINAL',args.seed,'BEST',f'{best:.12f}',
          'DELTA',f'{best-RECORD:+.9f}','CANDIDATES',hits,flush=True)


if __name__=='__main__':
    main()
