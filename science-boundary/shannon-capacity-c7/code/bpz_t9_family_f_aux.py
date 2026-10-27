#!/usr/bin/env python3
"""Test all 36 public Family-F C7^5 maxima as auxiliary sets for BPZ t=9.

The 36 states are taken from molind/c7-five at a pinned commit.  They are
independent 367-sets outside the BPZ I/X local components.  Every distinct
same-side-valid BPZ t=9 obstruction mask from the complete 243-state I component
is tested exactly.  Any Family-F state disjoint from one mask yields Gao's
134770-point C7^10 construction.
"""
import argparse,json,sys
from itertools import combinations,product
from pathlib import Path
Q=7;D=5;U=Q**D;N=367;T=9;TARGET=N*N+T*T

def conflict(a,b,d):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))
def independent(v,d):
    a=list(v);return all(not conflict(x,y,d) for x,y in combinations(a,2))
def values(bits):
    while bits:
        z=bits&-bits;yield z.bit_length()-1;bits^=z
def private(bits,nb):
    out=[]
    for q in range(U):
        if (bits>>q)&1:continue
        h=nb[q]&bits
        if h.bit_count()==1:out.append((h.bit_length()-1,q))
    return sorted(out)
def component(start,nb):
    seen={start};front=[start];pm={}
    while front:
        nxt=[]
        for b in front:
            pp=private(b,nb);pm[b]=pp
            for a,q in pp:
                c=b^(1<<a)^(1<<q)
                if c not in seen:seen.add(c);nxt.append(c)
        front=nxt
    return seen,pm
def masks(I0,ring,d,nb):
    comp,pm=component(sum(1<<z for z in I0),nb)
    if len(comp)!=243:raise RuntimeError(f'I component drift {len(comp)}')
    out={};ss=0
    for ib in comp:
        pp=pm[ib]
        if len({a for a,q in pp})<T:continue
        for pairs in combinations(pp,T):
            if len({a for a,q in pairs})<T:continue
            for o in product((0,1),repeat=T):
                PH=[q if s else a for (a,q),s in zip(pairs,o)];PV=[a if s else q for (a,q),s in zip(pairs,o)]
                if not independent(PH,d) or not independent(PV,d):continue
                ss+=1;Dset=ring.nbhd(set(PH))&ring.nbhd(set(PV));m=sum(1<<z for z in Dset);out.setdefault(m,(ib,pairs,o,PH,PV))
    if ss!=640 or len(out)!=160:raise RuntimeError(f'obstruction drift {ss} {len(out)}')
    return out
def build(Ibits,Xbits,pairs,PH,PV,ring):
    I=set(values(Ibits));X=set(values(Xbits));R={a for a,q in pairs};B=I-R;NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV))
    if X&NH&NV:raise RuntimeError('winning F state hits D')
    X0=X-(NH|NV);XH=X&NH;XV=X&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    if len(P)!=TARGET:raise RuntimeError(f'score drift {len(P)}')
    return sorted(''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P),(len(X0),len(XH),len(XV))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('family_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args();sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));ring=Ring(D);d=tuple(ring.decode(v) for v in range(U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(U)];obs=masks(I0,ring,d,nb)
    fam=json.loads((args.family_root/'data'/'family-f.json').read_text());states=fam['states']
    if len(states)!=36:raise RuntimeError(f'Family F state count drift {len(states)}')
    checks=0;winner=None;best=None;hist={}
    for si,state in enumerate(states):
        S=set(map(int,state))
        if len(S)!=N or not independent(S,d):raise RuntimeError(f'Family F state {si} invalid under coordinate-reversal convention')
        bits=sum(1<<z for z in S);local=10**9;localw=None
        for dm,w in obs.items():
            checks+=1;bad=(bits&dm).bit_count()
            if bad<local:local=bad;localw=w
            if bad==0:winner=(si,bits,w);break
        hist[str(local)]=hist.get(str(local),0)+1
        rec={'state_index':si,'min_double_hits':local}
        if best is None or local<best['min_double_hits']:best=rec
        if winner:break
    status={'method':'bpz-t9-public-Family-F-auxiliary-scan','candidate':winner is not None,'family_states':len(states),'obstruction_masks':len(obs),'checks':checks,'best':best,'min_hit_histogram':hist,'family_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'};args.status.parent.mkdir(parents=True,exist_ok=True)
    if not winner:
        status['score']=134753;args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True);return
    si,Xbits,w=winner;Ibits,pairs,o,PH,PV=w;pts,xp=build(Ibits,Xbits,pairs,PH,PV,ring);status.update({'score':len(pts),'winning_family_state':si,'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}});args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
