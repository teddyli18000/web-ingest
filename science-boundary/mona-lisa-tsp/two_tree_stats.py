#!/usr/bin/env python3
"""Audit the two-page book decomposition induced by the known Hamiltonian tour."""
import argparse,gzip,json,statistics,time
from collections import Counter,deque
from pathlib import Path
import networkx as nx

def e(a,b):return (a,b) if a<b else (b,a)
def pct(values,k):
    x=sorted(values)
    return x[min(len(x)-1,max(0,round(k*(len(x)-1))))] if x else None

def main():
    a=argparse.ArgumentParser()
    for p in ('edges','baseline','report'):a.add_argument('--'+p,required=True)
    z=a.parse_args()
    t0=time.monotonic()
    tour=[x-1 for x in json.loads(Path(z.baseline).read_text())['tour']]
    n=len(tour)
    assert n==100000
    base={e(tour[i],tour[(i+1)%n]) for i in range(n)}
    pos={v:i for i,v in enumerate(tour)}
    with gzip.open(z.edges,'rt') as f:
        h=list(map(int,f.readline().split()))
        rows=[tuple(map(int,line.split())) for line in f if line.strip()]
    assert h==[n,len(rows)]
    off=0 if min(min(u,v) for u,v,w in rows)==0 else 1
    w={e(u-off,v-off):d for u,v,d in rows}
    assert base<=w.keys()
    g=nx.Graph();g.add_nodes_from(range(n));g.add_edges_from(w)
    planar,emb=nx.check_planarity(g)
    assert planar
    half={};faces=[]
    for a,b in g.edges():
        for u,v in ((a,b),(b,a)):
            if (u,v) in half:continue
            vs=emb.traverse_face(u,v)
            fid=len(faces);faces.append(vs)
            half.update({(vs[i],vs[(i+1)%len(vs)]):fid for i in range(len(vs))})
    N=len(faces)
    dual=[[] for _ in faces]
    for a,b in (key for key in w if key not in base):
        f,h=half[(a,b)],half[(b,a)]
        assert f!=h
        dual[f].append(h);dual[h].append(f)
    labels=[-1]*N;components=[]
    for i in range(N):
        if labels[i]>=0:continue
        idx=len(components);stack=[i];labels[i]=idx;part=[]
        while stack:
            u=stack.pop();part.append(u)
            for v in dual[u]:
                if labels[v]<0:labels[v]=idx;stack.append(v)
        components.append(part)
    assert len(components)==2
    assert sum(len(p)-1 for p in components)==len(w)-n
    degrees=[len(ns) for ns in dual]
    pages=[[],[]]
    lengths=[[],[]]
    difference=[[0]*(n+1) for _ in range(2)]
    for (a,b),dist in w.items():
        if (a,b) in base:
            assert labels[half[(a,b)]]!=labels[half[(b,a)]]
            continue
        page=labels[half[(a,b)]]
        assert page==labels[half[(b,a)]]
        pages[page].append((a,b))
        i,j=sorted((pos[a],pos[b]))
        lengths[page].append(min(j-i,n-(j-i)))
        difference[page][i]+=1
        difference[page][j]-=1
    stats=[]
    for page in range(2):
        active=[];tot=0
        for x in difference[page][:-1]:
            tot+=x;active.append(tot)
        subset=components[page]
        deg=Counter(degrees[i] for i in subset)
        stats.append({'page':page,'faces':len(subset),'chords':len(pages[page]),
            'verified_dual_tree_edges':len(subset)-1,
            'dual_degree_histogram':dict(sorted(deg.items())),
            'chord_cyclic_span_median':pct(lengths[page],.5),
            'chord_cyclic_span_p95':pct(lengths[page],.95),
            'spine_cut_crossing_chords_median':pct(active,.5),
            'spine_cut_crossing_chords_p95':pct(active,.95),
            'spine_cut_crossing_chords_max':max(active),
            'spine_cut_crossing_chords_min':min(active)})
    out={'status':'verified_two_dual_trees','vertices':n,'edges':len(w),
        'faces':len(faces),'non_tour_chords':len(w)-n,
        'components':stats,'seconds':round(time.monotonic()-t0,2)}
    dest=Path(z.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out),flush=True)
if __name__=='__main__':main()
