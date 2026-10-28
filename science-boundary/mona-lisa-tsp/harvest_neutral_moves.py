#!/usr/bin/env python3
"""Harvest all nontrivial exact-neutral 4-edge exchanges from profitable face splits.

For each profitable alternating face in Cook et al.'s published planar reduction,
enumerate every sparse-graph 2-edge reconnect anywhere in the full instance.
Freeze a distinct neutral exchange per face if found. Any gain > 0 is written
as a full, independently verifiable p010 certificate, never only a claim.
"""
import argparse,gzip,importlib.util,json,os,time
from pathlib import Path
import networkx as nx

def e(a,b):return (a,b) if a<b else (b,a)
def switch(adj,removed,added):
    for a,b in removed:adj[a].remove(b);adj[b].remove(a)
    for a,b in added:adj[a].append(b);adj[b].append(a)
def components(adj):
    labels=bytearray(len(adj));sz=[]
    for start in range(len(adj)):
        if labels[start]:continue
        lab=len(sz)+1;u=start;prev=-1;count=0
        while not labels[u]:
            labels[u]=lab;count+=1
            a,b=adj[u];nxt=a if a!=prev else b
            prev,u=u,nxt
        assert u==start
        sz.append(count)
    return labels,sz
def reconstruct(adj):
    seen=bytearray(len(adj));u=0;prev=-1;t=[]
    while not seen[u]:
        seen[u]=1;t.append(u+1)
        a,b=adj[u];nxt=a if a!=prev else b
        prev,u=u,nxt
    assert u==0 and len(t)==len(adj)
    return t
def main():
    p=argparse.ArgumentParser()
    for name in ['edges','baseline','report','candidate']:p.add_argument('--'+name,required=True)
    z=p.parse_args();start=time.monotonic()
    tour=[x-1 for x in json.loads(Path(z.baseline).read_text())['tour']]
    n=len(tour);assert n==100000
    base={e(tour[i],tour[(i+1)%n]) for i in range(n)}
    with gzip.open(z.edges,'rt') as f:
        header=list(map(int,f.readline().split()))
        rows=[tuple(map(int,line.split())) for line in f if line.strip()]
    assert header==[n,len(rows)]
    off=0 if min(min(a,b) for a,b,w in rows)==0 else 1
    weights={e(a-off,b-off):w for a,b,w in rows}
    assert len(weights)==len(rows) and base<=weights.keys()
    graph=nx.Graph();graph.add_nodes_from(range(n));graph.add_edges_from(weights)
    planar,emb=nx.check_planarity(graph);assert planar
    visited=set();faces=[]
    for a,b in graph.edges():
        for u,v in ((a,b),(b,a)):
            if (u,v) in visited:continue
            verts=emb.traverse_face(u,v);L=len(verts)
            visited.update((verts[i],verts[(i+1)%L]) for i in range(L))
            if L!=4 or len(set(verts))!=4:continue
            boundary=[e(verts[i],verts[(i+1)%4]) for i in range(4)]
            marks=[edge in base for edge in boundary]
            if any(marks[i]==marks[(i+1)%4] for i in range(4)):continue
            gain=sum(weights[edge]*(1 if selected else -1) for edge,selected in zip(boundary,marks))
            if gain>0:faces.append((gain,tuple(edge for edge,sel in zip(boundary,marks) if sel),
                                         tuple(edge for edge,sel in zip(boundary,marks) if not sel)))
    faces.sort(reverse=True);assert len(faces)==279
    adj=[[] for _ in range(n)]
    for a,b in base:adj[a].append(b);adj[b].append(a)
    neutral=[];negative=[];positive=[];best_score=5757191
    for rank,(gain,removed,added) in enumerate(faces):
        switch(adj,removed,added)
        labels,sizes=components(adj)
        assert len(sizes)==2
        best=None
        cross=0
        for edge,weight in weights.items():
            a,b=edge
            if labels[a]==labels[b]:continue
            cross+=1
            for aa in adj[a]:
                for bb in adj[b]:
                    second=e(aa,bb)
                    if second not in weights:continue
                    old1=e(a,aa);old2=e(b,bb)
                    # Skip direct undoing of face flip.
                    if {old1,old2}==set(added) and {edge,second}==set(removed):continue
                    net=gain+weights[old1]+weights[old2]-weight-weights[second]
                    if best is None or net>best[0]:
                        best=(net,(old1,old2),(edge,second))
        if best is not None:
            net,repair_removed,repair_added=best
            toggled=set(removed)^set(added)^set(repair_removed)^set(repair_added)
            removed_all=sorted(ed for ed in toggled if ed in base)
            added_all=sorted(ed for ed in toggled if ed not in base)
            assert len(removed_all)==len(added_all)>0
            move={'rank':rank,'face_gain':gain,'net_gain':net,
                  'removed':[[a+1,b+1] for a,b in removed_all],
                  'added':[[a+1,b+1] for a,b in added_all]}
            if net==0:neutral.append(move)
            elif net>0:
                positive.append(move)
                if 5757191-net<best_score:
                    best_score=5757191-net
                    switch(adj,repair_removed,repair_added)
                    candidate=reconstruct(adj)
                    out=Path(z.candidate);out.parent.mkdir(parents=True,exist_ok=True)
                    out.write_text(json.dumps({'tour':candidate},separators=(',',':')))
                    switch(adj,repair_added,repair_removed)
            else:negative.append(net)
        switch(adj,added,removed)
        if rank%40==0:
            print(json.dumps({'stage':'progress','rank':rank,'neutrals':len(neutral),
              'positives':len(positive),'best_score':best_score}),flush=True)
    unique={}
    for move in neutral:
        identity=(tuple(tuple(q) for q in move['removed']),
                  tuple(tuple(q) for q in move['added']))
        unique.setdefault(identity,move)
    neutral=list(unique.values())
    data={'source':'few-shots p010 baseline and ElimTSP public sparse graph',
          'baseline_score':5757191,'positive_faces':len(faces),
          'neutral_moves':neutral,'positive_moves':positive,
          'negative_count':len(negative),
          'unique_neutral_count':len(neutral),
          'best_score':best_score,'seconds':round(time.monotonic()-start,2)}
    dest=Path(z.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({k:v for k,v in data.items()
      if k not in ['neutral_moves','positive_moves']}),flush=True)
    spec=importlib.util.spec_from_file_location('v',Path(os.environ['FEWSHOTS_ROOT'])/
        'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    if positive:
        assert v.tour_length(json.loads(Path(z.candidate).read_text())['tour'])==best_score
    assert v.tour_length([x+1 for x in tour])==5757191
if __name__=='__main__':main()
