#!/usr/bin/env python3
"""Exhaust all 2^9 transversal orientations in the two best BPZ one-swap states.

The one-swap sweep found exactly two neighbours with nine distinct private
pairs but no Definition-2 orientation.  This diagnostic separates intrinsic
same-side transversal conflicts from the X double-neighbour obstruction and
records the best orientations and offending X vertices.
"""
import argparse,json,sys
from itertools import combinations,product
from pathlib import Path

Q=7;D=5;U=Q**D;N=367
SEEDS=((6110,3716),(13677,14027))

def conflict(a,b,d):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))
def priv(I,ring):
    out=[]
    for q in range(U):
        if q in I:continue
        h=[z for z in ring.NB[q] if z in I]
        if len(h)==1:out.append((h[0],q))
    return sorted(out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args();root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X=set(map(int,raw['X']));ring=Ring(D);digits=tuple(ring.decode(v) for v in range(U));rows=[]
    for rem,add in SEEDS:
        I=set(I0);I.remove(rem);I.add(add);pairs=priv(I,ring)
        if len(pairs)!=9 or len({r for r,q in pairs})!=9:raise RuntimeError(f'seed {(rem,add)} private drift {pairs}')
        best=[];hist={};zero_side=[]
        for bits in product((0,1),repeat=9):
            PH=[];PV=[]
            for (r,q),s in zip(pairs,bits):
                PH.append(q if s else r);PV.append(r if s else q)
            hh=sum(conflict(a,b,digits) for a,b in combinations(PH,2));vv=sum(conflict(a,b,digits) for a,b in combinations(PV,2))
            DH=[]
            if hh==0 and vv==0:
                NH=set().union(*(ring.NB[h] for h in PH));NV=set().union(*(ring.NB[v] for v in PV));DH=sorted(X&NH&NV);zero_side.append((len(DH),bits,DH,PH,PV))
            key=(hh+vv,len(DH) if hh+vv==0 else -1);hist[str(key)]=hist.get(str(key),0)+1
        zero_side.sort(key=lambda z:(z[0],z[1]));
        if zero_side:
            md=zero_side[0][0]
            for dh,bits,bad,PH,PV in zero_side:
                if dh!=md or len(best)>=20:break
                best.append({'orientation':list(bits),'double_hit_count':dh,'double_hit_X':bad,'PH':PH,'PV':PV})
        row={'swap':{'remove':rem,'add':add},'private_pairs':[list(z) for z in pairs],'orientations':512,'same_side_valid_orientations':len(zero_side),'min_X_double_hits':zero_side[0][0] if zero_side else None,'best':best,'histogram':hist};rows.append(row);print(json.dumps(row,sort_keys=True),flush=True)
    out={'method':'bpz-t9-exhaustive-orientation-diagnostic','rows':rows};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
