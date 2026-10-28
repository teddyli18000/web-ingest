#!/usr/bin/env python3
"""Exact all-sparse-chord 2-opt scan across all 64 neutral hypercube vertices."""
import argparse,gzip,importlib.util,json,os,time
from pathlib import Path

def e(a,b):return (a,b) if a<b else (b,a)
def tour_edges(t):return {e(t[i],t[(i+1)%len(t)]) for i in range(len(t))}
def to_tour(n,edges):
    adj=[[] for _ in range(n+1)]
    for a,b in edges:
        adj[a].append(b);adj[b].append(a)
    assert all(len(adj[i])==2 for i in range(1,n+1))
    t=[];prev=0;u=1;seen=bytearray(n+1)
    while not seen[u]:
        seen[u]=1;t.append(u)
        a,b=adj[u];nxt=a if a!=prev else b
        prev,u=u,nxt
    assert u==1 and len(t)==n
    return t
def main():
    p=argparse.ArgumentParser()
    for name in ('edges','baseline','moves','report','output-dir'):p.add_argument('--'+name,required=True)
    p.add_argument('--mask-start',type=int,default=0)
    p.add_argument('--mask-count',type=int,default=16)
    args=p.parse_args();begin=time.monotonic()
    base_t=json.loads(Path(args.baseline).read_text())['tour']
    n=len(base_t);assert n==100000
    base_edges=tour_edges(base_t)
    mods=[]
    for move in json.loads(Path(args.moves).read_text())['neutral_moves']:
        mods.append((set(map(tuple,move['removed'])),set(map(tuple,move['added']))))
    assert len(mods)==6
    with gzip.open(args.edges,'rt') as f:
        header=list(map(int,f.readline().split()))
        raw=[tuple(map(int,line.split())) for line in f if line.strip()]
    assert header==[n,len(raw)]
    off=0 if min(min(a,b) for a,b,w in raw)==0 else 1
    chords=[(a-off+1,b-off+1,w) for a,b,w in raw]
    del raw
    spec=importlib.util.spec_from_file_location('v',Path(os.environ['FEWSHOTS_ROOT'])/
        'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    xs,ys=v.coordinates()
    def dist(a,b):
        ia=a-1;ib=b-1
        return v.euc_2d(xs[ia]-xs[ib],ys[ia]-ys[ib])
    assert v.tour_length(base_t)==5757191
    outdir=Path(args.output_dir);outdir.mkdir(parents=True,exist_ok=True)
    records=[]
    for mask in range(args.mask_start,min(64,args.mask_start+args.mask_count)):
        changed=set(base_edges)
        for i,(old,new) in enumerate(mods):
            if (mask>>i)&1:changed.difference_update(old)
        for i,(old,new) in enumerate(mods):
            if (mask>>i)&1:changed.update(new)
        t=to_tour(n,changed)
        position=[0]*(n+1)
        for i,city in enumerate(t):position[city]=i
        outgoing=[dist(t[i],t[(i+1)%n]) for i in range(n)]
        incoming=[outgoing[(i-1)%n] for i in range(n)]
        assert sum(outgoing)==5757191
        best=None;tested=0
        for a,b,w in chords:
            i=position[a];j=position[b]
            if i>j:i,j=j,i
            if j==i+1 or (i==0 and j==n-1):continue
            tested+=1
            gain1=outgoing[i]+outgoing[j]-w-dist(t[(i+1)%n],t[(j+1)%n])
            gain2=incoming[i]+incoming[j]-w-dist(t[(i-1)%n],t[(j-1)%n])
            if gain1>0 and (best is None or gain1>best[0]):
                best=(gain1,i,j,1)
            if gain2>0 and (best is None or gain2>best[0]):
                best=(gain2,i,j,2)
        rec={'mask':mask,'tested_chords':tested,'best_gain':best[0] if best else 0}
        if best:
            gain,i,j,variant=best
            if variant==1:t[i+1:j+1]=reversed(t[i+1:j+1])
            else:t[i:j]=reversed(t[i:j])
            score=v.tour_length(t)
            assert score==5757191-gain and score<5757191
            output=outdir/f'candidate-mask-{mask:02d}.json'
            output.write_text(json.dumps({'tour':t},separators=(',',':')))
            rec.update({'score':score,'candidate':str(output),'variant':variant})
        records.append(rec)
        print(json.dumps({'stage':'mask',**rec}),flush=True)
        Path(args.report).write_text(json.dumps({'records':records},indent=2)+'\n')
    out={'records':records,'best_score':min([x.get('score',5757191) for x in records]),
         'elapsed_seconds':round(time.monotonic()-begin,2)}
    Path(args.report).write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'stage':'complete','best_score':out['best_score'],'masks':len(records),
        'elapsed_seconds':out['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
