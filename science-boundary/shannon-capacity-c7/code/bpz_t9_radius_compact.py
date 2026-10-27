#!/usr/bin/env python3
"""Compact exact radius-k repair SAT for the best BPZ t=9 obstruction.

The published auxiliary X has one mandatory bad point b=10665 in the obstruction
D=N(PH) cap N(PV).  A radius-k repair removes b plus at most k-1 further X
owners and adds k new vertices outside X and D.

For every possible addition y, compute its conflict support against the original
published X.  After deleting b, y is admissible iff every remaining support
owner is among the optional deleted owners.  The SAT model therefore needs only:

  * one variable per candidate addition whose non-b support size <= k-1;
  * one variable per optional X owner;
  * implications addition -> each required deleted owner;
  * at most k-1 optional owners;
  * at least k additions;
  * exact C7^5 independence among additions via the binary-cube clique cover.

This is equivalent to a repair using at most k deletions.  If fewer than k-1
optional owners are actually needed, arbitrary additional compatible old X
points can be deleted to balance cardinality.  SAT is replayed explicitly and
materialized as Gao's 134770-point C7^10 construction.
"""
import argparse,json,sys
from itertools import combinations,product
from pathlib import Path
from pysat.formula import IDPool
from pysat.solvers import Minicard
Q=7;D=5;U=Q**D;N=367;T=9;TARGET=N*N+T*T;BAD=10665
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
    if X&NH&NV:raise RuntimeError('repaired X still hits obstruction')
    X0=X-(NH|NV);XH=X&NH;XV=X&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    if len(P)!=TARGET:raise RuntimeError(f'Gao score drift {len(P)}')
    return sorted(''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P),(len(X0),len(XH),len(XV))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--radius',type=int,required=True);args=ap.parse_args();k=args.radius
    if not 1<=k<=30:raise SystemExit('radius out of supported range')
    root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I=set(map(int,raw['I0']));X=set(map(int,raw['X']));ring=Ring(D);digits=tuple(ring.decode(v) for v in range(U))
    for a,b in I_SWAPS:I.remove(a);I.add(b)
    pairs=list(PAIRS);PH=[q if s else a for (a,q),s in zip(pairs,ORIENT)];PV=[a if s else q for (a,q),s in zip(pairs,ORIENT)]
    obstruction=ring.nbhd(set(PH))&ring.nbhd(set(PV));hits=sorted(X&obstruction)
    if len(obstruction)!=1098 or hits!=[BAD]:raise RuntimeError(f'witness drift {len(obstruction)} {hits}')
    if len(X)!=N or not independent(X,digits):raise RuntimeError('published X drift')
    xlist=sorted(X);xset=set(X);owners=[x for x in xlist if x!=BAD];owner_index={x:i for i,x in enumerate(owners)}
    supports={};hist={}
    for y in range(U):
        if y in xset or y in obstruction:continue
        s=tuple(sorted(x for x in ring.NB[y] if x in xset and x!=BAD))
        bc=len(s);hist[bc]=hist.get(bc,0)+1
        if bc<=k-1:supports[y]=s
    candidates=sorted(supports);cset=set(candidates);pool=IDPool();Y={y:pool.id(('y',y)) for y in candidates};R={x:pool.id(('r',x)) for x in owners};solver=Minicard();imp=0
    for y,s in supports.items():
        for x in s:solver.add_clause([-Y[y],R[x]]);imp+=1
    solver.add_atmost(list(R.values()),k-1)
    solver.add_atmost([-Y[y] for y in candidates],len(candidates)-k)
    cubes=0;cube_lits=0
    for a in range(U):
        lits=[Y[v] for v in cube(digits[a]) if v in cset]
        if len(lits)>=2:solver.add_atmost(lits,1);cubes+=1;cube_lits+=len(lits)
    setup={'radius':k,'mandatory_bad_X':BAD,'obstruction_size':len(obstruction),'candidate_additions':len(candidates),'support_size_histogram':{str(a):b for a,b in sorted(hist.items())},'optional_owner_variables':len(owners),'support_implications':imp,'cube_constraints':cubes,'cube_literal_total':cube_lits,'target_additions':k,'target_10d_score':TARGET};print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
    sat=solver.solve();model=solver.get_model() if sat else None;solver.delete();args.status.parent.mkdir(parents=True,exist_ok=True)
    if not sat:
        st={'candidate':False,'sat':False,'method':'bpz-t9-compact-exact-radius-repair','score':134753,'setup':setup};args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('UNSAT',json.dumps(st,sort_keys=True),flush=True);return
    pos={z for z in model if z>0};adds=[y for y in candidates if Y[y] in pos]
    if len(adds)<k:raise RuntimeError(f'SAT selected only {len(adds)} additions')
    adds=adds[:k]
    if not independent(adds,digits):raise RuntimeError('SAT additions conflict')
    needed=set()
    for y in adds:needed.update(supports[y])
    if len(needed)>k-1:raise RuntimeError('owner budget replay')
    removals={BAD}|needed
    # Balance to exactly k removals using old X points that are not required as
    # blockers; any such point is compatible with all selected additions by the
    # definition of support.
    for x in owners:
        if len(removals)>=k:break
        if x not in removals:removals.add(x)
    if len(removals)!=k:raise RuntimeError('could not balance removals')
    X2=(X-removals)|set(adds)
    if len(X2)!=N or not independent(X2,digits) or X2&obstruction:raise RuntimeError('repair replay failed')
    pts,xp=build(I,X2,pairs,PH,PV,ring);st={'candidate':True,'sat':True,'method':'bpz-t9-compact-exact-radius-repair','score':len(pts),'radius':k,'remove_X':sorted(removals),'add_X':adds,'required_owner_removals':sorted(needed),'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]},'setup':setup};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(st,sort_keys=True),flush=True)
if __name__=='__main__':main()
