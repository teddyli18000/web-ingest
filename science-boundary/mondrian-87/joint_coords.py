"""Joint integer optimization of ALL coordinate lines of a Mondrian tiling.

Unlike local edge perturbations and alternating MILPs, this enforces all
rectangle areas/shape uniqueness simultaneously and maintains exact coverage
by monotonically re-embedding an existing rectangulation.
"""
import argparse
import json
from pathlib import Path
from ortools.sat.python import cp_model
from cpsat_search import N, RECORD, verify

def solve(a, seed, secs, outdir):
    R=RECORD
    XX=sorted({x for x,y,w,h in R}|{x+w for x,y,w,h in R})
    YY=sorted({y for x,y,w,h in R}|{y+h for x,y,w,h in R})
    xidx={v:i for i,v in enumerate(XX)}
    yidx={v:i for i,v in enumerate(YY)}
    model=cp_model.CpModel()
    X=[model.NewIntVar(0,N,f"X_{i}") for i in range(len(XX))]
    Y=[model.NewIntVar(0,N,f"Y_{i}") for i in range(len(YY))]
    for v in (X,Y):
        model.Add(v[0]==0)
        model.Add(v[-1]==N)
        for i in range(len(v)-1):
            model.Add(v[i+1]>=v[i]+1)
    valid_wh=[(w,h) for w in range(1,N+1) for h in range(1,N+1)
              if a<=w*h<=a+17]
    valid_area=sorted({w*h for w,h in valid_wh})
    keys=[]
    widths=[]
    heights=[]
    areas=[]
    for i,(x,y,w,h) in enumerate(R):
        wi=model.NewIntVar(1,N,f"w{i}")
        hi=model.NewIntVar(1,N,f"h{i}")
        model.Add(wi==X[xidx[x+w]]-X[xidx[x]])
        model.Add(hi==Y[yidx[y+h]]-Y[yidx[y]])
        model.AddAllowedAssignments([wi,hi],valid_wh)
        small=model.NewIntVar(1,N,f"small{i}")
        large=model.NewIntVar(1,N,f"large{i}")
        model.AddMinEquality(small,[wi,hi])
        model.AddMaxEquality(large,[wi,hi])
        key=model.NewIntVar(1,N*(N+1),f"shape{i}")
        model.Add(key==small*(N+1)+large)
        keys.append(key)
        widths.append(wi)
        heights.append(hi)
        area=model.NewIntVar(a,a+17,f"area{i}")
        model.AddMultiplicationEquality(area,[wi,hi])
        areas.append(area)
        model.AddHint(X[xidx[x]],x)
        model.AddHint(Y[yidx[y]],y)
    model.AddAllDifferent(keys)
    model.Add(sum(areas)==N*N)
    s=cp_model.CpSolver()
    s.parameters.num_search_workers=4
    s.parameters.max_time_in_seconds=secs
    s.parameters.random_seed=seed
    status=s.Solve(model)
    print(json.dumps({"mode":"joint-coords","seed":seed,"A":a,
          "xlines":len(X),"ylines":len(Y),"status":s.StatusName(status),
          "branches":s.NumBranches(),"time":s.WallTime()}),flush=True)
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        rects=[]
        for x,y,w,h in R:
            xx=s.Value(X[xidx[x]]);yy=s.Value(Y[yidx[y]])
            rects.append([xx,yy,s.Value(X[xidx[x+w]])-xx,s.Value(Y[yidx[y+h]])-yy])
        D=verify(rects)
        assert D<=17
        outdir.mkdir(parents=True,exist_ok=True)
        path=outdir/f"certificate_joint_{a}_{seed}.json"
        path.write_text(json.dumps({"rectangles":rects},separators=(",",":")))
        print(f"BREAKTHROUGH defect={D} file={path} rects={rects}",flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--window",type=int,default=390)
    p.add_argument("--seed",type=int,default=1)
    p.add_argument("--seconds",type=int,default=660)
    p.add_argument("--outdir",type=Path,default=Path("found"))
    args=p.parse_args()
    solve(args.window,args.seed,args.seconds,args.outdir)

if __name__=="__main__":
    main()
