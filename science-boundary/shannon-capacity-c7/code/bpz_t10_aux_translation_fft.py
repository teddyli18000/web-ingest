#!/usr/bin/env python3
"""Search the BPZ private-neighbour component for t=10 C7^10 constructions.

For a valid t-witness (R,PH,PV) and an independent auxiliary X subset C7^5,
the seven-block construction has size

    (367-t)^2 + 2*t*|X|.

At t=10 the full 367 auxiliary gives 134789, and even deleting one obstruction
hit leaves 134769 > the Few Shots record 134753.  Therefore this search accepts
both zero-hit and one-hit translated public 367-sets.  Any FFT minimum <=1 is
replayed exactly, the hit (if present) is deleted, and the resulting 10D
certificate is checked by the caller with the upstream Few Shots verifier.
"""
import argparse
import json
import sys
from itertools import combinations, product
from pathlib import Path

import numpy as np

Q=7; D=5; U=Q**D; N=367; T=10; BASELINE=134753
POW=tuple(Q**i for i in range(D))

def dec(v): return tuple((v//POW[i])%Q for i in range(D))
def enc(w): return sum(w[i]*POW[i] for i in range(D))
def conflict(a,b,d): return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))
def independent(v,d):
    a=list(v); return all(not conflict(x,y,d) for x,y in combinations(a,2))
def values(bits):
    while bits:
        z=bits&-bits; yield z.bit_length()-1; bits^=z

def private(bits,nb):
    out=[]
    for q in range(U):
        if (bits>>q)&1: continue
        h=nb[q]&bits
        if h.bit_count()==1: out.append((h.bit_length()-1,q))
    return sorted(out)

def component(start,nb):
    seen={start}; front=[start]; pm={}
    while front:
        nxt=[]
        for b in front:
            pp=private(b,nb); pm[b]=pp
            for a,q in pp:
                c=b^(1<<a)^(1<<q)
                if c not in seen: seen.add(c); nxt.append(c)
        front=nxt
    return seen,pm

def obstruction_witnesses(I0,ring,digits,nb):
    comp,pm=component(sum(1<<z for z in I0),nb)
    if len(comp)!=243: raise RuntimeError(f'I component drift {len(comp)}')
    obs={}; raw=0; eligible_states=0; max_private_owners=0; max_private_pairs=0
    for ib in comp:
        pp=pm[ib]; owners=len({a for a,q in pp}); max_private_owners=max(max_private_owners,owners); max_private_pairs=max(max_private_pairs,len(pp))
        if owners<T: continue
        eligible_states+=1
        for pairs in combinations(pp,T):
            if len({a for a,q in pairs})<T: continue
            for o in product((0,1),repeat=T):
                PH=[q if s else a for (a,q),s in zip(pairs,o)]
                PV=[a if s else q for (a,q),s in zip(pairs,o)]
                if not independent(PH,digits) or not independent(PV,digits): continue
                raw+=1; Dset=ring.nbhd(set(PH))&ring.nbhd(set(PV)); mask=sum(1<<z for z in Dset)
                obs.setdefault(mask,(ib,pairs,o,PH,PV))
    stats={'component_states':len(comp),'eligible_states':eligible_states,'max_private_owners':max_private_owners,'max_private_pairs':max_private_pairs,'raw_valid_orientations':raw,'distinct_obstructions':len(obs),'obstruction_sizes':{}}
    for m in obs:
        k=m.bit_count(); stats['obstruction_sizes'][str(k)]=stats['obstruction_sizes'].get(str(k),0)+1
    return obs,stats

def arr(vals_,digits):
    a=np.zeros((Q,)*D,dtype=np.float64)
    for v in vals_: a[digits[v]]=1.0
    return a

def shift_set(S,t,digits,sign=1):
    return [enc(tuple((digits[v][j]+sign*t[j])%Q for j in range(D))) for v in S]

