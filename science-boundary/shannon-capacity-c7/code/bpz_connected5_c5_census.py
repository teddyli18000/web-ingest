#!/usr/bin/env python3
"""Census connected five-owner support graphs against pinned BPZ B.

Enumerates every size-5 owner set connected in the observed support hypergraph,
reconstructs the complete Y_C pool, computes alpha(Y_C) exactly, and flags an
induced C5.  The known unique alpha=6 defect is used as a hard self-check.

The purpose is not another radius search: alpha=5 C5-active graphs are neutral
in one dimension but are candidates for strong-product supermultiplicativity.
"""
from __future__ import annotations
import argparse, itertools, json, multiprocessing as mp, os, sys
from collections import Counter, defaultdict, deque
from pathlib import Path

KNOWN6=(1644,13347,13600,13692,14040)
G={}
def init_worker(g):
    global G;G=g

def conflict5(a:int,b:int)->bool:
    if a==b:return True
    for _ in range(5):
        x=a%7;y=b%7;a//=7;b//=7;d=(x-y)%7
        if d not in (0,1,6):return False
    return True

def alpha_and_c5(pool):
    v=list(pool);n=len(v); compat=[0]*n;conf=[0]*n
    for i in range(n):
        for j in range(i+1,n):
            if conflict5(v[i],v[j]):conf[i]|=1<<j;conf[j]|=1<<i
            else:compat[i]|=1<<j;compat[j]|=1<<i
    best=0
    def dfs(mask,d):
        nonlocal best
        if d+mask.bit_count()<=best:return
        if not mask:best=max(best,d);return
        # branch on highest conflict degree in remaining graph
        mm=mask;pick=(mm&-mm).bit_length()-1;bd=-1
        while mm:
            b=mm&-mm;i=b.bit_length()-1;deg=(conf[i]&mask).bit_count()
            if deg>bd:bd=deg;pick=i
            mm-=b
        dfs(mask&~(1<<pick),d)
        dfs(mask&compat[pick],d+1)
    dfs((1<<n)-1,0)
    c5=False
    if n>=5:
        for sub in itertools.combinations(range(n),5):
            mask=sum(1<<i for i in sub);ok=True
            for i in sub:
                if (conf[i]&mask).bit_count()!=2:ok=False;break
            if ok:c5=True;break
    return best,c5

def worker(C):
    C=tuple(C);pool=[]
    for r in range(1,6):
        for sub in itertools.combinations(C,r):pool.extend(G['groups'].get(sub,()))
    pool=tuple(sorted(set(pool)))
    a,c5=alpha_and_c5(pool)
    outs=[z for z in pool if z not in C]
    cols=Counter(G['killer'].get(z) for z in outs if G['killer'].get(z) is not None)
    return {'owners':list(C),'pool_size':len(pool),'outside':len(outs),'alpha':a,'induced_c5':c5,
            'killer_free_outside':sum(G['killer'].get(z) is None for z in outs),
            'distinct_killers':len(cols),'killer_histogram':{str(k):v for k,v in sorted(cols.items())},
            'pool':list(pool) if c5 else []}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--workers',type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args()
    root=a.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import load_base  # type: ignore
    p=root/'data'/'base_c7.json';raw=json.loads(p.read_text());base,_t,_e,ax=load_base(p)
    if not all(ax.values()):raise RuntimeError({k:v for k,v in ax.items() if not v})
    ring=base.ring;I=set(map(int,raw['I0']));pairs=[tuple(map(int,q)) for q in raw['private_pairs']];R={x for x,_ in pairs};B=I-R
    groups=defaultdict(list);killer={}
    for z in range(ring.n):
        S=tuple(sorted(ring.NB[z]&B))
        if S and len(S)<=5:groups[S].append(z)
        ks=[i for i,(u,v) in enumerate(pairs) if u in ring.NB[z] and v in ring.NB[z]]
        if len(ks)>1:raise RuntimeError(('multi-killer',z,ks))
        killer[z]=ks[0] if ks else None
    # Exact connected hypergraph state expansion to size 5.
    edges=[frozenset(s) for s in groups if 2<=len(s)<=5]
    inc=defaultdict(list)
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
    g={'groups':{tuple(k):tuple(v) for k,v in groups.items()},'killer':killer}
    ctx=mp.get_context('fork')
    with ctx.Pool(a.workers,initializer=init_worker,initargs=(g,)) as P:rows=list(P.imap_unordered(worker,finals,chunksize=32))
    rows.sort(key=lambda r:(-r['alpha'],-int(r['induced_c5']),-r['pool_size'],r['owners']))
    ah=Counter(r['alpha'] for r in rows);ps=Counter(r['pool_size'] for r in rows);c5=[r for r in rows if r['induced_c5']]
    six=[r for r in rows if r['alpha']>=6]
    if len(six)!=1 or tuple(six[0]['owners'])!=KNOWN6 or six[0]['alpha']!=6:raise RuntimeError(('alpha6 self-check',six[:10],len(six)))
    out={'method':'exact-connected5-support-census','connected5':len(finals),'alpha_histogram':{str(k):v for k,v in sorted(ah.items())},
         'pool_size_histogram':{str(k):v for k,v in sorted(ps.items())},'induced_c5_count':len(c5),
         'known_alpha6':six[0],
         'c5_cases':c5}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'connected5':len(finals),'alpha_histogram':out['alpha_histogram'],'induced_c5_count':len(c5),'max_pool':max(r['pool_size'] for r in rows),'c5_max_pool':max((r['pool_size'] for r in c5),default=0)},sort_keys=True))
if __name__=='__main__':main()
