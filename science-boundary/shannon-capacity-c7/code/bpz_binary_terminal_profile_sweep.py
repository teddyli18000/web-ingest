#!/usr/bin/env python3
"""Exact maximum-weight binary BPZ terminal-code sweep for known C7^5 profiles.

A seven-family valid tuple has labels (B,N,A,D,O,H,V).  Any pairwise-separated
set of length-2 label words is a valid terminal code, independently of the
family cardinalities.  There are only 49 words.  This script enumerates every
maximal compatible code exactly, reconstructs the 20 FunSearch t=9 one-hit
profiles after deleting their unique obstruction hit, adds the Lean/BPZ and Gao
base profiles and all reversed orientations, and evaluates every ordered pair.

Positive word weights imply some maximum-weight code is maximal, so exhaustive
maximal-code enumeration is an exact global optimization, not a heuristic.
"""
import argparse,json,sys
from pathlib import Path
from itertools import product

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t9_aux_translation_fft as f
from bpz_t9_funsearch_representative_case import cases

LABELS=("B","N","A","D","O","H","V")
PERP={
    "B":{"O","H","V"},
    "N":{"A","D","O","H","V"},
    "A":{"N","D","H"},
    "D":{"N","A","V"},
    "O":{"B","N"},
    "H":{"B","N","A"},
    "V":{"B","N","D"},
}
WORDS=list(product(LABELS,repeat=2))


def separated(x,y):
    return any(b in PERP[a] for a,b in zip(x,y))


def maximal_codes():
    n=len(WORDS); adj=[set() for _ in range(n)]
    for i in range(n):
        for j in range(i+1,n):
            if separated(WORDS[i],WORDS[j]): adj[i].add(j);adj[j].add(i)
    out=[]
    def bk(R,P,X):
        if not P and not X:
            out.append(tuple(sorted(R)));return
        U=P|X
        u=max(U,key=lambda z:len(P&adj[z])) if U else None
        todo=sorted(P-(adj[u] if u is not None else set()))
        for v in todo:
            bk(R+(v,),P&adj[v],X&adj[v])
            P.remove(v);X.add(v)
    bk(tuple(),set(range(n)),set())
    if not out: raise RuntimeError('no maximal codes')
    return out


def phi(profile):
    a,t,s,o,h,v=profile
    if o+h+v!=s: raise RuntimeError(('profile partition',profile))
    return dict(zip(LABELS,(a-t,o,v,h,t,t,t)))


def sigma_vec(v):
    return {'B':v['B'],'N':v['N'],'A':v['D'],'D':v['A'],'O':v['O'],'H':v['V'],'V':v['H']}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']))
    led=json.loads((args.tan_root/'data'/'certificates.json').read_text())
    ring=Ring(f.D);digits=tuple(ring.decode(v) for v in range(f.U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]
    cc=cases(I0,ring,digits,nb)
    profiles=[]
    def add(name,p,meta):
        v=phi(p);profiles.append({'name':name,'profile':list(p),'vector':v,'meta':meta})
        profiles.append({'name':'sigma('+name+')','profile':[p[0],p[1],p[2],p[3],p[5],p[4]],'vector':sigma_vec(v),'meta':dict(meta,orientation_reversed=True)})
    bpz=tuple(map(int,led['base_gadget']['profile']));add('BPZ8',bpz,{'source':'Tandon/BPZ pinned base profile'})
    add('Gao8',(367,8,367,321,26,20),{'source':'Gao published base profile'})
    for ci,c in enumerate(cc):
        X=set(c['S'])-set(c['D'])
        if len(X)!=366 or c['bad'] in X: raise RuntimeError(('one-hit deletion',ci,len(X)))
        Ibits,pairs,orient,PH,PV=c['witness']
        NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV))
        if X&NH&NV: raise RuntimeError(('obstruction survived',ci))
        X0=X-(NH|NV);XH=X&NH;XV=X&NV
        p=(367,9,366,len(X0),len(XH),len(XV))
        add(f'FunSearch9-case{ci}',p,{'case_index':ci,'obstruction_index':c['obstruction_index'],'bad':c['bad'],'PH':PH,'PV':PV,'private_pairs':[list(z) for z in pairs],'orientation':list(orient)})
    codes=maximal_codes()
    best=None; ties=0; pair_results=[]
    for L in profiles:
        for R in profiles:
            top=-1;topcode=None
            for code in codes:
                w=sum(L['vector'][WORDS[i][0]]*R['vector'][WORDS[i][1]] for i in code)
                if w>top: top=w;topcode=code
            rec={'left':L['name'],'right':R['name'],'score':top,'code':[list(WORDS[i]) for i in topcode]}
            pair_results.append(rec)
            if best is None or top>best['score']:
                best=rec;ties=1
            elif top==best['score']:ties+=1
    pair_results.sort(key=lambda z:(-z['score'],z['left'],z['right']))
    status={'method':'exact-binary-bpz-terminal-code-profile-sweep','profile_count':len(profiles),'funsearch_onehit_cases':len(cc),'word_count':len(WORDS),'maximal_terminal_codes':len(codes),'best':best,'best_score_ties':ties,'breakthrough_profile_level':best['score']>=134754,'top_pairs':pair_results[:30],'profiles':profiles}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(json.dumps(status,sort_keys=True))

if __name__=='__main__':main()
