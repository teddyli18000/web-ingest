#!/usr/bin/env python3
"""Scan all relative translations of many public C7^5 367-sets against all BPZ t=9 obstructions.

Seeds: the 36 public Family-F maxima from molind/c7-five, plus BPZ X and I0.
For each seed S and each of the 160 distinct obstruction masks D from the full
243-state BPZ I private-swap component, compute all 7^5 translation intersection
counts |(S+t) cap D| at once by exact-rounded 5D FFT correlation.  Every zero
reported by FFT is explicitly replayed in integer coordinates before use.

A replayed zero gives a valid 367-point auxiliary X for that Definition-2 t=9
witness and therefore materializes a 134770-point C7^10 certificate.
"""
import argparse,json,sys
from itertools import combinations,product
from pathlib import Path
import numpy as np
Q=7;D=5;U=Q**D;N=367;T=9;TARGET=N*N+T*T;POW=tuple(Q**i for i in range(D))

def dec(v):return tuple((v//POW[i])%Q for i in range(D))
def enc(w):return sum(w[i]*POW[i] for i in range(D))
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
def obstruction_witnesses(I0,ring,digits,nb):
    comp,pm=component(sum(1<<z for z in I0),nb)
    if len(comp)!=243:raise RuntimeError(f'I component drift {len(comp)}')
    obs={};raw=0
    for ib in comp:
        pp=pm[ib]
        if len({a for a,q in pp})<T:continue
        for pairs in combinations(pp,T):
            if len({a for a,q in pairs})<T:continue
            for o in product((0,1),repeat=T):
                PH=[q if s else a for (a,q),s in zip(pairs,o)];PV=[a if s else q for (a,q),s in zip(pairs,o)]
                if not independent(PH,digits) or not independent(PV,digits):continue
                raw+=1;Dset=ring.nbhd(set(PH))&ring.nbhd(set(PV));mask=sum(1<<z for z in Dset);obs.setdefault(mask,(ib,pairs,o,PH,PV))
    if raw!=640 or len(obs)!=160:raise RuntimeError(f'obstruction drift {raw} {len(obs)}')
    return obs
def arr(vals_,digits):
    a=np.zeros((Q,)*D,dtype=np.float64)
    for v in vals_:a[digits[v]]=1.0
    return a
def shift_set(S,t,digits,sign=1):
    out=[]
    for v in S:
        w=digits[v];out.append(enc(tuple((w[j]+sign*t[j])%Q for j in range(D))))
    return out
def build(Ibits,Xbits,pairs,PH,PV,ring):
    I=set(values(Ibits));X=set(values(Xbits));R={a for a,q in pairs};B=I-R;NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV))
    if X&NH&NV:raise RuntimeError('winning translated auxiliary still hits D')
    X0=X-(NH|NV);XH=X&NH;XV=X&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    if len(P)!=TARGET:raise RuntimeError(f'score drift {len(P)}')
    return sorted(''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P),(len(X0),len(XH),len(XV))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('family_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args();sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X0=set(map(int,raw['X']));ring=Ring(D);digits=tuple(ring.decode(v) for v in range(U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(U)];obs=obstruction_witnesses(I0,ring,digits,nb)
    fam=json.loads((args.family_root/'data'/'family-f.json').read_text());states=[set(map(int,s)) for s in fam['states']]
    seeds=[('bpz-X',X0),('bpz-I0',I0)]+[(f'family-f-{i}',s) for i,s in enumerate(states)]
    for name,S in seeds:
        if len(S)!=N or not independent(S,digits):raise RuntimeError(f'seed {name} invalid')
    obs_items=list(obs.items());Fobs=[]
    for mask,w in obs_items:Fobs.append((mask,w,np.fft.fftn(arr(values(mask),digits))))
    cases=0;zero_fft=0;replays=0;winner=None;best=None;hist={}
    for si,(name,S) in enumerate(seeds):
        FS=np.fft.fftn(arr(S,digits))
        for oi,(mask,w,FD) in enumerate(Fobs):
            cases+=1
            corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16)
            mn=int(corr.min());hist[str(mn)]=hist.get(str(mn),0)+1
            rec={'seed':name,'obstruction_index':oi,'min_hits':mn}
            if best is None or mn<best['min_hits']:best=rec
            if mn!=0:continue
            for idx in np.argwhere(corr==0):
                zero_fft+=1;t=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    replays+=1;X=shift_set(S,t,digits,sign);Xset=set(X)
                    if len(Xset)!=N or not independent(Xset,digits):raise RuntimeError('translated seed replay independence')
                    if Xset & set(values(mask)):continue
                    Ibits,pairs,o,PH,PV=w;winner=(name,t,sign,Xset,w,oi);break
                if winner:break
            if winner:break
        if winner:break
        print('SEED_DONE',json.dumps({'seed':name,'cases':cases,'best':best},sort_keys=True),flush=True)
    status={'method':'bpz-t9-all-translations-public-367-seeds-FFT','candidate':winner is not None,'seed_count':len(seeds),'obstruction_masks':len(obs_items),'seed_obstruction_cases':cases,'fft_zero_shifts_examined':zero_fft,'explicit_replays':replays,'best':best,'min_hit_histogram':hist,'family_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'};args.status.parent.mkdir(parents=True,exist_ok=True)
    if not winner:
        status['score']=134753;args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True);return
    name,t,sign,X,w,oi=winner;Ibits,pairs,o,PH,PV=w;Xbits=sum(1<<z for z in X);pts,xp=build(Ibits,Xbits,pairs,PH,PV,ring);status.update({'score':len(pts),'winning_seed':name,'winning_obstruction_index':oi,'winning_translation':list(t),'translation_sign':sign,'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}});args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
