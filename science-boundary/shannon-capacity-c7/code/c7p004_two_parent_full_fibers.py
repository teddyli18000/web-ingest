#!/usr/bin/env python3
"""Constructive 10D joint search with distinct left/right 367 parent basins.

BL=(IL-RL), BR=(IR-RR) need not arise from the same five-dimensional
code. Each 5D auxiliary word x may choose entirely independent fibers H[x],
V[x] from the respective supported endpoint domains. Unlike earlier models,
NO artificial upper cap of |R| is imposed on fiber cardinality; if an
independent fiber exceeds the deletion count, that itself yields a new 5D
code, which this model should find rather than forbid.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from c7p004_joint_fibers_construct import (
    NB,DIG,clash,legal,parent_codes,private_universe,choose_shift,
)

def optimize(IL,IR,X,l,r,seconds,workers,out,seed):
    ownL,EL,suppL=private_universe(IL)
    ownR,ER,suppR=private_universe(IR)
    oL={z:i for i,z in enumerate(ownL)}
    oR={z:i for i,z in enumerate(ownR)}
    excluded=set(X)
    EL=[e for e in EL if e not in excluded]
    ER=[e for e in ER if e not in excluded]
    idxL={e:i for i,e in enumerate(EL)}
    idxR={e:i for i,e in enumerate(ER)}
    relationL={x:tuple(idxL[e] for e in NB[x] if e in idxL) for x in X}
    relationR={x:tuple(idxR[e] for e in NB[x] if e in idxR) for x in X}
    active=[x for x in X if relationL[x] or relationR[x]]
    leftEdges=[(i,idxL[v]) for i,e in enumerate(EL) for v in NB[e] if idxL.get(v,-1)>i]
    rightEdges=[(i,idxR[v]) for i,e in enumerate(ER) for v in NB[e] if idxR.get(v,-1)>i]
    model=cp_model.CpModel()
    yL=[model.NewBoolVar(f"dL_{j}") for j in range(len(ownL))]
    yR=[model.NewBoolVar(f"dR_{j}") for j in range(len(ownR))]
    model.Add(sum(yL)==l);model.Add(sum(yR)==r)
    H=[[model.NewBoolVar(f"H_{i}_{j}") for j in range(len(EL))] for i in range(len(active))]
    V=[[model.NewBoolVar(f"V_{i}_{j}") for j in range(len(ER))] for i in range(len(active))]
    for i in range(len(active)):
        for j,e in enumerate(EL):
            for owner in suppL[e]:model.AddImplication(H[i][j],yL[oL[owner]])
        for j,e in enumerate(ER):
            for owner in suppR[e]:model.AddImplication(V[i][j],yR[oR[owner]])
        for j,k in leftEdges:model.AddAtMostOne(H[i][j],H[i][k])
        for j,k in rightEdges:model.AddAtMostOne(V[i][j],V[i][k])
    cross=0
    for i,xi in enumerate(active):
        for j,xj in enumerate(active):
            for e in relationL[xj]:
                for f in relationR[xi]:
                    model.AddAtMostOne(H[i][e],V[j][f])
                    cross+=1
    model.Maximize(sum(sum(h) for h in H)+sum(sum(v) for v in V))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=workers
    solver.parameters.random_seed=seed
    start=time.monotonic()
    status=solver.Solve(model)
    result={"method":"two-parent-unbounded-adaptive-10D-fibers",
            "status":solver.StatusName(status),"l":l,"r":r,
            "left_parent_private_owners":len(ownL),
            "right_parent_private_owners":len(ownR),
            "left_endpoints":len(EL),"right_endpoints":len(ER),
            "active_x":len(active),"inert_x":367-len(active),
            "cross_clauses":cross,"elapsed_seconds":round(time.monotonic()-start,2)}
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        RL=[ownL[i] for i in range(len(ownL)) if solver.BooleanValue(yL[i])]
        RR=[ownR[i] for i in range(len(ownR)) if solver.BooleanValue(yR[i])]
        BL=set(IL)-set(RL);BR=set(IR)-set(RR)
        Hd={x:RL for x in X};Vd={x:RR for x in X}
        for k,x in enumerate(active):
            Hd[x]=[e for j,e in enumerate(EL) if solver.BooleanValue(H[k][j])]
            Vd[x]=[e for j,e in enumerate(ER) if solver.BooleanValue(V[k][j])]
        # Complete independent replay on 5D fibers and all row/col cross pairs.
        assert all(legal(Hd[x]) and legal(Vd[x]) for x in X)
        assert all(not clash(a,b) for a in BL for L in Hd.values() for b in L)
        assert all(not clash(a,b) for a in BR for L in Vd.values() for b in L)
        assert all(not(any(clash(e,xj) for e in Hd[xi]) and
                       any(clash(xi,f) for f in Vd[xj]))
                   for xi in X for xj in X)
        score=(367-l)*(367-r)+sum(len(Hd[x])+len(Vd[x]) for x in X)
        core={(a,b) for a in BL for b in BR}
        for x in X:
            core.update((e,x) for e in Hd[x])
            core.update((x,f) for f in Vd[x])
        assert len(core)==score
        words=sorted("".join(str(d) for d in DIG[a]+DIG[b]) for a,b in core)
        (out/"best_certificate.json").write_text(
            json.dumps({"points":words},separators=(",",":"))+"\n")
        result.update({"score":score,"improvement":score-134753,
                       "selected_left_owners":RL,"selected_right_owners":RR,
                       "max_H_fiber":max(map(len,Hd.values())),
                       "max_V_fiber":max(map(len,Vd.values())),
                       "best_bound_fibers":solver.BestObjectiveBound(),
                       "objective_fibers":int(solver.ObjectiveValue())})
        if score>=134754:
            (out/"certificate.json").write_bytes((out/"best_certificate.json").read_bytes())
            result["candidate"]=True
        else:result["candidate"]=False
    else:result["candidate"]=False
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("parents",type=Path)
    ap.add_argument("aux",type=Path)
    ap.add_argument("out",type=Path)
    ap.add_argument("--left",choices=("neutral14a","neutral14b"),required=True)
    ap.add_argument("--right",choices=("neutral14a","neutral14b"),required=True)
    ap.add_argument("--aux-name",choices=("neutral14a","neutral14b","port12a","port12b"),required=True)
    ap.add_argument("--l",type=int,required=True);ap.add_argument("--r",type=int,required=True)
    ap.add_argument("--seconds",type=int,default=220)
    ap.add_argument("--workers",type=int,default=4)
    ap.add_argument("--rank",type=int,default=0)
    a=ap.parse_args()
    pool=parent_codes(a.parents)
    IL=pool[a.left];IR=pool[a.right]
    auxiliary=pool.get(a.aux_name)
    if auxiliary is None:auxiliary=list(map(int,(a.aux/(a.aux_name+".ids")).read_text().split()))
    EL=private_universe(IL)[1];ER=private_universe(IR)[1]
    X,offset,cost=choose_shift(auxiliary,sorted(set(EL)|set(ER)),a.rank)
    a.out.mkdir(parents=True,exist_ok=True)
    result=optimize(IL,IR,X,a.l,a.r,a.seconds,a.workers,a.out,2026110601)
    result.update({"left_parent":a.left,"right_parent":a.right,"aux":a.aux_name,
                   "aux_translation":list(offset),"minimum_active_x":cost})
    (a.out/"status.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("FINAL",json.dumps(result,sort_keys=True),flush=True)

if __name__=="__main__":main()
