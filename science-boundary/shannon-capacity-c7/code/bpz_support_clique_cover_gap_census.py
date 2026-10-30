#!/usr/bin/env python3
"""Exact clique-cover-gap census for connected k-owner BPZ support graphs.

For C subset B define Y_C={z: empty != N[z] cap B subseteq C}.  A graph with
alpha(Y_C)=|C| but clique-cover(Y_C)>|C| is a qualitatively stronger neutral
object than merely containing an induced odd hole: it cannot be partitioned
into |C| cliques, so the elementary product bound alpha(Y_C x H)<=|C|alpha(H)
no longer closes strong-product amplification.

This script enumerates every connected owner set of requested size k in the
observed support hypergraph, reconstructs Y_C exactly, first tests whether its
conflict graph is coverable by k cliques (equiv. complement k-colorable), and
only for cover-gap cases computes alpha exactly.  k=5 is a hard self-check:
121192 connected sets, exactly one alpha6 raw defect, and every alpha5 neutral
induced-C5 type must still be 5-clique-coverable.
"""
from __future__ import annotations
import argparse,itertools,json,multiprocessing as mp,os,sys
from collections import Counter,defaultdict,deque
from pathlib import Path
G={}
def init_worker(g):
    global G;G=g

def conflict5(a,b):
    if a==b:return True
    for _ in range(5):
        x=a%7;y=b%7;a//=7;b//=7
        if (x-y)%7 not in (0,1,6):return False
    return True

def graph_masks(pool):
    v=list(pool);n=len(v);adj=[0]*n
    for i in range(n):
        for j in range(i+1,n):
            if conflict5(v[i],v[j]):adj[i]|=1<<j;adj[j]|=1<<i
    return adj

def k_clique_coverable(adj,k):
    # k-colorability of complement via exact DSATUR.
    n=len(adj);full=(1<<n)-1;cadj=[full^(1<<i)^adj[i] for i in range(n)]
    color=[-1]*n;sat=[0]*n;deg=[m.bit_count() for m in cadj]
    def rec(done,maxc):
        if done==n:return True
        v=-1;bs=-1;bd=-1
        for i in range(n):
            if color[i]<0:
                s=sat[i].bit_count()
                if s>bs or (s==bs and deg[i]>bd):v=i;bs=s;bd=deg[i]
        forb=sat[v];limit=min(k,maxc+2)
        for c in range(limit):
            if (forb>>c)&1:continue
            color[v]=c;changed=[];m=cadj[v]
            while m:
                b=m&-m;m-=b;u=b.bit_length()-1
                if color[u]<0 and not ((sat[u]>>c)&1):sat[u]|=1<<c;changed.append(u)
            if rec(done+1,max(maxc,c)):return True
            for u in changed:sat[u]&=~(1<<c)
            color[v]=-1
        return False
    return rec(0,-1)

def alpha_exact(adj):
    n=len(adj);full=(1<<n)-1;compat=[full^(1<<i)^adj[i] for i in range(n)];best=0
    def dfs(mask,d):
        nonlocal best
        if d+mask.bit_count()<=best:return
        if not mask:best=max(best,d);return
        # choose max conflict degree in remaining graph
        mm=mask;v=(mm&-mm).bit_length()-1;bd=-1
        while mm:
            b=mm&-mm;mm-=b;i=b.bit_length()-1;z=(adj[i]&mask).bit_count()
            if z>bd:bd=z;v=i
        dfs(mask&~(1<<v),d)
        dfs(mask&compat[v],d+1)
    dfs(full,0);return best

def worker(C):
    C=tuple(C);pool=[]
    for r in range(1,len(C)+1):
        for s in itertools.combinations(C,r):pool.extend(G['groups'].get(tuple(s),()))
    pool=tuple(sorted(set(pool)));adj=graph_masks(pool)
    cover=k_clique_coverable(adj,len(C))
    if cover:return {'owners':list(C),'pool_size':len(pool),'cover_le_k':True}
    al=alpha_exact(adj)
    return {'owners':list(C),'pool_size':len(pool),'cover_le_k':False,'alpha':al,'gap':(len(C)-al if al<=len(C) else None),'pool':list(pool)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--k',type=int,required=True);ap.add_argument('--workers',type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args();k=a.k
    if k<2 or k>8:raise SystemExit('k 2..8')
    root=a.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import load_base  # type: ignore
    p=root/'data'/'base_c7.json';raw=json.loads(p.read_text());base,_t,_e,ax=load_base(p)
    if not all(ax.values()):raise RuntimeError({x:y for x,y in ax.items() if not y})
    ring=base.ring;I=set(map(int,raw['I0']));R={int(x) for x,_ in raw['private_pairs']};B=I-R;groups=defaultdict(list)
    for z in range(ring.n):
        S=tuple(sorted(ring.NB[z]&B))
        if S and len(S)<=k:groups[S].append(z)
    # connected-state expansion using observed support hyperedges up to k
    edges=[frozenset(s) for s in groups if 2<=len(s)<=k];inc=defaultdict(list)
    for e in edges:
        for u in e:inc[u].append(e)
    seen=set(edges);q=deque(edges)
    while q:
        S=q.popleft()
        if len(S)>=k:continue
        es=set()
        for u in S:es.update(inc[u])
        for e in es:
            U=S|e
            if len(U)<=k and U not in seen:seen.add(U);q.append(U)
    finals=sorted(tuple(sorted(s)) for s in seen if len(s)==k)
    global G;G={'groups':{tuple(x):tuple(v) for x,v in groups.items()}}
    ctx=mp.get_context('fork')
    with ctx.Pool(a.workers,initializer=init_worker,initargs=(G,)) as P:rows=list(P.imap_unordered(worker,finals,chunksize=32))
    gaps=[r for r in rows if not r['cover_le_k']];ac=Counter(r.get('alpha') for r in gaps);ph=Counter(r['pool_size'] for r in rows)
    out={'method':'exact-connected-support-clique-cover-gap','k':k,'connected_sets':len(finals),'cover_gap_count':len(gaps),'gap_alpha_histogram':{str(x):y for x,y in sorted(ac.items(),key=lambda z:str(z[0]))},'pool_size_histogram':{str(x):y for x,y in sorted(ph.items())},'max_pool':max((r['pool_size'] for r in rows),default=0),'cover_gap_cases':sorted(gaps,key=lambda r:(r.get('alpha',999),-r['pool_size'],r['owners']))}
    if k==5:
        # Known raw defect is alpha6 and therefore necessarily cover-gap relative to 5.
        known=[r for r in gaps if r.get('alpha')==6]
        if len(finals)!=121192 or len(known)!=1 or tuple(known[0]['owners'])!=(1644,13347,13600,13692,14040):raise RuntimeError(('k5 self-check',len(finals),known[:5],len(gaps)))
        neutral=[r for r in gaps if r.get('alpha')==5]
        if neutral:raise RuntimeError(('unexpected neutral k5 cover gap',neutral[:5],len(neutral)))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({x:y for x,y in out.items() if x!='cover_gap_cases'},sort_keys=True));print('gap_cases',len(gaps))
if __name__=='__main__':main()
