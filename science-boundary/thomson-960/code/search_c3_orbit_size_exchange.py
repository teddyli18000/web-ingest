#!/usr/bin/env python3
"""N960 record hunt by C3-symmetric ±3-particle orbit birth/death transport.

Existing nearby-size probes did individual N960<->N959/N961 particle events;
these normally broke 24-dislocation scar coordination into costly 23-defect
descendants. Here all intermediate geometries preserve a C3 point group:
temporarily remove or add ONE ENTIRE C3 orbit of three particles, optimize
N957/N963, then replace/release a *different* C3 orbit back at N960.

Candidate ranking uses the exact three-body orbit Coulomb insertion cost and
full-orbit removal contributions. An independent N960 quench can break C3.
All candidates with a lower physical N960 energy are frozen with 960 points.
This tests an unsearched coupled topological interface, not another ±1 hop.
"""
from __future__ import annotations
import argparse, json, math, pathlib

import numpy as np
from scipy.optimize import minimize

import search_c3_smooth as c3
import search_hamiltonian_scar_braid as hb
import search_size_beam as sb

RECORD=444368.3924061973
PERIOD=2*math.pi/3


def qfull(v):
    a=np.asarray(v,float).reshape(-1,2)
    z=np.vstack([a.copy() for _ in range(3)])
    k=len(a)
    z[k:2*k,1]+=PERIOD
    z[2*k:,1]+=2*PERIOD
    return z.ravel()


def xfull(v):
    return sb.vars_to_xyz(qfull(v))[0]


def polish(v,maxiter=800):
    q0=qfull(v)
    ref=hb.pair_inverse(q0)
    e0=math.fsum(ref.tolist())
    k=len(v)//2
    def fg(w):
        de,g=hb.relative_energy_gradient(qfull(w),ref)
        return de,g.reshape(3,k,2).sum(axis=0).ravel()
    res=minimize(fg,v,jac=True,method="L-BFGS-B",
        bounds=[(1e-8,math.pi-1e-8),(None,None)]*k,
        options={"maxiter":maxiter,"gtol":1e-8,"ftol":1e-15,
                 "maxls":58,"maxcor":25})
    de,g=fg(res.x)
    a=res.x.reshape(k,2)
    gr=float(np.sqrt(np.mean(g[::2]**2+
              (g[1::2]/np.maximum(np.sin(a[:,0]),1e-7))**2)))
    return e0+de,res.x,int(res.nit),gr


def remove_contribution(v):
    pts=xfull(v)
    k=len(v)//2
    reps=pts[:k]
    dots=reps@pts.T
    inv=1/np.sqrt(np.maximum(2-2*dots,1e-12))
    for m in range(3):inv[np.arange(k),np.arange(k)+m*k]=0.0
    pot=np.sum(inv,axis=1)
    own=np.sqrt(3)*np.maximum(1-reps[:,2]**2,1e-8)**.5
    # The other two members of the SAME orbit were excluded above.
    # Removing all three deletes 3*outside-potential plus three internal pairs.
    return 3*pot+3/own


def propose_insert(v,rng,num=900):
    pts=xfull(v)
    k=len(v)//2
    j=np.arange(num,dtype=float)+rng.random()
    z=1-2*j/num
    phi=(2.399963229728653*j+rng.uniform(0,PERIOD))%PERIOD-PERIOD/2
    rr=np.sqrt(1-z*z)
    yy=np.column_stack([rr*np.cos(phi),rr*np.sin(phi),z])
    dot=yy@pts.T
    maxdots=np.max(dot,axis=1)
    valid=(maxdots<math.cos(.055)) & ((1-z*z)>.008)
    pot=np.sum(1/np.sqrt(np.maximum(2-2*dot,1e-12)),axis=1)
    internal=np.sqrt(3)/np.sqrt(np.maximum(1-z*z,1e-10))
    cost=3*pot+internal
    cost[~valid]=np.inf
    ranked=np.argsort(cost)
    opts=[]
    for i in ranked:
        if not np.isfinite(cost[i]):break
        y=yy[i]
        if any(max(float(y@a),float(y@c3.rz(a[None,:],PERIOD)[0]))>math.cos(.12)
               for a in opts):continue
        opts.append(y)
        if len(opts)>=12:break
    return opts,{"candidates":int(np.sum(valid)),
                  "lowest_insertion_delta":float(np.min(cost))}


def remove_at(v,i):
    return np.delete(v.reshape(-1,2),i,axis=0).ravel()


def append_at(v,y):
    x=sb.vars_to_xyz(v)[0]
    return sb.xyz_to_vars(np.vstack([x,y]))


