#!/usr/bin/env python3
"""N960 Thomson: recombine low-energy donors' *edge connectivity*, not coordinates.

R/A/B/W and the independent D basin share tracked particle labels; every
donor is a physically polished local Thomson minimum. A C3/GA coordinate
mosaic or a linear displacement superposition can destroy crystal elastic
registry. Here a child inherits donor-specific Delaunay bond *motifs*
from different scar regions, then jointly re-equilibrates ALL 960 particles.

Given source and several elite donors, local scar-centred graph-set differences
produce a signed edge genome: remove old source-only edges, add donor-only
edges. An SO(3)-invariant differentiable bias for Euclidean pair separations
drives this exact joint graph change while the full Coulomb objective adapts
the surrounding lattice. Finally bias is removed completely and the true
N960 Coulomb energy is independently relaxed/scored. A known R->A directed
topology transfer serves as a construction positive control.

This is conceptually different from mixing the donor Cartesian coordinates,
symmetry-constrained GA, random fixed-N glides, or Gaussian basin exclusions.
"""
from __future__ import annotations
import argparse,json,math,pathlib
from collections import Counter
import numpy as np
from scipy.optimize import minimize
import search_hamiltonian_scar_braid as hb
import search_size_beam as sb
from search_e564_defect_flip_parallel import topology

RECORD=444368.3924061973


def edge_set(x):
    return set(topology(x)[1])


def scar_anchors(x):
    c,_,_=hb.scar_centers(x)
    assert len(c)==12,len(c)
    return c


def edge_region(x,e,centers):
    a,b=e
    mid=x[a]+x[b]
    mid/=np.linalg.norm(mid)
    return int(np.argmax(centers@mid))


def motif_genome(source,donors,regions,anchor_centers):
    old=edge_set(source)
    plus=set();minus=set();motifs=[]
    for region,name in regions:
        donor=donors[name]["points"]
        desired=edge_set(donor)
        added={e for e in desired-old if edge_region(source,e,anchor_centers)==region}
        deleted={e for e in old-desired if edge_region(source,e,anchor_centers)==region}
        plus.update(added);minus.update(deleted)
        motifs.append({"scar":int(region),"donor":name,
                       "add":len(added),"delete":len(deleted)})
    plus-=minus
    minus-=plus
    return sorted(plus),sorted(minus),motifs


def signed_edge_bias(q,plus,minus,strength):
    x,dt,dp=sb.vars_to_xyz(q)
    force=np.zeros_like(x)
    energy=0.
    scale=max(1.,math.sqrt((len(plus)+len(minus))/4.0))
    k=strength/scale
    for edges,sign in ((plus,1.),(minus,-1.)):
        for i,j in edges:
            delta=x[i]-x[j]
            d=float(np.linalg.norm(delta))
            energy+=sign*k*d
            df=sign*(k/d)*delta
            force[i]+=df
            force[j]-=df
    grad=np.column_stack([np.einsum("ij,ij->i",force,dt),
                          np.einsum("ij,ij->i",force,dp)]).ravel()
    return float(energy),grad


def bias_test(x,plus,minus):
    q=sb.xyz_to_vars(x)
    rng=np.random.default_rng(99831)
    noise=rng.normal(size=x.shape)
    noise-=np.sum(noise*x,axis=1)[:,None]*x
    noise*=.003/np.sqrt(float(np.mean(np.sum(noise*noise,axis=1))))
    y=hb.expmap(x,noise)
    qq=sb.xyz_to_vars(y)
    e,g=signed_edge_bias(qq,plus,minus,11.)
    worst=0.
    for j in rng.choice(len(qq),12,replace=False):
        h=1.5e-6
        a=qq.copy();b=qq.copy();a[j]+=h;b[j]-=h
        fd=(signed_edge_bias(a,plus,minus,11.)[0]-
            signed_edge_bias(b,plus,minus,11.)[0])/(2*h)
        err=abs(fd-g[j])/(1+abs(fd))
        worst=max(err,worst)
        if err>1e-6:
            raise RuntimeError(("edge-gene force gradient",j,fd,g[j],err))
    return {"bias":e,"max_scaled_gradient_error":worst}


