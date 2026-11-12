"""Constructive 85 -> 87 frame surgery.

The 85x85 verified 21-piece dissection has defect 16, areas 336..352.
The 2-wide frame added in 87x87 has area 344, exactly the average
needed for one extra nearly equal-area tile. Preserve interior tiles,
release the boundary tiles and a connected neighborhood, and retile all
remaining space jointly as 22 noncongruent tiles of area 335..352 or
336..353, using optional 2D intervals from cpsat_search.py.
"""
import argparse
import random
import time
from pathlib import Path
from cpsat_search import solve

SOURCE=[
    [0,0,5,69],[0,69,35,10],[0,79,58,6],[5,0,17,20],
    [5,20,7,49],[12,20,10,34],[12,54,23,15],[22,0,32,11],
    [22,11,57,6],[22,17,43,8],[22,25,22,16],[22,41,27,13],
    [35,54,14,25],[44,25,21,16],[49,41,9,38],[54,0,31,11],
    [58,41,8,44],[65,17,14,24],[66,41,13,26],
    [66,67,19,18],[79,11,6,56],
]
def touches(a,b):
    x,y,w,h=a;xx,yy,ww,hh=b
    return ((x+w==xx or xx+ww==x) and max(y,yy)<min(y+h,yy+hh)) or (
            (y+h==yy or yy+hh==y) and max(x,xx)<min(x+w,xx+ww))

BORDER={i for i,(x,y,w,h) in enumerate(SOURCE) if x+w==85 or y+h==85}
assert len(BORDER)==5
assert min(w*h for x,y,w,h in SOURCE)==336
assert max(w*h for x,y,w,h in SOURCE)==352
assert sum(w*h for x,y,w,h in SOURCE)==85*85

def release_more(seed, extra):
    rng=random.Random(seed)
    removed=set(BORDER)
    for i in range(extra):
        frontier=[j for j in range(len(SOURCE)) if j not in removed and
                 any(touches(SOURCE[j],SOURCE[k]) for k in removed)]
        j=rng.choice(frontier)
        removed.add(j)
    return [r for i,r in enumerate(SOURCE) if i not in removed]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed",type=int,default=1)
    ap.add_argument("--seconds",type=int,default=600)
    ap.add_argument("--window",type=int,default=335)
    ap.add_argument("--outdir",type=Path,default=Path("found"))
    args=ap.parse_args()
    rng=random.Random(args.seed)
    start=time.monotonic()
    i=0
    while time.monotonic()-start<args.seconds:
        i+=1
        extra=0 if i==1 else rng.choice([0,1,2,3,4,5,6,7,9,11,13])
        fixed=release_more(rng.randrange(10**9),extra)
        budget=min(args.seconds-(time.monotonic()-start),rng.choice([4,10,20,35,50]))
        print(f"FRAME trial={i} window={args.window} old_fixed={len(fixed)} "
              f"new_pieces={22-len(fixed)} seconds={budget:.1f}",flush=True)
        if solve(args.window,fixed,args.seed+i,budget,22,args.outdir):
            print(f"FRAME SUCCESS source85=16 target87<=17",flush=True)
            return
if __name__=="__main__":
    main()
