#!/usr/bin/env python3
"""Generate locally costly bridge exchanges around isolated 2-factor cycles.

These negative/zero-gain motifs are deliberately excluded from the previous
positive-only search. A single bridge motif can help merge the isolated
5- or 8-city component created by a positive 2-opt exchange.
Global validity is left to AddCircuit, not guessed from a local test.
"""
import argparse,gzip,importlib.util,json,os
from pathlib import Path
from collections import defaultdict

def ed(a,b):return (a,b) if a<b else (b,a)

def main():
    p=argparse.ArgumentParser()
    for k in ('baseline','graph','neutral-moves','positive-motifs','output'):
        p.add_argument('--'+k,required=True)
    p.add_argument('--min-gain',type=int,default=-60)
    p.add_argument('--max-gain',type=int,default=0)
    a=p.parse_args()
    tour=json.loads(Path(a.baseline).read_text())['tour'];n=len(tour)
    assert n==100000
    catalogue=json.loads(Path(a.neutral_moves).read_text())
    mods=[catalogue['moves'][i] for i in catalogue['selected_indices']]
    b0=[None]*(n+1)
    for i,v in enumerate(tour):
        b0[v]=(tour[(i-1)%n],tour[(i+1)%n])
    owner=[-1]*(n+1);b1=list(b0)
    for i,m in enumerate(mods):
        changes={}
        for u,v in m['removed']:
            changes.setdefault(u,list(b0[u])).remove(v)
            changes.setdefault(v,list(b0[v])).remove(u)
        for u,v in m['added']:
            changes.setdefault(u,list(b0[u])).append(v)
            changes.setdefault(v,list(b0[v])).append(u)
        for u,z in changes.items():
            assert len(z)==2 and len(set(z))==2
            assert owner[u]==-1
            owner[u]=i;b1[u]=tuple(z)
    with gzip.open(a.graph,'rt') as f:
        header=list(map(int,f.readline().split()))
        rows=[tuple(map(int,line.split())) for line in f if line.strip()]
    assert header==[n,len(rows)]
    off=0 if min(min(u,v) for u,v,w in rows)==0 else 1
    W={ed(u-off+1,v-off+1):weight for u,v,weight in rows}
    adjacency=defaultdict(list)
    for u,v in W:adjacency[u].append(v);adjacency[v].append(u)
    positive=json.loads(Path(a.positive_motifs).read_text())['positive_repair_motifs']
    # The source run has authoritative 2-factor checks:
    # motif 52 isolates five cities, motifs 52+105 isolate five and eight.
    anchors={11154,88231,55312,89013,53610,
             22708,29722,48604,29680,52441,41235,42439,98332}
    # Avoid handwaving: independently derive island sets for these motifs.
    def derive(motif_idxs):
        S={ed(tour[i],tour[(i+1)%n]) for i in range(n)}
        for j in motif_idxs:
            m=positive[j]
            for u,v in m['old']:
                assert ed(u,v) in S;S.remove(ed(u,v))
            for u,v in m['added']:
                assert ed(u,v) not in S;S.add(ed(u,v))
        adj=[[] for _ in range(n+1)]
        for u,v in S:adj[u].append(v);adj[v].append(u)
        assert all(len(adj[i])==2 for i in range(1,n+1))
        seen=bytearray(n+1);small=[]
        for start in range(1,n+1):
            if seen[start]:continue
            u=start;prev=0;cycle=[]
            while not seen[u]:
                seen[u]=1;cycle.append(u)
                x,y=adj[u];nxt=x if x!=prev else y
                prev,u=u,nxt
            assert u==start
            if len(cycle)<=20:small.extend(cycle)
        return set(small)
    actual=derive([52,105])
    assert actual==anchors,(sorted(actual),sorted(anchors))
    assert derive([52])<=anchors
    found={}
    for u in sorted(anchors):
        for v in adjacency[u]:
            if v==u:continue
            local={x for x in (owner[u],owner[v]) if x>=0}
            bits=sorted(local)
            for mask in range(1<<len(bits)):
                states={i:(mask>>q)&1 for q,i in enumerate(bits)}
                un=b1[u] if owner[u]>=0 and states[owner[u]] else b0[u]
                vn=b1[v] if owner[v]>=0 and states[owner[v]] else b0[v]
                if v in un:continue
                for x in un:
                    for y in vn:
                        if len({u,v,x,y})!=4:continue
                        second=ed(x,y)
                        if second not in W:continue
                        old=tuple(sorted((ed(u,x),ed(v,y))))
                        new=tuple(sorted((ed(u,v),second)))
                        gain=sum(W[e] for e in old)-sum(W[e] for e in new)
                        if not a.min_gain<=gain<=a.max_gain:continue
                        key=(old,new)
                        if key not in found:
                            found[key]={'gain':gain,
                                'old':[list(e) for e in old],
                                'added':[list(e) for e in new],
                                'anchor':u,
                                'local_state_example':{str(i):b for i,b in states.items()}}
                        else:assert found[key]['gain']==gain
    items=sorted(found.values(),key=lambda m:(-m['gain'],m['anchor']))
    out={'source':'public ElimTSP graph and 51-switch neutral family',
        'anchor_vertices':sorted(anchors),'positive_2factor_motifs':[52,105],
        'minimum_gain':a.min_gain,'maximum_gain':a.max_gain,
        'bridge_motifs':items}
    target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(out,separators=(',',':'))+'\n')
    print(json.dumps({'anchor_vertices':len(anchors),
         'bridge_motifs':len(items),'gain_histogram':dict(sorted(
             (g,sum(m['gain']==g for m in items)) for g in {m['gain'] for m in items}))}),flush=True)
if __name__=='__main__':main()
