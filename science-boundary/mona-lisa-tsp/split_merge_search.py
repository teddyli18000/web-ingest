#!/usr/bin/env python3
"""Exact arbitrary-distance 2-edge reconnections after a profitable facial split."""
import argparse,gzip,json,importlib.util,os,time
from pathlib import Path
import networkx as nx

def e(a,b):return (a,b) if a<b else (b,a)
def switch(adj,old,new):
    for a,b in old:adj[a].remove(b);adj[b].remove(a)
    for a,b in new:adj[a].append(b);adj[b].append(a)
def cycles(adj):
    labels=bytearray(len(adj));sizes=[]
    for start in range(len(adj)):
        if labels[start]:continue
        mark=len(sizes)+1;u=start;prev=-1;sz=0
        while not labels[u]:
            labels[u]=mark;sz+=1
            a,b=adj[u];nxt=a if a!=prev else b
            prev,u=u,nxt
        assert u==start
        sizes.append(sz)
    return labels,sizes
def tour_from(adj):
    u=0;prev=-1;seen=bytearray(len(adj));result=[]
    while not seen[u]:
        seen[u]=1;result.append(u+1)
        a,b=adj[u];nxt=a if a!=prev else b
        prev,u=u,nxt
    assert u==0 and len(result)==len(adj)
    return result
def main():
    p=argparse.ArgumentParser()
    for name in ['edges','baseline','report','output']:p.add_argument('--'+name,required=True)
    p.add_argument('--face-start',type=int,default=0)
    p.add_argument('--max-faces',type=int,default=50)
    z=p.parse_args();t0=time.monotonic()
    t=[x-1 for x in json.loads(Path(z.baseline).read_text())['tour']]
    n=len(t);assert n==100000
    base={e(t[i],t[(i+1)%n]) for i in range(n)}
    with gzip.open(z.edges,'rt') as f:
        header=list(map(int,f.readline().split()))
        rows=[tuple(map(int,x.split())) for x in f if x.strip()]
    assert header==[n,len(rows)]
    offset=0 if min(min(a,b) for a,b,w in rows)==0 else 1
    w={e(a-offset,b-offset):weight for a,b,weight in rows}
    assert len(w)==len(rows) and base<=w.keys()
    g=nx.Graph();g.add_nodes_from(range(n));g.add_edges_from(w)
    planar,emb=nx.check_planarity(g);assert planar
    visited=set();faces=[]
    for a,b in g.edges():
        for u,v in [(a,b),(b,a)]:
            if (u,v) in visited:continue
            vs=emb.traverse_face(u,v)
            L=len(vs)
            visited.update((vs[i],vs[(i+1)%L]) for i in range(L))
            if L!=4 or len(set(vs))!=4:continue
            edges=[e(vs[i],vs[(i+1)%4]) for i in range(4)]
            marks=[edge in base for edge in edges]
            if any(marks[i]==marks[(i+1)%4] for i in range(4)):continue
            gain=sum(w[edge]*(1 if m else -1) for edge,m in zip(edges,marks))
            if gain>0:faces.append((gain,tuple(x for x,m in zip(edges,marks) if m),
                                    tuple(x for x,m in zip(edges,marks) if not m)))
    faces.sort(reverse=True)
    assert len(faces)>0, 'No positive alternating faces on this starting tour'
    adj=[[] for _ in range(n)]
    for a,b in base:adj[a].append(b);adj[b].append(a)
    items=list(w.items());best=None;records=[]
    for rank in range(z.face_start,min(len(faces),z.face_start+z.max_faces)):
        gain,old,new=faces[rank]
        switch(adj,old,new)
        labels,sizes=cycles(adj)
        assert len(sizes)==2
        local=None;cross=0
        for (a,b),length in items:
            if labels[a]==labels[b]:continue
            cross+=1
            for aa in adj[a]:
                for bb in adj[b]:
                    edge2=e(aa,bb)
                    if edge2 not in w:continue
                    # Reject the automatic zero-gain reconnection that simply undoes this face flip.
                    if {e(a,aa),e(b,bb)}==set(new) and {e(a,b),edge2}==set(old):continue
                    net=gain+ w[e(a,aa)]+w[e(b,bb)]-length-w[edge2]
                    if local is None or net>local[0]:
                        local=(net,(a,aa),(b,bb),(a,b),(aa,bb))
        if local and (best is None or local[0]>best[0]):
            best=(local[0],rank,old,new,*local[1:])
        records.append({'rank':rank,'face_gain':gain,'cycle_sizes':sizes,
                        'cross_edges':cross,'best_merged_gain':local[0] if local else None})
        switch(adj,new,old)
        if rank%10==0:print(json.dumps({'stage':'progress','rank':rank,
                      'best_net_gain':best[0] if best else None}),flush=True)
    report={'baseline':5757191,'records':records,'best_net_gain':best[0] if best else None,
            'mergers_found':sum(x['best_merged_gain'] is not None for x in records),
            'seconds':round(time.monotonic()-t0,2)}
    if best and best[0]>=0:
        net,rank,old,new,old1,old2,new1,new2=best
        switch(adj,old,new);switch(adj,[old1,old2],[new1,new2])
        candidate=tour_from(adj)
        spec=importlib.util.spec_from_file_location('v',Path(os.environ['FEWSHOTS_ROOT'])/
                'problems/p010-mona-lisa-tsp/verify/verify.py')
        verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
        score=verify.tour_length(candidate)
        assert score==5757191-net
        output=Path(z.output);output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps({'tour':candidate},separators=(',',':')))
        report.update({'candidate_score':score,'candidate_rank':rank,
                       'candidate_is_breakthrough':score<5757191})
    dest=Path(z.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records'}),flush=True)
if __name__=='__main__':main()
