#!/usr/bin/env python3
"""Breadth-first scar->twin triangulation search with explicit coverage accounting.

This is the coverage-safe front-end for search_scar_to_twin_flips.py.  It
enumerates topology states by flip distance, so every depth-1 state is tested
before depth 2 and every depth-2 state before depth 3.  `max_states` is an
explicit coverage budget; hitting it is reported as truncation and must never be
interpreted as exhaustion of the depth bound.

A histogram-preserving single flip is possible.  With endpoint-degree changes
(-1,-1,+1,+1), the three degree-balanced patterns are
  removed 7,7 / added 6,6;
  removed 7,6 / added 6,5;
  removed 6,6 / added 5,5.
The mixed 7,6 -> 6,5 case can move one heptagon next to another pre-existing
heptagon and thereby create a first 7-7 twin without changing 36/900/24.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import deque
import numpy as np
import search_size_beam as sb
import search_scar_to_twin_flips as sf


def bfs_sequences(f0,n,max_depth,max_results,max_states):
    z0,_=sf.degrees(f0,n); target=sf.hist_tuple(z0); base_tw=len(sf.twin_edges(f0,n))
    results=[]; seen={frozenset(f0):0}; q=deque([(f0,[],None)]); explored=0; depth_counts={0:1}; truncated=False
    while q and len(results)<max_results:
        if explored>=max_states:
            truncated=True; break
        faces,seq,active=q.popleft(); explored+=1; depth=len(seq)
        if depth>0:
            z,_=sf.degrees(faces,n); tw=sf.twin_edges(faces,n)
            if sf.hist_tuple(z)==target and len(tw)>base_tw:
                results.append({'sequence':[list(e) for e in seq],'depth':depth,'twin_edges':tw,'coord_hist':sf.coord_hist(z)})
                # Do not expand a successful shortest-path topology further in
                # the same BFS; deeper descendants are redundant for finding
                # the first twin creation event.
                continue
        if depth>=max_depth: continue
        edges,dist,z,m,nb=sf.candidate_edges(faces,n,active)
        def key(e):
            quad={e[0],e[1],*m[e]}
            return (min(dist[list(quad)]), tuple(e))
        for e in sorted(edges,key=key):
            nf,info=sf.apply_flip(faces,e)
            if nf is None: continue
            nz,_=sf.degrees(nf,n)
            if np.min(nz)<5 or np.max(nz)>7: continue
            sig=frozenset(nf); nd=depth+1
            if seen.get(sig,99)<=nd: continue
            seen[sig]=nd; depth_counts[nd]=depth_counts.get(nd,0)+1
            a,b,c,d=info; changed={a,b,c,d}; nm=sf.edge_map(nf); nnb=sf.neighbors_from_map(nm,n); act=set(changed)
            for v in list(changed): act|=nnb[v]
            q.append((nf,seq+[e],act))
    results.sort(key=lambda r:(r['depth'],-len(r['twin_edges']),r['sequence']))
    return results,base_tw,sf.coord_hist(z0),{'states_explored':explored,'states_seen':len(seen),'depth_state_counts':depth_counts,'truncated':truncated,'queue_remaining':len(q)}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots'); ap.add_argument('--depth',type=int,default=3)
    ap.add_argument('--max-topologies',type=int,default=120); ap.add_argument('--max-states',type=int,default=250000)
    ap.add_argument('--screen',type=int,default=30); ap.add_argument('--relax',type=int,default=12); ap.add_argument('--out',required=True); args=ap.parse_args()
    root=pathlib.Path(args.few_shots); live,shot=sb.find_live(root); x=sb.load_cert(shot/'certificate.json'); E0,x,nit,ok=sb.stable_relax(x,1100); f0=sf.faces_of(x)
    seqs,base_tw,hist0,cov=bfs_sequences(f0,len(x),args.depth,args.max_topologies,args.max_states)
    print(f'live={live:.10f} polished={E0:.12f} hist={hist0} initial_twins={base_tw} candidates={len(seqs)} coverage={cov}',flush=True)
    starts=[]
    for i,r in enumerate(seqs[:args.screen]):
        y,fh=sf.realize_sequence(x,r['sequence'])
        if y is None:
            print(f'REALIZE {i} failed depth={r["depth"]} seq={r["sequence"]}',flush=True); continue
        ff=sf.faces_of(y); z,_=sf.degrees(ff,len(y)); tw=sf.twin_edges(ff,len(y)); eraw=sf.raw_energy(y)
        row={**r,'realized':True,'flip_geometry':fh,'start_energy':eraw,'realized_coord_hist':sf.coord_hist(z),'realized_twins':tw}
        starts.append((eraw,y,row)); print(f'REALIZE {i} depth={r["depth"]} raw={eraw:.9f} twins={len(tw)} seq={r["sequence"]}',flush=True)
    starts.sort(key=lambda t:t[0]); rows=[]; best=None
    for rank,(eraw,y,row) in enumerate(starts[:args.relax]):
        E,q,nit,ok=sb.stable_relax(y,2000); ff=sf.faces_of(q); z,_=sf.degrees(ff,len(q)); tw=sf.twin_edges(ff,len(q))
        rr={**row,'rank':rank,'relaxed_energy':E,'delta_vs_live':E-live,'post_coord_hist':sf.coord_hist(z),'post_twins':tw,'nit':nit,'success':ok}; rows.append(rr)
        print(f'RELAX {rank} E={E:.12f} dlive={E-live:+.9g} twins={len(tw)} hist={sf.coord_hist(z)} nit={nit}',flush=True)
        if best is None or E<best[0]: best=(E,q,rr)
    out={'live_score':live,'polished_live_energy':E0,'initial_coord_hist':hist0,'initial_twin_count':base_tw,
         'coverage':cov,'abstract_candidates':seqs,'realized_count':len(starts),'relaxed_rows':rows}
    if best is not None:
        out.update(best_float_energy=best[0],best_delta_vs_live=best[0]-live,best_row=best[2],best_points=best[1].tolist() if best[0]<live-2e-7 else None)
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__': main()
