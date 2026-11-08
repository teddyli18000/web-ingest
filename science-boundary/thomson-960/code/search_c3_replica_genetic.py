#!/usr/bin/env python3
"""Construct N960 competitors using C3 replica exchange + genetic orbit crossover.

The accepted p007 C3 minimum was discovered with six-temperature replica
exchange, whereas the earlier D2 success used symmetry-preserving Deaven-Ho
cut-and-splice GA. This hybrid tests their unexploited combination within the
320-orbit C3 quotient: local collective defect moves and registered C3-group
crossovers, with population exchange across six temperatures.

All Coulomb terms are summed as a stable trial-relative objective using the
already independently tested numba Coulomb gradient. Symmetry is *released*
on diverse low-energy quotient minima, including those above R+0.10, and
only physically quenched 960-point energies are compared with the live score.
Full sub-record point sets are saved for independent exact-certificate checks.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib

import numpy as np
from scipy.optimize import linear_sum_assignment, minimize

import search_c3_smooth as c3
import search_hamiltonian_scar_braid as hb
import search_size_beam as sb

RECORD = 444368.3924061973
M = 320
PERIOD = 2 * math.pi / 3


def full_q(v):
    a=np.asarray(v,float).reshape(M,2)
    blocks=[]
    for k in range(3):
        q=a.copy()
        q[:,1]+=k*PERIOD
        blocks.append(q)
    return np.vstack(blocks).ravel()


def full_xyz(v):
    return c3.vars_to_full(np.asarray(v,float))[0]


def c3_polish(v0,maxiter):
    q0=full_q(v0)
    ref=hb.pair_inverse(q0)
    e0=math.fsum(ref.tolist())
    def fg(v):
        de,g=hb.relative_energy_gradient(full_q(v),ref)
        return float(de),g.reshape(3,M,2).sum(axis=0).ravel()
    r=minimize(fg,v0,jac=True,method='L-BFGS-B',
        bounds=[(1e-8,math.pi-1e-8),(None,None)]*M,
        options={'maxiter':maxiter,'gtol':1e-8,'ftol':1e-15,
                 'maxls':55,'maxcor':28})
    de,g=fg(r.x)
    a=r.x.reshape(M,2)
    gr=float(np.sqrt(np.mean(g[::2]**2+
         (g[1::2]/np.maximum(np.sin(a[:,0]),1e-7))**2)))
    return e0+de,r.x,int(r.nit),gr


def canonical_reps(x):
    # The three representatives of the same C3 orbit are interchangeable.
    # Canonicalize each into the same angular wedge without altering its orbit.
    phi=np.arctan2(x[:,1],x[:,0])
    shift=np.floor((phi+PERIOD/2)/PERIOD)
    ang=-shift*PERIOD
    cp=np.cos(ang);sp=np.sin(ang)
    out=x.copy()
    out[:,0]=cp*x[:,0]-sp*x[:,1]
    out[:,1]=sp*x[:,0]+cp*x[:,1]
    return out


def three_rotations(center):
    return np.vstack([c3.rz(center[None,:],k*PERIOD) for k in range(3)])


def kick(v,rng,mode,scale):
    x=full_xyz(v)
    reps=x[:M].copy()
    centers,_,_=hb.scar_centers(x)
    if mode=="scar-flow":
        m=int(rng.integers(1,4))
        pick=rng.choice(len(centers),m,replace=False)
        vel=np.zeros_like(reps)
        for idx in pick:
            ctr=three_rotations(centers[int(idx)])
            width=float(rng.uniform(.12,.53))
            a=float(rng.normal())
            for c in ctr:
                vel+=a*np.exp((reps@c-1.)/(width*width))[:,None]*np.cross(reps,c)/(width*width)
    elif mode=="scar-noise":
        k=int(rng.integers(1,4))
        ctr=np.vstack([three_rotations(centers[int(j)]) for j in rng.choice(len(centers),k,replace=False)])
        width=float(rng.uniform(.13,.53))
        weights=np.sum(np.exp((reps@ctr.T-1.)/(width*width)),axis=1)
        vel=rng.normal(size=(M,3))*weights[:,None]
    elif mode=="global-noise":
        vel=rng.normal(size=(M,3))
    else:
        raise ValueError(mode)
    vel-=np.sum(vel*reps,axis=1)[:,None]*reps
    norm=float(np.sqrt(np.mean(np.sum(vel*vel,axis=1))))
    if norm<1e-12:
        return v.copy()
    vel*=scale/norm
    maxstep=float(np.max(np.linalg.norm(vel,axis=1)))
    if maxstep>.37:vel*=.37/maxstep
    return sb.xyz_to_vars(hb.expmap(reps,vel))


def registered_patch(A,B,rng):
    x=canonical_reps(full_xyz(A)[:M])
    y=canonical_reps(full_xyz(B)[:M])
    twist=float(rng.uniform(0.,PERIOD))
    y=canonical_reps(c3.rz(y,twist))
    dist=2-2*np.clip(x@y.T,-1,1)
    ii,jj=linear_sum_assignment(dist)
    assert np.array_equal(ii,np.arange(M))
    y=y[jj]
    core=x[int(rng.integers(M))]
    r=float(rng.uniform(.18,.85))
    w=np.exp((x@core-1.)/(r*r))
    w*=float(rng.uniform(.65,1.4))
    w=np.clip(w,0.,1.)
    z=(1.-w[:,None])*x+w[:,None]*y
    z/=np.linalg.norm(z,axis=1)[:,None]
    return sb.xyz_to_vars(z),{"type":"registered-patch","twist":twist,"radius":r,
                             "weight_rms":float(np.sqrt(np.mean(w*w)))}


def cut_splice(A,B,rng):
    x=canonical_reps(full_xyz(A)[:M])
    y=canonical_reps(full_xyz(B)[:M])
    twist=float(rng.uniform(0.,PERIOD))
    y=canonical_reps(c3.rz(y,twist))
    k=int(rng.integers(70,260))
    phase=float(rng.uniform(0.,PERIOD))
    amp=float(rng.uniform(-.55,.55))
    phi_x=np.arctan2(x[:,1],x[:,0])
    phi_y=np.arctan2(y[:,1],y[:,0])
    sx=x[:,2]+amp*(1-x[:,2]**2)*np.cos(3*(phi_x-phase))
    sy=y[:,2]+amp*(1-y[:,2]**2)*np.cos(3*(phi_y-phase))
    ip=np.argpartition(sx,-k)[-k:]
    iq=np.argpartition(sy,M-k)[:M-k]
    z=np.vstack([x[ip],y[iq]])
    assert len(z)==M
    return sb.xyz_to_vars(z),{"type":"cut-splice","twist":twist,
                             "cut_amp":amp,"k_A":k}


def quality_candidates(pop,E,pts,tag,limit=35):
    if any(abs(z["energy"]-E)<3e-6 for z in pop):
        return False
    pop.append({"energy":float(E),"v":None if pts is None else pts.copy(),"tag":tag})
    pop.sort(key=lambda z:z["energy"])
    if len(pop)>limit:pop.pop()
    return True


def weak_symmetry_break(x,rng,amp):
    v=rng.normal(size=x.shape)
    v-=np.sum(v*x,axis=1)[:,None]*x
    v*=amp/float(np.sqrt(np.mean(np.sum(v*v,axis=1))))
    return hb.expmap(x,v)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("few_shots",type=pathlib.Path)
    ap.add_argument("--seed",type=int,required=True)
    ap.add_argument("--sweeps",type=int,default=100)
    ap.add_argument("--maxiter",type=int,default=740)
    ap.add_argument("--out",type=pathlib.Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    live,shot=sb.find_live(args.few_shots)
    if abs(live-RECORD)>1e-7:raise RuntimeError(("record changed",live))
    R=sb.load_cert(shot/"certificate.json")
    reps=c3.c3_representatives(R)
    v0=c3.xyz_to_vars(reps)
    E0,v0,nit,gr=c3_polish(v0,1500)
    print("CHECK_C3",f"{E0:.12f}","grms",gr,"nit",nit,flush=True)
    if abs(E0-RECORD)>2e-5:raise RuntimeError(("C3 reconstruct mismatch",E0))
    hb.energy_gradient_selftest(sb.xyz_to_vars(full_xyz(v0)))
    temps=np.geomspace(.004,.32,6)
    replicas=[{"energy":E0,"v":v0.copy()} for _ in temps]
    c3pop=[{"energy":E0,"v":v0.copy(),"tag":"record"}]
    freebest=RECORD
    fullpop=[{"energy":E0,"tag":"record"}]
    stats=[]
    record_candidates=0
    nfull=0
    new_basin_count=0
    for sweep in range(args.sweeps):
        for j in rng.permutation(6):
            j=int(j)
            current=replicas[j]
            mode=str(rng.choice(["scar-flow","scar-noise","global-noise"],
                                p=[.48,.37,.15]))
            scale=float(np.exp(rng.uniform(math.log(.01),math.log(.15))))
            x=kick(current["v"],rng,mode,scale)
            E,v,nit,gr=c3_polish(x,args.maxiter)
            if gr>1e-3:
                E,v,nmore,gr=c3_polish(v,1100)
                nit+=nmore
            de=E-current["energy"]
            accept=de<0 or rng.random()<math.exp(-max(0.,de)/temps[j])
            if accept:replicas[j]={"energy":E,"v":v}
            unique=E<RECORD+.80 and quality_candidates(c3pop,E,v,f"{sweep}:{j}:{mode}")
            row={"sweep":sweep,"replica":j,"mode":mode,"start_energy":current["energy"],
                 "energy_c3":E,"delta_record":E-RECORD,"accepted":accept,
                 "c3_unique":unique,"nit":nit,"gradient_rms":gr}
            if unique and E<RECORD+.55:
                # C3 minima may be unstable under symmetry-breaking mode.
                # Physically release the whole 960-particle state.
                xfull=full_xyz(v)
                for amp in (.0003,.009):
                    noise=weak_symmetry_break(xfull,rng,amp)
                    ef,y,fnit,fok,fgr=hb.polish(noise,1450)
                    if fgr>1e-4:
                        ef,y,n2,fok,fgr=hb.polish(y,1600)
                        fnit+=n2
                    nfull+=1
                    novel=quality_candidates(fullpop,ef,None,
                                             f"{sweep}:{j}:{mode}:{amp}",50)
                    if novel:
                        new_basin_count+=1
                        print("FREE_NEW",sweep,j,mode,f"C3={E:.10f}",
                              f"full={ef:.12f}",f"dR={ef-RECORD:+.9f}",flush=True)
                    if ef<freebest-2e-7:
                        freebest=ef
                        print("FREE_BEST",sweep,j,mode,f"E={ef:.12f}",flush=True)
                    if ef<RECORD-2e-7:
                        fname=args.out/f"CANDIDATE-{args.seed}-{sweep}-{j}.json"
                        fname.write_text(json.dumps({"energy":ef,"points":y.tolist(),
                            "seed":args.seed,"sweep":sweep,"replica":j,
                            "symmetry_break_amp":amp,"gradient_rms":fgr})+"\n")
                        record_candidates+=1
                        print("CANDIDATE",fname,"E",ef,flush=True)
            stats.append(row)
        # Genetic children are *new combinatorial C3 orbit assemblies*, unlike
        # smooth coordinate averaging or whole-sphere field compositions.
        if len(c3pop)>=3:
            for childnum in range(3):
                ranks=np.arange(min(12,len(c3pop)))
                w=np.exp(-ranks/3.5);w/=w.sum()
                a,b=rng.choice(ranks,size=2,replace=False,p=w)
                A=c3pop[int(a)]["v"];B=c3pop[int(b)]["v"]
                move="cut-splice" if rng.random()<.68 else "registered-patch"
                offspring,meta=(cut_splice(A,B,rng) if move=="cut-splice"
                                else registered_patch(A,B,rng))
                y=full_xyz(offspring)
                dmin=hb.min_spacing(y)
                if dmin<.032:
                    continue
                E,v,nit,gr=c3_polish(offspring,args.maxiter+240)
                if gr>1e-3:E,v,n2,gr=c3_polish(v,1300);nit+=n2
                unique=E<RECORD+.80 and quality_candidates(
                    c3pop,E,v,f"GA:{sweep}:{childnum}")
                if unique and E<RECORD+.7:
                    ef,yy,fnit,fok,fgr=hb.polish(
                        weak_symmetry_break(full_xyz(v),rng,.005),1600)
                    nfull+=1
                    novelty=quality_candidates(fullpop,ef,None,
                        f"GA:{sweep}:{childnum}",50)
                    if novelty:
                        new_basin_count+=1
                        print("GA_FREE_NEW",sweep,childnum,
                              f"C3={E:.11f}",f"full={ef:.12f}",
                              f"dR={ef-RECORD:+.9f}",flush=True)
                    if ef<freebest-2e-7:
                        freebest=ef
                        print("GA_FREE_BEST",sweep,childnum,
                              f"E={ef:.12f}",flush=True)
                    if ef<RECORD-2e-7:
                        fname=args.out/f"CANDIDATE-GA-{args.seed}-{sweep}-{childnum}.json"
                        fname.write_text(json.dumps({"energy":ef,"points":yy.tolist(),
                            "seed":args.seed,"sweep":sweep,"GA":meta,
                            "gradient_rms":fgr})+"\n")
                        record_candidates+=1
                        print("CANDIDATE",fname,"E",ef,flush=True)
                stats.append({"sweep":sweep,"replica":"GA","mode":move,
                    "energy_c3":E,"delta_record":E-RECORD,"c3_unique":unique,
                    "nit":nit,"grad_c3":gr,"min_spacing":dmin,**meta})
        for k in range(sweep%2,5,2):
            e1=replicas[k]["energy"];e2=replicas[k+1]["energy"]
            logacc=(1/temps[k]-1/temps[k+1])*(e1-e2)
            if logacc>=0 or rng.random()<math.exp(max(-700,logacc)):
                replicas[k],replicas[k+1]=replicas[k+1],replicas[k]
        if sweep%5==0:
            print("SWEEP",sweep,"replica_dR",
                [round(x["energy"]-RECORD,6) for x in replicas],
                "best_c3",f"{c3pop[0]['energy']:.12f}",
                "freebest",f"{freebest:.12f}",
                "c3elite",len(c3pop),"freeelites",len(fullpop),
                "full_release",nfull,flush=True)
        if sweep%10==0 or sweep==args.sweeps-1:
            archive={"seed":args.seed,"sweeps_done":sweep+1,
                "temp":temps.tolist(),"live_record":RECORD,
                "best_c3":c3pop[0]["energy"],
                "best_full":freebest,
                "full_releases":nfull,
                "subrecord_candidates":record_candidates,
                "new_full_basins":new_basin_count,
                "c3_elites":[{"energy":z["energy"],"tag":z["tag"],
                              "points":full_xyz(z["v"]).tolist()} for z in c3pop[:14]],
                "full_elites":[{"energy":z["energy"],"tag":z["tag"]} for z in fullpop[:30]],
                "rows":stats}
            (args.out/"result.json").write_text(
                json.dumps(archive,separators=(",",":"))+"\n")
    print("FINAL",args.seed,"sweeps",args.sweeps,
          "best_c3",f"{c3pop[0]['energy']:.12f}",
          "best_full",f"{freebest:.12f}",
          "nfull",nfull,"candidates",record_candidates,flush=True)

if __name__=="__main__":
    main()
