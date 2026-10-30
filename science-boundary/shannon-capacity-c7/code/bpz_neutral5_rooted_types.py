#!/usr/bin/env python3
"""Exact rooted-isomorphism census of the 2003 neutral induced-C5 k=5 pools."""
from __future__ import annotations
import argparse,itertools,json,sys
from collections import defaultdict,deque,Counter
from pathlib import Path

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
        b=mask&-mask;i=b.bit_length()-1
        dfs(mask^b,d);dfs(mask&compat[i],d+1)
    dfs((1<<n)-1,0)
    c5=False
    for sub in itertools.combinations(range(n),5):
        mask=sum(1<<i for i in sub)
        if all((conf[i]&mask).bit_count()==2 for i in sub):c5=True;break
    return best,c5

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    import networkx as nx
    root=a.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import load_base  # type: ignore
    p=root/'data'/'base_c7.json';raw=json.loads(p.read_text());base,_t,_e,ax=load_base(p)
    if not all(ax.values()):raise RuntimeError({k:v for k,v in ax.items() if not v})
    ring=base.ring;I=set(map(int,raw['I0']));R={int(x) for x,_ in raw['private_pairs']};B=I-R
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
    def pool(C):
        out=[]
        for r in range(1,6):
            for s in itertools.combinations(C,r):out.extend(groups.get(tuple(s),()))
        return tuple(sorted(set(out)))
    cases=[];six=[]
    for C in sorted(tuple(sorted(s)) for s in seen if len(s)==5):
        P=pool(C);al,c5=alpha_c5(P)
        if al>=6:six.append((C,al))
        elif al==5 and c5:cases.append((C,P))
    if six!=[((1644,13347,13600,13692,14040),6)] or len(cases)!=2003:raise RuntimeError(('self-check',len(cases),six))
    nm=nx.algorithms.isomorphism.categorical_node_match('root',False)
    buckets=defaultdict(list)
    for C,P in cases:
        g=nx.Graph();cs=set(C)
        for i,z in enumerate(P):g.add_node(i,root=(z in cs))
        for i in range(len(P)):
            for j in range(i+1,len(P)):
                if conflict5(P[i],P[j]):g.add_edge(i,j)
        h=nx.weisfeiler_lehman_graph_hash(g,node_attr='root',iterations=4)
        placed=False
        for t in buckets[h]:
            if nx.is_isomorphic(g,t['graph'],node_match=nm):t['count']+=1;t['examples'].append((C,P));placed=True;break
        if not placed:buckets[h].append({'graph':g,'count':1,'examples':[(C,P)]})
    types=[]
    for h,arr in buckets.items():
        for t in arr:
            C,P=t['examples'][0];types.append({'hash':h,'count':t['count'],'owners':list(C),'pool':list(P),'pool_size':len(P),'edges':t['graph'].number_of_edges()})
    types.sort(key=lambda x:(-x['count'],-x['pool_size'],x['owners']))
    out={'method':'exact-rooted-isomorphism-neutral5-c5','cases':len(cases),'rooted_types':len(types),'multiplicity_histogram':{str(k):v for k,v in sorted(Counter(t['count'] for t in types).items())},'types':types}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='types'},sort_keys=True))
if __name__=='__main__':main()
