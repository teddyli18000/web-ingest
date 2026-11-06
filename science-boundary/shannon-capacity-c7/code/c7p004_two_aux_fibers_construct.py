#!/usr/bin/env python3
"""Constructive C7^10 independent-set search with TWO distinct 367-word auxiliaries.

Release three coupled variables simultaneously: independent left/right parent
cores I_L,I_R, distinct row/column auxiliary codes X_H,X_V, and unbounded
per-auxiliary endpoint fibers. The union code is

 (B_L x B_R) U (union_{x in X_H} H_x x {x})
             U (union_{y in X_V} {y} x V_y).

All hard constraints are encoded exactly; every resulting 10D point is
materialized and subjected to independent combinatorial replay.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from c7p004_joint_fibers_construct import (
    NB,DIG,clash,legal,private_universe,parent_codes,choose_shift
)

def solve(IL,IR,XH,XV,l,r,limit,workers,out):
    ownL,EL,suppL=private_universe(IL)
    ownR,ER,suppR=private_universe(IR)
    assert legal(IL) and legal(IR) and legal(XH) and legal(XV)
    assert len(IL)==len(IR)==len(XH)==len(XV)==367
    assert not set(XH).intersection(ER) and not set(XV).intersection(EL)
    idxL={e:j for j,e in enumerate(EL)}
    idxR={e:j for j,e in enumerate(ER)}
    ownersL={v:i for i,v in enumerate(ownL)}
    ownersR={v:i for i,v in enumerate(ownR)}
    rL={x:tuple(idxL[e] for e in NB[x] if e in idxL) for x in XV}
    rR={x:tuple(idxR[e] for e in NB[x] if e in idxR) for x in XH}
    activeH=[x for x in XH if rR[x]]
    activeV=[y for y in XV if rL[y]]
    eL=[(i,idxL[e]) for i,v in enumerate(EL) for e in NB[v] if idxL.get(e,-1)>i]
    eR=[(i,idxR[e]) for i,v in enumerate(ER) for e in NB[v] if idxR.get(e,-1)>i]
    m=cp_model.CpModel()
    dL=[m.NewBoolVar(f"dL{i}") for i in range(len(ownL))]
    dR=[m.NewBoolVar(f"dR{i}") for i in range(len(ownR))]
    m.Add(sum(dL)==l);m.Add(sum(dR)==r)
    H=[[m.NewBoolVar(f"H{i}_{j}") for j in range(len(EL))] for i in range(len(activeH))]
    V=[[m.NewBoolVar(f"V{i}_{j}") for j in range(len(ER))] for i in range(len(activeV))]
    for i in range(len(activeH)):
        for j,e in enumerate(EL):
            for b in suppL[e]:m.AddImplication(H[i][j],dL[ownersL[b]])
        for j,k in eL:m.AddAtMostOne(H[i][j],H[i][k])
    for i in range(len(activeV)):
        for j,e in enumerate(ER):
            for b in suppR[e]:m.AddImplication(V[i][j],dR[ownersR[b]])
        for j,k in eR:m.AddAtMostOne(V[i][j],V[i][k])
    cross=0
    for i,x in enumerate(activeH):
        for j,y in enumerate(activeV):
            for e in rL[y]:
                for f in rR[x]:
                    m.AddAtMostOne(H[i][e],V[j][f]);cross+=1
    m.Maximize(sum(sum(h) for h in H)+sum(sum(v) for v in V))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=limit
    solver.parameters.num_search_workers=workers
    solver.parameters.random_seed=20261106
    start=time.monotonic();status=solver.Solve(m)
    report={"method":"constructive-two-independent-auxiliary-full-10D-fibers",
            "status":solver.StatusName(status),"left_removed":l,"right_removed":r,
            "left_endpoints":len(EL),"right_endpoints":len(ER),
            "active_row_auxiliary":len(activeH),"active_column_auxiliary":len(activeV),
            "cross_clauses":cross,"elapsed_seconds":round(time.monotonic()-start,2)}
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        RL=[ownL[i] for i in range(len(ownL)) if solver.BooleanValue(dL[i])]
        RR=[ownR[i] for i in range(len(ownR)) if solver.BooleanValue(dR[i])]
        BL=set(IL)-set(RL);BR=set(IR)-set(RR)
        Hd={x:RL for x in XH};Vd={y:RR for y in XV}
        for i,x in enumerate(activeH):
            Hd[x]=[e for j,e in enumerate(EL) if solver.BooleanValue(H[i][j])]
        for i,y in enumerate(activeV):
            Vd[y]=[e for j,e in enumerate(ER) if solver.BooleanValue(V[i][j])]
        assert all(legal(Hd[x]) for x in XH) and all(legal(Vd[y]) for y in XV)
        assert all(not clash(e,b) for row in Hd.values() for e in row for b in BL)
        assert all(not clash(f,b) for col in Vd.values() for f in col for b in BR)
        assert all(not(any(clash(e,y) for e in Hd[x]) and
                       any(clash(x,f) for f in Vd[y])) for x in XH for y in XV)
        points={(a,b) for a in BL for b in BR}
        for x in XH:points.update((e,x) for e in Hd[x])
        for y in XV:points.update((y,f) for f in Vd[y])
        score=(367-l)*(367-r)+sum(map(len,Hd.values()))+sum(map(len,Vd.values()))
        assert len(points)==score
        report.update({"score":score,"improvement":score-134753,
                       "selected_left_owners":RL,"selected_right_owners":RR,
                       "max_row_fiber":max(map(len,Hd.values())),
                       "max_col_fiber":max(map(len,Vd.values())),
                       "objective_fibers":int(solver.ObjectiveValue()),
                       "best_objective_bound":solver.BestObjectiveBound()})
        words=sorted("".join(str(d) for d in DIG[a]+DIG[b]) for a,b in points)
        (out/"best_certificate.json").write_text(
            json.dumps({"points":words},separators=(",",":"))+"\n")
        if score>=134754:
            (out/"certificate.json").write_bytes((out/"best_certificate.json").read_bytes())
            report["candidate"]=True
        else:report["candidate"]=False
    else:report["candidate"]=False
    return report

def main():
    a=argparse.ArgumentParser()
    a.add_argument("parents",type=Path);a.add_argument("aux_dir",type=Path);a.add_argument("out",type=Path)
    for arg in ("left","right","row","column"):
        a.add_argument("--"+arg,choices=("neutral14a","neutral14b","port12a","port12b"),required=True)
    a.add_argument("--l",type=int,required=True);a.add_argument("--r",type=int,required=True)
    a.add_argument("--seconds",type=int,default=200);a.add_argument("--workers",type=int,default=4)
    a.add_argument("--row-rank",type=int,default=0);a.add_argument("--column-rank",type=int,default=0)
    args=a.parse_args()
    pool=parent_codes(args.parents)
    for n in ("port12a","port12b"):pool[n]=list(map(int,(args.aux_dir/(n+".ids")).read_text().split()))
    IL=pool[args.left];IR=pool[args.right];EL=private_universe(IL)[1];ER=private_universe(IR)[1]
    XH,shH,actH=choose_shift(pool[args.row],ER,args.row_rank)
    XV,shV,actV=choose_shift(pool[args.column],EL,args.column_rank)
    args.out.mkdir(parents=True,exist_ok=True)
    report=solve(IL,IR,XH,XV,args.l,args.r,args.seconds,args.workers,args.out)
    report.update({"left_parent":args.left,"right_parent":args.right,
                   "row_auxiliary":args.row,"column_auxiliary":args.column,
                   "row_shift":list(shH),"column_shift":list(shV),
                   "row_phase_conflicts":actH,"column_phase_conflicts":actV})
    (args.out/"status.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("FINAL",json.dumps(report,sort_keys=True),flush=True)
if __name__=="__main__":main()