def constrained_polish(x,plus,minus,k,maxiter):
    q=sb.xyz_to_vars(x)
    ref=hb.pair_inverse(q)
    E0=math.fsum(ref.tolist())
    def fg(v):
        de,g=hb.relative_energy_gradient(v,ref)
        ep,gp=signed_edge_bias(v,plus,minus,k)
        return de+ep,g+gp
    r=minimize(fg,q,jac=True,method="L-BFGS-B",
        bounds=[(1e-8,math.pi-1e-8),(None,None)]*len(x),
        options={"maxiter":maxiter,"ftol":1e-15,"gtol":1e-8,
                 "maxls":60,"maxcor":25})
    de,g=hb.relative_energy_gradient(r.x,ref)
    ep,gp=signed_edge_bias(r.x,plus,minus,k)
    return E0+de,ep,sb.vars_to_xyz(r.x)[0],int(r.nit)


def overlap(x,plus,minus):
    es=edge_set(x)
    return sum(e in es for e in plus),sum(e not in es for e in minus)


def physical(x,maxiter=1350):
    E,Y,n,ok,gr=hb.polish(x,maxiter)
    if gr>1e-4:
        E,Y,n2,ok,gr=hb.polish(Y,1400)
    return E,Y,gr


def load_donors(fewshots,a_json,b_json,w_json,d_json):
    rec,shot=sb.find_live(fewshots)
    assert abs(rec-RECORD)<1e-7
    def json_pts(p):
        return np.asarray(json.loads(p.read_text())["points"],float)
    base={
        "R":sb.load_cert(shot/"certificate.json"),
        "A":json_pts(a_json),
        "B":json_pts(b_json),
        "W":np.asarray(json.loads(w_json.read_text())["minima"][0]["points"],float),
        "D":json_pts(d_json)}
    expected={"R":RECORD,"A":444368.3956862257,
      "B":444368.4029728612,"D":444368.4109930845,
      "W":444368.42162124}
    donors={}
    for name,X in base.items():
        e,Y,gr=physical(X,1550)
        assert abs(e-expected[name])<3e-5,(name,e,expected[name])
        donors[name]={"energy":e,"points":Y,"tag":name}
        print("SEED",name,f"{e:.12f}","gradient",gr,flush=True)
    return donors


