#!/usr/bin/env python3
"""Exact fractionally unchargeable C7 nine-factor nucleus; independent raw-core MILP."""
import argparse
import itertools
import json
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import coo_matrix

F=(1012,1025,1285,1299,3722,6501,13109,13359,15759)
W={z:2 if z==13359 else 1 for z in F}
T={983:1,1292:1,1360:1,3420:1,3680:1,4106:1,15468:1,15712:2}
P=tuple(7**i for i in range(5))

def cf(x,y):
    return all(((x//p)%7-(y//p)%7)%7 in (0,1,6) for p in P)

def geometry(raw):
    I=set(raw['I0'])
    B=I-{a for a,b in raw['private_pairs']}
    assert len(I)==367 and len(B)==359
    assert all(not cf(a,b) for i,a in enumerate(sorted(B)) for b in sorted(B)[i+1:])
    S={}
    for b in B:
        d=[(b//p)%7 for p in P]
        for e in itertools.product((-1,0,1),repeat=5):
            z=sum((di+ei)%7*p for di,ei,p in zip(d,e,P))
            if z not in B:S.setdefault(z,set()).add(b)
    h=Counter(map(len,S.values()))
    assert (h[1],h[2],h[3])==(50,375,1581)
    return B,S

def dual_check(S):
    assert sum(W.values())==10 and sum(T.values())==9
    assert set().union(*(S[z] for z in F))==set(T)
    for b,cap in T.items():
        L=[z for z in F if b in S[z]]
        val=max(sum(W[z] for z in C)
                for mask in range(1<<len(L))
                for C in [[z for i,z in enumerate(L) if mask>>i&1]]
                if all(cf(z,w) for i,z in enumerate(C) for w in C[i+1:]))
        assert val<=cap,(b,val,cap)
    return {'weights_twice':W,'capacities_twice':T,'dual_gap':0.5}

def prize(F0,S):
    Q=[(u,v) for u in F0 for v in F0]
    D=sorted({(a,b) for u,v in Q for a in S[u] for b in S[v]})
    idx={x:i for i,x in enumerate(D)}
    m=len(Q);n=len(D);rr=[];cc=[];vv=[];ub=[]
    def row(t,k):
        i=len(ub);ub.append(k)
        for j,v in t:rr.append(i);cc.append(j);vv.append(v)
    for i,(u,v) in enumerate(Q):
        for a in S[u]:
            for b in S[v]:row(((i,1),(m+idx[a,b],-1)),0)
    edges=0
    for i,(u,v) in enumerate(Q):
        for j in range(i+1,m):
            x,y=Q[j]
            if cf(u,x) and cf(v,y):
                row(((i,1),(j,1)),1);edges+=1
    A=coo_matrix((np.array(vv,float),(rr,cc)),shape=(len(ub),m+n)).tocsr()
    opt=milp(np.r_[-np.ones(m),np.ones(n)],integrality=np.ones(m+n),
             bounds=Bounds(np.zeros(m+n),np.ones(m+n)),
             constraints=LinearConstraint(A,-np.inf,ub),
             options={'mip_rel_gap':0,'time_limit':45})
    if opt.status!=0:
        return {'status':int(opt.status),'candidate_count':m,'core_cells':n}
    chosen=[Q[i] for i in range(m) if opt.x[i]>0.5]
    deletion={(a,b) for u,v in chosen for a in S[u] for b in S[v]}
    assert not any(cf(u,x) and cf(v,y) for i,(u,v) in enumerate(chosen) for x,y in chosen[i+1:])
    gain=len(chosen)-len(deletion)
    assert gain==-round(opt.fun)
    return {'status':0,'candidate_count':m,'core_cells':n,'conflict_edges':edges,
            'gain':gain,'selected':len(chosen),'deletions':len(deletion),
            'positive_witness':chosen if gain>0 else None}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('source',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args()
    B,S=geometry(json.loads(a.source.read_text()))
    dual=dual_check(S)
    base=prize(F,S)
    shell=sorted(z for z in S if len(S[z])<=2 and z not in F and S[z]&set(T))
    assert len(shell)==38
    ext=[{'added':z,**prize(F+(z,),S)} for z in shell]
    double=[z for z in shell if len(S[z]&set(T))==2]
    assert len(double)==6
    pairs=[{'added_pair':[x,y],**prize(F+(x,y),S)} for x,y in itertools.combinations(double,2)]
    result={'method':'fractional-nine-charge','source_core':len(B),'factors':list(F),
            'fractional_dual':dual,'base':base,'single_extensions':ext,'pair_extensions':pairs,
            'all_exact':all(x['status']==0 for x in [base]+ext+pairs)}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'base':base,'shell':len(shell),'pairs':len(pairs),
          'positive':sum(x.get('gain',0)>0 for x in ext+pairs),'all_exact':result['all_exact']},sort_keys=True))
    assert result['all_exact']

if __name__=='__main__':
    main()
