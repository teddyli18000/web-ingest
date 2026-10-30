#!/usr/bin/env python3
"""One-shot exact MaxSAT for mixed public 367-point terminal fibers.

For each side choose exactly eight vertices of the exact 16-vertex zero-support
Q graph, with at most one public 367-set attached to each chosen endpoint and
hard clauses for every Q-conflicting endpoint pair.  Thus endpoint selection and
per-fiber 367-set assignment are optimized jointly in one model; no enumeration
of the many maximum independent 8-sets of Q is needed.

For a left fiber q x S and right fiber T x r, complete coexistence is equivalent
to
    T cap N[q] = empty OR S cap N[r] = empty.
Every incompatible pair of choices is a hard clause.  All feasible solutions
have 16 disjoint full fibers, hence 5872 periphery points and score 134753 with
the fixed BB core.  Soft weights maximize the exact number of periphery points
outside the canonical PH x X union X x PV reference, producing a far record-tie
mother in one solver call.
"""
from __future__ import annotations
import argparse,itertools,json,sys
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from pysat.card import CardEnc,EncType

def conflict5(a:int,b:int)->bool:
    if a==b:return True
    for _ in range(5):
        x,y=a%7,b%7;a//=7;b//=7
        if (x-y)%7 not in (0,1,6):return False
    return True

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('corpus',type=Path);ap.add_argument('output',type=Path);ap.add_argument('certificate',type=Path);a=ap.parse_args()
    root=a.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import load_base
    raw=json.loads((root/'data'/'base_c7.json').read_text());base,_t,_e,ax=load_base(root/'data'/'base_c7.json')
    if not all(ax.values()):raise RuntimeError({k:v for k,v in ax.items() if not v})
    ring=base.ring;I=set(map(int,raw['I0']));owners={int(p[0]) for p in raw['private_pairs']};B=I-owners
    Q=sorted(z for z in range(ring.n) if not (ring.NB[z]&B));PH=set(map(int,raw['PH']));PV=set(map(int,raw['PV']));X=frozenset(map(int,raw['X']))
    if len(B)!=359 or len(Q)!=16 or len(PH)!=8 or len(PV)!=8:raise RuntimeError((len(B),len(Q),len(PH),len(PV)))
    if any(conflict5(u,v) for u,v in itertools.combinations(PH,2)):raise RuntimeError('PH not independent')
    if any(conflict5(u,v) for u,v in itertools.combinations(PV,2)):raise RuntimeError('PV not independent')

    corp=json.loads(a.corpus.read_text());sets=[]
    for row in corp['sets']:
        S=frozenset(map(int,row['points']))
        if len(S)!=367:raise RuntimeError(('corpus size',row['sha256'],len(S)))
        vv=sorted(S)
        for i,u in enumerate(vv):
            for v in vv[i+1:]:
                if conflict5(u,v):raise RuntimeError(('bad corpus',row['sha256'],u,v))
        sets.append((row['sha256'],tuple(row['sources']),S))
    m=len(sets)
    if not m:raise RuntimeError('empty corpus')
    if sum(S==X for _h,_src,S in sets)!=1:raise RuntimeError('BPZ-X corpus mismatch')

    reference={(q,z) for q in PH for z in X}|{(z,q) for q in PV for z in X}
    if len(reference)!=5872:raise RuntimeError(('reference',len(reference)))

    choice={};rev={};nv=0
    for side in (0,1):
        for q in Q:
            for si in range(m):
                nv+=1;choice[(side,q,si)]=nv;rev[nv]=(side,q,si)
    w=WCNF();hard=0
    # Each endpoint carries at most one public set.
    for side in (0,1):
        for q in Q:
            lits=[choice[(side,q,si)] for si in range(m)]
            for i in range(m):
                for j in range(i+1,m):w.append([-lits[i],-lits[j]]);hard+=1
    # Same-side Q endpoint conflicts, independent of which public sets are used.
    qedges=[(q,r) for q,r in itertools.combinations(Q,2) if conflict5(q,r)]
    for side in (0,1):
        for q,r in qedges:
            for si in range(m):
                u=choice[(side,q,si)]
                for ti in range(m):w.append([-u,-choice[(side,r,ti)]]);hard+=1
    # Exactly eight endpoint+set choices on each side. At-most-one-per-endpoint
    # above makes these eight distinct endpoints.
    top=nv
    for side in (0,1):
        lits=[choice[(side,q,si)] for q in Q for si in range(m)]
        enc=CardEnc.equals(lits=lits,bound=8,top_id=top,encoding=EncType.totalizer)
        for c in enc.clauses:w.append(c);hard+=1
        top=enc.nv

    safe={(si,q):not any(z in ring.NB[q] for z in S) for si,(_h,_src,S) in enumerate(sets) for q in Q}
    cross=0
    for q in Q:
        for r in Q:
            for si in range(m):
                if safe[(si,r)]:continue
                lv=choice[(0,q,si)]
                for ti in range(m):
                    if safe[(ti,q)]:continue
                    w.append([-lv,-choice[(1,r,ti)]]);cross+=1

    rewards={}
    for side in (0,1):
        for q in Q:
            for si,(_h,_src,S) in enumerate(sets):
                fiber={(q,z) for z in S} if side==0 else {(z,q) for z in S}
                reward=len(fiber-reference);v=choice[(side,q,si)];rewards[v]=reward
                if reward:w.append([v],weight=reward)

    with RC2(w,solver='g4',adapt=True,exhaust=True,incr=True,verbose=0) as rc2:model=rc2.compute()
    if model is None:raise RuntimeError('mixed-fiber global model UNSAT')
    pos={z for z in model if z>0};chosen=[rev[v] for v in range(1,nv+1) if v in pos]
    if len(chosen)!=16:raise RuntimeError(('choice count',len(chosen)))
    for side in (0,1):
        ep=[q for s,q,_si in chosen if s==side]
        if len(ep)!=8 or len(set(ep))!=8 or any(conflict5(u,v) for u,v in itertools.combinations(ep,2)):raise RuntimeError(('endpoint set',side,ep))

    per=set();assign=[];reward=0
    for side,q,si in chosen:
        h,src,S=sets[si];fiber={(q,z) for z in S} if side==0 else {(z,q) for z in S};per.update(fiber);reward+=rewards[choice[(side,q,si)]]
        assign.append({'side':'L' if side==0 else 'R','endpoint':q,'sha256':h,'sources':list(src),'outside_reference':rewards[choice[(side,q,si)]]})
    if len(per)!=5872:raise RuntimeError(('periphery overlap',len(per)))
    if len(per-reference)!=reward:raise RuntimeError(('reward drift',reward,len(per-reference)))
    pv=list(per)
    for i,p in enumerate(pv):
        nx,ny=ring.NB[p[0]],ring.NB[p[1]]
        for z in pv[i+1:]:
            if z[0] in nx and z[1] in ny:raise RuntimeError(('periphery conflict',p,z))
    core={(x,y) for x in B for y in B};cand=core|per
    if len(cand)!=134753:raise RuntimeError(('score',len(cand)))
    for p in per:
        nx,ny=ring.NB[p[0]],ring.NB[p[1]]
        for z in core:
            if z[0] in nx and z[1] in ny:raise RuntimeError(('core conflict',p,z))
    def encp(p):return ''.join(str(d) for d in ring.decode(p[0])+ring.decode(p[1]))
    a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({'points':sorted(encp(p) for p in cand)},separators=(',',':'))+'\n')
    out={'method':'exact-global-mixed-public367-full-fibers','corpus_sets':m,'choice_variables':nv,'aux_variables':top-nv,'q_edges':len(qedges),'hard_clauses':hard,'cross_clauses':cross,'score':134753,'outside_reference':reward,'symmetric_difference_reference':2*reward,'assignments':sorted(assign,key=lambda x:(x['side'],x['endpoint']))}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='assignments'},sort_keys=True));print('assignments',json.dumps(out['assignments'],sort_keys=True))
if __name__=='__main__':main()