def main():
    p=argparse.ArgumentParser()
    p.add_argument("few_shots",type=pathlib.Path)
    p.add_argument("--a-json",type=pathlib.Path,required=True)
    p.add_argument("--b-json",type=pathlib.Path,required=True)
    p.add_argument("--w-json",type=pathlib.Path,required=True)
    p.add_argument("--d-json",type=pathlib.Path,required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--cycles",type=int,default=70)
    p.add_argument("--maxiter",type=int,default=550)
    p.add_argument("--out",type=pathlib.Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    donors=load_donors(args.few_shots,args.a_json,args.b_json,args.w_json,args.d_json)
    anchors=scar_anchors(donors["R"]["points"])
    pool=list(donors.values())
    genome=motif_genome(donors["R"]["points"],donors,
                        [(j,"A") for j in range(12)],anchors)
    src=donors["R"]["points"]
    plus,minus,meta=genome
    assert len(plus)>0 and len(minus)>0,(len(plus),len(minus))
    chk=bias_test(src,plus,minus)
    print("POSITIVE_TEMPLATE_RA","add",len(plus),
          "delete",len(minus),"gradient",chk,flush=True)
    best=RECORD;novel=0;winners=0;rows=[]
    for t in range(args.cycles):
        ctrl=t%10==0
        positive=t%23==1
        if positive:
            parent=donors["R"]
            regions=[(j,"A") for j in range(12)]
        else:
            if t%7==0:parent=pool[0]
            else:
                weights=np.exp(-np.arange(min(10,len(pool)))/3.0)
                weights/=weights.sum()
                parent=pool[int(rng.choice(len(weights),p=weights))]
            nscars=int(rng.integers(2,9))
            ids=rng.choice(12,nscars,replace=False)
            region_donors=[name for name in donors if
                           abs(donors[name]["energy"]-parent["energy"])>1e-7]
            regions=[(int(j),str(rng.choice(region_donors))) for j in ids]
        x=parent["points"].copy()
        plus,minus,motifs=motif_genome(x,donors,regions,anchors)
        if not plus and not minus:
            continue
        k=float(np.exp(rng.uniform(math.log(4.),math.log(60.))))
        if positive:
            k=float(rng.choice([12.,24.,45.]))
        if ctrl:
            # Same origin and motifs but no edge bias, applied ordinary
            # Hamiltonian collective flow; scores are true physics.
            z=hb.transport(x,rng,hb.scar_centers(x)[0],.035,"braid")
            init_added=init_deleted=0;stages=[]
        else:
            z=x
            stages=[]
            for frac in (.33,.75,1.):
                E,bias,z,n=constrained_polish(
                    z,plus,minus,k*frac,args.maxiter)
                a,d=overlap(z,plus,minus)
                stages.append({"fraction":frac,"Coulomb_E":E,
                               "bias_E":bias,"added":a,"deleted":d,
                               "niter":n})
            init_added,init_deleted=overlap(z,plus,minus)
            if t%3==0:
                E,bias,z,n=constrained_polish(
                    z,plus,minus,.25*k,args.maxiter//2)
                a,d=overlap(z,plus,minus)
                stages.append({"fraction":.25,"Coulomb_E":E,
                               "bias_E":bias,"added":a,"deleted":d,
                               "niter":n})
        Ef,Y,gr=physical(z,args.maxiter+750)
        after_added,after_deleted=overlap(Y,plus,minus)
        if Ef<best-2e-7:
            best=Ef
            print("BEST",t,f"{Ef:.12f}","dR",f"{Ef-RECORD:+.9f}",flush=True)
        isnew=all(abs(Ef-s["energy"])>3e-7 for s in pool)
        if isnew and Ef<RECORD+1.0:
            novel+=1
            pool.append({"energy":Ef,"points":Y.copy(),
                         "tag":f"{t}-edge-genome"})
            pool.sort(key=lambda r:r["energy"])
            pool=pool[:22]
            print("NEW",t,"E",f"{Ef:.12f}",
                "dR",f"{Ef-RECORD:+.9f}","motifs",motifs,
                "added_after",after_added,"control",ctrl,flush=True)
        if Ef<RECORD-2e-7:
            f=args.out/f"CANDIDATE-{args.seed}-{t}.json"
            f.write_text(json.dumps({"energy":Ef,"points":Y.tolist(),
                "cycle":t,"seed":args.seed,"grad_rms":gr,
                "motifs":motifs})+"\n")
            winners+=1
            print("CANDIDATE",f,f"{Ef:.12f}",flush=True)
        rows.append({"cycle":t,"parent":parent["tag"],"positive_control":positive,
            "no_bias_control":ctrl,"strength":k,"source_energy":parent["energy"],
            "motifs":motifs,"genes_add":len(plus),"genes_delete":len(minus),
            "under_bias_added":init_added,"under_bias_deleted":init_deleted,
            "after_quench_added":after_added,"after_quench_deleted":after_deleted,
            "energy":Ef,"dR":Ef-RECORD,"new":isnew,
            "grad_rms":gr,"stages":stages})
        if t%5==0:
            print("CYCLE",t,"E",f"{Ef:.12f}",
                  "genes",len(plus),len(minus),"bias_contacts",init_added,
                  "physical_contacts",after_added,"best",f"{best:.12f}",flush=True)
        if t%10==0 or t==args.cycles-1:
            result={"seed":args.seed,"cycles_done":t+1,
                "best":best,"new":novel,"candidates":winners,
                "positive_template_size":{"add":len(genome[0]),"delete":len(genome[1])},
                "gradient_test":chk,
                "elites":[{"energy":s["energy"],"tag":s["tag"],
                           "points":s["points"].tolist()} for s in pool[:14]],
                "rows":rows}
            (args.out/"result.json").write_text(
                json.dumps(result,separators=(",",":"))+"\n")
    print("FINAL",args.seed,"cycles",args.cycles,
          "best",f"{best:.12f}","new",novel,
          "candidates",winners,flush=True)


if __name__=="__main__":
    main()
