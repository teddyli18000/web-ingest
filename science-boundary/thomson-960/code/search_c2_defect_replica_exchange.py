#!/usr/bin/env python3
"""Construct N960 competitors by replica-exchange basin hopping in C2 orbit space.

The accepted record is C3; the independently strong D2 20-dislocation parent
contains three exact C2 subgroups but has not been exploited with a C2 replica
exchange ensemble. Here the D2 parent is projected onto a 480-representative
C2 orbit manifold, then six temperature replicas make either equivariant
topology-aware divergence-free scar flows or C2-independent local noise kicks.
Every new sufficiently low C2 minimum is also released into the unconstrained
960-particle physical landscape. Candidates below the live score are saved.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib

import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree

import search_hamiltonian_scar_braid as braid
import search_size_beam as sb

NREP=480
RECORD=444368.3924061973


def rot_pi(x):
    y=np.asarray(x,float).copy()
    y[:,0]*=-1.0
    y[:,1]*=-1.0
    return y


def from_d2(x):
    tree=cKDTree(x)
    d,idx=tree.query(rot_pi(x),k=1)
    if len(np.unique(idx))!=len(x) or float(max(d))>1e-3:
        raise RuntimeError(('D2 source not C2 about z axis',float(max(d))))
    seen=set()
    reps=[]
    for i in range(len(x)):
        if i in seen:continue
        j=int(idx[i])
        if j==i or int(idx[j])!=i:raise RuntimeError(('bad pairing',i,j))
        seen.update([i,j])
        a=(x[i]+rot_pi(x[j:j+1])[0])/2.0
        a/=np.linalg.norm(a)
        reps.append(a)
    if len(reps)!=NREP:raise RuntimeError(('incorrect orbit count',len(reps)))
    return np.asarray(reps,float),float(max(d))


def qfull(v):
    a=v.reshape(-1,2)
    b=a.copy()
    b[:,1]+=math.pi
    return np.vstack([a,b]).ravel()


def xyzfull(v):
    x=sb.vars_to_xyz(v)[0]
    return np.vstack([x,rot_pi(x)])


def c2_polish(v0,maxiter):
    q0=qfull(v0)
    ref=braid.pair_inverse(q0)
    E0=math.fsum(ref.tolist())
    def fg(v):
        d,g=braid.relative_energy_gradient(qfull(v),ref)
        return d,g[:2*NREP]+g[2*NREP:]
    r=minimize(fg,v0,method='L-BFGS-B',jac=True,
               bounds=[(1e-8,math.pi-1e-8),(None,None)]*NREP,
               options={'maxiter':maxiter,'gtol':2e-8,'ftol':1e-15,
                        'maxls':60,'maxcor':35})
    de,g=fg(r.x)
    p=r.x.reshape(-1,2)
    gr=float(np.sqrt(np.mean(g[0::2]**2+
             (g[1::2]/np.maximum(np.sin(p[:,0]),1e-7))**2)))
    return E0+de,r.x,int(r.nit),bool(r.success),gr


def move(v,rng,mode):
    x=xyzfull(v)
    centers,_,_=braid.scar_centers(x)
    if mode=='randomcap':
        sel=centers[rng.integers(len(centers),size=int(rng.integers(1,4)))]
        h=float(rng.uniform(.14,.48))
        w=np.sum([np.exp((x[:NREP]@c-1)/(h*h)) for c in sel],axis=0)
        u=rng.normal(size=(NREP,3))
        z=x[:NREP]
        u-=np.sum(u*z,axis=1)[:,None]*z
        u*=w[:,None]
        rms=np.sqrt(float(np.mean(np.sum(u*u,axis=1))))
        scale=float(np.exp(rng.uniform(math.log(.009),math.log(.10))))
        if rms>1e-10:u*=scale/rms
        md=float(np.max(np.linalg.norm(u,axis=1)))
        if md>.35:u*=.35/md
        result=braid.expmap(z,u)
        return sb.xyz_to_vars(result),scale
    k=int(rng.integers(1,5))
    sel=centers[rng.integers(len(centers),size=k)]
    ctr=np.vstack([sel,rot_pi(sel)])
    amp=rng.normal(size=k)
    coeff=np.r_[amp,amp]
    widths=rng.uniform(.14,.49,size=k)
    widths=np.r_[widths,widths]
    scale=float(np.exp(rng.uniform(math.log(.012),math.log(.15))))
    y=x.copy()
    tscale=scale
    factor=None
    for _ in range(5):
        field=braid.hamiltonian_velocity(y,ctr,coeff,widths)
        if factor is None:
            norm=np.sqrt(float(np.mean(np.sum(field*field,axis=1))))
            if norm<1e-12:return v.copy(),scale
            factor=tscale/norm
        step=field*(factor/5)
        ms=float(np.max(np.linalg.norm(step,axis=1)))
        if ms>.09:step*=.09/ms
        y=braid.expmap(y,step)
    return sb.xyz_to_vars(y[:NREP]),scale


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots',type=pathlib.Path)
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--steps',type=int,default=160)
    ap.add_argument('--maxiter',type=int,default=650)
    ap.add_argument('--out',type=pathlib.Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    live,shot=sb.find_live(args.few_shots)
    assert abs(live-RECORD)<1e-7
    d2path=args.few_shots/'problems/p007-thomson-problem/shots/Abreto/thomson960-d2-ga/certificate.json'
    x=sb.load_cert(d2path)
    reps,err=from_d2(x)
    base_v=sb.xyz_to_vars(reps)
    e0,base_v,nit,ok,gr=c2_polish(base_v,1800)
    print('D2_C2_BASE',f'{e0:.12f}','delta',f'{e0-RECORD:+.9f}',
          'axis_fit',err,'nit',nit,'grad',gr,flush=True)
    if abs(e0-444368.40408053)>5e-4:
        raise RuntimeError(('unexpected D2 start energy',e0))
    temperatures=np.geomspace(.012,.35,6)
    replicas=[{'energy':e0,'v':base_v.copy()} for _ in temperatures]
    pool=[{'energy':e0,'v':base_v.copy(),'t':-1,'replica':-1}]
    best_full=1e100
    best_c2=e0
    rows=[]
    count_full=0
    candidates=0
    for step in range(args.steps):
        order=rng.permutation(len(replicas))
        for repidx in order:
            current=replicas[int(repidx)]
            mode='flow' if rng.random()<.68 else 'randomcap'
            start,scale=move(current['v'],rng,mode)
            E,v,nit,ok,gr=c2_polish(start,args.maxiter)
            if gr>1e-3:E,v,nmore,ok,gr=c2_polish(v,950);nit+=nmore
            de=E-current['energy']
            temperature=float(temperatures[repidx])
            accept=de<=0 or rng.random()<math.exp(-min(1e5,max(0.,de))/temperature)
            if accept:replicas[repidx]={'energy':E,'v':v}
            unique=E<RECORD+.50 and all(abs(E-p['energy'])>3e-7 for p in pool)
            row={'step':step,'replica':int(repidx),'temp':temperature,'mode':mode,
                 'scale':scale,'energy_c2':E,'delta_record_c2':E-RECORD,
                 'nit':nit,'grad_c2':gr,'accepted':bool(accept),'unique':bool(unique)}
            if unique:
                pool.append({'energy':E,'v':v.copy(),'t':step,'replica':int(repidx)})
                pool.sort(key=lambda p:p['energy'])
                if len(pool)>35:pool.pop()
            if E<best_c2-1e-7:
                best_c2=E
                print('BEST_C2',step,int(repidx),f'E={E:.12f}',
                      f'delta={E-RECORD:+.9f}',mode,flush=True)
            # Release all distinct plausible C2 minima; do not assume a C2
            # constrained minimum is a stable full-space state.
            if unique and E<RECORD+.10:
                Efull,y,fnit,fok,fgr=braid.polish(xyzfull(v),1600)
                count_full+=1
                row['energy_full']=Efull
                row['delta_record_full']=Efull-RECORD
                row['full_nit']=fnit
                row['full_grad_rms']=fgr
                if Efull<best_full-1e-8:
                    best_full=Efull
                    print('BEST_FULL',step,int(repidx),f'E={Efull:.12f}',
                          f'delta={Efull-RECORD:+.9f}',f'grad={fgr:.4g}',flush=True)
                if Efull<RECORD-2e-7:
                    fname=f'CANDIDATE-c2-{args.seed}-{step}-{repidx}.json'
                    (args.out/fname).write_text(json.dumps(
                        {'points':y.tolist(),'energy':Efull,'seed':args.seed,'step':step,
                         'replica':int(repidx),'source_c2_energy':E})+'\n')
                    row['candidate_file']=fname
                    candidates+=1
                    print('CANDIDATE',fname,'E',f'{Efull:.12f}',flush=True)
            rows.append(row)
        # Adjacent replica swaps preserve the product Boltzmann measure.
        for i in range(step%2,5,2):
            ei,ej=replicas[i]['energy'],replicas[i+1]['energy']
            logr=(1/temperatures[i]-1/temperatures[i+1])*(ei-ej)
            if logr>=0 or rng.random()<math.exp(max(-700.,logr)):
                replicas[i],replicas[i+1]=replicas[i+1],replicas[i]
        if step%4==0:
            print('SWEEP',step,'energies',[round(x['energy']-RECORD,6) for x in replicas],
                  'C2',f'{best_c2:.12f}','FULL',best_full,'pool',len(pool),
                  'full_releases',count_full,flush=True)
        if step%10==0 or step==args.steps-1:
            result={'seed':args.seed,'steps_done':step+1,'steps_target':args.steps,
                    'parent_energy':e0,'axis_fit':err,
                    'best_c2_energy':best_c2,'best_full_energy':best_full,
                    'full_releases':count_full,'candidates':candidates,
                    'temperatures':temperatures.tolist(),
                    'pool':[{'energy':p['energy'],'step':p['t'],'replica':p['replica']}
                            for p in pool],
                    'rows':rows}
            (args.out/'result.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    print('FINAL',args.seed,'best_c2',f'{best_c2:.12f}',
          'best_full',f'{best_full:.12f}','candidates',candidates,flush=True)


if __name__=='__main__':
    main()
