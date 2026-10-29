#!/usr/bin/env python3
"""Convert N=960 scar motifs into twinned motifs by finite Delaunay-flip search.

The live R minimum and the historical N=972 twinned family have the same 5/7
counts (36/24) but different defect adjacency.  This program searches directly
in the triangulation flip graph, not coordinate-kick space:

1. enumerate local edge-flip sequences of length <=3 near existing defects;
2. require the final coordination histogram to equal the live histogram while
   increasing the number of 7-7 edges / twin-like motifs;
3. realize each abstract flip geometrically by crossing the four-point coplanar
   (zero oriented tetrahedron volume) boundary on the sphere;
4. fully relax the best realized starts and test whether the twin topology
   survives or heals back to the scar family.

This differs from earlier defect-deletion flips, whose target was 22 rather than
24 dislocations.  Here defect counts are explicitly conserved at the endpoint.
"""
from __future__ import annotations
import argparse,json,math,pathlib
from collections import defaultdict,deque
import numpy as np
from scipy.spatial import ConvexHull
import search_size_beam as sb


def faces_of(x): return {tuple(sorted(map(int,t))) for t in ConvexHull(x).simplices}
def edge_map(faces):
    m=defaultdict(list)
    for a,b,c in faces:
        m[(min(a,b),max(a,b))].append(c);m[(min(a,c),max(a,c))].append(b);m[(min(b,c),max(b,c))].append(a)
    return m
def degrees(faces,n):
    m=edge_map(faces);z=np.zeros(n,int)
    for a,b in m:z[a]+=1;z[b]+=1
    return z,m
def neighbors_from_map(m,n):
    nb=[set() for _ in range(n)]
    for a,b in m:nb[a].add(b);nb[b].add(a)
    return nb
def coord_hist(z): return {int(k):int(np.sum(z==k)) for k in sorted(set(map(int,z)))}
def twin_edges(faces,n):
    z,m=degrees(faces,n);nb=neighbors_from_map(m,n);out=[]
    for a,b in m:
        if z[a]==7 and z[b]==7:
            ring=(nb[a]|nb[b])-{a,b};p5=sorted(v for v in ring if z[v]==5)
            out.append({'edge':[a,b],'peripheral_fives':p5,'peripheral_five_count':len(p5)})
    return out
def flip_info(faces,e):
    a,b=e;m=edge_map(faces);opp=m.get((min(a,b),max(a,b)),[])
    if len(opp)!=2:return None
    c,d=opp
    if c==d or (min(c,d),max(c,d)) in m:return None
    return a,b,c,d
def apply_flip(faces,e):
    q=flip_info(faces,e)
    if q is None:return None,None
    a,b,c,d=q;f=set(faces);f.discard(tuple(sorted((a,b,c))));f.discard(tuple(sorted((a,b,d))))
    f.add(tuple(sorted((c,d,a))));f.add(tuple(sorted((c,d,b))));return f,q
def defect_distance(faces,n):
    z,m=degrees(faces,n);nb=neighbors_from_map(m,n);dist=np.full(n,999,int);q=deque()
    for v in np.flatnonzero(z!=6):dist[v]=0;q.append(int(v))
    while q:
        u=q.popleft()
        for v in nb[u]:
            if dist[v]>dist[u]+1:dist[v]=dist[u]+1;q.append(v)
    return dist,z,m,nb
def candidate_edges(faces,n,active=None):
    dist,z,m,nb=defect_distance(faces,n);out=[]
    for e,opp in m.items():
        if len(opp)!=2:continue
        a,b=e;c,d=opp
        if (min(c,d),max(c,d)) in m:continue
        quad={a,b,c,d}
        if active is None:
            if min(dist[list(quad)])>1:continue
        else:
            if not (quad & active):continue
        out.append(e)
    return out,dist,z,m,nb
def hist_tuple(z):
    return tuple(int(np.sum(z==k)) for k in range(4,9))
def search_sequences(f0,n,max_depth,max_results):
    z0,_=degrees(f0,n);target=hist_tuple(z0);base_tw=len(twin_edges(f0,n));results=[];seen={frozenset(f0):0}
    first,_,_,_,nb0=candidate_edges(f0,n)
    stack=[(f0,[],None)]
    while stack and len(results)<max_results:
        faces,seq,active=stack.pop();depth=len(seq)
        if depth>0:
            z,_=degrees(faces,n);tw=twin_edges(faces,n)
            if hist_tuple(z)==target and len(tw)>base_tw:
                results.append({'sequence':[list(e) for e in seq],'depth':depth,'twin_edges':tw,'coord_hist':coord_hist(z)})
                continue
        if depth>=max_depth:continue
        edges,dist,z,m,nb=candidate_edges(faces,n,active)
        # Favor flips tightly coupled to the current defect/change region.
        edges=sorted(edges,key=lambda e:min(dist[list({e[0],e[1],*m[e]})]))
        for e in edges:
            nf,q=apply_flip(faces,e)
            if nf is None:continue
            nz,_=degrees(nf,n)
            if np.min(nz)<5 or np.max(nz)>7:continue
            sig=frozenset(nf);nd=depth+1
            if seen.get(sig,99)<=nd:continue
            seen[sig]=nd;a,b,c,d=q
            # Keep later flips local: changed vertices plus one graph shell.
            changed={a,b,c,d};na=edge_map(nf);nnb=neighbors_from_map(na,n);act=set(changed)
            for v in list(changed):act|=nnb[v]
            stack.append((nf,seq+[e],act))
    results.sort(key=lambda r:(r['depth'],-len(r['twin_edges'])))
    return results,base_tw,coord_hist(z0)

