#!/usr/bin/env python3
"""Exact audit of the 2003 neutral k=5 C5-containing support factors.

For every connected five-owner C with alpha(Y_C)=5 and an induced C5, enumerate
maximum independent 5-sets and lexicographically minimize:
  1. number of reused deleted owners in the 5-set;
  2. among equal owner reuse, number of distinct BPZ private-pair killer colors.

An owner-intersection-zero witness is a genuine outside-only 5->5 neutral move.
Low killer count is especially valuable when pairing such a neutral factor with
one of the irreducible k=6 6->7 factors: the raw rectangle has 5*7=35 new points
for 30 core deletions, leaving four terminal losses while still reaching 134754.
"""
from __future__ import annotations
import argparse,itertools,json,multiprocessing as mp,os,sys
from collections import Counter,defaultdict,deque
from pathlib import Path
G={}

def conflict5(a,b):
    if a==b:return True
    for _ in range(5):
        x,y=a%7,b%7;a//=7;b//=7
        if (x-y)%7 not in (0,1,6):return False
    return True

def init_worker(state):
    global G;G=state

def audit_case(C):
    C=tuple(C);pool=[]
    for r in range(1,6):
        for s in itertools.combinations(C,r):pool.extend(G['groups'].get(tuple(s),()))
    pool=tuple(sorted(set(pool)));n=len(pool);compat=[0]*n;conf=[0]*n
    for i in range(n):
        for j in range(i+1,n):
            if conflict5(pool[i],pool[j]):conf[i]|=1<<j;conf[j]|=1<<i
            else:compat[i]|=1<<j;compat[j]|=1<<i
    best_alpha=-1;best_owner=99;best_kill=99;best=[]
    def rec(mask,chosen,owner_hits,kmask):
        nonlocal best_alpha,best_owner,best_kill,best
        d=len(chosen);ub=d+mask.bit_count()
        if ub<best_alpha:return
        if ub==best_alpha and (owner_hits>best_owner or (owner_hits==best_owner and kmask.bit_count()>=best_kill)):return
        if not mask:
            kk=kmask.bit_count()
            if d>best_alpha or (d==best_alpha and (owner_hits<best_owner or (owner_hits==best_owner and kk<best_kill))):
                best_alpha=d;best_owner=owner_hits;best_kill=kk;best=[pool[i] for i in chosen]
            return
        mm=mask;pick=(mm&-mm).bit_length()-1;worst=-1
        while mm:
            b=mm&-mm;mm-=b;i=b.bit_length()-1;z=(conf[i]&mask).bit_count()
            if z>worst:worst=z;pick=i
        z=pool[pick]
        rec(mask&compat[pick],chosen+[pick],owner_hits+(z in C),kmask|G['killer'][z])
        rec(mask&~(1<<pick),chosen,owner_hits,kmask)
    rec((1<<n)-1,[],0,0)
    if best_alpha!=5:raise RuntimeError(('neutral alpha drift',C,best_alpha))
    return {'owners':list(C),'pool_size':n,'alpha':best_alpha,'min_owner_intersection':best_owner,'min_killer_colors_given_owner_min':best_kill,'witness':sorted(best)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--workers',type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args();root=a.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import load_base
    p=root/'data'/'base_c7.json';raw=json.loads(p.read_text());base,_t,_e,ax=load_base(p)
    if not all(ax.values()):raise RuntimeError(ax)
    ring=base.ring;I=set(map(int,raw['I0']));pairs=[tuple(map(int,p)) for p in raw['private_pairs']];R={x for x,_ in pairs};B=I-R
    groups=defaultdict(list)
    for z in range(ring.n):
        S=tuple(sorted(ring.NB[z]&B))
        if S and len(S)<=5:groups[S].append(z)
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
    finals=sorted(tuple(sorted(s)) for s in seen if len(s)==5)
    def pool(C):
        out=[]
        for r in range(1,6):
            for s in itertools.combinations(C,r):out.extend(groups.get(tuple(s),()))
        return tuple(sorted(set(out)))
    def alpha_c5(P):
        n=len(P);compat=[0]*n;conf=[0]*n;best=0
        for i in range(n):
            for j in range(i+1,n):
                if conflict5(P[i],P[j]):conf[i]|=1<<j;conf[j]|=1<<i
                else:compat[i]|=1<<j;compat[j]|=1<<i
        def dfs(mask,d):
            nonlocal best
            if d+mask.bit_count()<=best:return
            if not mask:best=max(best,d);return
            b=mask&-mask;i=b.bit_length()-1;dfs(mask&~b,d);dfs(mask&compat[i],d+1)
        dfs((1<<n)-1,0)
        c5=False
        if n>=5:
            for sub in itertools.combinations(range(n),5):
                m=sum(1<<i for i in sub)
                if all((conf[i]&m).bit_count()==2 for i in sub):c5=True;break
        return best,c5
    cases=[];six=[]
    for C in finals:
        P=pool(C);al,c5=alpha_c5(P)
        if al>=6:six.append((C,al))
        elif al==5 and c5:cases.append(C)
    if len(cases)!=2003 or six!=[((1644,13347,13600,13692,14040),6)]:raise RuntimeError(('self-check',len(cases),six))
    killer=[0]*ring.n
    for z in range(ring.n):
        m=0
        for i,(u,v) in enumerate(pairs):
            if u in ring.NB[z] and v in ring.NB[z]:m|=1<<i
        killer[z]=m
    state={'groups':{tuple(k):tuple(v) for k,v in groups.items()},'killer':killer};workers=max(1,min(a.workers,4));ctx=mp.get_context('fork')
    with ctx.Pool(workers,initializer=init_worker,initargs=(state,)) as P:rows=list(P.imap_unordered(audit_case,cases,chunksize=16))
    rows.sort(key=lambda r:(r['min_owner_intersection'],r['min_killer_colors_given_owner_min'],r['owners']));oh=Counter(r['min_owner_intersection'] for r in rows);kh=Counter(r['min_killer_colors_given_owner_min'] for r in rows if r['min_owner_intersection']==0);outside=[r for r in rows if r['min_owner_intersection']==0]
    out={'method':'exact-neutral5-maxset-owner-killer-audit','neutral_cases':len(rows),'outside_only_count':len(outside),'owner_intersection_histogram':{str(k):v for k,v in sorted(oh.items())},'outside_killer_histogram':{str(k):v for k,v in sorted(kh.items())},'best_outside':outside[:100],'rows':rows}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('rows','best_outside')},sort_keys=True));print('top',json.dumps(outside[:10],sort_keys=True))
if __name__=='__main__':main()
