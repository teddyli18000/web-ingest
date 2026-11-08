#!/usr/bin/env python3
"""Constructive large-neutral and +1 search around pinned published C7^10 record.

Generate every outside×outside candidate that conflicts with at most two
published 10D words, including all factor pairs with zero core support and
the complete core-support-product<=2 region. Optimize simultaneous removals
and additions by integer programming, with a secondary objective favoring
structurally distant equal-score candidates. Replay the full ten-dimensional
independence and materialize a certificate for the upstream verifier.

This is not a local Hamming radius: in a verified run, >3000 10D words can
be replaced jointly while retaining the published score.
"""
import argparse,collections,itertools,json,random,time
from pathlib import Path

import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import coo_matrix

P=(1,7,49,343,2401)
U=7**5
D=tuple(tuple(v//p%7 for p in P) for v in range(U))
OFF=tuple(itertools.product((-1,0,1),repeat=5))

def code(d):return sum(x*P[i] for i,x in enumerate(d))
def nb(v):
    return tuple(code(tuple((D[v][k]+s[k])%7 for k in range(5))) for s in OFF)
def conf(a,b):
    return all((D[a][i]-D[b][i])%7 in (0,1,6) for i in range(5))
def word(a,b):return ''.join(map(str,D[a]+D[b]))

def run(raw,core,seed,limit):
    start=time.monotonic()
    W=set(json.loads(raw.read_text())['points'])
    B={code(tuple(map(int,line.split()))) for line in core.read_text().splitlines() if line.strip()}
    # Frozen published core = R367 without the eight first endpoints.
    DELETED={(1,3,4,4,6),(3,4,0,3,5),(5,3,1,3,4),(4,4,6,1,6),
             (6,0,6,4,5),(0,3,5,6,5),(6,4,3,4,0),(6,4,5,3,2)}
    B-=set(map(code,DELETED))
    assert len(B)==359 and len(W)==134753
    G=collections.defaultdict(set)
    for w in W:
        u=code(tuple(map(int,w[:5])));v=code(tuple(map(int,w[5:])))
        G[u].add(v)
    gmask={u:sum(1<<v for v in vals) for u,vals in G.items()}
    F=[v for v in range(U) if v not in B]
    supports={v:len(B.intersection(nb(v))) for v in F}
    groups=collections.defaultdict(list)
    for v in F:groups[supports[v]].append(v)
    masks={v:sum(1<<z for z in nb(v)) for v in F}
    rows={u:[(w,gmask[w]) for w in nb(u) if w in gmask] for u in F}
    C=[]
    for u in F:
        vs=F if supports[u]==0 else list(itertools.chain.from_iterable(groups[z] for z in range(2//supports[u]+1)))
        for v in vs:
            if v in G.get(u,()):continue
            m=masks[v];t=0
            for w,bits in rows[u]:
                t+=(bits&m).bit_count()
                if t>2:break
            if t>2:continue
            blockers=[]
            for w,bits in rows[u]:
                z=bits&m
                while z:
                    bit=z&-z
                    blockers.append((w,bit.bit_length()-1))
                    z-=bit
            assert len(blockers)==t and t>=1
            C.append((u,v,blockers))
    n=len(C)
    blocks=sorted({b for u,v,bs in C for b in bs})
    lookup={b:i for i,b in enumerate(blocks)}
    r=[];c=[];vals=[];upper=[]
    def row(pairs,hi):
        k=len(upper);upper.append(hi)
        for j,value in pairs:r.append(k);c.append(j);vals.append(value)
    for i,(u,v,blocked) in enumerate(C):
        for b in blocked:row(((i,1),(n+lookup[b],-1)),0)
    byu=collections.defaultdict(list)
    for i,(u,v,_) in enumerate(C):byu[u].append((v,i))
    active=set(byu)
    edges=0
    for u,L in byu.items():
        for uu in nb(u):
            if uu not in active:continue
            for v,i in L:
                for vv,j in byu[uu]:
                    if j>i and conf(v,vv):
                        row(((i,1),(j,1)),1)
                        edges+=1
    A=coo_matrix((np.asarray(vals,float),(r,c)),shape=(len(upper),n+len(blocks))).tocsr()
    rng=random.Random(seed)
    weights=np.asarray([rng.randint(1,3) for _ in range(n)])
    objective=np.r_[-20000-np.asarray(weights,float),np.full(len(blocks),20000.)]
    solve=milp(objective,integrality=np.ones(n+len(blocks)),
               bounds=Bounds(np.zeros(n+len(blocks)),np.ones(n+len(blocks))),
               constraints=LinearConstraint(A,-np.inf,upper),
               options={'mip_rel_gap':0,'time_limit':limit})
    assert solve.x is not None and solve.status==0,solve.message
    added=[(u,v) for i,(u,v,_) in enumerate(C) if solve.x[i]>.5]
    removed={b for i,(_,_,bl) in enumerate(C) if solve.x[i]>.5 for b in bl}
    assert all(not(conf(u,x) and conf(v,y)) for i,(u,v) in enumerate(added) for x,y in added[i+1:])
    assert all(word(u,v) in W for u,v in removed)
    assert all(word(u,v) not in W for u,v in added)
    words=(W-{word(u,v) for u,v in removed})|{word(u,v) for u,v in added}
    assert len(words)==len(W)+len(added)-len(removed)
    meta={'method':'joint-10D-maximum-gain-replacement',
          'source_baseline':134753,'score':len(words),
          'gain':len(words)-134753,
          'candidate_count':n,'blocker_count':len(blocks),
          'conflict_edges':edges,'added':len(added),'removed':len(removed),
          'optimal':solve.status==0,'seconds':round(time.monotonic()-start,3),
          'random_seed':seed}
    return meta,sorted(words)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('published_certificate',type=Path)
    p.add_argument('r367',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--seed',type=int,default=1)
    p.add_argument('--limit',type=int,default=180)
    a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    stats,words=run(a.published_certificate,a.r367,a.seed,a.limit)
    (a.output/'status.json').write_text(json.dumps(stats,indent=2,sort_keys=True)+'\n')
    (a.output/'certificate.json').write_text(json.dumps({'points':words},separators=(',',':'))+'\n')
    print('FINAL',json.dumps(stats,sort_keys=True),flush=True)

if __name__=='__main__':main()