def build(Ibits,X,pairs,PH,PV,ring):
    I=set(values(Ibits)); R={a for a,q in pairs}; B=I-R
    if len(R)!=T: raise RuntimeError(f'R size drift {len(R)}')
    NH=ring.nbhd(set(PH)); NV=ring.nbhd(set(PV))
    if X&NH&NV: raise RuntimeError('auxiliary still hits obstruction')
    X0=X-(NH|NV); XH=X&NH; XV=X&NV; P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C: P.add((a,c))
    expected=(N-T)**2 + 2*T*len(X)
    if len(P)!=expected: raise RuntimeError(f'score drift {len(P)} != {expected}')
    return sorted(''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P),(len(X0),len(XH),len(XV))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('family_root',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve())); from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text()); I0=set(map(int,raw['I0'])); X0=set(map(int,raw['X']))
    ring=Ring(D); digits=tuple(ring.decode(v) for v in range(U)); nb=[sum(1<<z for z in ring.NB[v]) for v in range(U)]
    obs,ostats=obstruction_witnesses(I0,ring,digits,nb)
    print('OBSTRUCTION_STATS',json.dumps(ostats,sort_keys=True),flush=True)
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if not obs:
        status={'candidate':False,'method':'bpz-t10-all-translations-public-367-seeds-FFT','score':BASELINE,'obstruction_stats':ostats,'conclusion':'no valid t=10 witness in pinned private-neighbour component'}
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(status,sort_keys=True)); return

    fam=json.loads((args.family_root/'data'/'family-f.json').read_text()); states=[set(map(int,s)) for s in fam['states']]
    seeds=[('bpz-X',X0),('bpz-I0',I0)]+[(f'family-f-{i}',s) for i,s in enumerate(states)]
    for name,S in seeds:
        if len(S)!=N or not independent(S,digits): raise RuntimeError(f'seed {name} invalid')
    Fobs=[(mask,w,np.fft.fftn(arr(values(mask),digits))) for mask,w in obs.items()]
    best=None; hist={}; cases=0; winner=None
    for name,S in seeds:
        FS=np.fft.fftn(arr(S,digits))
        for oi,(mask,w,FD) in enumerate(Fobs):
            cases+=1; corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16); mn=int(corr.min()); hist[str(mn)]=hist.get(str(mn),0)+1
            rec={'seed':name,'obstruction_index':oi,'min_hits':mn,'obstruction_size':mask.bit_count()}
            if best is None or mn<best['min_hits']:
                best=rec; print('NEW_BEST',json.dumps(best,sort_keys=True),flush=True)
            if mn>1: continue
            Dset=set(values(mask))
            for idx in np.argwhere(corr==mn):
                t=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    Xfull=set(shift_set(S,t,digits,sign))
                    if len(Xfull)!=N or not independent(Xfull,digits): raise RuntimeError('translated seed replay failed')
                    hits=Xfull&Dset
                    if len(hits)>1: continue
                    X=Xfull-Dset
                    score=(N-T)**2+2*T*len(X)
                    if score<=BASELINE: continue
                    winner=(name,oi,t,sign,Xfull,X,hits,w,score,mask); break
                if winner: break
            if winner: break
        if winner: break
        print('SEED_DONE',json.dumps({'seed':name,'cases':cases,'best':best},sort_keys=True),flush=True)

    status={'method':'bpz-t10-all-translations-public-367-seeds-FFT-one-hit-tolerant','candidate':winner is not None,'seed_count':len(seeds),'obstruction_stats':ostats,'seed_obstruction_cases':cases,'best':best,'min_hit_histogram':hist}
    if winner is None:
        status['score']=BASELINE; args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(status,sort_keys=True),flush=True); return
    name,oi,t,sign,Xfull,X,hits,w,score,mask=winner; Ibits,pairs,o,PH,PV=w; pts,xp=build(Ibits,X,pairs,PH,PV,ring)
    if len(pts)!=score or score<=BASELINE: raise RuntimeError(f'candidate score replay {len(pts)} {score}')
    status.update({'score':score,'winning_seed':name,'winning_obstruction_index':oi,'winning_obstruction_size':mask.bit_count(),'winning_translation':list(t),'translation_sign':sign,'deleted_auxiliary_hits':sorted(hits),'auxiliary_size':len(X),'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n'); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
