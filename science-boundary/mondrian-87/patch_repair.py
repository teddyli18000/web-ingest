"""Topology-changing exact repair around all record-window violations.

Given target [A,A+17], mandatory release every incumbent rectangle outside the
window, grow a connected neighborhood in the rectangle-contact graph, and
re-construct all released tiles with simultaneous shape/placement choices.
Nothing enforces the original T-junction topology.
"""
import argparse
import random
import time
from pathlib import Path
from cpsat_search import RECORD, solve

def adjacent(p,q):
    x,y,w,h=p;xx,yy,ww,hh=q
    return (((x+w==xx or xx+ww==x) and max(y,yy)<min(y+h,yy+hh))
            or ((y+h==yy or yy+hh==y) and max(x,xx)<min(x+w,xx+ww)))

ADJ=[{j for j in range(len(RECORD)) if j!=i and adjacent(RECORD[i],RECORD[j])}
     for i in range(len(RECORD))]

def shortest_connect(selected, seed):
    rng=random.Random(seed)
    connected={min(selected)}
    while not selected.issubset(connected):
        options=[j for j in range(len(RECORD)) if j not in connected]
        goals=selected-connected
        def dist_to_goal(j):
            seen={j}
            fringe=[j]
            d=0
            while fringe:
                if any(x in goals for x in fringe):return d
                fringe=[y for x in fringe for y in ADJ[x] if y not in seen]
                seen.update(fringe);d+=1
            return 100
        # Randomized shortest expansion guarantees a connected released region.
        choices=[j for j in options if any(v in connected for v in ADJ[j])]
        costs=[dist_to_goal(j) for j in choices]
        best=min(costs)
        connected.add(rng.choice([j for j,d in zip(choices,costs) if d==best]))
    return connected

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--window',type=int,default=390)
    ap.add_argument('--seed',type=int,default=1)
    ap.add_argument('--seconds',type=int,default=660)
    ap.add_argument('--outdir',type=Path,default=Path('found'))
    args=ap.parse_args()
    mandatory={i for i,(x,y,w,h) in enumerate(RECORD) if not args.window<=w*h<=args.window+17}
    assert mandatory
    rng=random.Random(args.seed)
    start=time.monotonic()
    trial=0
    while time.monotonic()-start<args.seconds:
        trial+=1
        removed=shortest_connect(mandatory,rng.randrange(10**9))
        desired=rng.choice([max(len(removed),n) for n in (4,5,6,7,8,9,10,11,12,13,14)])
        while len(removed)<desired:
            fringe={j for i in removed for j in ADJ[i]}-removed
            removed.add(rng.choice(sorted(fringe)))
        fixed=[r for i,r in enumerate(RECORD) if i not in removed]
        remain=args.seconds-(time.monotonic()-start)
        budget=min(remain,rng.choice([5,10,20,35,55]))
        print(f"PATCH trial={trial} A={args.window} mandatory={sorted(mandatory)} "
              f"released={sorted(removed)} k_new={len(removed)} budget={budget:.1f}",flush=True)
        if solve(args.window,fixed,args.seed+trial,budget,19,args.outdir):
            print(f"PATCH SUCCESS defect<=17 released={sorted(removed)}",flush=True)
            return

if __name__=='__main__':
    main()
