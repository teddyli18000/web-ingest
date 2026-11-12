#!/usr/bin/env python3
"""Construct lower N=960 Thomson minima by dynamically coupled defect-glide forces.

The 2026-10-30 exact R->A topology audit showed that a local dependent
3-step dislocation glide triggered *remote* simultaneous scar rearrangements.
Prior attempts typically fixed four-vertex flip scaffolds, tested one/two
events, and released, often healing back. Here entire particle coordinates
are mobile throughout and the search control is a *combinatorial set of
Delaunay diagonals*, not an externally invented displacement vector.

A differentiable SO(3)-invariant bias sum_i k_i [|opposite_i|-|old_i|]
favors topologically distinct flip diagonals. First drive 2-5 spatially
separated legal scar glides; re-triangulate under the changed elastic field;
add 1-4 newly legal glides, either adjacent to the initiating scar(s) or
on remote other scars. Jointly relax Coulomb+edge bias, then fully remove all
bias and score the physically quenched unconstrained N960 state. Independent
slow/abrupt release and no-bias controls are interleaved.

This is not an exhaustive graph proof and the biased energies are never
reported as Thomson candidates. Every record-competitive endpoint is saved
as 960 true unit-vector coordinates, pending independent exact verifier.
"""
from __future__ import annotations
import argparse, json, math, pathlib
from collections import Counter
import numpy as np
from scipy.optimize import minimize
import search_hamiltonian_scar_braid as hb
import search_size_beam as sb
from search_e564_defect_flip_parallel import topology

RECORD=444368.3924061973


def enumerate_glides(x):
    deg, faces=topology(x)
    old=set(faces)
    before=Counter(map(int,deg))
    centers,_,_=hb.scar_centers(x)
    out=[]
    for (u,v),other in faces.items():
        if len(other)!=2:
            continue
        a,b=map(int,other)
        ne=tuple(sorted((a,b)))
        if ne in old:
            continue
        nd=deg.copy()
        nd[u]-=1;nd[v]-=1;nd[a]+=1;nd[b]+=1
        if Counter(map(int,nd))!=before:
            continue
        quad=(int(u),int(v),a,b)
        oldlen=float(np.linalg.norm(x[u]-x[v]))
        newlen=float(np.linalg.norm(x[a]-x[b]))
        gap=newlen-oldlen
        ctr=x[list(quad)].sum(axis=0)
        ctr/=np.linalg.norm(ctr)
        nearest=int(np.argmax(centers@ctr))
        out.append({"quad":quad,"gap":gap,"scar_id":nearest,
                    "center":ctr,"oldlen":oldlen,"newlen":newlen})
    out.sort(key=lambda r:r["gap"])
    return out


def select_glides(candidates,rng,n,used=None,spread=True):
    used=[] if used is None else list(used)
    chosen=[]
    pool=[c for c in candidates if c["gap"]<.15]
    while len(chosen)<n:
        good=[z for z in pool
              if all(not(set(z["quad"]) & set(t["quad"])) for t in used+chosen)]
        if spread:
            strong=[z for z in good if all(z["scar_id"]!=t["scar_id"]
                    and float(z["center"]@t["center"])<.78
                    for t in used+chosen)]
            if strong:good=strong
        if not good:break
        rank=min(len(good),28)
        weights=np.exp(-np.arange(rank)/8.0);weights/=weights.sum()
        z=good[int(rng.choice(rank,p=weights))]
        chosen.append(z)
    return chosen


def active_flips(x,glides):
    _,ef=topology(x)
    edges=set(ef)
    return [tuple(sorted((g["quad"][2],g["quad"][3]))) in edges
            and tuple(sorted(g["quad"][:2])) not in edges for g in glides]


def pair_bias(q,glides,weights):
    x,dth,dph=sb.vars_to_xyz(q)
    force=np.zeros_like(x)
    e=0.
    for g,k in zip(glides,weights):
        u,v,a,b=g["quad"]
        for i,j,sign in [(a,b,1.),(u,v,-1.)]:
            delta=x[i]-x[j]
            d=float(np.linalg.norm(delta))
            weight=k*sign
            e+=weight*d
            grad=(weight/d)*delta
            force[i]+=grad
            force[j]-=grad
    gth=np.einsum("ij,ij->i",force,dth)
    gph=np.einsum("ij,ij->i",force,dph)
    return float(e),np.column_stack([gth,gph]).ravel()


