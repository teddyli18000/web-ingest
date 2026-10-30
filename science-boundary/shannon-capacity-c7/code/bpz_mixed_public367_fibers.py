#!/usr/bin/env python3
"""Exact mixed-public-367 full-fiber terminal search for the pinned BPZ core.

With BB=B x B fixed, every q in the 16-point zero-support set Q can support a
full 367-point five-dimensional independent-set fiber.  This search permits a
different public 367-set on every one of eight left and eight right fibers.

For left fiber q x S and right fiber T x r, all 367+367 points coexist iff
    T cap N[q] = empty  OR  S cap N[r] = empty.
Same-side fibers coexist whenever their Q endpoints are pairwise nonconfusable.
We enumerate every maximum independent 8-set of Q on each side and solve the
multi-valued fiber assignment exactly with weighted MaxSAT.  The objective is
secondary only: maximize the number of periphery points outside the canonical
BPZ-X PH(left)/PV(right) terminal.  Every feasible model has exactly 5872
periphery points and hence score 134753 with the fixed 128881-point BB core.
A farthest tie is a new mother basin, not a breakthrough by itself.
"""
from __future__ import annotations
import argparse,itertools,json
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2


def cf5(a,b):
    if a==b:return True
    for _ in range(5):
        x,y=a%7,b%7;a//=7;b//=7
        if (x-y)%7 not in (0,1,6):return False
    return True

def q_independent(S):return all(not cf5(a,b) for a,b in itertools.combinations(S,2))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('corpus',type=Path);ap.add_argument('output',type=Path);ap.add_argument('certificate',type=Path);a=ap.parse_args()
    import sys;sys.path.insert(0,str(a.tan_root.resolve()));from shannon.certificates import load_base
    raw=json.loads((a.tan_root/'data'/'base_c7.json').read_text());base,_t,_e,ax=load_base(a.tan_root/'data'/'base_c7.json')
    if not all(ax.values()):raise RuntimeError('base axioms')
    ring=base.ring;I=set(map(int,raw['I0']));owners={int(x) for x,_ in raw['private_pairs']};B=I-owners
    Q={z for z in range(ring.n) if not (ring.NB[z]&B)}
    if len(B)!=359 or len(Q)!=16:raise RuntimeError((len(B),len(Q)))
    PH=set(map(int,raw['PH']));PV=set(map(int,raw['PV']));X=set(map(int,raw['X']))
    if not (len(PH)==len(PV)==8 and PH<=Q and PV<=Q and len(X)==367):raise RuntimeError('terminal data')
    qs=sorted(Q);maxq=[tuple(c) for c in itertools.combinations(qs,8) if q_independent(c)]
    if not maxq:raise RuntimeError('no Q maximum independent set')
    corp=json.loads(a.corpus.read_text());sets=[]
    for row in corp['sets']:
        S=frozenset(map(int,row['points']))
        if len(S)!=367 or not q_independent(S): # q_independent is the same C7^5 conflict test
            raise RuntimeError(('bad corpus',row['sha256'],len(S)))
        sets.append((row['sha256'],tuple(row['sources']),S))
    # Exact zero-neighborhood flags and BPZ-X overlaps.
    safe={(si,q):not any(z in ring.NB[q] for z in S) for si,(_h,_src,S) in enumerate(sets) for q in Q}
    overlap=[len(S&X) for _h,_src,S in sets]
    xidx=[i for i,(_h,_src,S) in enumerate(sets) if S==X]
    if len(xidx)!=1:raise RuntimeError(('BPZ X corpus match',xidx))
    scenarios=[]
    for L in maxq:
      for R in maxq:
        slots=[('L',q) for q in L]+[('R',r) for r in R];m=len(sets);nvar=len(slots)*m
        def var(k,s):return k*m+s+1
        w=WCNF()
        # Exactly one public 367-set per fiber.
        for k in range(len(slots)):
            w.append([var(k,s) for s in range(m)])
            for s in range(m):
                for t in range(s+1,m):w.append([-var(k,s),-var(k,t)])
        # Cross-fiber complete compatibility.
        for li,q in enumerate(L):
            for rj,r in enumerate(R):
                rk=8+rj
                for si in range(m):
                    if safe[(si,r)]:continue
                    for ti in range(m):
                        if safe[(ti,q)]:continue
                        w.append([-var(li,si),-var(rk,ti)])
        # Maximize points outside PH x X union X x PV.  Cross-overlap with the
        # opposite side is impossible for a feasible full-fiber pair, so this
        # additive reward is exact.
        rewards=[]
        for k,(side,q) in enumerate(slots):
            for si in range(m):
                if side=='L':reward=367-overlap[si] if q in PH else 367
                else:reward=367-overlap[si] if q in PV else 367
                rewards.append((var(k,si),reward))
                if reward:w.append([var(k,si)],weight=reward)
        with RC2(w,solver='g4',adapt=True,exhaust=True,incr=False,verbose=0) as rc2:model=rc2.compute();cost=rc2.cost
        if model is None:continue
        pos={z for z in model if z>0};assign=[];reward=0
        for k,(side,q) in enumerate(slots):
            hit=[si for si in range(m) if var(k,si) in pos]
            if len(hit)!=1:raise RuntimeError(('onehot',k,hit))
            si=hit[0];assign.append((side,q,si));reward+=367-overlap[si] if ((side=='L' and q in PH) or (side=='R' and q in PV)) else 367
        scenarios.append({'L':list(L),'R':list(R),'reward_outside_reference':reward,'assign':[[side,q,si] for side,q,si in assign]})
    if not scenarios:raise RuntimeError('no mixed-fiber terminal')
    scenarios.sort(key=lambda z:z['reward_outside_reference'],reverse=True);best=scenarios[0]
    L=set(best['L']);R=set(best['R']);per=set();assign_public=[]
    for side,q,si in best['assign']:
        h,src,S=sets[si];assign_public.append({'side':side,'q':q,'sha256':h,'sources':list(src)})
        if side=='L':per.update((q,z) for z in S)
        else:per.update((z,q) for z in S)
    if len(per)!=5872:raise RuntimeError(('periphery size',len(per)))
    core={(x,y) for x in B for y in B};cand=core|per
    if len(cand)!=134753:raise RuntimeError(('score',len(cand)))
    # Structural replay: core compatibility follows q support-zero.  Same-side
    # and cross-side conditions were exact; recheck the final periphery anyway.
    pv=list(per)
    for i,p in enumerate(pv):
        nx,ny=ring.NB[p[0]],ring.NB[p[1]]
        for z in pv[i+1:]:
            if z[0] in nx and z[1] in ny:raise RuntimeError(('periphery conflict',p,z))
    def enc(p):return ''.join(str(d) for d in ring.decode(p[0])+ring.decode(p[1]))
    a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({'points':sorted(enc(p) for p in cand)},separators=(',',':'))+'\n')
    out={'method':'exact-mixed-public367-full-fiber-terminal','corpus_sets':len(sets),'q_maximum_independent_sets':len(maxq),'scenarios_feasible':len(scenarios),'score':134753,'best_reward_outside_reference':best['reward_outside_reference'],'best_L':best['L'],'best_R':best['R'],'assignments':assign_public,'top10':[{'reward':z['reward_outside_reference'],'L':z['L'],'R':z['R']} for z in scenarios[:10]]}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='assignments' and k!='top10'},sort_keys=True));print('assignments',json.dumps(assign_public,sort_keys=True))
if __name__=='__main__':main()
