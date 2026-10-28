#!/usr/bin/env python3
"""Search pairs of disjoint alternating planar faces that jointly restore a tour."""
import argparse, gzip, json, importlib.util, os, time
from pathlib import Path
import networkx as nx

def norm(a,b):
    return (a,b) if a<b else (b,a)

def components_for_pair(t,position,rec_a,rec_b):
    removed=rec_a[1]+rec_b[1]
    if len(set(removed))<4:return None
    vertices={x for e in removed for x in e}
    if len(vertices)!=8:return None
    ps=sorted(position[e] for e in removed)
    n=len(t)
    segment={}
    for k,p in enumerate(ps):
        segment[t[(p+1)%n]]=k
        segment[t[p]]=(k-1)%4
    added=rec_a[2]+rec_b[2]
    parent=[0,1,2,3]
    def find(x):
        while parent[x]!=x:x=parent[x]
        return x
    for u,v in added:
        a,b=find(segment[u]),find(segment[v])
        parent[a]=b
    return len({find(i) for i in range(4)})

def make_tour(n,base,rec_a,rec_b):
    adj=[[] for _ in range(n)]
    for a,b in base:
        adj[a].append(b)
        adj[b].append(a)
    for rec in (rec_a,rec_b):
        for a,b in rec[1]:
            adj[a].remove(b)
            adj[b].remove(a)
        for a,b in rec[2]:
            adj[a].append(b)
            adj[b].append(a)
    assert all(len(x)==2 for x in adj)
    tour=[]
    prev=-1
    curr=0
    for _ in range(n):
        tour.append(curr)
        a,b=adj[curr]
        other=a if a!=prev else b
        prev,curr=curr,other
    assert curr==0 and len(set(tour))==n
    return [x+1 for x in tour]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--edges',required=True)
    p.add_argument('--baseline',required=True)
    p.add_argument('--report',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--minimum-face-gain',type=int,default=-16)
    args=p.parse_args()
    started=time.monotonic()
    t=[x-1 for x in json.loads(Path(args.baseline).read_text())['tour']]
    n=len(t)
    assert n==100000
    base={norm(t[i],t[(i+1)%n]) for i in range(n)}
    positions={norm(t[i],t[(i+1)%n]):i for i in range(n)}
    with gzip.open(args.edges,'rt') as f:
        header=list(map(int,f.readline().split()))
        raw=[tuple(map(int,s.split())) for s in f if s.strip()]
    assert header==[n,len(raw)]
    offset=0 if min(min(a,b) for a,b,w in raw)==0 else 1
    edges={norm(a-offset,b-offset):w for a,b,w in raw}
    assert len(edges)==len(raw) and base <= edges.keys()
    g=nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(edges)
    planar,embedding=nx.check_planarity(g)
    assert planar
    visited=set()
    records=[]
    face_count=0
    for a,b in g.edges():
        for u,v in ((a,b),(b,a)):
            if (u,v) in visited:
                continue
            vs=embedding.traverse_face(u,v)
            face_count+=1
            L=len(vs)
            visited.update((vs[i],vs[(i+1)%L]) for i in range(L))
            if L!=4 or len(set(vs))!=4:
                continue
            boundary=[norm(vs[i],vs[(i+1)%L]) for i in range(L)]
            flags=[e in base for e in boundary]
            if any(flags[i]==flags[(i+1)%4] for i in range(4)):
                continue
            removed=tuple(e for e,f in zip(boundary,flags) if f)
            added=tuple(e for e,f in zip(boundary,flags) if not f)
            gain=sum(edges[e] for e in removed)-sum(edges[e] for e in added)
            if gain>=args.minimum_face_gain:
                records.append((gain,removed,added))
    records.sort(key=lambda r:-r[0])
    positive=[r for r in records if r[0]>0]
    checked=0
    valid=0
    best=None
    for a in positive:
        for b in records:
            if b[0]+a[0]<=0:
                break
            if a is b:
                continue
            checked+=1
            cc=components_for_pair(t,positions,a,b)
            if cc==1:
                valid+=1
                score_gain=a[0]+b[0]
                if best is None or score_gain>best[0]:
                    best=(score_gain,a,b)
    result={'baseline':5757191,'planar_faces':face_count,
            'candidate_faces':len(records),'positive_faces':len(positive),
            'tested_ordered_pairs':checked,'connected_improving_pairs':valid,
            'best_pair_gain':best[0] if best else None,
            'elapsed_seconds':round(time.monotonic()-started,2)}
    if best:
        tour=make_tour(n,base,best[1],best[2])
        target=5757191-best[0]
        spec=importlib.util.spec_from_file_location(
            'v',Path(os.environ['FEWSHOTS_ROOT'])/
            'problems/p010-mona-lisa-tsp/verify/verify.py')
        v=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(v)
        score=v.tour_length(tour)
        result.update({'exact_recomputed_score':score,'expected_score':target})
        assert score==target and score<5757191
        Path(args.output).parent.mkdir(parents=True,exist_ok=True)
        Path(args.output).write_text(json.dumps({'tour':tour},separators=(',',':')))
    Path(args.report).parent.mkdir(parents=True,exist_ok=True)
    Path(args.report).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)

if __name__=='__main__':
    main()
