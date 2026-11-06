#!/usr/bin/env python3
"""Constructive Thomson N=960 search via anisotropic metric hysteresis loops.

Change the geometry of repulsion, not the seed perturbation alone. The physical
sphere and the number of particles remain fixed. At a nonidentity SPD
3x3 matrix Q, temporarily optimize
      E_Q(X) = sum_{i<j} [(x_i-x_j)^T Q (x_i-x_j)]^{-1/2}.
Two noncommuting defect-centered anisotropies Q1 and Q2 are traversed in a
closed loop through the SPD metric manifold. A coupled scar-flow disturbance
is made at Q1, the structure is reoptimized at Q2, then all anisotropy is
removed and a true physical s=1 Thomson quench scores the result.

The goal is hysteretic scar reorganization inaccessible to a one-shot
Hamiltonian displacement in a fixed isotropic potential. All derivatives
and Q=I equivalence to the independent Coulomb evaluator are self-tested.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from numba import njit
from scipy.optimize import minimize
import search_hamiltonian_scar_braid as hb
import search_size_beam as sb
RECORD=444368.3924061973

@njit(cache=True)
def pair_terms(q,Q):
    n=len(q)//2
    x=np.empty((n,3))
    for i in range(n):
        th=q[2*i];ph=q[2*i+1];st=math.sin(th)
        x[i,0]=st*math.cos(ph);x[i,1]=st*math.sin(ph);x[i,2]=math.cos(th)
    terms=np.empty(n*(n-1)//2)
    k=0
    for i in range(n):
        for j in range(i+1,n):
            a=x[i,0]-x[j,0];b=x[i,1]-x[j,1];c=x[i,2]-x[j,2]
            qa=Q[0,0]*a+Q[0,1]*b+Q[0,2]*c
            qb=Q[1,0]*a+Q[1,1]*b+Q[1,2]*c
            qc=Q[2,0]*a+Q[2,1]*b+Q[2,2]*c
            d2=max(a*qa+b*qb+c*qc,1e-20)
            terms[k]=1/math.sqrt(d2)
            k+=1
    return terms

@njit(cache=True)
def relative_fg(q,ref,Q):
    n=len(q)//2
    x=np.empty((n,3));dt=np.empty((n,3));dp=np.empty((n,3))
    for i in range(n):
        th=q[2*i];ph=q[2*i+1];st=math.sin(th);ct=math.cos(th)
        cp=math.cos(ph);sp=math.sin(ph)
        x[i,0]=st*cp;x[i,1]=st*sp;x[i,2]=ct
        dt[i,0]=ct*cp;dt[i,1]=ct*sp;dt[i,2]=-st
        dp[i,0]=-st*sp;dp[i,1]=st*cp;dp[i,2]=0.
    force=np.zeros((n,3))
    energy=0.;comp=0.;k=0
    for i in range(n):
        for j in range(i+1,n):
            a=x[i,0]-x[j,0];b=x[i,1]-x[j,1];c=x[i,2]-x[j,2]
            qa=Q[0,0]*a+Q[0,1]*b+Q[0,2]*c
            qb=Q[1,0]*a+Q[1,1]*b+Q[1,2]*c
            qc=Q[2,0]*a+Q[2,1]*b+Q[2,2]*c
            d2=max(a*qa+b*qb+c*qc,1e-20)
            inv=1/math.sqrt(d2)
            term=inv-ref[k]-comp
            nxt=energy+term
            comp=(nxt-energy)-term
            energy=nxt
            w=inv/d2
            force[i,0]-=qa*w;force[i,1]-=qb*w;force[i,2]-=qc*w
            force[j,0]+=qa*w;force[j,1]+=qb*w;force[j,2]+=qc*w
            k+=1
    g=np.empty(len(q))
    for i in range(n):
        g[2*i]=force[i,0]*dt[i,0]+force[i,1]*dt[i,1]+force[i,2]*dt[i,2]
        g[2*i+1]=force[i,0]*dp[i,0]+force[i,1]*dp[i,1]+force[i,2]*dp[i,2]
    return energy,g

def metric_polish(x,Q,maxiter):
    q=sb.xyz_to_vars(x)
    ref=pair_terms(q,Q)
    E0=math.fsum(ref.tolist())
    def fg(q):return relative_fg(q,ref,Q)
    r=minimize(fg,q,jac=True,method='L-BFGS-B',
        bounds=[(1e-8,math.pi-1e-8),(None,None)]*len(x),
        options={'maxiter':maxiter,'gtol':1e-8,'ftol':1e-15,
                 'maxls':60,'maxcor':30})
    d,g=fg(r.x)
    th=r.x[::2]
    gr=float(np.sqrt(np.mean(g[::2]**2+
         (g[1::2]/np.maximum(np.sin(th),1e-7))**2)))
    return E0+d,sb.vars_to_xyz(r.x)[0],int(r.nit),gr

def tracefree_axis(a):
    a=np.asarray(a,float)
    a/=np.linalg.norm(a)
    return 3*np.outer(a,a)-np.eye(3)

def metric_from_log(log):
    vals,V=np.linalg.eigh(log)
    return (V*np.exp(vals)[None,:])@V.T

def check(x):
    q=sb.xyz_to_vars(x)
    I=np.eye(3)
    ref=pair_terms(q,I)
    other=hb.pair_inverse(q)
    assert np.max(np.abs(ref-other))<1e-10
    # Cross-evaluate force components, not only the energy.
    e,g=relative_fg(q,ref,I)
    e2,g2=hb.relative_energy_gradient(q,other)
    assert abs(e)<1e-8 and abs(e2)<1e-8
    assert np.max(np.abs(g-g2))<5e-8,(np.max(np.abs(g-g2)),)
    rng=np.random.default_rng(1122)
    A=tracefree_axis(np.array([.4,.7,.59]))
    Q=metric_from_log(.31*A)
    reference=pair_terms(q,Q)
    e,g=relative_fg(q,reference,Q)
    assert abs(e)<1e-8
    for j in rng.choice(len(q),12,replace=False):
        d=1.5e-6
        p=q.copy();m=q.copy();p[j]+=d;m[j]-=d
        ep=relative_fg(p,reference,Q)[0];em=relative_fg(m,reference,Q)[0]
        fd=(ep-em)/(2*d)
        if abs(fd-g[j])>7e-5*(1+abs(fd)):
            raise RuntimeError(('metric gradient',int(j),float(fd),float(g[j])))
    return math.fsum(ref.tolist())

def seeds_from_sources(fewshots,elites):
    score,shot=sb.find_live(fewshots)
    assert abs(score-RECORD)<1e-7
    d2=fewshots/'problems/p007-thomson-problem/shots/Abreto/thomson960-d2-ga/certificate.json'
    out=[('R',sb.load_cert(shot/'certificate.json')),('D2',sb.load_cert(d2))]
    d=json.loads(elites.read_text())
    for p in d['minima'][:4]:out.append((p['origin_tag'],np.asarray(p['points'],float)))
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots',type=pathlib.Path)
    ap.add_argument('--elite-json',type=pathlib.Path,required=True)
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--cycles',type=int,default=110)
    ap.add_argument('--stage-maxiter',type=int,default=400)
    ap.add_argument('--out',type=pathlib.Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    starts=seeds_from_sources(args.few_shots,args.elite_json)
    selftest=check(starts[0][1])
    assert abs(selftest-RECORD)<3e-6
    pool=[]
    for name,X in starts:
        E,Y,n,gr=metric_polish(X,np.eye(3),1200)
        print('SEED',name,f'{E:.12f}','grad',gr,flush=True)
        if all(abs(E-z['energy'])>3e-6 for z in pool):
            pool.append({'energy':E,'points':Y,'tag':name})
    pool.sort(key=lambda r:r['energy'])
    best=RECORD
    seen=[]
    candidates=0;rows=[]
    for t in range(args.cycles):
        if t%8==0:parent=pool[0]
        else:
            weights=np.exp(-np.arange(len(pool))/3.0);weights/=weights.sum()
            parent=pool[int(rng.choice(len(pool),p=weights))]
        x=parent['points'].copy()
        centers,_,_=hb.scar_centers(x)
        if rng.random()<.65:
            a=centers[int(rng.integers(len(centers)))]
            b=centers[int(rng.integers(len(centers)))]
        else:
            a=rng.normal(size=3);a/=np.linalg.norm(a)
            b=rng.normal(size=3);b/=np.linalg.norm(b)
        T1=tracefree_axis(a);T2=tracefree_axis(b)
        strength=float(np.exp(rng.uniform(math.log(.07),math.log(.45))))
        direction=float(rng.choice([-1.,1.]))
        orientation=float(rng.choice([-1.,1.]))
        L1=direction*strength*T1
        L2=orientation*strength*T2
        direct=(t%9==0)
        energies=[]
        if not direct:
            for phase,log in [
                ('enter',.5*L1),('anisotropic1',L1)]:
                E,x,n,gr=metric_polish(x,metric_from_log(log),args.stage_maxiter)
                energies.append({'phase':phase,'E':E,'n':n,'gr':gr})
        mode=str(rng.choice(['vortices','dipole','braid','randomcap'],
                            p=[.30,.27,.33,.10]))
        mag=float(np.exp(rng.uniform(math.log(.014),math.log(.14))))
        Y=hb.transport(x,rng,centers,mag,mode)
        collision=hb.min_spacing(Y);shrink=0
        while collision<.037 and shrink<6:
            Y=.5*(x+Y)
            Y/=np.linalg.norm(Y,axis=1)[:,None]
            collision=hb.min_spacing(Y);shrink+=1
        if collision<.037:
            rows.append({'cycle':t,'skipped':'collision','direct':direct})
            continue
        x=Y
        if not direct:
            for phase,log in [
                ('kick_at_anisotropy1',L1),
                ('shear_metric',.4*L1+.6*L2),
                ('anisotropic2',L2),
                ('exit',.5*L2)]:
                E,x,n,gr=metric_polish(x,metric_from_log(log),args.stage_maxiter)
                energies.append({'phase':phase,'E':E,'n':n,'gr':gr})
        E,x,n,gr=metric_polish(x,np.eye(3),args.stage_maxiter+850)
        if gr>2e-4:
            E,x,n2,gr=metric_polish(x,np.eye(3),1200);n+=n2
        novel=E<RECORD+.5 and all(abs(E-z['energy'])>4e-6 for z in pool)
        if novel:
            pool.append({'energy':E,'points':x.copy(),'tag':f'{t}-{mode}-{strength:.3f}'})
            pool.sort(key=lambda r:r['energy'])
            pool=pool[:20]
            print('NEW',t,mode,'E',f'{E:.12f}','dR',f'{E-RECORD:+.9f}',
                  'strength',strength,'direct',direct,flush=True)
        if E<best-2e-7:
            best=E
            print('BEST',t,'E',f'{E:.12f}','dR',f'{E-RECORD:+.9f}',flush=True)
        if E<RECORD-2e-7:
            fname=args.out/f'CANDIDATE-{args.seed}-{t}.json'
            fname.write_text(json.dumps({'points':x.tolist(),'energy':E,
                'seed':args.seed,'cycle':t,'metric_strength':strength,
                'gradient_rms':gr})+'\n')
            candidates+=1
            print('CANDIDATE',fname,'E',E,flush=True)
        row={'cycle':t,'parent':parent['tag'],'energy':E,'delta_record':E-RECORD,
             'novel':novel,'control_at_isotropic':direct,'mode':mode,
             'metric_strength':strength,'metric_orientation':orientation,
             'min_spacing':collision,'contractions':shrink,'grad_rms':gr,
             'phase_energies':energies}
        rows.append(row)
        if t%8==0:
            print('CYCLE',t,'E',f'{E:.12f}','dR',f'{E-RECORD:+.7f}',
                  'novel',novel,'best',f'{best:.12f}',flush=True)
        if t%10==0 or t==args.cycles-1:
            result={'seed':args.seed,'cycles_done':t+1,'target_cycles':args.cycles,
                'best_energy':best,'best_delta_record':best-RECORD,
                'candidates':candidates,'selftest_record':selftest,
                'pool':[{'energy':p['energy'],'tag':p['tag'],
                         'points':p['points'].tolist()} for p in pool[:15]],
                'rows':rows}
            (args.out/'result.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    print('FINAL',args.seed,'best',f'{best:.12f}',
          'delta',f'{best-RECORD:+.9f}','candidates',candidates,flush=True)

if __name__=='__main__':
    main()