def fit_T(tfile,seed):
    import search_t_c3_basin_hop as t3
    xx=t3.load_points(tfile)
    pole,_=t3.approximate_threefold_axis(xx,seed)
    e,rm,axis,_=t3.refine_symmetry_axis(xx,pole)
    xx,alignerr,rms=t3.align_axis_to_z(xx,axis)
    if alignerr>2e-6:raise RuntimeError(("T symmetry fit",e,alignerr))
    return c3.xyz_to_vars(c3.c3_representatives(xx))


def physical_release(x,rng,maxiter):
    # Relax both exact C3 and weakly symmetry-broken basins; no symmetry
    # restriction on the physical full-960 score.
    d=rng.normal(size=x.shape)
    d-=np.sum(x*d,axis=1)[:,None]*x
    d*=.006/np.sqrt(np.mean(np.sum(d*d,axis=1)))
    y=hb.expmap(x,d)
    E,z,nit,ok,gr=hb.polish(y,maxiter)
    if gr>2e-4:
        E,z,nmore,ok,gr=hb.polish(z,maxiter+650)
        nit+=nmore
    return E,z,nit,gr


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("few_shots",type=pathlib.Path)
    ap.add_argument("--seed",type=int,required=True)
    ap.add_argument("--t-file",type=pathlib.Path)
    ap.add_argument("--cycles",type=int,default=120)
    ap.add_argument("--polish-iter",type=int,default=700)
    ap.add_argument("--out",type=pathlib.Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    rec,shot=sb.find_live(args.few_shots)
    if abs(rec-RECORD)>1e-7:raise RuntimeError(("record changed",rec))
    R=sb.load_cert(shot/"certificate.json")
    v0=c3.xyz_to_vars(c3.c3_representatives(R))
    e0,v0,n0,g0=polish(v0,1200)
    assert abs(e0-RECORD)<5e-6
    # Verify the three-point removal contribution against two independent
    # full pair sums, before relying on any orbit ranking.
    source_full=xfull(v0)
    base_abs=math.fsum(hb.pair_inverse(sb.xyz_to_vars(source_full)).tolist())
    contrib=remove_contribution(v0)
    for rep_id in (0,len(v0)//4,len(v0)//2-1):
        reduced=xfull(remove_at(v0,rep_id))
        e_reduced=math.fsum(hb.pair_inverse(sb.xyz_to_vars(reduced)).tolist())
        actual=base_abs-e_reduced
        predicted=contrib[rep_id]
        if abs(actual-predicted)>3e-7:
            raise RuntimeError(("orbit removal sum mismatch",rep_id,actual,predicted))
    print("VERIFIED_ORBIT_REMOVE",len(contrib),"first",float(contrib[0]),flush=True)
    pool=[{"energy":e0,"v":v0.copy(),"tag":"R"}]
    if args.t_file is not None:
        vt=fit_T(args.t_file,args.seed+1701)
        et,vt,nt,gt=polish(vt,1500)
        assert abs(et-444368.4373479895)<.0003,(et,)
        pool.append({"energy":et,"v":vt.copy(),"tag":"T"})
        print("INDEPENDENT_T",f"{et:.12f}","grad",gt,flush=True)
    print("C3_BASE",f"{e0:.12f}","grad",g0,"n",len(v0)//2,flush=True)
    physical_best=RECORD
    physical_new={}
    saved=[]
    nrelease=0
    nwinning=0
    unique_c3=[]
    for cycle in range(args.cycles):
        order=np.argsort([p["energy"] for p in pool])
        ordered=[pool[int(i)] for i in order]
        sel=ordered[int(rng.integers(min(len(ordered),8)))]
        v=sel["v"]
        direction="minus" if cycle%2 else "plus"
        if direction=="minus":
            contr=remove_contribution(v)
            top=np.argsort(contr)[-min(45,len(contr)):]
            idx=int(rng.choice(top))
            start=remove_at(v,idx)
            Ee,w,nt,gt=polish(start,args.polish_iter)
            expected=319
            # Under N957, there are 319 C3 orbits.
            if len(w)//2!=expected:raise RuntimeError("N957 size")
            candidates,meta=propose_insert(w,rng)
            if not candidates:continue
            noffspring=min(3,len(candidates))
            options=rng.choice(len(candidates),size=noffspring,replace=False)
            tasks=[("insert",j,append_at(w,candidates[int(j)])) for j in options]
        else:
            candidates,meta=propose_insert(v,rng)
            if not candidates:continue
            inserted=candidates[int(rng.integers(min(5,len(candidates))))]
            start=append_at(v,inserted)
            Ee,w,nt,gt=polish(start,args.polish_iter)
            expected=321
            if len(w)//2!=expected:raise RuntimeError("N963 size")
            contr=remove_contribution(w)
            # Removing the just-inserted orbital label (last one) merely
            # inverts the operation. Force a distinct orbit removal.
            scores=np.argsort(contr[:-1])[-min(45,len(contr)-1):]
            ids=rng.choice(scores,size=min(3,len(scores)),replace=False)
            tasks=[("remove",int(j),remove_at(w,int(j))) for j in ids]
        for which,label,z in tasks:
            ec,u,nit,grad=polish(z,args.polish_iter+280)
            if grad>1e-3:ec,u,nmore,grad=polish(u,1200);nit+=nmore
            if ec<RECORD+1.5 and all(abs(ec-x["energy"])>1e-6 for x in pool):
                if ec<RECORD+.9:
                    pool.append({"energy":ec,"v":u.copy(),
                                 "tag":f"{cycle}-{direction}-{which}-{label}"})
                    pool.sort(key=lambda x:x["energy"])
                    pool=pool[:24]
                if all(abs(ec-x)>2e-5 for x in unique_c3):
                    unique_c3.append(ec)
                    print("NEW_C3",cycle,direction,"E",f"{ec:.12f}",
                          "delta",f"{ec-RECORD:+.8f}",flush=True)
            if ec<RECORD+1.4:
                Ef,Y,nf,gf=physical_release(xfull(u),rng,maxiter=1500)
                nrelease+=1
                if Ef<physical_best-2e-7:
                    physical_best=Ef
                    print("BEST_N960",cycle,direction,
                          f"E={Ef:.12f}",f"delta={Ef-RECORD:+.9f}",flush=True)
                basin=round(Ef,5)
                if Ef<RECORD+.45 and basin not in physical_new:
                    physical_new[basin]={"energy":Ef,"source":cycle,
                                         "direction":direction,"points":Y.tolist()}
                    print("NEW_N960",cycle,direction,
                          f"E={Ef:.12f}",f"delta={Ef-RECORD:+.9f}",flush=True)
                if Ef<RECORD-2e-7:
                    dest=args.out/f"CANDIDATE-{args.seed}-{cycle}-{direction}-{label}.json"
                    dest.write_text(json.dumps({
                        "points":Y.tolist(),"energy":Ef,"cycle":cycle,
                        "seed":args.seed,"direction":direction,
                        "source_c3":ec,"grad_rms":gf})+"\n")
                    nwinning+=1
                    print("CANDIDATE",dest,"E",Ef,flush=True)
            else:
                Ef=None;gf=None
            row={"cycle":cycle,"direction":direction,"old_parent":sel["tag"],
                 "old_parent_E":sel["energy"],"intermediate_E":Ee,
                 "intermediate_grad":gt,"return_type":which,"return_index":int(label),
                 "c3_end_E":ec,"c3_end_grad":grad,
                 "free_end_E":Ef,"free_grad":gf}
            saved.append(row)
        if cycle%5==0:
            print("CYCLE",cycle,direction,"size_intermediate",957 if direction=="minus" else 963,
                  "parent",sel["tag"],"intermediate",f"{Ee:.9f}",
                  "lowest_C3",f"{min(x['energy'] for x in pool):.12f}",
                  "free_best",f"{physical_best:.12f}",
                  "unique_C3",len(unique_c3),
                  "unique_phys",len(physical_new),
                  "full_releases",nrelease,flush=True)
        if cycle%10==0 or cycle==args.cycles-1:
            data={"seed":args.seed,"cycles_done":cycle+1,
                  "target_cycles":args.cycles,
                  "best_N960":physical_best,"delta_record":physical_best-RECORD,
                  "winning_candidates":nwinning,"full_releases":nrelease,
                  "unique_c3_energies":unique_c3,
                  "pool":[{"energy":p["energy"],"tag":p["tag"],
                           "points":xfull(p["v"]).tolist()} for p in pool[:12]],
                  "new_full_basins":sorted(physical_new.values(),key=lambda x:x["energy"])[:12],
                  "rows":saved}
            (args.out/"result.json").write_text(json.dumps(data,separators=(",",":"))+"\n")
    print("FINAL",args.seed,"cycles",args.cycles,
          "BEST_N960",f"{physical_best:.12f}",
          "delta",f"{physical_best-RECORD:+.9f}",
          "CANDIDATES",nwinning,"unique_C3",len(unique_c3),
          "full_releases",nrelease,flush=True)


if __name__=="__main__":
    main()