def exp_move(x,ids,dirs,amp):
    y=x.copy();D=np.asarray([dirs[i] for i in ids],float);norm=np.sqrt(np.mean(np.sum(D*D,axis=1)))
    if norm<1e-15:raise RuntimeError('zero flip direction')
    D*=amp/norm
    for j,i in enumerate(ids):
        v=D[j];a=np.linalg.norm(v);p=x[i]
        y[i]=math.cos(a)*p+math.sin(a)*v/a
    y/=np.linalg.norm(y,axis=1)[:,None];return y
def volume_grads(x,a,b,c,d):
    A,B,C,D=x[a],x[b],x[c],x[d]
    gb=np.cross(C-A,D-A);gc=np.cross(D-A,B-A);gd=np.cross(B-A,C-A);ga=-(gb+gc+gd)
    V=float((B-A)@np.cross(C-A,D-A));raw={a:ga,b:gb,c:gc,d:gd};dirs={}
    s=-1.0 if V>0 else 1.0
    for i,g in raw.items():dirs[i]=s*(g-float(g@x[i])*x[i])
    return V,dirs
def realize_one_flip(x,e):
    f=faces_of(x);q=flip_info(f,tuple(e))
    if q is None:return None,None
    a,b,c,d=q;target=(min(c,d),max(c,d));old=(min(a,b),max(a,b));V,dirs=volume_grads(x,a,b,c,d);ids=[a,b,c,d]
    # Search monotonically along the coplanarity-crossing direction.  Start very
    # small to avoid triggering unrelated flips; accept only when the requested
    # old diagonal disappears and the new one appears.
    for amp in np.geomspace(2e-5,0.035,80):
        y=exp_move(x,ids,dirs,float(amp));m=edge_map(faces_of(y))
        if target in m and old not in m:return y,{'edge':[a,b],'opposites':[c,d],'volume':V,'amp':float(amp)}
    return None,None
def realize_sequence(x,seq):
    y=x.copy();hist=[]
    for e in seq:
        y,info=realize_one_flip(y,e)
        if y is None:return None,hist
        hist.append(info)
    return y,hist
def raw_energy(x):
    d=np.clip(x@x.T,-1,1);r2=np.maximum(2-2*d,1e-300);np.fill_diagonal(r2,np.inf);iu=np.triu_indices(len(x),1)
    return float(np.sum(np.asarray((1/np.sqrt(r2))[iu],np.longdouble),dtype=np.longdouble))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('few_shots');ap.add_argument('--depth',type=int,default=3);ap.add_argument('--max-topologies',type=int,default=80);ap.add_argument('--screen',type=int,default=24);ap.add_argument('--relax',type=int,default=12);ap.add_argument('--out',required=True);args=ap.parse_args()
    root=pathlib.Path(args.few_shots);live,shot=sb.find_live(root);x=sb.load_cert(shot/'certificate.json');E0,x,nit,ok=sb.stable_relax(x,1100);f0=faces_of(x)
    seqs,base_tw,hist0=search_sequences(f0,len(x),args.depth,args.max_topologies)
    print(f'live={live:.10f} polished={E0:.12f} hist={hist0} initial_twins={base_tw} abstract_candidates={len(seqs)}',flush=True)
    starts=[]
    for i,r in enumerate(seqs[:args.screen]):
        y,fh=realize_sequence(x,r['sequence'])
        if y is None:
            print(f'REALIZE {i} failed seq={r["sequence"]}',flush=True);continue
        ff=faces_of(y);z,_=degrees(ff,len(y));tw=twin_edges(ff,len(y));eraw=raw_energy(y)
        row={**r,'realized':True,'flip_geometry':fh,'start_energy':eraw,'realized_coord_hist':coord_hist(z),'realized_twins':tw}
        starts.append((eraw,y,row));print(f'REALIZE {i} depth={r["depth"]} raw={eraw:.9f} twins={len(tw)} seq={r["sequence"]}',flush=True)
    starts.sort(key=lambda t:t[0]);rows=[];best=None
    for rank,(eraw,y,row) in enumerate(starts[:args.relax]):
        E,q,nit,ok=sb.stable_relax(y,2000);ff=faces_of(q);z,_=degrees(ff,len(q));tw=twin_edges(ff,len(q));rr={**row,'rank':rank,'relaxed_energy':E,'delta_vs_live':E-live,'post_coord_hist':coord_hist(z),'post_twins':tw,'nit':nit,'success':ok};rows.append(rr)
        print(f'RELAX {rank} E={E:.12f} dlive={E-live:+.9g} twins={len(tw)} hist={coord_hist(z)} nit={nit}',flush=True)
        if best is None or E<best[0]:best=(E,q,rr)
    out={'live_score':live,'polished_live_energy':E0,'initial_coord_hist':hist0,'initial_twin_count':base_tw,'abstract_candidates':seqs,'realized_count':len(starts),'relaxed_rows':rows}
    if best is not None:
        out['best_float_energy']=best[0];out['best_delta_vs_live']=best[0]-live;out['best_row']=best[2];out['best_points']=best[1].tolist() if best[0]<live-2e-7 else None
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
