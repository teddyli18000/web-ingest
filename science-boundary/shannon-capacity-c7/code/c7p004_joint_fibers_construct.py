#!/usr/bin/env python3
"""Construct C7^10 record by joint owner deletion and x-specific 5D row/col fibers.

Unlike fixed PH/PV port gadgets, every auxiliary x may select its OWN
independent endpoint sets H_x,V_x. Deleted parent owner set R is selected
jointly. Optimize the ACTUAL 10D certificate size; any score >=134754 is
materialized and must pass the upstream p004 verifier.

Only the compact high-port endpoint envelope is fixed; the active auxiliary
fibers are fully reoptimized and their pairwise cross constraints are exact.
"""
from __future__ import annotations
import argparse,base64,hashlib,itertools,json,struct,time
from pathlib import Path
import numpy as np
from ortools.sat.python import cp_model

Q=7
U=Q**5
P=(1,7,49,343,2401)
DIG=tuple(tuple(v//p%Q for p in P) for v in range(U))
NB=tuple(tuple(sum(((DIG[v][i]+d[i])%Q)*P[i] for i in range(5))
               for d in itertools.product((-1,0,1),repeat=5))
         for v in range(U))

def clash(a,b):
    return all((u-v)%Q in (0,1,6) for u,v in zip(DIG[a],DIG[b]))

def legal(S):
    return len(S)==len(set(S)) and all(
        not clash(a,b) for i,a in enumerate(S) for b in S[i+1:])

def decode(code):
    raw=base64.b64decode(code["data"])
    assert hashlib.sha256(raw).hexdigest()==code["sha256"]
    return list(struct.unpack("<367H",raw))

def parent_codes(path):
    d=json.loads(path.read_text())
    return {item["name"]:decode(item) for item in d["parents"]}

def private_universe(I):
    flags=set(I)
    supp=[[] for _ in range(U)]
    for a in I:
        for z in NB[a]:supp[z].append(a)
    owners=sorted({supp[z][0] for z in range(U)
                   if z not in flags and len(supp[z])==1})
    ownerset=set(owners)
    E=sorted(v for v in range(U) if supp[v] and set(supp[v])<=ownerset)
    return owners,E,supp

def shift(S,delta):
    return sorted(sum(((DIG[x][i]+delta[i])%Q)*P[i] for i in range(5))
                  for x in S)

def tensor_arr(S):
    a=np.zeros((7,)*5,dtype=np.float64)
    for v in S:a[DIG[v]]=1.
    return a

def choose_shift(S,E,rank):
    near=set(z for e in E for z in NB[e])
    f=np.fft.fftn(tensor_arr(S))
    correlation=np.rint(np.fft.ifftn(np.conj(f)*np.fft.fftn(tensor_arr(near))).real).astype(np.int16)
    intersections=np.rint(np.fft.ifftn(np.conj(f)*np.fft.fftn(tensor_arr(E))).real).astype(np.int16)
    chosen=[(int(correlation.flat[k]), tuple(map(int,np.unravel_index(k,correlation.shape))))
            for k in range(correlation.size) if intersections.flat[k]==0]
    chosen.sort()
    _,delta=chosen[rank]
    X=shift(S,delta)
    assert not set(X)&set(E)
    assert sum(x in near for x in X)==chosen[rank][0]
    return X,delta,chosen[rank][0]

def make_certificate(B,H,V,X,out):
    pts={(a,c) for a in B for c in B}
    n=0
    for x in X:
        pts.update((a,x) for a in H[x])
        pts.update((x,b) for b in V[x])
        n+=len(H[x])+len(V[x])
    assert len(pts)==len(B)**2+n
    for x in X:
        assert legal(H[x]) and legal(V[x])
    for xi in X:
        for xj in X:
            if any(clash(e,xj) for e in H[xi]):
                assert all(not clash(xi,f) for f in V[xj])
    assert all(not clash(b,e) for b in B for row in
               list(H.values())+list(V.values()) for e in row)
    words=sorted(''.join(str(d) for d in DIG[a]+DIG[c]) for a,c in pts)
    assert len(words)==len(pts)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"points":words},separators=(",",":"))+"\n")
    return len(pts)

