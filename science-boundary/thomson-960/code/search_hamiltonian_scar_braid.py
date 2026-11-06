#!/usr/bin/env python3
"""Candidate-generating Thomson N=960 basin search by scar-coupled spherical flows.

Instead of a fixed Hessian/event/basin boundary representation, construct
collective particle motions as compositions of area-preserving Hamiltonian
flows whose streamfunction centers track the 12 topological defect scars.
Every proposed 960-point configuration is locally minimized and scored
against the *actual* live Few Shots energy. Distinct near-record minima are
reused as parents; a control operator uses independent local particle noise.

The Coulomb pair kernel is NumBa-compiled for efficient gradient evaluations,
and minimizes a compensated pair-energy difference against the trial's fixed
starting geometry to avoid cancellation at the N=960 baseline ~4.4e5.
This is a global stochastic candidate generator, not a proof or certificate.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
from collections import Counter

import numpy as np
from numba import njit
from scipy.optimize import minimize
from scipy.spatial import ConvexHull

import search_size_beam as sb

N = 960
RECORD = 444368.3924061973


@njit(cache=True)
def pair_inverse(q):
    n=q.size//2
    x=np.empty((n,3),np.float64)
    for i in range(n):
        th=q[2*i]; ph=q[2*i+1]
        st=math.sin(th)
        x[i,0]=st*math.cos(ph)
        x[i,1]=st*math.sin(ph)
        x[i,2]=math.cos(th)
    pairs=np.empty(n*(n-1)//2,np.float64)
    k=0
    for i in range(n):
        for j in range(i+1,n):
            dx=x[i,0]-x[j,0]
            dy=x[i,1]-x[j,1]
            dz=x[i,2]-x[j,2]
            d2=dx*dx+dy*dy+dz*dz
            pairs[k]=1.0/math.sqrt(max(d2,1e-20))
            k+=1
    return pairs


@njit(cache=True)
def relative_energy_gradient(q,reference):
    n=q.size//2
    x=np.empty((n,3),np.float64)
    theta=np.empty((n,3),np.float64)
    phi=np.empty((n,3),np.float64)
    for i in range(n):
        th=q[2*i]; ph=q[2*i+1]
        st=math.sin(th); ct=math.cos(th)
        cp=math.cos(ph); sp=math.sin(ph)
        x[i,0]=st*cp; x[i,1]=st*sp; x[i,2]=ct
        theta[i,0]=ct*cp; theta[i,1]=ct*sp; theta[i,2]=-st
        phi[i,0]=-st*sp; phi[i,1]=st*cp; phi[i,2]=0.0
    gc=np.zeros((n,3),np.float64)
    de=0.0
    compensation=0.0
    k=0
    for i in range(n):
        for j in range(i+1,n):
            dx=x[i,0]-x[j,0]
            dy=x[i,1]-x[j,1]
            dz=x[i,2]-x[j,2]
            d2=max(dx*dx+dy*dy+dz*dz,1e-20)
            inv=1.0/math.sqrt(d2)
            term=(inv-reference[k])-compensation
            accum=de+term
            compensation=(accum-de)-term
            de=accum
            w=inv/d2
            for a in range(3):
                gc[i,a]+=w*x[j,a]
                gc[j,a]+=w*x[i,a]
            k+=1
    g=np.empty(q.size,np.float64)
    for i in range(n):
        g[2*i]=gc[i,0]*theta[i,0]+gc[i,1]*theta[i,1]+gc[i,2]*theta[i,2]
        g[2*i+1]=gc[i,0]*phi[i,0]+gc[i,1]*phi[i,1]+gc[i,2]*phi[i,2]
    return de,g


def energy_gradient_selftest(q):
    pair=pair_inverse(q)
    E=math.fsum(pair.tolist())
    e,g=relative_energy_gradient(q,pair)
    assert abs(e)<5e-9
    rng=np.random.default_rng(960)
    indices=rng.choice(len(q),size=12,replace=False)
    for idx in indices:
        h=2e-6
        qp=q.copy(); qm=q.copy(); qp[idx]+=h;qm[idx]-=h
        fp,_=relative_energy_gradient(qp,pair)
        fm,_=relative_energy_gradient(qm,pair)
        fd=(fp-fm)/(2*h)
        if abs(fd-g[idx])>5e-5*(1+abs(fd)):
            raise RuntimeError(('gradient mismatch',idx,fd,g[idx]))
    return E


def energy_abs(q):
    return math.fsum(pair_inverse(q).tolist())


def polish(x0,maxiter):
    q0=sb.xyz_to_vars(x0)
    ref=pair_inverse(q0)
    E0=math.fsum(ref.tolist())
    def fg(q):
        return relative_energy_gradient(q,ref)
    r=minimize(fg,q0,jac=True,method='L-BFGS-B',
               bounds=[(1e-8,math.pi-1e-8),(None,None)]*len(x0),
               options={'maxiter':maxiter,'gtol':1e-8,'ftol':1e-15,
                        'maxls':60,'maxcor':30})
    de,g=fg(r.x)
    q=r.x.reshape(-1,2)
    gradphys=np.sqrt(float(np.mean(g[0::2]**2+
                     (g[1::2]/np.maximum(np.sin(q[:,0]),1e-7))**2)))
    x=sb.vars_to_xyz(r.x)[0]
    return E0+de,x,int(r.nit),bool(r.success),gradphys


def scar_centers(x):
    hull=ConvexHull(x)
    tri=hull.simplices
    edges=np.vstack([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]])
    edges=np.unique(np.sort(edges,axis=1),axis=0)
    degree=np.bincount(edges.ravel(),minlength=len(x))
    defect=np.flatnonzero(degree!=6)
    adj=[[] for _ in range(len(x))]
    for a,b in edges:
        if degree[a]!=6 and degree[b]!=6:
            adj[a].append(int(b))
            adj[b].append(int(a))
    visited=set(); parts=[]
    for v in defect:
        v=int(v)
        if v in visited:continue
        queue=[v];visited.add(v);component=[]
        while queue:
            i=queue.pop();component.append(i)
            for j in adj[i]:
                if j not in visited:
                    visited.add(j);queue.append(j)
        charge=int(np.sum(6-degree[component]))
        center=np.mean(x[component],axis=0)
        center/=np.linalg.norm(center)
        parts.append((charge,len(component),center))
    # Center positive topological-charge objects, not arbitrary particle labels.
    centers=np.array([c for charge,_,c in parts if charge>0])
    if len(centers)<3:
        centers=np.array([x[i] for i in np.flatnonzero(degree==5)])
    return centers,Counter(map(int,degree)),len(parts)


def expmap(x,v):
    speed=np.linalg.norm(v,axis=1)
    out=np.cos(speed)[:,None]*x
    small=speed<1e-12
    f=np.empty_like(speed)
    f[small]=1.0
    f[~small]=np.sin(speed[~small])/speed[~small]
    out+=f[:,None]*v
    out/=np.linalg.norm(out,axis=1)[:,None]
    return out


def hamiltonian_velocity(x,centers,amplitudes,widths):
    # x cross grad(psi), psi=sum_j a_j*exp[(c_j.x-1)/h_j^2].
    # Continuum vector field has exactly zero spherical divergence.
    v=np.zeros_like(x)
    for c,a,h in zip(centers,amplitudes,widths):
        k=np.exp((x@c-1.0)/(h*h))*(a/(h*h))
        v+=k[:,None]*np.cross(x,c)
    return v


def transport(x,rng,centers,scale,mode):
    n=len(x)
    if mode=='randomcap':
        k=int(rng.integers(1,5))
        src=centers[rng.integers(len(centers),size=k)]
        r=float(rng.uniform(0.14,0.50))
        w=np.sum([np.exp((x@c-1)/(r*r)) for c in src],axis=0)
        v=rng.normal(size=x.shape)
        v-=np.sum(v*x,axis=1)[:,None]*x
        v*=w[:,None]
        nr=math.sqrt(float(np.mean(np.sum(v*v,axis=1))))
        if nr<1e-12:return x.copy()
        v*=scale/nr
        mx=float(np.max(np.linalg.norm(v,axis=1)))
        if mx>0.43:v*=0.43/mx
        return expmap(x,v)

    rounds=1 if mode in ('vortices','dipole') else int(rng.integers(2,5))
    z=x.copy()
    for t in range(rounds):
        if mode=='dipole':
            ids=rng.choice(len(centers),2,replace=False)
            ctr=centers[ids]
            coeff=np.array([1.0,-1.0])*float(rng.choice([-1.,1.]))
        else:
            k=int(rng.integers(2,7))
            ids=rng.choice(len(centers),k,replace=k>len(centers))
            ctr=centers[ids]
            coeff=rng.normal(size=k)
            coeff-=np.mean(coeff)
        widths=rng.uniform(0.14,0.55,size=len(ctr))
        nsub=5
        tscale=scale/math.sqrt(rounds)
        amp=None
        for sub in range(nsub):
            v=hamiltonian_velocity(z,ctr,coeff,widths)
            if amp is None:
                norm=math.sqrt(float(np.mean(np.sum(v*v,axis=1))))
                if norm<1e-12:break
                amp=tscale/norm
            dv=v*(amp/nsub)
            localmax=float(np.max(np.linalg.norm(dv,axis=1)))
            if localmax>0.095:dv*=0.095/localmax
            z=expmap(z,dv)
    return z


def min_spacing(x):
    from scipy.spatial import cKDTree
    return float(cKDTree(x).query(x,k=2)[0][:,1].min())


def load_seed_files(fewshots,chord_dir):
    score,shot=sb.find_live(fewshots)
    if abs(score-RECORD)>1e-7:
        raise RuntimeError(('live score changed',score,RECORD))
    x=sb.load_cert(shot/'certificate.json')
    d2=fewshots/'problems/p007-thomson-problem/shots/Abreto/thomson960-d2-ga/certificate.json'
    seeds=[('R',x),('D2',sb.load_cert(d2))]
    if chord_dir is not None:
        for name,label in [('A','886-380-s0.48'),('B','886-960-s0.78')]:
            path=chord_dir/f'thomson-saddle-chord-{label}'/'result.json'
            d=json.loads(path.read_text())
            y=np.asarray(d['rows'][0]['saddle_points'],float)
            seeds.append((name,np.delete(y,960,axis=0)))
    return seeds


def novel_pool(pool,energy,coords,tag,limit=22):
    if energy>RECORD+1.5:return False
    if any(abs(energy-p['energy'])<4e-7 for p in pool):return False
    pool.append({'energy':float(energy),'points':coords.copy(),'tag':tag})
    pool.sort(key=lambda p:p['energy'])
    if len(pool)>limit:pool.pop()
    return True


def serial_pool(pool,max_keep=12):
    return [{'energy':p['energy'],'tag':p['tag'],
             'points':p['points'].tolist()} for p in pool[:max_keep]]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots',type=pathlib.Path)
    ap.add_argument('--chord-dir',type=pathlib.Path)
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--trials',type=int,default=250)
    ap.add_argument('--maxiter',type=int,default=650)
    ap.add_argument('--temp',type=float,default=0.055)
    ap.add_argument('--out',type=pathlib.Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    seeds=load_seed_files(args.few_shots,args.chord_dir)
    selftest=energy_gradient_selftest(sb.xyz_to_vars(seeds[0][1]))
    if abs(selftest-RECORD)>1e-5:raise RuntimeError(('bad seed energy',selftest))
    pool=[];parents=[]
    for name,x in seeds:
        E,y,nit,ok,grms=polish(x,1800)
        print('SEED',name,'E',f'{E:.12f}','grms',grms,'nit',nit,flush=True)
        if name=='R' and abs(E-RECORD)>3e-6:raise RuntimeError(('bad record polish',E))
        novel_pool(pool,E,y,'seed-'+name)
        parents.append({'energy':E,'points':y,'label':name})
    walkers=[dict(p) for p in parents]
    best=min(p['energy'] for p in pool)
    rows=[];hits=0
    modes=['vortices','dipole','braid','randomcap']
    mode_weights=np.array([0.30,0.25,0.35,0.10])
    for t in range(args.trials):
        widx=t%len(walkers)
        parent=walkers[widx]
        if t>0 and t%40==0:
            chosen=pool[int(rng.integers(min(len(pool),10)))]
            walkers[widx]={'energy':chosen['energy'],'points':chosen['points'].copy(),
                           'label':'pool-reseed'}
            parent=walkers[widx]
        x=parent['points']
        centers,degrees,components=scar_centers(x)
        mode=str(rng.choice(modes,p=mode_weights))
        scale=float(np.exp(rng.uniform(math.log(0.018),math.log(0.16))))
        pert=transport(x,rng,centers,scale,mode)
        spacing=min_spacing(pert)
        if spacing<0.026:
            rows.append({'trial':t,'mode':mode,'scale':scale,'skip':'collision',
                         'min_spacing':spacing})
            continue
        E,z,nit,ok,grms=polish(pert,args.maxiter)
        if grms>1e-3:
            E,z,more,ok2,grms=polish(z,1000)
            nit+=more
        unique=novel_pool(pool,E,z,f'{t}-{mode}')
        de=E-parent['energy']
        T=args.temp*(0.6+0.65*(widx/max(1,len(walkers)-1)))
        accepted=de<0 or rng.random()<math.exp(-max(de,0)/T)
        if accepted:walkers[widx]={'energy':E,'points':z,'label':f'{t}-{mode}'}
        if E<best-1e-7:
            best=E
            print('BEST',t,mode,'E',f'{E:.12f}','delta',f'{E-RECORD:+.9f}',
                  'nit',nit,'grms',grms,'uniques',len(pool),flush=True)
        if E<RECORD-2e-7:
            candidate={'energy':E,'points':z.tolist(),'trial':t,'mode':mode,
                       'seed':args.seed,'gradient_rms':grms}
            target=args.out/f'CANDIDATE-{args.seed}-{t}.json'
            target.write_text(json.dumps(candidate,separators=(',',':'))+'\n')
            print('CANDIDATE',target,'E',f'{E:.12f}',flush=True)
            hits+=1
        row={'trial':t,'parent_energy':parent['energy'],'energy':E,
             'delta_record':E-RECORD,'mode':mode,'scale':scale,
             'min_spacing':spacing,'nit':nit,'grad_rms':grms,
             'accepted':accepted,'unique':unique,
             'num_scar_centers':len(centers),'num_defect_components':components,
             'coord_counts':{str(k):int(v) for k,v in degrees.items()}}
        rows.append(row)
        if t%10==0:
            print('TRIAL',t,mode,'E',f'{E:.12f}','delta',f'{E-RECORD:+.6f}',
                  'acc',accepted,'unique',unique,'grms',f'{grms:.2g}',
                  'pool',len(pool),'best',f'{best:.12f}',flush=True)
        if t%20==0 or t==args.trials-1:
            saved={'seed':args.seed,'trials_target':args.trials,'trials_done':t+1,
                   'best_energy':best,'best_delta_record':best-RECORD,
                   'record_score':RECORD,'candidates_below_record':hits,
                   'population':serial_pool(pool),'rows':rows,
                   'mode_weights':dict(zip(modes,mode_weights.tolist()))}
            (args.out/'result.json').write_text(json.dumps(saved,separators=(',',':'))+'\n')
    print('FINAL',args.seed,'trials',args.trials,'best',f'{best:.12f}',
          'delta',f'{best-RECORD:+.9g}','candidates',hits,
          'pool',len(pool),flush=True)


if __name__=='__main__':
    main()
