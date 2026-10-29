#!/usr/bin/env python3
"""Two-stage topology repair: improving split followed by costly bridge.

The second swap is enumerated ON THE DISCONNECTED 2-FACTOR so it can remove
edges added by the first. Base, all one-bit neutral states, and optionally
two-bit neutral states are searched. Any improving tour is checked upstream.
"""
import argparse,gzip,importlib.util,json,os,time
from pathlib import Path

def ed(a,b):return (a,b) if a<b else (b,a)

def twofactor(n,edges):
    adj=[[] for _ in range(n+1)]
    for a,b in edges:adj[a].append(b);adj[b].append(a)
    assert all(len(adj[v])==2 for v in range(1,n+1))
    seen=bytearray(n+1);label=[0]*(n+1);cycles=[]
    for start in range(1,n+1):
        if seen[start]:continue
        cid=len(cycles)+1;now=start;prev=0;cities=[]
        while not seen[now]:
            seen[now]=1;label[now]=cid;cities.append(now)
            x,y=adj[now];nxt=x if x!=prev else y
            prev,now=now,nxt
        assert now==start
        cycles.append(cities)
    return adj,label,cycles

def main():
    p=argparse.ArgumentParser()
    for k in ('graph','baseline','neutral-moves','positive-motifs','report','candidate'):
        p.add_argument('--'+k,required=True)
    p.add_argument('--seed-indices',default='52,105')
    p.add_argument('--max-switches',type=int,default=1)
    a=p.parse_args();begin=time.monotonic()
    base_t=json.loads(Path(a.baseline).read_text())['tour'];n=len(base_t)
    assert n==100000
    base={ed(base_t[i],base_t[(i+1)%n]) for i in range(n)}
    moves=json.loads(Path(a.neutral_moves).read_text())
    mods=[moves['moves'][i] for i in moves['selected_indices']]
    assert len(mods)==51
    oldsets=[{ed(*x) for x in m['removed']} for m in mods]
    newsets=[{ed(*x) for x in m['added']} for m in mods]
    source=json.loads(Path(a.positive_motifs).read_text())['positive_repair_motifs']
    with gzip.open(a.graph,'rt') as f:
        head=list(map(int,f.readline().split()))
        raw=[tuple(map(int,x.split())) for x in f if x.strip()]
    assert head==[n,len(raw)]
    off=0 if min(min(u,v) for u,v,w in raw)==0 else 1
    W={ed(u-off+1,v-off+1):w for u,v,w in raw}
    adjW=[[] for _ in range(n+1)]
    for u,v in W:adjW[u].append(v);adjW[v].append(u)
    spec=importlib.util.spec_from_file_location('v',Path(os.environ['FEWSHOTS_ROOT'])/
         'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    assert v.tour_length(base_t)==5757191
    masks=[0]+[1<<i for i in range(51)]
    if a.max_switches>=2:
        masks += [(1<<i)|(1<<j) for i in range(51) for j in range(i+1,51)]
    records=[];best=None
    for j in map(int,a.seed_indices.split(',')):
        motif=source[j]
        gain=motif['gain']
        assert gain>0
        old_seed={ed(*e) for e in motif['old']}
        new_seed={ed(*e) for e in motif['added']}
        for mask in masks:
            edges=set(base)
            for i in range(51):
                if (mask>>i)&1:edges.difference_update(oldsets[i])
            for i in range(51):
                if (mask>>i)&1:edges.update(newsets[i])
            if not old_seed<=edges or (new_seed&edges):continue
            edges.difference_update(old_seed);edges.update(new_seed)
            adj,labels,cycles=twofactor(n,edges)
            if len(cycles)!=2:continue
            small=min(cycles,key=len)
            local_best=None;bridges=0
            for u in small:
                for w in adjW[u]:
                    if labels[w]==labels[u]:continue
                    for pu in adj[u]:
                        for pw in adj[w]:
                            second=ed(pu,pw)
                            if second not in W:continue
                            bridges+=1
                            old1=ed(u,pu);old2=ed(w,pw)
                            new1=ed(u,w)
                            net=gain+W[old1]+W[old2]-W[new1]-W[second]
                            if local_best is None or net>local_best[0]:
                                local_best=(net,old1,old2,new1,second)
            rec={'seed':j,'switch_mask':str(mask),'seed_gain':gain,
                 'small_cycle':len(small),'bridge_pairings':bridges,
                 'best_total_gain':local_best[0] if local_best else None}
            records.append(rec)
            if local_best is None:continue
            net,old1,old2,new1,new2=local_best
            if best is None or net>best[0]:
                best=(net,j,mask)
                if net>0:
                    new_edges=set(edges)
                    new_edges.remove(old1);new_edges.remove(old2)
                    new_edges.add(new1);new_edges.add(new2)
                    _,_,fixed_cycles=twofactor(n,new_edges)
                    assert len(fixed_cycles)==1
                    route=fixed_cycles[0]
                    score=v.tour_length(route)
                    assert score==5757191-net and score<5757191
                    target=Path(a.candidate);target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_text(json.dumps({'tour':route},separators=(',',':')))
                    print(json.dumps({'stage':'improvement','seed':j,'mask':str(mask),
                         'score':score,'net':net}),flush=True)
        print(json.dumps({'stage':'seed_complete','seed':j,
              'checked_masks':sum(r['seed']==j for r in records),
              'best_net':best[0] if best else None}),flush=True)
    report={'baseline':5757191,'seeds':list(map(int,a.seed_indices.split(','))),
        'switch_state_max_weight':a.max_switches,
        'checked_split_instances':len(records),
        'bridged_instances':sum(x['best_total_gain'] is not None for x in records),
        'max_net_gain':best[0] if best else None,
        'best':{'gain':best[0],'seed':best[1],'mask':str(best[2])} if best else None,
        'strict_improvement':bool(best and best[0]>0),
        'records':records,'wall_seconds':round(time.monotonic()-begin,2)}
    dest=Path(a.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records'}),flush=True)
if __name__=='__main__':main()
