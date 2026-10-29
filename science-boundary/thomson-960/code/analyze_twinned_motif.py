#!/usr/bin/env python3
"""Diagnose twinned/grain-boundary defect motifs in a spherical Thomson XYZ file.

A historical 'twinned' defect consists of two seven-coordinated sites sharing a
Voronoi/Delaunay edge, with pentagons on its periphery. Current N=960 R/A/B/D
scar minima use separated 7-fold sites in 5-7-5-7-5 chains. Counting 7-7
Delaunay edges is therefore a direct topology-family discriminator.
"""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np
from scipy.spatial import ConvexHull

def load_xyz(path):
    rows=[]
    for line in pathlib.Path(path).read_text().splitlines():
        t=line.split(); vals=None
        if len(t)<3: continue
        for off in (0,1):
            try:
                a=list(map(float,t[off:off+3]))
                if len(a)==3: vals=a; break
            except Exception: pass
        if vals is None:
            try: vals=list(map(float,t[-3:]))
            except Exception: continue
        rows.append(vals)
    x=np.asarray(rows,float)
    if len(x)<10: raise ValueError(f'could not parse point cloud from {path}')
    x/=np.linalg.norm(x,axis=1)[:,None]; return x

def graph(x):
    h=ConvexHull(x); nb=[set() for _ in range(len(x))]; edges=set()
    for tri in h.simplices:
        a,b,c=map(int,tri)
        for u,v in ((a,b),(b,c),(c,a)):
            if u>v:u,v=v,u
            edges.add((u,v)); nb[u].add(v); nb[v].add(u)
    z=np.array([len(s) for s in nb],int); return nb,edges,z

def components(vertices,edges):
    adj={v:set() for v in vertices}
    for a,b in edges:
        if a in adj and b in adj: adj[a].add(b);adj[b].add(a)
    out=[]; unseen=set(vertices)
    while unseen:
        r=unseen.pop(); comp={r}; stack=[r]
        while stack:
            u=stack.pop()
            for v in adj[u]:
                if v in unseen: unseen.remove(v);comp.add(v);stack.append(v)
        out.append(sorted(comp))
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('xyz'); ap.add_argument('--out'); args=ap.parse_args()
    x=load_xyz(args.xyz); nb,edges,z=graph(x); sevens=set(np.flatnonzero(z==7)); fives=set(np.flatnonzero(z==5))
    e77=[(a,b) for a,b in edges if a in sevens and b in sevens]; e55=[(a,b) for a,b in edges if a in fives and b in fives]
    twin=[]
    for a,b in e77:
        ring=(nb[a]|nb[b])-{a,b}; p5=sorted(v for v in ring if z[v]==5); common5=sorted(v for v in (nb[a]&nb[b]) if z[v]==5)
        twin.append({'edge':[a,b],'peripheral_fives':p5,'common_fives':common5,'peripheral_five_count':len(p5)})
    out={'file':str(args.xyz),'n':len(x),'coordination_counts':{str(k):int(np.sum(z==k)) for k in sorted(set(map(int,z)))},
         'topological_charge':int(np.sum(6-z)),'seven_seven_edge_count':len(e77),'five_five_edge_count':len(e55),
         'seven_components':components(sevens,e77),'twin_edges':twin}
    print(json.dumps(out,indent=2),flush=True)
    if args.out:pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
