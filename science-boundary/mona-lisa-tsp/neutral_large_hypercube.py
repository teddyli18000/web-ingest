#!/usr/bin/env python3
"""Exact connectivity census of maximum vertex-disjoint neutral move family.

Contract every unchanged baseline path between moved endpoints. All 2^k
combinations then reduce to tiny (<=8k vertex) degree-2 multigraphs.
A fully reconstructed tour is independently checked by the official verifier.
"""
import argparse,importlib.util,itertools,json,os,time
from pathlib import Path

def edge(a,b):return (a,b) if a<b else (b,a)
def tour_edges(t):return {edge(t[i],t[(i+1)%len(t)]) for i in range(len(t))}
def full_tour(n,edges):
    adj=[[] for _ in range(n+1)]
    for a,b in edges:adj[a].append(b);adj[b].append(a)
    assert all(len(adj[i])==2 for i in range(1,n+1))
    u=1;prev=0;t=[];seen=bytearray(n+1)
    while not seen[u]:
        seen[u]=1;t.append(u)
        a,b=adj[u];nxt=a if a!=prev else b
        prev,u=u,nxt
    assert u==1 and len(t)==n
    return t

def main():
    p=argparse.ArgumentParser()
    for name in ('baseline','harvest','report','output-dir'):p.add_argument('--'+name,required=True)
    z=p.parse_args();start=time.monotonic()
    base_t=json.loads(Path(z.baseline).read_text())['tour']
    n=len(base_t);assert n==100000
    base=tour_edges(base_t)
    all_moves=json.loads(Path(z.harvest).read_text())['neutral_moves']
    assert len(all_moves)>=6
    support=[{v for pair in m['removed']+m['added'] for v in pair} for m in all_moves]
    best=()
    for mask in range(1<<len(all_moves)):
        choices=tuple(i for i in range(len(all_moves)) if (mask>>i)&1)
        if len(choices)<=len(best):continue
        if any(support[i]&support[j] for i,j in itertools.combinations(choices,2)):continue
        best=choices
    assert len(best)>=6
    moves=[all_moves[i] for i in best]
    oldsets=[set(map(tuple,m['removed'])) for m in moves]
    newsets=[set(map(tuple,m['added'])) for m in moves]
    for old,new in zip(oldsets,newsets):
        assert len(old)==len(new)>0 and old<=base and not(new&base)
    endpoints=set().union(*(support[i] for i in best))
    pos={v:i for i,v in enumerate(base_t)}
    verts=sorted(endpoints,key=lambda v:pos[v])
    K=len(verts)
    idx={v:i for i,v in enumerate(verts)}
    owner={}
    for i,old in enumerate(oldsets):
        for ed in old:
            assert ed not in owner
            owner[ed]=i
    fixed=[]
    optional=[]
    for i,u in enumerate(verts):
        v=verts[(i+1)%K]
        ed=edge(u,v)
        if ed in owner and ((pos[u]+1)%n)==pos[v]:
            optional.append((idx[u],idx[v],owner[ed]))
        else:
            fixed.append((idx[u],idx[v]))
    assert len(optional)==sum(len(s) for s in oldsets)
    additional=[[(idx[a],idx[b]) for a,b in additions] for additions in newsets]
    assert sum(len(es) for es in additional)==len(optional)
    outcomes=[]
    selected_eu=0
    for mask in range(1<<len(moves)):
        parent=list(range(K));size=[1]*K;degree=[0]*K
        def find(u):
            while parent[u]!=u:
                parent[u]=parent[parent[u]]
                u=parent[u]
            return u
        def connect(u,v):
            degree[u]+=1;degree[v]+=1
            a,b=find(u),find(v)
            if a!=b:
                if size[a]<size[b]:a,b=b,a
                parent[b]=a;size[a]+=size[b]
        for u,v in fixed:connect(u,v)
        for u,v,i in optional:
            if not (mask>>i)&1:connect(u,v)
        for i,edges in enumerate(additional):
            if (mask>>i)&1:
                for u,v in edges:connect(u,v)
        assert all(d==2 for d in degree)
        connected=len({find(i) for i in range(K)})==1
        outcomes.append(connected)
    nonham=[i for i,ok in enumerate(outcomes) if not ok]
    best_eu_mask=sum(1<<i for i,m in enumerate(moves) if m['euclidean_delta']<0)
    best_eu=sum(m['euclidean_delta'] for i,m in enumerate(moves) if (best_eu_mask>>i)&1)
    outdir=Path(z.output_dir);outdir.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('v',Path(os.environ['FEWSHOTS_ROOT'])/
        'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    assert v.tour_length(base_t)==5757191
    canonical={}
    for mask in [0,(1<<len(moves))-1,best_eu_mask]:
        if not outcomes[mask]:continue
        current=set(base)
        for i,old in enumerate(oldsets):
            if (mask>>i)&1:current.difference_update(old)
        for i,new in enumerate(newsets):
            if (mask>>i)&1:current.update(new)
        assert len(current)==n
        t=full_tour(n,current)
        assert v.tour_length(t)==5757191
        digest=v.canonical_hash({'tour':v.canonical_tour(t)})
        canonical[str(mask)]=digest
        (outdir/f'mask-{mask}.json').write_text(json.dumps({'tour':t},separators=(',',':')))
    data={'source_run':40693410570,'harvest_count':len(all_moves),
          'max_vertex_disjoint_neutrals':len(moves),
          'selected_harvest_indices':list(best),
          'selected_face_ranks':[m['rank'] for m in moves],
          'contracted_vertices':K,'fixed_superedges':len(fixed),
          'optional_old_edges':len(optional),
          'combinations':len(outcomes),
          'connected_combinations':sum(outcomes),
          'disconnected_count':len(nonham),
          'first_disconnected_masks':nonham[:30],
          'fully_verified_hashes':canonical,
          'best_continuous_delta':best_eu,
          'best_continuous_mask':best_eu_mask,
          'seconds':round(time.monotonic()-start,3)}
    Path(z.report).parent.mkdir(parents=True,exist_ok=True)
    Path(z.report).write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data),flush=True)
if __name__=='__main__':main()
