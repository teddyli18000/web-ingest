#!/usr/bin/env python3
"""Construct N960 descendants of a new C2 near-D2 stationary configuration.

Search source: successful C2 20/24-dislocation genetic run 42500890656,
seed 84201, whose archived N960 C2-quotient minimum at E~444368.404283112
is only +0.00020258 above D2, yet one random symmetry-breaking kick
descended to D2. Classify full-space constrained-stationary Hessian, then
release +/- all lowest negative physical tangent modes and targeted
phase-combinations, rather than assuming a single random exit is exhaustive.

All endpoints are *fully unconstrained* actual N960 Coulomb minima. Source
coordinate archives are downloaded from the completed original Action;
nothing is reconstructed from an approximate energy scalar.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.sparse.linalg import eigsh
import search_c2_defect_replica_exchange as c2
import search_hamiltonian_scar_braid as hb
import search_size_beam as sb
import diagnose_soft_modes as sm

RECORD=444368.3924061973
TARGET=444368.404283112

def source_points(root):
    files=sorted(root.rglob("result.json"))
    results=[json.loads(f.read_text()) for f in files]
    d=next(q for q in results if q.get("seed")==84201
           and q.get("sweeps_done")==85)
    source=min(d["c2_pool"],key=lambda z:abs(z["E"]-TARGET))
    if abs(source["E"]-TARGET)>1e-5:
        raise RuntimeError(("C2 near D2 elite not in saved artifact",source["E"]))
    return np.asarray(source["points"],float),source,d

def reconstruct_stationary(x):
    reps=x[:480]
    e,v,n,ok,gr=c2.c2_polish(sb.xyz_to_vars(reps),1800)
    y=c2.xyzfull(v)
    assert abs(e-TARGET)<4e-6,(e,TARGET)
    return e,y,gr

def physical_q_kick(q,vec,amp):
    scale=sm.physical_scale(q)
    dq=vec/scale
    q0=q+amp*math.sqrt(len(q)//2)*dq
    q0[0::2]=np.clip(q0[0::2],1e-7,math.pi-1e-7)
    return q0

def main():
    p=argparse.ArgumentParser()
    p.add_argument("few_shots",type=pathlib.Path)
    p.add_argument("--artifact-root",type=pathlib.Path,required=True)
    p.add_argument("--out",type=pathlib.Path,required=True)
    p.add_argument("--seed",type=int,default=55233)
    p.add_argument("--maxiter",type=int,default=1500)
    p.add_argument("--k",type=int,default=9)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    live,shot=sb.find_live(args.few_shots)
    assert abs(live-RECORD)<1e-7
    source,meta,result=source_points(args.artifact_root)
    e,x,gr=reconstruct_stationary(source)
    print("C2_SOURCE",f"{e:.12f}","tag",meta["tag"],
          "C2grad",gr,flush=True)
    q=sb.xyz_to_vars(x)
    E_sm,gsm=sm.fg(q)
    scale=sm.physical_scale(q)
    physrms=float(np.sqrt(np.mean((gsm/scale)**2)))
    true_e=hb.energy_abs(q)
    print("INDEPENDENT_STATIONARITY","E_sm",f"{E_sm:.12f}",
          "E_compiled",f"{true_e:.12f}",
          "physical_rms",physrms,flush=True)
    if abs(true_e-e)>2e-5 or physrms>.004:
        raise RuntimeError(("C2 stationary Hessian invalid",E_sm,true_e,e,physrms))
    H,raw,Q,calls=sm.build_hessian(q,2e-6,3e5)
    rng=np.random.default_rng(args.seed)
    a=rng.normal(size=len(q));b=rng.normal(size=len(q))
    a-=Q@(Q.T@a);b-=Q@(Q.T@b)
    a/=np.linalg.norm(a);b/=np.linalg.norm(b)
    sym=abs(float(a@raw(b)-b@raw(a)))
    print("HESSIAN_SYMMETRY",sym,flush=True)
    if sym>3e-3:raise RuntimeError(("Hessian not symmetric",sym))
    vals,V=eigsh(H,k=args.k,which="SA",tol=3e-5,
                 maxiter=1000,ncv=max(45,4*args.k))
    idx=np.argsort(vals);vals=vals[idx];V=V[:,idx]
    modes=[]
    for i,lam in enumerate(vals):
        v=V[:,i]
        rotation=float(np.sum((Q.T@v)**2))
        residual=float(np.linalg.norm(raw(v)+3e5*(Q@(Q.T@v))-lam*v))
        modes.append({"index":int(i),"lambda":float(lam),
                      "rot_overlap":rotation,"residual":residual})
        print("MODE",i,"lambda",f"{lam:.12f}",
              "rotation",rotation,"residual",residual,flush=True)
    neg=list(np.flatnonzero(vals<-.002))
    print("NEGATIVE_MODES",neg,"lowest",float(vals[0]),flush=True)
    # All soft negative modes are tested. We add two lowest positive
    # modes as side controls; correlation pairs are tested if two
    # unstable directions exist.
    active=neg[:6]+[int(i) for i in range(len(vals))
                    if vals[i]>=-.002][:2]
    active=sorted(set(active))
    tests=[]
    for i in active:
        for s in (-1,1):
            for amp in (.0015,.004,.009,.018):
                tests.append((f"eig{i}{'p' if s>0 else 'm'}",
                              s*V[:,i],amp))
    if len(neg)>=2:
        v0=V[:,neg[0]];v1=V[:,neg[1]]
        for theta in np.linspace(0,2*math.pi,12,endpoint=False):
            w=math.cos(theta)*v0+math.sin(theta)*v1
            for amp in (.004,.012):
                tests.append((f"unstable-circle-{theta:.3f}",w,amp))
    if not neg:
        for i in range(min(3,len(vals))):
            for amp in (.018,.04):
                tests.append((f"positive-escape-{i}",V[:,i],amp))
    rows=[];elites=[];best=RECORD;winners=0
    for t,(tag,mode,amp) in enumerate(tests):
        start=sm.vars_to_xyz(physical_q_kick(q,mode,amp))[0]
        Ep,y,n,ok,gr=hb.polish(start,args.maxiter)
        if gr>2e-4:
            Ep,y,n2,ok,gr=hb.polish(y,1500);n+=n2
        distinct=all(abs(Ep-z["E"])>3e-7 for z in elites)
        if distinct:
            elites.append({"E":Ep,"tag":tag,"amp":amp,
                           "points":y.tolist(),"gr":gr})
            elites.sort(key=lambda z:z["E"])
            elites=elites[:15]
        if Ep<best-2e-7:
            best=Ep
            print("BEST",t,tag,"E",f"{Ep:.12f}",flush=True)
        if Ep<RECORD-2e-7:
            path=args.out/f"CANDIDATE-{args.seed}-{t}.json"
            path.write_text(json.dumps({"points":y.tolist(),
                "energy":Ep,"tag":tag,"amp":amp,"gradient_rms":gr})+"\n")
            winners+=1
            print("CANDIDATE",path,"E",f"{Ep:.12f}",flush=True)
        print("RELEASE",t,tag,amp,"E",f"{Ep:.12f}",
              "dR",f"{Ep-RECORD:+.9f}","gr",gr,flush=True)
        rows.append({"test":t,"tag":tag,"amp":amp,"energy":Ep,
                     "delta_record":Ep-RECORD,"gr":gr,"nit":n})
        if t%8==0 or t==len(tests)-1:
            data={"source_E":e,"source_tag":meta["tag"],
                  "independent_gradient_rms":physrms,
                  "hessian_symmetry":sym,
                  "lowest_modes":modes,"negative_indices":neg,
                  "mode_gradient_calls":calls["n"],
                  "release_count":len(rows),"best_energy":best,
                  "winning_candidates":winners,
                  "new_elites":elites,"rows":rows}
            (args.out/"result.json").write_text(
                json.dumps(data,separators=(",",":"))+"\n")
    print("FINAL","lowest_new_elite",
          [(r["E"],r["tag"]) for r in elites[:7]],
          "best",f"{best:.12f}","winners",winners,
          "releases",len(rows),flush=True)

if __name__=="__main__":
    main()
