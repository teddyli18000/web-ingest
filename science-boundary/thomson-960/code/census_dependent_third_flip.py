#!/usr/bin/env python3
"""Census same-count Delaunay flips newly legal after a dependent two-flip state.

The input reconstruction result must contain last_both_flipped_state.points.  We
compare the immediate same-count flip neighborhood there with the live record's
neighborhood using the same natural labels, then rank only newly legal moves by
balanced crossing threshold and graph distance to the two-event support.
"""
from __future__ import annotations
import argparse,json,pathlib,collections
import numpy as np

from search_from_seed_modes import load_seed
from search_e564_defect_flip_parallel import topology,threshold


def flip_rows(x):
    deg,ef=topology(x); edges=set(ef); base=collections.Counter(deg.tolist()); rows=[]
    for (u,v),opp in ef.items():
        if len(opp)!=2: continue
        a,b=opp; ne=(min(a,b),max(a,b))
        if ne in edges: continue
        nd=deg.copy(); nd[u]-=1; nd[v]-=1; nd[a]+=1; nd[b]+=1
        if collections.Counter(nd.tolist())!=base: continue
        q=(int(u),int(v),int(a),int(b)); t=threshold(x,q,'balanced')
        if t is None: continue
        rows.append({'quad':list(q),'delete':[int(min(u,v)),int(max(u,v))],
                     'add':[int(min(a,b)),int(max(a,b))],'threshold':float(t),
                     'degrees_before':[int(deg[i]) for i in q]})
    rows.sort(key=lambda r:(r['threshold'],r['quad']))
    return deg,ef,rows


def edge_key(r):
    return (tuple(r['delete']),tuple(r['add']))


def distances(ef,sources,n):
    adj=[set() for _ in range(n)]
    for u,v in ef:
        adj[u].add(v); adj[v].add(u)
    inf=10**9; d=[inf]*n; q=collections.deque()
    for s in sources: d[s]=0; q.append(s)
    while q:
        u=q.popleft()
        for v in adj[u]:
            if d[v]>d[u]+1: d[v]=d[u]+1; q.append(v)
    return d


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('live_json'); ap.add_argument('reconstruction_result')
    ap.add_argument('--first-quad',default='108,282,511,599')
    ap.add_argument('--second-quad',default='108,511,502,599')
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    _,live=load_seed(args.live_json)
    rec=json.load(open(args.reconstruction_result))
    state=rec.get('last_both_flipped_state')
    if not state or 'points' not in state: raise RuntimeError('result lacks last_both_flipped_state.points')
    x=np.asarray(state['points'],dtype=float)
    q1=tuple(int(z) for z in args.first_quad.split(',')); q2=tuple(int(z) for z in args.second_quad.split(','))
    _,ef_live,live_rows=flip_rows(live); deg,ef,rows=flip_rows(x)
    live_keys={edge_key(r) for r in live_rows}; support=set(q1)|set(q2); dist=distances(ef,support,len(x))
    new=[]
    for r in rows:
        if edge_key(r) in live_keys: continue
        verts=set(r['quad']); r=dict(r)
        r['min_graph_distance_to_support']=int(min(dist[v] for v in verts))
        r['touches_support']=bool(verts & support)
        r['support_overlap']=sorted(int(v) for v in verts & support)
        new.append(r)
    new.sort(key=lambda r:(r['min_graph_distance_to_support'],r['threshold'],r['quad']))
    print('STATE_KAPPA',state.get('kappa'),'E',state.get('energy'),'coord',state.get('coord_counts'),flush=True)
    print('LIVE_FLIPS',len(live_rows),'STATE_FLIPS',len(rows),'NEWLY_LEGAL',len(new),flush=True)
    for i,r in enumerate(new[:80]):
        print('NEW',i,'dist',r['min_graph_distance_to_support'],'t',r['threshold'],
              'quad',r['quad'],'deg',r['degrees_before'],'overlap',r['support_overlap'],flush=True)
    pathlib.Path(args.out).write_text(json.dumps({
        'state_kappa':state.get('kappa'),'state_energy':state.get('energy'),'state_coord':state.get('coord_counts'),
        'first_quad':list(q1),'second_quad':list(q2),'live_flip_count':len(live_rows),
        'state_flip_count':len(rows),'newly_legal':new},separators=(',',':'))+'\n')

if __name__=='__main__': main()
