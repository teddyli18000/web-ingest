#!/usr/bin/env python3
"""Exact 3-for-3 repair of the published BPZ X for the best t=9 obstruction.

The best exact joint-component witness has independent P^H/P^V and the
published X intersects D=N(P^H) cap N(P^V) in exactly one vertex.  One- and
two-point repairs are already closed.  Here the unique bad X vertex is forced
removed together with any other two X vertices; all outside vertices avoiding D
whose conflict support against the original X is contained in those three
owners are eligible additions.  Every independent triple of additions is
checked.  This exactly exhausts all 3-for-3 repairs of that witness.
"""
import argparse,json,sys
from itertools import combinations
from pathlib import Path

Q=7;D=5;U=Q**D;N=367;T=9;TARGET=N*N+T*T
I_SWAPS=((6110,3716),(13677,14027))
PAIRS=((1553,15910),(3716,6110),(8888,6494),(10708,13158),(13065,13358),(14027,13677),(14329,12277),(15075,14733),(15384,15685))
ORIENT=(0,0,1,1,0,1,1,0,0)

def conflict(a,b,d):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))
def independent(v,d):
    a=list(v);return all(not conflict(x,y,d) for x,y in combinations(a,2))
def build(I,X,pairs,PH,PV,ring):
    R={a for a,q in pairs};B=set(I)-R;NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV));X=set(X)
    if X&NH&NV:raise RuntimeError('repair still hits obstruction')
    X0=X-(NH|NV);XH=X&NH;XV=X&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    if len(P)!=TARGET:raise RuntimeError(f'score drift {len(P)}')
    return sorted(''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P),(len(X0),len(XH),len(XV))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args();root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I=set(map(int,raw['I0']));X=set(map(int,raw['X']));ring=Ring(D);digits=tuple(ring.decode(v) for v in range(U))
    for a,b in I_SWAPS:I.remove(a);I.add(b)
    if len(I)!=N or not independent(I,digits) or len(X)!=N or not independent(X,digits):raise RuntimeError('base/witness drift')
    pairs=list(PAIRS);PH=[q if s else a for (a,q),s in zip(pairs,ORIENT)];PV=[a if s else q for (a,q),s in zip(pairs,ORIENT)]
    if not independent(PH,digits) or not independent(PV,digits):raise RuntimeError('witness transversals drift')
    Dset=ring.nbhd(set(PH))&ring.nbhd(set(PV));bad=sorted(X&Dset)
    if len(bad)!=1:raise RuntimeError(f'expected one bad X, got {bad}')
    badx=bad[0];xlist=sorted(X);xindex={x:i for i,x in enumerate(xlist)};badidx=xindex[badx]
    groups={};support_hist={1:0,2:0,3:0};zero=[]
    for y in range(U):
        if y in X or y in Dset:continue
        hits=tuple(sorted(xindex[x] for x in ring.NB[y] if x in X));bc=len(hits)
        if bc==0:zero.append(y)
        elif bc<=3:
            groups.setdefault(hits,[]).append(y);support_hist[bc]+=1
    if zero:raise RuntimeError(f'found {len(zero)} zero-support additions; X would not be maximum')
    tested_owner_triples=0;eligible_pools=0;candidate_triples=0;winner=None;max_pool=0
    others=[i for i in range(N) if i!=badidx]
    for ia,a in enumerate(others):
        for b in others[ia+1:]:
            R=tuple(sorted((badidx,a,b)));pool=[]
            for k in (1,2,3):
                for ss in combinations(R,k):pool.extend(groups.get(tuple(ss),()))
            pool=sorted(set(pool));max_pool=max(max_pool,len(pool));tested_owner_triples+=1
            if len(pool)<3:continue
            eligible_pools+=1
            for i,x in enumerate(pool):
                for j in range(i+1,len(pool)):
                    y=pool[j]
                    if conflict(x,y,digits):continue
                    for z in pool[j+1:]:
                        candidate_triples+=1
                        if conflict(x,z,digits) or conflict(y,z,digits):continue
                        winner=(R,(x,y,z));break
                    if winner:break
                if winner:break
            if winner:break
        if winner:break
    status={'method':'bpz-t9-exact-X-three-for-three-repair','candidate':winner is not None,'bad_X':badx,'obstruction_size':len(Dset),'support1_candidates':support_hist[1],'support2_candidates':support_hist[2],'support3_candidates':support_hist[3],'owner_triples_tested':tested_owner_triples,'eligible_pools':eligible_pools,'candidate_add_triples':candidate_triples,'max_pool':max_pool};args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        status['score']=134753;args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True);return
    Ridx,adds=winner;rem={xlist[i] for i in Ridx};X2=(X-rem)|set(adds)
    if len(X2)!=N or not independent(X2,digits) or X2&Dset:raise RuntimeError('repair replay failed')
    pts,xp=build(I,X2,pairs,PH,PV,ring);status.update({'score':len(pts),'remove_X':sorted(rem),'add_X':list(adds),'PH':PH,'PV':PV,'private_pairs':[list(z) for z in pairs],'orientation':list(ORIENT),'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}});args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
