#!/usr/bin/env python3
"""Exact Hamming-radius search for a 367-set avoiding the best BPZ obstruction.

The published auxiliary X has 367 points and exactly one lies in the best t=9
obstruction D.  For radius k, require a new independent 367-set X' disjoint
from D that retains at least 367-k published X points.  Thus k counts total
removed published points, including the mandatory bad point.  The C7^5
independence constraints use the exact 7^5 binary-cube clique cover.
"""
import argparse,json,sys
from itertools import combinations,product
from pathlib import Path
from pysat.solvers import Minicard
Q=7;D=5;U=Q**D;N=367;T=9;TARGET=N*N+T*T
I_SWAPS=((6110,3716),(13677,14027))
PAIRS=((1553,15910),(3716,6110),(8888,6494),(10708,13158),(13065,13358),(14027,13677),(14329,12277),(15075,14733),(15384,15685))
ORIENT=(0,0,1,1,0,1,1,0,0)

def conflict(a,b,d):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))
def independent(v,d):
    a=list(v);return all(not conflict(x,y,d) for x,y in combinations(a,2))
def enc(w):
    v=0;m=1
    for x in w:v+=x*m;m*=Q
    return v
def cube(a):
    for b in product((0,1),repeat=D):yield enc(tuple((a[j]+b[j])%Q for j in range(D)))
def build(I,X,pairs,PH,PV,ring):
    R={a for a,q in pairs};B=set(I)-R;NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV));X=set(X)
    if X&NH&NV:raise RuntimeError('double hit')
    X0=X-(NH|NV);XH=X&NH;XV=X&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    if len(P)!=TARGET:raise RuntimeError(f'score {len(P)}')
    return sorted(''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P),(len(X0),len(XH),len(XV))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--radius',type=int,required=True);args=ap.parse_args();k=args.radius
    if not 1<=k<=N:raise SystemExit('bad radius')
    root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I=set(map(int,raw['I0']));X0=set(map(int,raw['X']));ring=Ring(D);digits=tuple(ring.decode(v) for v in range(U))
    for a,b in I_SWAPS:I.remove(a);I.add(b)
    pairs=list(PAIRS);PH=[q if s else a for (a,q),s in zip(pairs,ORIENT)];PV=[a if s else q for (a,q),s in zip(pairs,ORIENT)]
    obstruction=ring.nbhd(set(PH))&ring.nbhd(set(PV));hits=sorted(X0&obstruction)
    if len(obstruction)!=1098 or hits!=[10665]:raise RuntimeError(f'witness drift {len(obstruction)} {hits}')
    allowed=[v for v in range(U) if v not in obstruction];aset=set(allowed);var={v:i+1 for i,v in enumerate(allowed)};good=sorted(X0-obstruction)
    s=Minicard();nc=0
    for a in range(U):
        lits=[var[v] for v in cube(digits[a]) if v in aset]
        if len(lits)>=2:s.add_atmost(lits,1);nc+=1
    s.add_atmost([-var[v] for v in allowed],len(allowed)-N)
    keep=N-k
    if keep>0:s.add_atmost([-var[v] for v in good],len(good)-keep)
    setup={'radius':k,'must_keep_published':keep,'published_good_points':len(good),'obstruction_size':len(obstruction),'allowed_vertices':len(allowed),'cube_constraints':nc,'target_auxiliary_size':N,'target_10d_score':TARGET};print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
    sat=s.solve();model=s.get_model() if sat else None;s.delete();args.status.parent.mkdir(parents=True,exist_ok=True)
    if not sat:
        st={'candidate':False,'sat':False,'method':'bpz-t9-obstruction-MIS-radius-exact','score':134753,'setup':setup};args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('UNSAT',json.dumps(st,sort_keys=True),flush=True);return
    pos={z for z in model if z>0};X=[v for v in allowed if var[v] in pos][:N]
    if len(X)!=N or not independent(X,digits) or set(X)&obstruction:raise RuntimeError('model replay')
    overlap=len(set(X)&X0);removed=N-overlap
    if removed>k:raise RuntimeError(f'radius replay {removed}>{k}')
    pts,xp=build(I,X,pairs,PH,PV,ring);st={'candidate':True,'sat':True,'method':'bpz-t9-obstruction-MIS-radius-exact','score':len(pts),'removed_from_published_X':removed,'added_to_published_X':len(set(X)-X0),'auxiliary_points':X,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]},'setup':setup};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps({x:y for x,y in st.items() if x!='auxiliary_points'},sort_keys=True),flush=True)
if __name__=='__main__':main()
