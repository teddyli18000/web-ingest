"""Constructive CP-SAT search for a defect <=17 Mondrian-87 dissection.

Uses distinct shape variables, optional intervals and NoOverlap2D. The exact
area equality forces full board coverage. No preselected separator topology.
The LNS mode freezes random subsets of PR #62 to reoptimize remaining pieces.
"""
import argparse
import json
import random
import time
from pathlib import Path
from ortools.sat.python import cp_model

N = 87
RECORD = [
    [8, 0, 66, 6], [29, 6, 5, 81], [17, 6, 12, 33],
    [17, 39, 12, 34], [0, 73, 29, 14], [8, 6, 9, 44],
    [0, 50, 17, 23], [0, 0, 8, 50], [34, 6, 40, 10],
    [34, 16, 7, 56], [34, 72, 26, 15], [41, 16, 24, 17],
    [41, 33, 10, 39], [51, 33, 14, 28], [51, 61, 36, 11],
    [60, 72, 27, 15], [65, 16, 9, 45],
    [74, 0, 13, 30], [74, 30, 13, 31],
]

def verify(rects):
    cover = bytearray(N * N)
    shapes = set()
    areas = []
    for x, y, w, h in rects:
        assert 0 <= x < x+w <= N and 0 <= y < y+h <= N
        shape = tuple(sorted((w, h)))
        assert shape not in shapes
        shapes.add(shape)
        areas.append(w*h)
        for yy in range(y, y+h):
            idx = yy*N+x
            assert not any(cover[idx:idx+w])
            cover[idx:idx+w] = bytes([1])*w
    assert all(cover) and sum(areas) == N*N
    return max(areas) - min(areas)

assert verify(RECORD) == 18

def solve(window, fixed, seed, seconds, k, outdir):
    forbidden = {tuple(sorted((w,h))) for x,y,w,h in fixed}
    shapes = [(w,h) for w in range(1,N+1) for h in range(w,N+1)
              if window <= w*h <= window+17 and (w,h) not in forbidden]
    model = cp_model.CpModel()
    x_intervals, y_intervals, variables, areas = [], [], [], []
    for idx,(x,y,w,h) in enumerate(fixed):
        x_intervals.append(model.NewFixedSizeIntervalVar(x,w,f"fx{idx}"))
        y_intervals.append(model.NewFixedSizeIntervalVar(y,h,f"fy{idx}"))
    for idx,(w,h) in enumerate(shapes):
        orientation_bits = []
        for wi,hi in ([(w,h)] if w==h else [(w,h),(h,w)]):
            p = model.NewBoolVar(f"p{idx}_{wi}_{hi}")
            x = model.NewIntVar(0,N-wi,f"x{idx}_{wi}_{hi}")
            y = model.NewIntVar(0,N-hi,f"y{idx}_{wi}_{hi}")
            x_intervals.append(model.NewOptionalFixedSizeIntervalVar(x,wi,p,f"xi{idx}_{wi}_{hi}"))
            y_intervals.append(model.NewOptionalFixedSizeIntervalVar(y,hi,p,f"yi{idx}_{wi}_{hi}"))
            model.Add(x==0).OnlyEnforceIf(p.Not())
            model.Add(y==0).OnlyEnforceIf(p.Not())
            variables.append((p,x,y,wi,hi))
            areas.append(w*h)
            orientation_bits.append(p)
        model.Add(sum(orientation_bits)<=1)
    model.AddNoOverlap2D(x_intervals,y_intervals)
    model.Add(sum(p*a for (p,_,_,_,_),a in zip(variables,areas)) ==
              N*N - sum(w*h for x,y,w,h in fixed))
    model.Add(sum(p for p,x,y,w,h in variables) == k-len(fixed))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = 4
    solver.parameters.random_seed = seed
    solver.parameters.symmetry_level = 2
    status = solver.Solve(model)
    print(json.dumps({"seed":seed,"window":window,"fixed":len(fixed),"k":k,
          "status":solver.StatusName(status),"time":solver.WallTime(),
          "branches":solver.NumBranches(),"conflicts":solver.NumConflicts()}),flush=True)
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        rects = fixed + [[solver.Value(x),solver.Value(y),w,h]
                         for p,x,y,w,h in variables if solver.BooleanValue(p)]
        defect = verify(rects)
        assert defect <= 17
        outdir.mkdir(parents=True,exist_ok=True)
        path = outdir/f"certificate_{seed}_{window}_{k}.json"
        path.write_text(json.dumps({"rectangles":rects},separators=(",",":")))
        print(f"BREAKTHROUGH defect={defect} file={path} rects={rects}",flush=True)
        return True
    return False

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed",type=int,default=1)
    ap.add_argument("--seconds",type=int,default=600)
    ap.add_argument("--window",type=int,default=390)
    ap.add_argument("--k",type=int,default=19)
    ap.add_argument("--mode",choices=["lns","full"],default="lns")
    ap.add_argument("--outdir",type=Path,default=Path("science-boundary/mondrian-87/results"))
    args=ap.parse_args()
    rng=random.Random(args.seed)
    if args.mode=="full":
        solve(args.window,[],args.seed,args.seconds,args.k,args.outdir)
        return
    eligible=[r for r in RECORD if args.window<=r[2]*r[3]<=args.window+17]
    start=time.monotonic()
    trial=0
    while time.monotonic()-start < args.seconds:
        trial+=1
        keep=min(rng.choice([0,3,5,7,9,11,13,15]),len(eligible))
        fixed=rng.sample(eligible,keep)
        remaining=args.seconds-(time.monotonic()-start)
        budget=min(remaining,rng.choice([20,40,60,90]))
        print(f"LNS trial={trial} window={args.window} keep={keep} seconds={budget:.1f}",flush=True)
        if solve(args.window,fixed,args.seed+trial,budget,args.k,args.outdir):
            break

if __name__=="__main__":
    main()
