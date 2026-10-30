#!/usr/bin/env python3
"""Exact Hall upper-bound screen for 68 nonperfect-4 x 2003 neutral-C5 products.

For each connected nonperfect four-owner support set A and each connected
five-owner support set C with alpha(Y_C)=5 and an induced C5, form the complete
new product universe

    T = (Y_A x Y_C) \ I,

where I is the pinned 134753-point BPZ record.  We deliberately IGNORE all
conflicts among candidates in T and ask only whether the candidate-to-baseline
blocker bipartite graph has positive Hall deficiency.

Because dropping candidate conflicts is a relaxation, Hall deficiency <= 0 is
a rigorous upper-bound exclusion for the true exchange problem.  Only Hall-
positive products need any later conflict-aware MaxSAT/MIS solve.
"""
from __future__ import annotations
import argparse,itertools,json,multiprocessing as mp,os,sys
from collections import defaultdict,deque,Counter
from pathlib import Path

LABELS=("B","N","A","D","O","H","V")
RECORD_CODE=(("B","B"),("N","O"),("A","H"),("D","V"),("O","N"),("H","D"),("V","A"))
G={}

def conflict5(a,b):
    if a==b:return True
    for _ in range(5):
        x=a%7;y=b%7;a//=7;b//=7;d=(x-y)%7
        if d not in (0,1,6):return False
    return True

def alpha_c5(pool):
    v=list(pool);n=len(v);compat=[0]*n;conf=[0]*n
    for i in range(n):
        for j in range(i+1,n):
            if conflict5(v[i],v[j]):conf[i]|=1<<j;conf[j]|=1<<i
            else:compat[i]|=1<<j;compat[j]|=1<<i
    best=0
    def dfs(mask,d):
        nonlocal best
        if d+mask.bit_count()<=best:return
        if not mask:best=max(best,d);return
        mm=mask;pick=(mm&-mm).bit_length()-1;bd=-1
        while mm:
            b=mm&-mm;i=b.bit_length()-1;deg=(conf[i]&mask).bit_count()
            if deg>bd:bd=deg;pick=i
            mm-=b
        dfs(mask&~(1<<pick),d);dfs(mask&compat[pick],d+1)
    dfs((1<<n)-1,0)
    c5=False
    for sub in itertools.combinations(range(n),5):
        mask=sum(1<<i for i in sub)
        if all((conf[i]&mask).bit_count()==2 for i in sub):c5=True;break
    return best,c5

def nonperfect(pool):
    # For the small four-owner pools exact SPGT recognition by odd holes/antiholes.
    v=list(pool);n=len(v);adj=[0]*n
    for i in range(n):
        for j in range(i+1,n):
            if conflict5(v[i],v[j]):adj[i]|=1<<j;adj[j]|=1<<i
    full=(1<<n)-1;cadj=[full^(1<<i)^adj[i] for i in range(n)]
    def cyc(sub,A):
        mask=sum(1<<i for i in sub)
        if not all((A[i]&mask).bit_count()==2 for i in sub):return False
        seen=1<<sub[0];st=[sub[0]]
        while st:
            u=st.pop();m=A[u]&mask&~seen
            while m:
                b=m&-m;m-=b;seen|=b;st.append(b.bit_length()-1)
        return (seen&mask)==mask
    for k in range(5,n+1,2):
        for sub in itertools.combinations(range(n),k):
            if cyc(sub,adj) or cyc(sub,cadj):return True
    return False

def hk_deficiency(adj):
    n=len(adj)
    # Compress right labels for this case.
    rights={b for a in adj for b in a}
    if len(rights)<n:return n-len(rights)  # lower bound already positive; exact not needed for screening sign
    rid={b:i for i,b in enumerate(rights)};A=[[rid[b] for b in a] for a in adj];m=len(rid)
    ml=[-1]*n;mr=[-1]*m;dist=[0]*n
    INF=10**9
    def bfs():
        q=deque();found=False
        for u in range(n):
            if ml[u]<0:dist[u]=0;q.append(u)
            else:dist[u]=INF
        while q:
            u=q.popleft()
            for v in A[u]:
                w=mr[v]
                if w<0:found=True
                elif dist[w]==INF:dist[w]=dist[u]+1;q.append(w)
        return found
    def dfs(u):
        for v in A[u]:
            w=mr[v]
            if w<0 or (dist[w]==dist[u]+1 and dfs(w)):
                ml[u]=v;mr[v]=u;return True
        dist[u]=INF;return False
    mat=0
    while bfs():
        for u in range(n):
            if ml[u]<0 and dfs(u):mat+=1
    return n-mat

