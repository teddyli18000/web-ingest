#!/usr/bin/env python3
"""Exhaust all 7^5 relative translations of the BPZ auxiliary X for t=9.

Definition 2 only requires X to be a 367-point independent set satisfying the
double-neighbour exclusion against P^H/P^V.  It does not require the published
relative placement of X and I.  Translation is an automorphism of C7^5, so all
16807 translates of the published X remain independent 367-sets.

We generate every same-side-valid t=9 obstruction mask from the complete
243-state private-swap component of I, deduplicate the 640 orientations to their
obstruction masks, and test every relative translation of X exactly.  A zero
intersection immediately materializes Gao's 134770-point C7^10 construction.
"""

import argparse,json,sys
from itertools import combinations,product
from pathlib import Path

Q=7;D=5;U=Q**D;N=367;T=9;TARGET=N*N+T*T
POW=(1,7,49,343,2401)

def conflict(a,b,d):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))
def independent(v,d):
    a=list(v);return all(not conflict(x,y,d) for x,y in combinations(a,2))
def values(bits):
    while bits:
        z=bits&-bits;yield z.bit_length()-1;bits^=z

def support_singles(bits,nbmask):
    out=[];zero=[]
    for q in range(U):
        if (bits>>q)&1:continue
        h=nbmask[q]&bits;bc=h.bit_count()
        if bc==0:zero.append(q)
        elif bc==1:out.append((h.bit_length()-1,q))
    return sorted(out),zero

def private_component(start,nbmask):
    seen={start};front=[start];priv={}
    while front:
        nxt=[]
        for bits in front:
            pp,z=support_singles(bits,nbmask)
            if z:raise RuntimeError('direct-add state in I component')
            priv[bits]=pp
            for a,q in pp:
                b=bits^(1<<a)^(1<<q)
                if b not in seen:seen.add(b);nxt.append(b)
        front=nxt
    return seen,priv

def obstruction_witnesses(Istart,nbmask,ring,digits):
    comp,priv=private_component(Istart,nbmask)
    if len(comp)!=243:raise RuntimeError(f'I component drift {len(comp)}')
    obs={};eligible=subsets=orients=sameside=0
    for Ibits in comp:
        pp=priv[Ibits]
        if len({a for a,q in pp})<T:continue
        eligible+=1
        for pairs in combinations(pp,T):
            if len({a for a,q in pairs})<T:continue
            subsets+=1
            for o in product((0,1),repeat=T):
                orients+=1;PH=[q if s else a for (a,q),s in zip(pairs,o)];PV=[a if s else q for (a,q),s in zip(pairs,o)]
                if not independent(PH,digits) or not independent(PV,digits):continue
                sameside+=1;Dset=ring.nbhd(set(PH))&ring.nbhd(set(PV));mask=sum(1<<z for z in Dset);obs.setdefault(mask,(Ibits,pairs,o,PH,PV))
    if sameside!=640:raise RuntimeError(f'same-side count drift {sameside}')
    return obs,{'I_component_states':len(comp),'eligible_I_states':eligible,'nine_pair_subsets':subsets,'orientations':orients,'same_side_valid':sameside,'unique_obstruction_masks':len(obs)}

def translate(v,td,digits):
    w=digits[v];return sum(((w[j]+td[j])%Q)*POW[j] for j in range(D))

def build(Ibits,Xbits,pairs,PH,PV,ring):
    I=set(values(Ibits));X=set(values(Xbits));R={a for a,q in pairs};B=I-R;NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV))
    if X&NH&NV:raise RuntimeError('winning translation still double-hits')
    X0=X-(NH|NV);XH=X&NH;XV=X&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    if len(P)!=TARGET:raise RuntimeError(f'score drift {len(P)}')
    return sorted(''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P),(len(X0),len(XH),len(XV))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args();root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X0=set(map(int,raw['X']));ring=Ring(D);digits=tuple(ring.decode(v) for v in range(U));nbmask=[sum(1<<z for z in ring.NB[v]) for v in range(U)]
    if len(I0)!=N or len(X0)!=N or not independent(I0,digits) or not independent(X0,digits):raise RuntimeError('base drift')
    obs,ost=obstruction_witnesses(sum(1<<z for z in I0),nbmask,ring,digits);xlist=sorted(X0);checks=0;winner=None;best_bad=None;best_translation=None;hist={}
    for t in range(U):
        td=digits[t];Xbits=0
        for x in xlist:Xbits|=1<<translate(x,td,digits)
        if Xbits.bit_count()!=N:raise RuntimeError('translation collision')
        local=10**9
        for dm,w in obs.items():
            checks+=1;bad=(Xbits&dm).bit_count();local=min(local,bad)
            if bad==0:winner=(t,Xbits,w);break
        hist[str(local)]=hist.get(str(local),0)+1
        if best_bad is None or local<best_bad:best_bad=local;best_translation=t
        if winner:break
        if t%2000==0:print('PROGRESS',json.dumps({'translations':t+1,'checks':checks,'best_bad':best_bad,'best_translation':best_translation},sort_keys=True),flush=True)
    status={'method':'bpz-t9-exact-all-relative-X-translations','candidate':winner is not None,'translations_total':U,'translations_tested':(winner[0]+1 if winner else U),'obstruction_checks':checks,'best_double_hits':best_bad,'best_translation_code':best_translation,'min_hit_histogram':hist,**ost};args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        status['score']=134753;args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True);return
    t,Xbits,w=winner;Ibits,pairs,o,PH,PV=w;pts,xp=build(Ibits,Xbits,pairs,PH,PV,ring);status.update({'score':len(pts),'winning_translation_code':t,'winning_translation':list(digits[t]),'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}});args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
