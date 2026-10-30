#!/usr/bin/env python3
"""Exact prize MaxSAT on the highest-blocker-slack nonperfect4 x neutral5 products.

Rebuilds the exact 68 x 2003 support-product family, ranks cases by the very
cheap optimistic blocker-union slack |T|-|N_I(T)|, and solves the top K cases
with full candidate-conflict clauses and exact baseline blocker activation cost.
Any positive objective is an actual improvement of the 134753 record and is
materialized for the upstream Few Shots verifier.
"""
from __future__ import annotations
import argparse,itertools,json,multiprocessing as mp,os,sys,heapq
from collections import defaultdict,deque
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
        b=mask&-mask;i=b.bit_length()-1;dfs(mask^b,d);dfs(mask&compat[i],d+1)
    dfs((1<<n)-1,0)
    c5=False
    for sub in itertools.combinations(range(n),5):
        mask=sum(1<<i for i in sub)
        if all((conf[i]&mask).bit_count()==2 for i in sub):c5=True;break
    return best,c5

def nonperfect(pool):
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
            while m:b=m&-m;m-=b;seen|=b;st.append(b.bit_length()-1)
        return (seen&mask)==mask
    for k in range(5,n+1,2):
        for sub in itertools.combinations(range(n),k):
            if cyc(sub,adj) or cyc(sub,cadj):return True
    return False

def rank_ai(ai):
    A,YA=G['four'][ai];cache={};out=[]
    def blockers(p):
        q=cache.get(p)
        if q is not None:return q
        u,v=p;bs=[]
        for x,y in RECORD_CODE:
            for a in G['nbm'][x][u]:
                for b in G['nbm'][y][v]:bs.append(G['owner'][(a,b)])
        q=tuple(bs);cache[p]=q;return q
    for ci,(C,YC) in enumerate(G['five']):
        cand=[(x,y) for x in YA for y in YC if (x,y) not in G['baseline']]
        un=set()
        for p in cand:un.update(blockers(p))
        slack=len(cand)-len(un)
        out.append((slack,len(cand),ai,ci))
    return out

def solve_one(item):
    slack,_n,ai,ci=item;A,YA=G['four'][ai];C,YC=G['five'][ci]
    cand=sorted((x,y) for x in YA for y in YC if (x,y) not in G['baseline']);n=len(cand)
    from pysat.formula import WCNF
    from pysat.examples.rc2 import RC2
    w=WCNF();dv={};blocker_edges=0
    def bvar(b):
        if b not in dv:dv[b]=n+len(dv)+1
        return dv[b]
    for i,(u,v) in enumerate(cand):
        for x,y in RECORD_CODE:
            for a in G['nbm'][x][u]:
                for b in G['nbm'][y][v]:w.append([-(i+1),bvar(G['owner'][(a,b)])]);blocker_edges+=1
    conflicts=0
    for i,(x,y) in enumerate(cand):
        for j in range(i+1,n):
            u,v=cand[j]
            if conflict5(x,u) and conflict5(y,v):w.append([-(i+1),-(j+1)]);conflicts+=1
    for i in range(n):w.append([i+1],weight=1)
    for v in dv.values():w.append([-v],weight=1)
    with RC2(w,solver='g4',adapt=True,exhaust=True,incr=False) as rc2:model=rc2.compute();cost=rc2.cost
    pos={z for z in model if z>0};sel=[cand[i] for i in range(n) if i+1 in pos];deleted=[b for b,v in dv.items() if v in pos];gain=n-cost
    r={'A':list(A),'C':list(C),'YA':len(YA),'YC':len(YC),'candidates':n,'rank_slack':slack,'conflicts':conflicts,'blocker_edges':blocker_edges,'touched_blockers':len(dv),'gain':gain,'selected':len(sel),'deleted':len(deleted)}
    if gain>0:r['selected_vertices']=[list(p) for p in sel];r['deleted_ids']=deleted
    return r

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('shot_dir',type=Path);ap.add_argument('--top',type=int,default=1000);ap.add_argument('--workers',type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args()
    root=a.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import load_base  # type: ignore
    p=root/'data'/'base_c7.json';raw=json.loads(p.read_text());base,_t,_e,ax=load_base(p)
    if not all(ax.values()):raise RuntimeError({k:v for k,v in ax.items() if not v})
    ring=base.ring;I=set(map(int,raw['I0']));R={int(x) for x,_ in raw['private_pairs']};B=I-R;groups=defaultdict(list)
    for z in range(ring.n):
        S=tuple(sorted(ring.NB[z]&B))
        if S and len(S)<=5:groups[S].append(z)
    def pool(C):
        out=[]
        for r in range(1,len(C)+1):
            for s in itertools.combinations(C,r):out.extend(groups.get(tuple(s),()))
        return tuple(sorted(set(out)))
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
    four=[];five=[];six=[]
    for S in sorted(tuple(sorted(s)) for s in seen if len(s)==4):
        P=pool(S)
        if nonperfect(P):four.append((S,P))
    for S in sorted(tuple(sorted(s)) for s in seen if len(s)==5):
        P=pool(S);al,c5=alpha_c5(P)
        if al>=6:six.append((S,al))
        elif al==5 and c5:five.append((S,P))
    if len(four)!=68 or len(five)!=2003 or six!=[((1644,13347,13600,13692,14040),6)]:raise RuntimeError(('self-check',len(four),len(five),six))
    fam={'B':set(base.B.elements),'N':set(base.X0.elements),'A':set(base.XV.elements),'D':set(base.XH.elements),'O':set(base.R.elements),'H':set(base.PH.elements),'V':set(base.PV.elements)}
    owner={};op=[]
    for x,y in RECORD_CODE:
        for u in sorted(fam[x]):
            for v in sorted(fam[y]):owner[(u,v)]=len(op);op.append((u,v))
    if len(owner)!=134753:raise RuntimeError(('record',len(owner)))
    nbm={lab:[None]*ring.n for lab in LABELS}
    for lab in LABELS:
        F=fam[lab]
        for z in range(ring.n):nbm[lab][z]=tuple(q for q in ring.NB[z] if q in F)
    global G;G={'four':four,'five':five,'baseline':set(owner),'owner':owner,'nbm':nbm}
    ctx=mp.get_context('fork')
    with ctx.Pool(a.workers) as P:ranked=[x for row in P.imap_unordered(rank_ai,range(68),chunksize=1) for x in row]
    ranked=heapq.nlargest(a.top,ranked)
    with ctx.Pool(a.workers) as P:results=list(P.imap_unordered(solve_one,ranked,chunksize=1))
    results.sort(key=lambda r:(-r['gain'],-r['rank_slack'],-r['candidates'],r['A'],r['C']));best=results[0]
    out={'method':'exact-prize-top-slack-nonperfect4-neutral5','family_size':68*2003,'top_solved':len(results),'best':best,'positive_count':sum(r['gain']>0 for r in results),'results':results}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    if best['gain']>0:
        sel={tuple(p) for p in best['selected_vertices']};oplist=op;deleted={oplist[i] for i in best['deleted_ids']};cand=(set(owner)-deleted)|sel
        if len(cand)!=134753+best['gain']:raise RuntimeError(('size',len(cand),best['gain']))
        a.shot_dir.mkdir(parents=True,exist_ok=True)
        def enc(p):return ''.join(str(d) for d in (ring.decode(p[0])+ring.decode(p[1])))
        pts=sorted(enc(p) for p in cand);(a.shot_dir/'certificate.json').write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');(a.shot_dir/'metadata.json').write_text(json.dumps(best,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='results'},sort_keys=True))
if __name__=='__main__':main()