def biased_relax(x,glides,weights,maxiter):
    q0=sb.xyz_to_vars(x)
    ref=hb.pair_inverse(q0)
    e0=math.fsum(ref.tolist())
    def fg(q):
        ec,gc=hb.relative_energy_gradient(q,ref)
        eb,gb=pair_bias(q,glides,weights)
        return ec+eb,gc+gb
    res=minimize(fg,q0,jac=True,method="L-BFGS-B",
        bounds=[(1e-8,math.pi-1e-8),(None,None)]*len(x),
        options={"maxiter":maxiter,"gtol":1e-8,"ftol":1e-15,
                 "maxcor":25,"maxls":55})
    q=res.x
    ec,gc=hb.relative_energy_gradient(q,ref)
    eb,gb=pair_bias(q,glides,weights)
    x=sb.vars_to_xyz(q)[0]
    return e0+ec,eb,x,int(res.nit),float(np.linalg.norm(gc+gb)/math.sqrt(len(q)))


def gradient_test(x,glides):
    q=sb.xyz_to_vars(x)
    rng=np.random.default_rng(267310)
    tangent=rng.normal(size=x.shape)
    tangent-=np.sum(tangent*x,axis=1)[:,None]*x
    tangent*=.006/math.sqrt(float(np.mean(np.sum(tangent*tangent,axis=1))))
    z=hb.expmap(x,tangent)
    qq=sb.xyz_to_vars(z)
    w=np.arange(1,len(glides)+1,dtype=float)*3.0
    energy,grad=pair_bias(qq,glides,w)
    maxerr=0.
    for idx in rng.choice(len(qq),size=12,replace=False):
        a=qq.copy();b=qq.copy();h=1.2e-6;a[idx]+=h;b[idx]-=h
        fd=(pair_bias(a,glides,w)[0]-pair_bias(b,glides,w)[0])/(2*h)
        err=abs(fd-grad[idx])/(1+abs(fd))
        maxerr=max(maxerr,float(err))
        if err>1e-6:raise RuntimeError(("biased pair gradient",idx,fd,grad[idx],err))
    return {"bias":energy,"max_relative_finite_difference":maxerr}


def seed_pool(fewshots,aj,bj,wj):
    score,shot=sb.find_live(fewshots)
    assert abs(score-RECORD)<1e-7
    R=sb.load_cert(shot/"certificate.json")
    A=np.asarray(json.loads(aj.read_text())["points"],float)
    B=np.asarray(json.loads(bj.read_text())["points"],float)
    W=np.asarray(json.loads(wj.read_text())["minima"][0]["points"],float)
    seeds=[]
    for tag,X,e0 in [
        ("R",R,RECORD),("A",A,444368.3956862257),
        ("B",B,444368.4029728612),("W",W,444368.42162124)]:
        E,Y,n,ok,gr=hb.polish(X,1350)
        assert abs(E-e0)<2e-5,(tag,E,e0)
        print("SEED",tag,f"{E:.12f}","gr",gr,flush=True)
        seeds.append({"energy":E,"points":Y,"tag":tag})
    return seeds


def physical_score(X,maxiter):
    E,Y,n,ok,gr=hb.polish(X,maxiter)
    if gr>1e-4:
        E,Y,n2,ok,gr=hb.polish(Y,1300)
        n+=n2
    return E,Y,gr


