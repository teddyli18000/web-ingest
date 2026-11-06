#!/usr/bin/env python3
"""Constructive asymmetric per-auxiliary 10D fibers, with jointly chosen R_L,R_R.

This releases the same-deletion-set restriction: left/right core sets differ,
and each 5D auxiliary word receives independent fiber choices.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from c7p004_joint_fibers_construct import (
    DIG,NB,clash,legal,parent_codes,private_universe,choose_shift)

def construct(BL,BR,H,V,X,out):
    pts={(a,b) for a in BL for b in BR}
    expected=len(pts)
    for x in X:
        assert legal(H[x]) and legal(V[x])
        pts.update((a,x) for a in H[x])
        pts.update((x,b) for b in V[x])
        expected+=len(H[x])+len(V[x])
    assert len(pts)==expected
    for xi in X:
        for xj in X:
            if any(clash(e,xj) for e in H[xi]):
                assert not any(clash(xi,f) for f in V[xj])
    assert all(not clash(b,e) for b in BL for row in H.values() for e in row)
    assert all(not clash(b,e) for b in BR for row in V.values() for e in row)
    words=sorted(''.join(map(str,DIG[a]+DIG[b])) for a,b in pts)
    out.write_text(json.dumps({"points":words},separators=(",",":"))+"\n")
    return len(words)

def solve(I,X,l,r,seconds,workers,seed,out):
    owners,E,support=private_universe(I)
    assert len(owners)>=max(l,r) and legal(I) and legal(X)
    E=[e for e in E if e not in set(X)]
    owner_idx={a:j for j,a in enumerate(owners)}
    ei={e:j for j,e in enumerate(E)}
    edges=[(i,ei[z]) for i,e in enumerate(E) for z in NB[e]
           if ei.get(z,-1)>i]
    relation={x:tuple(ei[z] for z in NB[x] if z in ei) for x in X}
    active=[x for x in X if relation[x]]
    a=len(active);m=len(E);model=cp_model.CpModel()
    yL=[model.NewBoolVar(f"delL{j}") for j in range(len(owners))]
    yR=[model.NewBoolVar(f"delR{j}") for j in range(len(owners))]
    model.Add(sum(yL)==l);model.Add(sum(yR)==r)
    H=[[model.NewBoolVar(f"h{k}_{j}") for j in range(m)] for k in range(a)]
    V=[[model.NewBoolVar(f"v{k}_{j}") for j in range(m)] for k in range(a)]
    for k in range(a):
        model.Add(sum(H[k])<=l);model.Add(sum(V[k])<=r)
        for j,e in enumerate(E):
            for b in support[e]:
                model.AddImplication(H[k][j],yL[owner_idx[b]])
                model.AddImplication(V[k][j],yR[owner_idx[b]])
        for i,j in edges:
            model.AddAtMostOne(H[k][i],H[k][j])
            model.AddAtMostOne(V[k][i],V[k][j])
    for i,xi in enumerate(active):
        for j,xj in enumerate(active):
            for e in relation[xj]:
                for f in relation[xi]:
                    model.AddAtMostOne(H[i][e],V[j][f])
    obj=sum(sum(v) for v in H)+sum(sum(v) for v in V)
    model.Maximize(obj)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=workers
    solver.parameters.random_seed=seed
    t0=time.monotonic();status=solver.Solve(model)
    info={"method":"constructive-asymmetric-x-specific-fibers",
          "status":solver.StatusName(status),"left_deletions":l,"right_deletions":r,
          "active_auxiliary":a,"inert_auxiliary":367-a,"endpoints":m,
          "owners":len(owners),"elapsed_seconds":round(time.monotonic()-t0,3)}
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        RL=[owners[j] for j in range(len(owners)) if solver.BooleanValue(yL[j])]
        RR=[owners[j] for j in range(len(owners)) if solver.BooleanValue(yR[j])]
        BL=sorted(set(I)-set(RL));BR=sorted(set(I)-set(RR))
        Hd={x:RL for x in X};Vd={x:RR for x in X}
        for k,x in enumerate(active):
            Hd[x]=[E[j] for j in range(m) if solver.BooleanValue(H[k][j])]
            Vd[x]=[E[j] for j in range(m) if solver.BooleanValue(V[k][j])]
        actual=construct(BL,BR,Hd,Vd,X,out/"best_certificate.json")
        objval=(367-l)*(367-r)+(367-a)*(l+r)+int(solver.ObjectiveValue())
        assert actual==objval
        info.update({"score":actual,"improvement":actual-134753,
                     "best_objective_bound":solver.BestObjectiveBound(),
                     "left_removed":RL,"right_removed":RR,
                     "active_fiber_count":int(solver.ObjectiveValue())})
        if actual>=134754:
            (out/"certificate.json").write_bytes(
                (out/"best_certificate.json").read_bytes())
            info["candidate"]=True
        else: info["candidate"]=False
    else: info["candidate"]=False
    return info

def main():
    p=argparse.ArgumentParser()
    p.add_argument("parents",type=Path);p.add_argument("auxiliary",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("--parent",choices=("neutral14a","neutral14b"),required=True)
    p.add_argument("--aux",choices=("neutral14a","neutral14b","port12a","port12b"),required=True)
    p.add_argument("--left",type=int,required=True)
    p.add_argument("--right",type=int,required=True)
    p.add_argument("--rank",type=int,default=0)
    p.add_argument("--seconds",type=int,default=220)
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--seed",type=int,default=2026110689)
    p.add_argument("--aux-file",type=Path)
    a=p.parse_args()
    src=parent_codes(a.parents)
    I=src[a.parent]
    _,E,_=private_universe(I)
    if a.aux_file:
        X=sorted(map(int,a.aux_file.read_text().split()))
        assert len(X)==367 and legal(X) and not set(X).intersection(E)
        endpoint_neighborhood={z for e in E for z in NB[e]}
        active_min=sum(x in endpoint_neighborhood for x in X)
        offset=None
    else:
        S=src.get(a.aux)
        if S is None:S=list(map(int,(a.auxiliary/(a.aux+".ids")).read_text().split()))
        X,offset,active_min=choose_shift(S,E,a.rank)
    a.out.mkdir(parents=True,exist_ok=True)
    result=solve(I,X,a.left,a.right,a.seconds,a.workers,a.seed,a.out)
    result.update({"parent":a.parent,"auxiliary":a.aux,"shift":list(offset) if offset is not None else None,
                   "chosen_rank":a.rank,"phase_active_count":active_min})
    (a.out/"status.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("FINAL",json.dumps(result,sort_keys=True),flush=True)
if __name__=="__main__":main()
