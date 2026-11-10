#!/usr/bin/env python3
"""Thomson N=960 physical-space basin-filling search by alignment-invariant bias.

Search-space reset after C3/C2 genetic and symmetric size-exchange plateaus:
temporarily penalize previously visited MINIMA in the full unsymmetrized
Coulomb landscape, not displace another fixed parent to a random location.
Each repulsive Gaussian is a well-filling potential in the RMS positional
distance after optimal SO(3) registration. The potential is invariant under
global rotations. Its analytic gradient follows the Kabsch envelope theorem.

The true Coulomb energy has no bias, and every final N960 candidate is scored
by independent compiled Coulomb relaxation. R, A, B, and the newly generated
W basin are all explicit, independently scored initial wells. Deposit/adapt
small bias hills upon repeated visits to known basins, so an attraction basin
that was already sampled becomes progressively less attractive.

This is distinct from Riesz/anisotropic metric homotopy and from local scar
kicks: the *interaction* stays Coulomb; only a history-dependent
configurational repulsion suppresses repeated returns to known configurations.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib

import numpy as np
from scipy.optimize import minimize

import search_hamiltonian_scar_braid as hb
import search_size_beam as sb

RECORD=444368.3924061973


def aligned_squared_chord_and_gradient(x,ref):
    """Mean squared chord distance after optimal proper rotational alignment.

    Labels are physical tracked trajectories from the R seed. All enrolled
    reference configurations (A, B, W) descend from the same N960 indexing.
    Rotational gauge is optimized at each evaluation; gradient of the minimum
    is the gradient at its best rotation (envelope theorem).
    """
    u,s,vt=np.linalg.svd(x.T@ref)
    sign=np.linalg.det(u@vt)
    flip=np.diag([1.,1.,1. if sign>0 else -1.])
    rot=u@flip@vt
    target=ref@rot.T
    diff=x-target
    d2=float(np.mean(np.einsum("ij,ij->i",diff,diff)))
    return d2,2.*diff/len(x)


def gaussian_bias(q,hills):
    x,dth,dph=sb.vars_to_xyz(q)
    total=0.;force=np.zeros_like(x)
    for h in hills:
        d2,dg=aligned_squared_chord_and_gradient(x,h["points"])
        strength=float(h["height"]);sigma=float(h["sigma"])
        w=strength*math.exp(-d2/(2*sigma*sigma))
        total+=w
        force-=w/(2*sigma*sigma)*dg
    grad=np.column_stack([np.einsum("ij,ij->i",force,dth),
                          np.einsum("ij,ij->i",force,dph)]).ravel()
    return total,grad


def selftest(x,other):
    q=sb.xyz_to_vars(x)
    base=hb.energy_gradient_selftest(q)
    assert abs(base-RECORD)<4e-6,(base,)
    rng=np.random.default_rng(96424)
    tangent=rng.normal(size=x.shape)
    tangent-=np.sum(tangent*x,axis=1)[:,None]*x
    tangent*=.012/np.sqrt(np.mean(np.sum(tangent*tangent,axis=1)))
    y=hb.expmap(x,tangent)
    qq=sb.xyz_to_vars(y)
    hills=[{"points":x,"height":.43,"sigma":.023},
           {"points":other,"height":.21,"sigma":.017}]
    f,g=gaussian_bias(qq,hills)
    maxrel=0.
    for j in rng.choice(len(qq),12,replace=False):
        d=1.3e-6
        a=qq.copy();b=qq.copy();a[j]+=d;b[j]-=d
        fd=(gaussian_bias(a,hills)[0]-gaussian_bias(b,hills)[0])/(2*d)
        err=abs(fd-g[j])/(1+abs(fd))
        maxrel=max(maxrel,float(err))
        if err>2e-5:raise RuntimeError(("gaussian bias analytical gradient",int(j),fd,float(g[j]),err))
    val0,gg0=gaussian_bias(q,[{"points":x,"height":.9,"sigma":.021}])
    assert abs(val0-.9)<1e-9,(val0,)
    assert np.max(np.abs(gg0))<1e-7,np.max(np.abs(gg0))
    return {"record":base,"finite_difference_max_scaled_error":maxrel,
            "identity_bias":val0,"perturbed_bias":f}


def biased_polish(x,hills,maxiter):
    q0=sb.xyz_to_vars(x)
    reference=hb.pair_inverse(q0)
    e0=math.fsum(reference.tolist())
    def fg(q):
        ec,gc=hb.relative_energy_gradient(q,reference)
        eb,gb=gaussian_bias(q,hills)
        return float(ec+eb),gc+gb
    res=minimize(fg,q0,jac=True,method="L-BFGS-B",
       bounds=[(1e-8,math.pi-1e-8),(None,None)]*len(x),
       options={"maxiter":maxiter,"ftol":1e-15,"gtol":1e-8,
                "maxls":55,"maxcor":25})
    q=res.x
    X=sb.vars_to_xyz(q)[0]
    ec,gc=hb.relative_energy_gradient(q,reference)
    eb,gb=gaussian_bias(q,hills)
    return e0+ec,eb,X,int(res.nit),float(np.linalg.norm(gc+gb)/math.sqrt(len(q)))


def align_distance(x,y):
    return math.sqrt(aligned_squared_chord_and_gradient(x,y)[0])


def seed_pool(fewshots,a_json,b_json,w_json):
    score,shot=sb.find_live(fewshots)
    assert abs(score-RECORD)<1e-7
    R=sb.load_cert(shot/"certificate.json")
    A=np.array(json.loads(a_json.read_text())["points"],dtype=float)
    B=np.array(json.loads(b_json.read_text())["points"],dtype=float)
    W=np.array(json.loads(w_json.read_text())["minima"][0]["points"],dtype=float)
    out=[]
    for name,xyz,expected in [
        ("R",R,RECORD),
        ("A",A,444368.3956862257),
        ("B",B,444368.4029728612),
        ("W",W,444368.42162124),
    ]:
        E,Y,n,ok,gr=hb.polish(xyz,1800)
        print("SEED",name,f"{E:.12f}","grad",gr,"nit",n,flush=True)
        assert abs(E-expected)<2e-5,(name,E,expected)
        out.append({"energy":E,"points":Y,"tag":name})
    return out


def pool_insert(pool,E,x,tag,maxlen=28):
    if any(abs(E-p["energy"])<3e-7 for p in pool):return False
    pool.append({"energy":E,"points":x.copy(),"tag":tag})
    pool.sort(key=lambda p:p["energy"])
    if len(pool)>maxlen:pool.pop()
    return True


def update_hills(hills,E,x,seed,rng,base_sigma,base_height,max_hills=20):
    matches=[(i,h) for i,h in enumerate(hills)
             if h["energy"] is not None and abs(h["energy"]-E)<3e-6]
    if matches:
        j,h=matches[0]
        h["height"]=min(base_height*8,h["height"]+float(rng.uniform(.20,.52))*base_height)
        h["visits"]+=1
        return False,j
    if E<RECORD+.20:
        hill={"points":x.copy(),"height":float(rng.uniform(.70,1.25))*base_height,
              "sigma":float(base_sigma*rng.uniform(.70,1.40)),
              "energy":float(E),"visits":1,"tag":f"cycle-{seed}"}
        hills.append(hill)
        if len(hills)>max_hills:
            # Drop the least visited nonrecord well, preserving R.
            rem=min(range(4,len(hills)),key=lambda i:
                    hills[i]["visits"]+.08*hills[i]["height"])
            hills.pop(rem)
        return True,len(hills)-1
    return False,-1


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("few_shots",type=pathlib.Path)
    ap.add_argument("--a-json",type=pathlib.Path,required=True)
    ap.add_argument("--b-json",type=pathlib.Path,required=True)
    ap.add_argument("--w-json",type=pathlib.Path,required=True)
    ap.add_argument("--seed",type=int,required=True)
    ap.add_argument("--cycles",type=int,default=110)
    ap.add_argument("--maxiter",type=int,default=650)
    ap.add_argument("--sigma",type=float,default=.021)
    ap.add_argument("--out",type=pathlib.Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    pool=seed_pool(args.few_shots,args.a_json,args.b_json,args.w_json)
    baseline=pool[0]["points"]
    check=selftest(baseline,pool[1]["points"])
    print("BIAS_SELFTEST",check,flush=True)
    distances={q["tag"]:align_distance(baseline,q["points"]) for q in pool}
    print("INITIAL_DISTANCES",distances,flush=True)
    # The first campaign used sigma=.021, while the actual R->A/B/W
    # aligned collective RMS distances are only 0.0039-0.0055.
    # At that width the bias hills overlap nearly completely.
    # Set height proportional to sigma^2, preserving approximate
    # physical tangent curvature while narrowing basins to the
    # empirically measured separation scale.
    base_height=min(.24,.075*(args.sigma/.0035)**2)
    print("HILL_GEOMETRY","sigma",args.sigma,"height",base_height,
          "nearest_parent_gap",min(v for k,v in distances.items() if k!="R"),
          flush=True)
    # All existing known near-R states are filled at start to discourage
    # repeatedly falling back into already characterized low basins.
    hills=[{"points":p["points"].copy(),"height":base_height,
            "sigma":args.sigma,"energy":p["energy"],"visits":1,
            "tag":p["tag"]} for p in pool]
    best=RECORD
    novel=0;candidates=0;control_runs=0
    rows=[]
    for t in range(args.cycles):
        if t%6==0:
            parent=pool[0]
            direct=True
            control_runs+=1
        elif t%7==0:
            parent=pool[min(int(rng.integers(min(4,len(pool)))),len(pool)-1)]
            direct=False
        else:
            weights=np.exp(-np.arange(min(13,len(pool)))/3.5)
            weights/=weights.sum()
            parent=pool[int(rng.choice(len(weights),p=weights))]
            direct=False
        x=parent["points"]
        ctr,_,_=hb.scar_centers(x)
        mode=str(rng.choice(["vortices","dipole","braid","randomcap"],
                           p=[.28,.34,.27,.11]))
        scale=float(np.exp(rng.uniform(math.log(.003),math.log(.06))))
        y=hb.transport(x,rng,ctr,scale,mode)
        spacing=hb.min_spacing(y)
        shrink=0
        while spacing<.038 and shrink<8:
            y=x*.5+y*.5
            y/=np.linalg.norm(y,axis=1)[:,None]
            spacing=hb.min_spacing(y);shrink+=1
        if direct:
            biasedE=None;biasV=0.;biasedGrad=None
            Z=y
        else:
            # Saddle-node traversal is induced by continually reweighting
            # positional Gaussian hills, not by changing physical charges.
            biasedE,biasV,Z,niter,biasedGrad=biased_polish(y,hills,args.maxiter)
        Ef,Q,n,ok,gr=hb.polish(Z,args.maxiter+700)
        if gr>2e-4:
            Ef,Q,n2,ok,gr=hb.polish(Q,1300)
            n+=n2
        is_new=pool_insert(pool,Ef,Q,f"{t}:{mode}:{'control' if direct else 'filled'}")
        if is_new:
            novel+=1
            print("NEW",t,"E",f"{Ef:.12f}",f"dR={Ef-RECORD:+.9f}",
                  "source",parent["tag"],"control",direct,flush=True)
        if not direct:
            hillnew,hillidx=update_hills(
                hills,Ef,Q,t,rng,args.sigma,base_height)
        else:
            hillnew=False;hillidx=-1
        if Ef<best-2e-7:
            best=Ef
            print("BEST",t,"E",f"{Ef:.12f}",f"dR={Ef-RECORD:+.9f}",flush=True)
        if Ef<RECORD-2e-7:
            path=args.out/f"CANDIDATE-{args.seed}-{t}.json"
            path.write_text(json.dumps({"energy":Ef,"points":Q.tolist(),
                "seed":args.seed,"cycle":t,"control":direct,
                "gradient_rms":gr})+"\n")
            candidates+=1
            print("CANDIDATE",path,f"E={Ef:.12f}",flush=True)
        rows.append({"cycle":t,"control":direct,"parent":parent["tag"],
            "mode":mode,"scale":scale,"contractions":shrink,
            "start_min_spacing":spacing,"biased_coulomb_E":biasedE,
            "bias_at_biased_min":biasV,"gradient_bias":biasedGrad,
            "true_coulomb_E":Ef,"delta_record":Ef-RECORD,
            "grad_rms":gr,"new_basin":is_new,"new_hill":hillnew})
        if t%6==0:
            print("CYCLE",t,"E",f"{Ef:.12f}",
                 "best",f"{best:.12f}","pool",len(pool),
                 "hills",len(hills),"new",novel,flush=True)
        if t%10==0 or t==args.cycles-1:
            result={"seed":args.seed,"cycles_done":t+1,
               "best_record_candidate":best,
               "new_unconstrained_basins":novel,
               "control_count":control_runs,
               "winning_candidates":candidates,
               "selftest":check,
               "bias_width":args.sigma,"base_height":base_height,
               "initial_parent_distances":distances,
               "hills":[{"height":h["height"],"sigma":h["sigma"],
                         "energy":h["energy"],"visits":h["visits"],
                         "tag":h["tag"]} for h in hills],
               "elites":[{"energy":z["energy"],"tag":z["tag"],
                          "points":z["points"].tolist()} for z in pool[:14]],
               "rows":rows}
            (args.out/"result.json").write_text(
                json.dumps(result,separators=(",",":"))+"\n")
    print("FINAL",args.seed,"best",f"{best:.12f}",
          "new_basins",novel,"hills",len(hills),
          "candidates",candidates,flush=True)


if __name__=="__main__":
    main()