def main():
    p=argparse.ArgumentParser()
    p.add_argument("few_shots",type=pathlib.Path)
    p.add_argument("--a-json",type=pathlib.Path,required=True)
    p.add_argument("--b-json",type=pathlib.Path,required=True)
    p.add_argument("--w-json",type=pathlib.Path,required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--cycles",type=int,default=80)
    p.add_argument("--maxiter",type=int,default=550)
    p.add_argument("--out",type=pathlib.Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    pool=seed_pool(args.few_shots,args.a_json,args.b_json,args.w_json)
    rootglides=enumerate_glides(pool[0]["points"])
    assert len(rootglides)>=50,len(rootglides)
    test=gradient_test(pool[0]["points"],rootglides[:3])
    assert test["max_relative_finite_difference"]<1e-6
    print("ROOT",len(rootglides),"lowest_gaps",
          [round(z["gap"],6) for z in rootglides[:8]],
          "BIAS_GRADIENT",test,flush=True)
    best=RECORD;new=0;wins=0
    rows=[]
    for t in range(args.cycles):
        if t%8==0:parent=pool[0]
        else:
            weights=np.exp(-np.arange(min(9,len(pool)))/3.0)
            weights/=weights.sum()
            parent=pool[int(rng.choice(len(weights),p=weights))]
        x=parent["points"].copy()
        orig=enumerate_glides(x)
        if not orig:
            print("NO_GLIDES",t,parent["tag"],flush=True)
            continue
        control=t%11==0
        strength=float(np.exp(rng.uniform(math.log(3.5),math.log(75.))))
        nfirst=int(rng.integers(2,6))
        chosen=select_glides(orig,rng,nfirst,spread=True)
        if not chosen:
            continue
        stage=[]
        if control:
            # Same number of proposed/selected dislocation families,
            # but no combinatorial drive. This is a TRUE physical control.
            z=hb.transport(x,rng,hb.scar_centers(x)[0],.045,"braid")
            Ef,Y,gr=physical_score(z,args.maxiter+950)
            flipped_before=[]
            flipped_after=[]
        else:
            z=x
            # All 960 points respond to simultaneous remote 2-5 local
            # pair-force fields. Source Delaunay topology not fixed.
            for ratio in (.30,.75):
                physical,bias,z,nit,grb=biased_relax(
                    z,chosen,[strength*ratio]*len(chosen),args.maxiter)
                flips=active_flips(z,chosen)
                stage.append({"ratio":ratio,"physical_E":physical,
                              "bias_E":bias,"flips":sum(flips),"nit":nit})
            flipped_before=active_flips(z,chosen)
            # Newly legal candidates are recomputed in the deformed
            # global crystal; these may not exist at the source.
            revised=enumerate_glides(z)
            nnew=int(rng.integers(1,5))
            follow=select_glides(revised,rng,nnew,used=chosen,
                                 spread=bool(rng.integers(2)))
            chosen+=follow
            ratios=(1.0,.42) if t%2==0 else (1.0,)
            for ratio in ratios:
                physical,bias,z,nit,grb=biased_relax(
                    z,chosen,[strength*ratio]*len(chosen),args.maxiter+100)
                flips=active_flips(z,chosen)
                stage.append({"ratio":ratio,"physical_E":physical,
                              "bias_E":bias,"flips":sum(flips),"nit":nit})
            flipped_after=active_flips(z,chosen)
            Ef,Y,gr=physical_score(z,args.maxiter+1000)
        if Ef<best-2e-7:
            best=Ef
            print("BEST",t,parent["tag"],f"{Ef:.12f}",
                  "delta",f"{Ef-RECORD:+.9f}",flush=True)
        old=any(abs(Ef-p["energy"])<4e-7 for p in pool)
        if not old and Ef<RECORD+1.5:
            new+=1
            pool.append({"energy":Ef,"points":Y.copy(),
                         "tag":f"{t}:{len(chosen)}:glides"})
            pool.sort(key=lambda x:x["energy"]);pool=pool[:23]
            print("NEW",t,"E",f"{Ef:.12f}",
                  "delta",f"{Ef-RECORD:+.8f}",
                  "glides",len(chosen),"strength",f"{strength:.3f}",
                  "changed",sum(flipped_after),
                  "ctrl",control,flush=True)
        if Ef<RECORD-2e-7:
            f=args.out/f"CANDIDATE-{args.seed}-{t}.json"
            f.write_text(json.dumps({"energy":Ef,"points":Y.tolist(),
                "seed":args.seed,"cycle":t,"grad_rms":gr,
                "glides":[list(g["quad"]) for g in chosen]})+"\n")
            wins+=1
            print("CANDIDATE",f,f"{Ef:.12f}",flush=True)
        rows.append({"cycle":t,"parent":parent["tag"],"parent_E":parent["energy"],
          "control":control,"chosen":len(chosen),"first_n":len(flipped_before),
          "first_flipped":sum(flipped_before),"after_flipped":sum(flipped_after),
          "strength":strength,"energy":Ef,"delta_R":Ef-RECORD,
          "grad_rms":gr,"new":not old,"stages":stage,
          "quads":[list(g["quad"]) for g in chosen]})
        if t%5==0:
            print("CYCLE",t,"parent",parent["tag"],
                  "E",f"{Ef:.12f}","best",f"{best:.12f}",
                  "pool",len(pool),"new",new,"wins",wins,flush=True)
        if t%10==0 or t==args.cycles-1:
            result={"seed":args.seed,"cycles_done":t+1,
                 "record":RECORD,"best":best,"new_basins":new,
                 "winners":wins,"gradient_test":test,
                 "pool":[{"energy":p["energy"],"tag":p["tag"],
                          "points":p["points"].tolist()} for p in pool[:15]],
                 "rows":rows}
            (args.out/"result.json").write_text(
                json.dumps(result,separators=(",",":"))+"\n")
    print("FINAL",args.seed,"cycles",args.cycles,
          "best",f"{best:.12f}","new",new,
          "wins",wins,flush=True)


if __name__=="__main__":
    main()
