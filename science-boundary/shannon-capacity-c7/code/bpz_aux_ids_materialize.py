#!/usr/bin/env python3
"""Replay a 367-point auxiliary set and materialize the fixed best BPZ t=9 witness."""
import argparse,json,sys
from itertools import combinations
from pathlib import Path
Q=7;D=5;N=367;TARGET=N*N+81
I_SWAPS=((6110,3716),(13677,14027))
PAIRS=((1553,15910),(3716,6110),(8888,6494),(10708,13158),(13065,13358),(14027,13677),(14329,12277),(15075,14733),(15384,15685))
ORIENT=(0,0,1,1,0,1,1,0,0)

def conflict(a,b,d):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))
def independent(v,d):
    a=list(v);return all(not conflict(x,y,d) for x,y in combinations(a,2))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('ids',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args();root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I=set(map(int,raw['I0']));ring=Ring(D);digits=tuple(ring.decode(v) for v in range(Q**D))
    for a,b in I_SWAPS:I.remove(a);I.add(b)
    X=[int(x) for x in args.ids.read_text().split()];pairs=list(PAIRS);PH=[q if s else a for (a,q),s in zip(pairs,ORIENT)];PV=[a if s else q for (a,q),s in zip(pairs,ORIENT)]
    if len(X)!=N or len(set(X))!=N or any(not 0<=x<Q**D for x in X):raise RuntimeError('bad auxiliary size/ids')
    if not independent(X,digits):raise RuntimeError('auxiliary set is not independent')
    if len(I)!=N or not independent(I,digits) or not independent(PH,digits) or not independent(PV,digits):raise RuntimeError('fixed witness drift')
    obstruction=ring.nbhd(set(PH))&ring.nbhd(set(PV))
    if len(obstruction)!=1098:raise RuntimeError(f'obstruction drift {len(obstruction)}')
    if set(X)&obstruction:raise RuntimeError(f'auxiliary hits obstruction: {sorted(set(X)&obstruction)}')
    R={a for a,q in pairs};B=I-R;NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV));Xs=set(X);X0=Xs-(NH|NV);XH=Xs&NH;XV=Xs&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    if len(P)!=TARGET:raise RuntimeError(f'Gao product score drift {len(P)}')
    pts=sorted(''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P)
    st={'candidate':True,'score':len(pts),'auxiliary_size':len(X),'X_partition':{'X0':len(X0),'XH':len(XH),'XV':len(XV)},'PH':PH,'PV':PV,'private_pairs':[list(z) for z in pairs],'orientation':list(ORIENT)};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print(json.dumps(st,sort_keys=True))
if __name__=='__main__':main()
