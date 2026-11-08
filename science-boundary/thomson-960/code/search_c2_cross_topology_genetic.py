#!/usr/bin/env python3
"""p007 N960: cross-topology C2 orbital genetic / replica-exchange search.

Construct *independent* donors with 20 vs 24 dislocations:
  - 20-dislocation Few Shots D2=444368.4040805305, an exact C2 subgroup.
  - 24-dislocation Amore-Wales T=444368.4373479895, rotated into an exact
    C2 subgroup selected by its threefold axis and 180-degree symmetry fit.

Unlike previous C3 GA (24-dislocation R x T), C2 admits full recombination of
different defect counts without enforcing either parental D2/T point groups.
At each step: six-temperature replicas hop via C2 scar flow and noise;
two distinct parents make C2 symmetry preserving Deaven-Ho orbit cut-splice
and patch-transport offspring; selected C2 structures release all 960 points.
The only real metric is independent full-size Coulomb energy and all sub-R
numerical candidates are serialized for official Few Shots verification.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from scipy.optimize import linear_sum_assignment
import search_c2_defect_replica_exchange as c2
import search_t_c3_basin_hop as t3
import search_hamiltonian_scar_braid as hb
import search_size_beam as sb
RECORD=444368.3924061973
M=480
TWOPI=2*math.pi

def old_t_c2_reps(path,seed):
    x=t3.load_points(path)
    pole,_=t3.approximate_threefold_axis(x,seed=seed+100)
    err,rmse,axis,_=t3.refine_symmetry_axis(x,pole)
    y,alignmax,_=t3.align_axis_to_z(x,axis)
    # In an exact tetrahedral arrangement, the C2 axes form an angle
    # arccos(1/sqrt(3)) with a chosen C3 axis. Optimize azimuth of one axis.
    st=math.sqrt(2./3);ct=1./math.sqrt(3)
    tree=cKDTree(y)
    def test(phi):
        a=np.array([st*math.cos(phi),st*math.sin(phi),ct])
        z=2*(y@a)[:,None]*a[None,:]-y
        d,_=tree.query(z,k=1)
        return float(np.mean(d*d))
    phases=np.linspace(0,TWOPI/3,180,endpoint=False)
    p0=float(phases[np.argmin([test(p) for p in phases])])
    opt=minimize(lambda z:test(float(z[0])),[p0],method="Nelder-Mead",
                 options={"xatol":1e-14,"fatol":1e-24,"maxiter":450})
    phi=float(opt.x[0])
    n=np.array([st*math.cos(phi),st*math.sin(phi),ct])
    rot,_=Rotation.align_vectors(np.array([[0.,0.,1.]]),n[None,:])
    aligned=rot.apply(y)
    reps,c2err=c2.from_d2(aligned)
    if c2err>1e-6:raise RuntimeError(("T to C2 fit",c2err,err,alignmax))
    return sb.xyz_to_vars(reps),{"c3_max_err":alignmax,"c2_max_err":c2err,
              "azimuth":phi,"fit_objective":float(opt.fun)}

def phi_reps(v):
    return sb.vars_to_xyz(v)[0]

def canon(x):
    phi=np.arctan2(x[:,1],x[:,0])
    a=-np.floor((phi+math.pi/2)/math.pi)*math.pi
    cp=np.cos(a);sp=np.sin(a)
    y=x.copy()
    y[:,0]=cp*x[:,0]-sp*x[:,1]
    y[:,1]=sp*x[:,0]+cp*x[:,1]
    return y

def rotate_z(x,a):
    cp=math.cos(a);sp=math.sin(a);y=x.copy()
    y[:,0]=cp*x[:,0]-sp*x[:,1]
    y[:,1]=sp*x[:,0]+cp*x[:,1]
    return y

def splice(A,B,rng):
    x=canon(phi_reps(A));y=canon(phi_reps(B))
    twist=float(rng.uniform(0,math.pi))
    y=canon(rotate_z(y,twist))
    k=int(rng.integers(110,370))
    amp=float(rng.uniform(-.45,.45));phase=float(rng.uniform(0,math.pi))
    px=np.arctan2(x[:,1],x[:,0]);py=np.arctan2(y[:,1],y[:,0])
    sx=x[:,2]+amp*(1-x[:,2]**2)*np.cos(2*(px-phase))
    sy=y[:,2]+amp*(1-y[:,2]**2)*np.cos(2*(py-phase))
    ix=np.argpartition(sx,-k)[-k:]
    iy=np.argpartition(sy,M-k)[:M-k]
    v=sb.xyz_to_vars(np.vstack([x[ix],y[iy]]))
    return v,{"type":"cut-splice","twist":twist,"from_A":k}

def patch(A,B,rng):
    x=canon(phi_reps(A));y=canon(phi_reps(B))
    twist=float(rng.uniform(0,math.pi))
    y=canon(rotate_z(y,twist))
    cost=2-2*np.clip(x@y.T,-1,1)
    i,j=linear_sum_assignment(cost)
    assert np.array_equal(i,np.arange(M))
    y=y[j]
    ctr=x[int(rng.integers(M))]
    theta=float(rng.uniform(.2,.8))
    ww=np.exp((x@ctr-1)/(theta*theta))
    amp=float(rng.uniform(.7,1.5))
    ww=np.minimum(1.,amp*ww)
    z=(1-ww[:,None])*x+ww[:,None]*y
    z/=np.linalg.norm(z,axis=1)[:,None]
    return sb.xyz_to_vars(z),{"type":"patch","twist":twist,"r":theta}

def insert_elite(pool,E,v,tag,maxlen=32,tol=3e-8):
    if any(abs(E-p["energy"])<tol for p in pool):return False
    pool.append({"energy":float(E),"v":v.copy(),"tag":tag})
    pool.sort(key=lambda p:p["energy"])
    if len(pool)>maxlen:pool.pop()
    return True

def release(v,rng,maxiter):
    X=c2.xyzfull(v)
    field=rng.normal(size=X.shape)
    field-=np.sum(X*field,axis=1)[:,None]*X
    field*=.003/np.sqrt(float(np.mean(np.sum(field*field,axis=1))))
    Y=hb.expmap(X,field)
    E,y,n,ok,gr=hb.polish(Y,maxiter)
    if gr>3e-4:
        E,y,n2,ok,gr=hb.polish(y,maxiter+600)
        n+=n2
    return E,y,gr

def main():
    p=argparse.ArgumentParser()
    p.add_argument("few_shots",type=pathlib.Path)
    p.add_argument("--old-t",type=pathlib.Path,required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--sweeps",type=int,default=100)
    p.add_argument("--maxiter",type=int,default=650)
    p.add_argument("--out",type=pathlib.Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    score,_=sb.find_live(args.few_shots)
    assert abs(score-RECORD)<1e-7
    d2file=args.few_shots/"problems/p007-thomson-problem/shots/Abreto/thomson960-d2-ga/certificate.json"
    xd2=sb.load_cert(d2file)
    rd,derr=c2.from_d2(xd2)
    E_d2,vd2,n,ok,g=c2.c2_polish(sb.xyz_to_vars(rd),1500)
    vt,fit=old_t_c2_reps(args.old_t,args.seed)
    E_t,vt,n2,ok2,g2=c2.c2_polish(vt,1500)
    print("PARENTS",{"D2":E_d2,"T":E_t},"FIT",fit,"D2error",derr,flush=True)
    assert abs(E_d2-444368.4040805305)<2e-5
    assert abs(E_t-444368.4373479895)<2e-5
    # Pairwise identity: C2 orbit-v evaluates as complete unconstrained N960.
    assert abs(math.fsum(hb.pair_inverse(c2.qfull(vd2)).tolist())-E_d2)<5e-6
    temps=np.geomspace(.007,.34,6)
    reps=[{"energy":E_d2,"v":vd2.copy()} for _ in temps]
    reps[-1]={"energy":E_t,"v":vt.copy()}
    reps[-2]={"energy":E_t,"v":vt.copy()}
    pool=[{"energy":E_d2,"v":vd2.copy(),"tag":"D2-20"},
          {"energy":E_t,"v":vt.copy(),"tag":"T-24"}]
    fullpool=[{"energy":RECORD,"tag":"record"}]
    archive=[]
    hits=0;fulltries=0;best=RECORD
    nC2=0
    modes={"flow":0,"randomcap":0,"cut-splice":0,"patch":0}
    for t in range(args.sweeps):
        for j in rng.permutation(6):
            j=int(j)
            mode="flow" if rng.random()<.65 else "randomcap"
            start,step=c2.move(reps[j]["v"],rng,mode)
            E,v,n,ok,gr=c2.c2_polish(start,args.maxiter)
            de=E-reps[j]["energy"]
            good=de<=0 or rng.random()<math.exp(-max(0,de)/temps[j])
            if good:reps[j]={"energy":E,"v":v}
            modes[mode]+=1
            new=E<RECORD+1.0 and insert_elite(pool,E,v,f"{t}-{j}-{mode}")
            if new:
                nC2+=1
                print("C2_NEW",t,j,mode,f"{E:.12f}",
                      "dR",f"{E-RECORD:+.8f}",flush=True)
            if new and E<RECORD+.85:
                ef,y,gf=release(v,rng,1500)
                fulltries+=1
                if ef<best-2e-7:
                    best=ef;print("RECORD_CANDIDATE",t,j,f"{ef:.12f}",flush=True)
                if all(abs(ef-z["energy"])>2e-7 for z in fullpool):
                    fullpool.append({"energy":ef,"tag":f"{t}-{j}-{mode}"})
                    fullpool.sort(key=lambda z:z["energy"])
                    if len(fullpool)>50:fullpool.pop()
                    print("FULL_NEW",t,j,mode,f"{ef:.12f}",
                          "delta",f"{ef-RECORD:+.9f}",flush=True)
                if ef<RECORD-2e-7:
                    fname=args.out/f"CANDIDATE-C2-{args.seed}-{t}-{j}.json"
                    fname.write_text(json.dumps({"points":y.tolist(),
                        "energy":ef,"seed":args.seed,"step":t,
                        "C2_energy":E,"grad_rms":gf})+"\n")
                    hits+=1;print("CANDIDATE",fname,flush=True)
            archive.append({"sweep":t,"op":mode,"energy_c2":E,
                            "accepted":good,"new":new})
        # Recombine independent 20/24-dislocation elite arrangements in C2,
        # preserving neither input's full D2 or T symmetry. Population mates
        # include original donors throughout to prevent genetic collapse.
        for child in range(3):
            if child==0 or t%5==0:
                A,B=vd2,vt
            else:
                pop=pool[:min(14,len(pool))]
                weights=np.exp(-np.arange(len(pop))/5.0);weights/=weights.sum()
                ia,ib=rng.choice(len(pop),size=2,replace=False,p=weights)
                A,B=pop[int(ia)]["v"],pop[int(ib)]["v"]
            op="cut-splice" if rng.random()<.72 else "patch"
            v,meta=(splice(A,B,rng) if op=="cut-splice" else patch(A,B,rng))
            X=c2.xyzfull(v)
            md=hb.min_spacing(X)
            if md<.034:
                continue
            E,v,n,ok,gr=c2.c2_polish(v,args.maxiter+250)
            if gr>2e-3:
                E,v,n2,ok,gr=c2.c2_polish(v,1300)
            modes[op]+=1
            new=E<RECORD+1.2 and insert_elite(pool,E,v,f"GA:{t}:{child}")
            if new:
                nC2+=1
                print("GA_NEW",t,child,op,f"E={E:.12f}",
                      f"dR={E-RECORD:+.8f}",flush=True)
            if new and E<RECORD+.9:
                ef,y,gf=release(v,rng,1500)
                fulltries+=1
                if ef<best-2e-7:
                    best=ef;print("RECORD_CANDIDATE",t,child,
                                  f"{ef:.12f}",flush=True)
                if all(abs(ef-z["energy"])>2e-7 for z in fullpool):
                    fullpool.append({"energy":ef,"tag":f"GA:{t}:{child}:{op}"})
                    fullpool.sort(key=lambda z:z["energy"])
                    if len(fullpool)>50:fullpool.pop()
                    print("GA_FULL_NEW",t,child,op,f"{ef:.12f}",
                          "delta",f"{ef-RECORD:+.9f}",flush=True)
                if ef<RECORD-2e-7:
                    fname=args.out/f"CANDIDATE-GA-{args.seed}-{t}-{child}.json"
                    fname.write_text(json.dumps({"points":y.tolist(),
                        "energy":ef,"seed":args.seed,"step":t,"GA":meta,
                        "C2_energy":E,"grad_rms":gf})+"\n")
                    hits+=1;print("CANDIDATE",fname,flush=True)
            archive.append({"sweep":t,"op":op,"energy_c2":E,
                            "new":new,"pair":meta})
        for j in range(t%2,5,2):
            a,b=reps[j]["energy"],reps[j+1]["energy"]
            logacc=(1/temps[j]-1/temps[j+1])*(a-b)
            if logacc>=0 or rng.random()<math.exp(max(-700,logacc)):
                reps[j],reps[j+1]=reps[j+1],reps[j]
        if t%5==0:
            print("SWEEP",t,"min_C2",f"{pool[0]['energy']:.12f}",
                  "best_full",f"{best:.12f}",
                  "pool",len(pool),"full",fulltries,
                  "operators",modes,flush=True)
        if t%10==0 or t==args.sweeps-1:
            out={"seed":args.seed,"sweeps_done":t+1,
                "best_C2":pool[0]["energy"],"best_full":best,
                "num_C2_new":nC2,"full_releases":fulltries,
                "hits":hits,"operators":modes,"fit_old_T":fit,
                "c2_pool":[{"E":z["energy"],"tag":z["tag"],
                    "points":c2.xyzfull(z["v"]).tolist()} for z in pool[:15]],
                "full_pool":fullpool[:35],"rows":archive}
            (args.out/"result.json").write_text(
                json.dumps(out,separators=(",",":"))+"\n")
    print("FINAL",args.seed,"best_C2",f"{pool[0]['energy']:.12f}",
          "best_full",f"{best:.12f}","candidates",hits,
          "full_releases",fulltries,"operators",modes,flush=True)

if __name__=="__main__":
    main()