def screen_ai(ai):
    A,YA=G['four'][ai];cache={};positive=[];mx=0
    def blockers(p):
        q=cache.get(p)
        if q is not None:return q
        u,v=p;out=[]
        for x,y in RECORD_CODE:
            for a in G['nbm'][x][u]:
                for b in G['nbm'][y][v]:out.append(G['owner'][(a,b)])
        q=tuple(out);cache[p]=q;return q
    for C,YC in G['five']:
        cand=[(x,y) for x in YA for y in YC if (x,y) not in G['baseline']]
        adj=[blockers(p) for p in cand]
        d=hk_deficiency(adj);mx=max(mx,d)
        if d>0:positive.append({'A':list(A),'C':list(C),'YA':len(YA),'YC':len(YC),'candidates':len(cand),'hall_deficiency_lower_or_exact':d})
    return {'ai':ai,'tested':len(G['five']),'max_deficiency':mx,'positive':positive,'cache':len(cache)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--workers',type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args()
    root=a.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import load_base  # type: ignore
    p=root/'data'/'base_c7.json';raw=json.loads(p.read_text());base,_t,_e,ax=load_base(p)
    if not all(ax.values()):raise RuntimeError({k:v for k,v in ax.items() if not v})
    ring=base.ring;I=set(map(int,raw['I0']));pairs=[tuple(map(int,q)) for q in raw['private_pairs']];R={x for x,_ in pairs};B=I-R
    groups=defaultdict(list)
    for z in range(ring.n):
        S=tuple(sorted(ring.NB[z]&B))
        if S and len(S)<=5:groups[S].append(z)
    def pool(C):
        out=[]
        for r in range(1,len(C)+1):
            for s in itertools.combinations(C,r):out.extend(groups.get(tuple(s),()))
        return tuple(sorted(set(out)))
    # Connected owner sets of sizes 4 and 5 from observed hyperedges.
    edges=[frozenset(s) for s in groups if 2<=len(s)<=5];inc=defaultdict(list)
    for e in edges:
        for u in e:inc[u].append(e)
    seen=set(edges);q=deque(edges)
    while q:
        S=q.popleft()
        if len(S)>=5:continue
        es=set()
        for u in S:es.update(inc[u])
        for e in es:
            U=S|e
            if len(U)<=5 and U not in seen:seen.add(U);q.append(U)
    fours=[]
    for S in sorted(tuple(sorted(s)) for s in seen if len(s)==4):
        P=pool(S)
        if nonperfect(P):fours.append((S,P))
    if len(fours)!=68:raise RuntimeError(('four self-check',len(fours)))
    fives=[];six=[]
    for S in sorted(tuple(sorted(s)) for s in seen if len(s)==5):
        P=pool(S);al,c5=alpha_c5(P)
        if al>=6:six.append((S,al))
        elif al==5 and c5:fives.append((S,P))
    if six!=[((1644,13347,13600,13692,14040),6)] or len(fives)!=2003:raise RuntimeError(('five self-check',len(fives),six))
    fam={'B':set(base.B.elements),'N':set(base.X0.elements),'A':set(base.XV.elements),'D':set(base.XH.elements),'O':set(base.R.elements),'H':set(base.PH.elements),'V':set(base.PV.elements)}
    owner={};op=[]
    for x,y in RECORD_CODE:
        for u in sorted(fam[x]):
            for v in sorted(fam[y]):
                if (u,v) in owner:raise RuntimeError(('record overlap',(u,v)))
                owner[(u,v)]=len(op);op.append((u,v))
    if len(op)!=134753:raise RuntimeError(('score drift',len(op)))
    nbm={lab:[None]*ring.n for lab in LABELS}
    for lab in LABELS:
        F=fam[lab]
        for z in range(ring.n):nbm[lab][z]=tuple(q for q in ring.NB[z] if q in F)
    global G;G={'four':fours,'five':fives,'baseline':set(owner),'owner':owner,'nbm':nbm}
    ctx=mp.get_context('fork')
    with ctx.Pool(a.workers) as P:rows=list(P.imap_unordered(screen_ai,range(68),chunksize=1))
    pos=[x for r in rows for x in r['positive']];mx=max(r['max_deficiency'] for r in rows);tested=sum(r['tested'] for r in rows)
    out={'method':'hall-relaxation-nonperfect4-x-neutral-c5-five','four_cases':68,'five_cases':2003,'products_tested':tested,'max_hall_deficiency':mx,'hall_positive_count':len(pos),'hall_positive':pos,
         'worker_cache_sizes':sorted(r['cache'] for r in rows)}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('hall_positive','worker_cache_sizes')},sort_keys=True))
if __name__=='__main__':main()
