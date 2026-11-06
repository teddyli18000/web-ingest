#!/usr/bin/env python3
"""Exhaust all oriented ten-port gadgets from two 367-point circular basins.

For each parent I and each candidate oriented ten-tuple (PH,PV), compute the
forbidden D = N[PH] ∩ N[PV] in C7^5.  For every pinned independent auxiliary
367-code X, check all 7^5 translations of X against D by cyclic FFT.
A zero intersection yields a 134,789 point 10-dimensional construction by
the BPZ two-sided port lemma, checked before any certificate is exported.

A nonzero minimum is a finite-family obstruction only, NOT an impossibility
result for 367-word codes or the 10-dimensional Few Shots problem.
"""
from __future__ import annotations
import argparse, base64, hashlib, itertools, json, struct
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

Q=7
P=(1,7,49,343,2401)
N=Q**5
STEPS=tuple(itertools.product((-1,0,1),repeat=5))
DIG=tuple(tuple(v//p%Q for p in P) for v in range(N))

def conf(a,b):
    return all((x-y)%Q in (0,1,6) for x,y in zip(DIG[a],DIG[b]))

def independent(S):
    return len(S)==367 and len(set(S))==367 and all(
        not conf(a,b) for i,a in enumerate(S) for b in S[i+1:])

def read_encoded(path):
    info=json.loads(path.read_text())
    bb=base64.b64decode(info['data'])
    assert len(bb)==2*info['n']
    assert hashlib.sha256(bb).hexdigest()==info['sha256_decoded_bytes']
    S=list(struct.unpack('<'+str(info['n'])+'H',bb))
    assert independent(S)
    return S

def neighbors(v):
    d=DIG[v]
    return tuple(sum((d[k]+step[k])%Q*P[k] for k in range(5)) for step in STEPS)

def nbhd(S):
    out=set()
    for v in S:out.update(neighbors(v))
    return out

def private_pairs(I):
    counts=[0]*N
    unique=[-1]*N
    for a in I:
        for v in neighbors(a):
            counts[v]+=1
            unique[v]=a
    inside=set(I)
    groups=defaultdict(list)
    for v in range(N):
        if v not in inside and counts[v]==1:
            groups[unique[v]].append(v)
    return groups

def orientations(groups,t):
    owners=sorted(groups)
    out=[]
    def rec(i,pairs,h,v):
        if len(pairs)==t:
            out.append((tuple(pairs),tuple(h),tuple(v)))
            return
        if i>=len(owners) or len(pairs)+len(owners)-i<t:
            return
        a=owners[i]
        for b in groups[a]:
            for ha,va in ((a,b),(b,a)):
                if all(not conf(ha,x) for x in h) and all(not conf(va,y) for y in v):
                    rec(i+1,pairs+[(a,b)],h+[ha],v+[va])
        rec(i+1,pairs,h,v)
    rec(0,[],[],[])
    return out

def arr(S):
    a=np.zeros((Q,)*5,dtype=np.float64)
    for v in S:a[DIG[v]]=1.0
    return a

def translated(S,delta):
    return sorted(sum((DIG[v][k]+int(delta[k]))%Q*P[k] for k in range(5)) for v in S)

def build(I,X,pairs,H,V):
    R={a for a,b in pairs}
    B=set(I)-R
    NH,NV=nbhd(H),nbhd(V)
    assert set(X).isdisjoint(NH&NV)
    X0=set(X)-(NH|NV)
    XH=set(X)&NH
    XV=set(X)&NV
    points=set()
    for A,C in ((B,B),(R,X0),(H,XH),(V,XV),(X0,R),(XH,V),(XV,H)):
        points.update((a,b) for a in A for b in C)
    assert len(points)==367**2+len(pairs)**2,(len(points),len(pairs))
    words=[''.join(str(z) for z in DIG[a]+DIG[b]) for a,b in points]
    return sorted(words)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('bpz',type=Path)
    p.add_argument('family',type=Path)
    p.add_argument('circular',type=Path)
    p.add_argument('port12a',type=Path)
    p.add_argument('port12b',type=Path)
    p.add_argument('status',type=Path)
    p.add_argument('certificate',type=Path)
    p.add_argument('near_miss',type=Path)
    p.add_argument('--parent',choices=('port12a','port12b'),required=True)
    a=p.parse_args()
    bpz=json.loads(a.bpz.read_text())
    family=json.loads(a.family.read_text())
    sources={
      'I0':list(map(int,bpz['I0'])),
      'X':list(map(int,bpz['X'])),
      'circle':read_encoded(a.circular),
      'port12a':read_encoded(a.port12a),
      'port12b':read_encoded(a.port12b)
    }
    for i,S in enumerate(family['states']):sources[f'F{i}']=list(map(int,S))
    assert len(sources)==41
    for name,S in sources.items():
        assert independent(S),name
    I=sources[a.parent]
    groups=private_pairs(I)
    assert len(groups)==12,(a.parent,len(groups))
    ports=orientations(groups,10)
    expected={'port12a':48,'port12b':576}[a.parent]
    assert len(ports)==expected,(a.parent,len(ports))
    F={name:np.fft.fftn(arr(S)) for name,S in sources.items()}
    best=None
    min_hist=Counter()
    min_by_aux={}
    winner=None
    cases=0
    for oi,(pairs,H,V) in enumerate(ports):
        mask=nbhd(H)&nbhd(V)
        FD=np.fft.fftn(arr(mask))
        for name,FS in F.items():
            cases+=1
            vals=np.fft.ifftn(np.conj(FS)*FD).real
            rounded=np.rint(vals)
            assert np.max(np.abs(vals-rounded))<1e-6
            mn=int(rounded.min())
            min_hist[mn]+=1
            if name not in min_by_aux or mn<min_by_aux[name]:
                min_by_aux[name]=mn
            if best is None or (mn,len(mask))<(best['minimum_hits'],best['forbidden_size']):
                delta=tuple(int(v) for v in np.unravel_index(int(rounded.argmin()),rounded.shape))
                trial=translated(sources[name],delta)
                exact=len(set(trial)&mask)
                assert exact==mn,(mn,exact)
                best={'minimum_hits':mn,'forbidden_size':len(mask),
                      'orientation_index':oi,'auxiliary':name,
                      'delta':list(delta),'hit_vertices':sorted(set(trial)&mask),
                      'pairs':[list(x) for x in pairs],
                      'PH':list(H),'PV':list(V)}
                print('BEST',json.dumps({k:v for k,v in best.items()
                      if k not in ('pairs','PH','PV')},sort_keys=True),flush=True)
            if mn==0:
                delta=tuple(int(v) for v in np.unravel_index(int(rounded.argmin()),rounded.shape))
                X=translated(sources[name],delta)
                assert not (set(X)&mask)
                words=build(I,X,pairs,H,V)
                assert len(words)==134789
                a.certificate.parent.mkdir(parents=True,exist_ok=True)
                a.certificate.write_text(json.dumps({'points':words},separators=(',',':'))+'\n')
                winner={'parent':a.parent,'orientation_index':oi,'auxiliary':name,
                        'delta':list(delta),'score':len(words)}
                break
        if winner:break
    near={'method':'ten-port-367-auxiliary-exhaustive-translation',
          'parent':a.parent,'best':best}
    a.near_miss.parent.mkdir(parents=True,exist_ok=True)
    a.near_miss.write_text(json.dumps(near,indent=2,sort_keys=True)+'\n')
    result={'method':near['method'],'parent':a.parent,'private_owner_count':len(groups),
            'valid_ten_port_orientations':len(ports),'auxiliary_codes':len(sources),
            'translations_per_case':N,'orientation_auxiliary_cases':cases,
            'all_cases_exhausted':cases==len(ports)*len(sources),
            'minimum_hit_histogram':dict(sorted(min_hist.items())),
            'best_by_auxiliary':dict(sorted(min_by_aux.items())),
            'best':{k:v for k,v in best.items() if k not in ('pairs','PH','PV')},
            'verified_candidate':winner}
    a.status.parent.mkdir(parents=True,exist_ok=True)
    a.status.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('FINAL',json.dumps(result,sort_keys=True),flush=True)

if __name__=='__main__':
    main()