def search(I,X,t,seconds,workers,seed,out_dir):
    assert len(I)==len(X)==367 and legal(I) and legal(X)
    owners,E,support=private_universe(I)
    assert len(owners)>=t
    owner_index={v:i for i,v in enumerate(owners)}
    E=[e for e in E if e not in set(X)]
    ei={e:i for i,e in enumerate(E)}
    edges=[(i,ei[z]) for i,e in enumerate(E) for z in NB[e]
           if ei.get(z,-1)>i]
    relations={x:tuple(ei[z] for z in NB[x] if z in ei) for x in X}
    active=[x for x in X if relations[x]]
    m=len(E);a=len(active);inert=367-a
    mod=cp_model.CpModel()
    y=[mod.NewBoolVar(f"delete_{i}") for i in range(len(owners))]
    mod.Add(sum(y)==t)
    H=[[mod.NewBoolVar(f"h_{k}_{j}") for j in range(m)] for k in range(a)]
    V=[[mod.NewBoolVar(f"v_{k}_{j}") for j in range(m)] for k in range(a)]
    for k in range(a):
        mod.Add(sum(H[k])<=t)
        mod.Add(sum(V[k])<=t)
        for j,e in enumerate(E):
            for b in support[e]:
                mod.AddImplication(H[k][j],y[owner_index[b]])
                mod.AddImplication(V[k][j],y[owner_index[b]])
        for i,j in edges:
            mod.AddAtMostOne(H[k][i],H[k][j])
            mod.AddAtMostOne(V[k][i],V[k][j])
    # Cross orientations: (e,x_i) conflicts with (x_j,f)
    # iff e~x_j and f~x_i.
    for i,xi in enumerate(active):
        for j,xj in enumerate(active):
            for e in relations[xj]:
                for f in relations[xi]:
                    mod.AddAtMostOne(H[i][e],V[j][f])
    port_count=sum(sum(row) for row in H)+sum(sum(row) for row in V)
    fixed=(367-t)**2+2*t*inert
    mod.Maximize(port_count)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=workers
    solver.parameters.random_seed=seed
    start=time.monotonic()
    status=solver.Solve(mod)
    result={"method":"constructive-joint-deletion-per-auxiliary-fibers",
            "status":solver.StatusName(status),"t":t,"owners":len(owners),
            "endpoints":m,"active_auxiliary":a,"inert_auxiliary":inert,
            "edge_count":len(edges),"cross_constraints":
                 sum(len(relations[x]) for x in active)**2,
            "elapsed_seconds":round(time.monotonic()-start,3),
            "search_seed":seed,"target_score":134754}
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        R=[owners[j] for j in range(len(owners)) if solver.BooleanValue(y[j])]
        B=sorted(set(I)-set(R))
        Hd={x:list(R) for x in X}
        Vd={x:list(R) for x in X}
        for k,x in enumerate(active):
            Hd[x]=[E[j] for j in range(m) if solver.BooleanValue(H[k][j])]
            Vd[x]=[E[j] for j in range(m) if solver.BooleanValue(V[k][j])]
        expected=fixed+sum(len(Hd[x])+len(Vd[x]) for x in active)
        # fixed counts both inert fibers, active counts are the variables
        result.update({"selected_deleted_owners":R,
                       "score":expected,"improvement":expected-134753,
                       "active_fiber_count":sum(len(Hd[x])+len(Vd[x]) for x in active),
                       "best_objective_bound":solver.BestObjectiveBound()})
        # Independently replay every cross conflict and materialize the full 10D
        # candidate regardless of whether the requested record was reached.
        result["replayed_score"]=make_certificate(B,Hd,Vd,X,out_dir/"best_certificate.json")
        assert result["replayed_score"]==expected
        if expected>=134754:
            (out_dir/"certificate.json").write_bytes(
                (out_dir/"best_certificate.json").read_bytes())
            result["candidate"]=True
        else:
            result["candidate"]=False
    else:
        result["candidate"]=False
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("parents",type=Path)
    ap.add_argument("auxiliary",type=Path)
    ap.add_argument("output",type=Path)
    ap.add_argument("--parent",choices=("neutral14a","neutral14b"),required=True)
    ap.add_argument("--aux",choices=("neutral14a","neutral14b","port12a","port12b"),required=True)
    ap.add_argument("--t",type=int,required=True)
    ap.add_argument("--rank",type=int,default=0)
    ap.add_argument("--seconds",type=int,default=270)
    ap.add_argument("--workers",type=int,default=4)
    ap.add_argument("--seed",type=int,default=20261106)
    args=ap.parse_args()
    I=parent_codes(args.parents)[args.parent]
    aux=parent_codes(args.parents).get(args.aux)
    if aux is None:
        aux=list(map(int,(args.auxiliary/(args.aux+".ids")).read_text().split()))
    _,E,_=private_universe(I)
    X,shiftvec,active_min=choose_shift(aux,E,args.rank)
    args.output.mkdir(parents=True,exist_ok=True)
    result=search(I,X,args.t,args.seconds,args.workers,args.seed,args.output)
    result.update({"parent":args.parent,"auxiliary":args.aux,
                   "shift":list(shiftvec),"chosen_rank":args.rank,
                   "phase_active_count":active_min})
    (args.output/"status.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("FINAL",json.dumps(result,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
