#!/usr/bin/env python3
"""Symbolic 2-edge exchange screening over an exponential neutral TSP family.

Every city's two tour neighbors depend on at most ONE of the 51 independent
binary switches. A 2-edge exchange using a candidate chord u-v has gain
determined only by the switches touching u and v (at most two), not 2**51
global configurations. Enumerate *all local switch states* exactly.

Positive-gain degree-two reconnections may disconnect the tour. Test those
against many globally valid 51-switch states; a found Hamiltonian cycle is
independently scored by the upstream verifier. A negative sampled result is
NOT a proof of global 2-opt optimality.
"""
import argparse,gzip,importlib.util,json,os,random,time
from pathlib import Path
from collections import defaultdict

def edge(a,b):return (a,b) if a<b else (b,a)
def tour_edges(t):return {edge(t[i],t[(i+1)%len(t)]) for i in range(len(t))}

def build_tour(base_edges,oldsets,newsets,mask,n):
    eds=set(base_edges)
    for i in range(len(oldsets)):
        if (mask>>i)&1:eds.difference_update(oldsets[i])
    for i in range(len(newsets)):
        if (mask>>i)&1:eds.update(newsets[i])
    assert len(eds)==n
    adj=[[] for _ in range(n+1)]
    for a,b in eds:adj[a].append(b);adj[b].append(a)
    assert all(len(adj[v])==2 for v in range(1,n+1))
    tour=[];seen=bytearray(n+1);cur=1;prev=0
    while not seen[cur]:
        seen[cur]=1;tour.append(cur)
        a,b=adj[cur];nxt=a if a!=prev else b
        prev,cur=cur,nxt
    assert cur==1 and len(tour)==n
    succ=[0]*(n+1)
    for i in range(n):succ[tour[i]]=tour[(i+1)%n]
    return eds,tour,succ

def main():
    p=argparse.ArgumentParser()
    for name in ('baseline','graph','moves','proof','report','candidate'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--samples',type=int,default=80)
    p.add_argument('--positive-file',default=None)
    args=p.parse_args()
    begin=time.monotonic()
    base_t=json.loads(Path(args.baseline).read_text())['tour']
    n=len(base_t);assert n==100000
    base=tour_edges(base_t)
    catalogue=json.loads(Path(args.moves).read_text())
    verified=json.loads(Path(args.proof).read_text())
    assert verified['universal_dimension']==51
    choices=catalogue['selected_indices']
    assert len(choices)==51
    moves=[catalogue['moves'][i] for i in choices]
    oldsets=[set(tuple(x) for x in m['removed']) for m in moves]
    newsets=[set(tuple(x) for x in m['added']) for m in moves]
    owner=[-1]*(n+1)
    b0=[None]*(n+1)
    for i,a in enumerate(base_t):
        b0[a]=(base_t[(i-1)%n],base_t[(i+1)%n])
    b1=list(b0)
    for i,(old,new) in enumerate(zip(oldsets,newsets)):
        changes={}
        for a,b in old:
            changes.setdefault(a,list(b0[a])).remove(b)
            changes.setdefault(b,list(b0[b])).remove(a)
        for a,b in new:
            changes.setdefault(a,list(b0[a]))
            changes.setdefault(b,list(b0[b]))
            changes[a].append(b);changes[b].append(a)
        for u,newnbr in changes.items():
            assert len(newnbr)==2 and len(set(newnbr))==2
            assert owner[u] in (-1,i)
            owner[u]=i
            b1[u]=tuple(newnbr)
    assert sum(x>=0 for x in owner)==len({v for m in moves for pair in m['removed']+m['added'] for v in pair})
    spec=importlib.util.spec_from_file_location('p010_verifier',
         Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    xs,ys=v.coordinates()
    assert v.tour_length(base_t)==5757191
    with gzip.open(args.graph,'rt') as f:
        head=list(map(int,f.readline().split()))
        raw=[tuple(map(int,line.split())) for line in f if line.strip()]
    assert head==[n,len(raw)]
    off=0 if min(min(a,b) for a,b,w in raw)==0 else 1
    W={edge(a-off+1,b-off+1):w for a,b,w in raw}
    assert base<=W.keys()
    # Independent exact audit of every public candidate edge weight.
    for (a,b),w in W.items():
        assert w==v.euc_2d(xs[a-1]-xs[b-1],ys[a-1]-ys[b-1])
    rng=random.Random(20871)
    allbits=(1<<len(moves))-1
    bestmask=sum(1<<i for i,m in enumerate(moves) if m['continuous_delta']<0)
    masks=set([0,allbits,bestmask])
    while len(masks)<args.samples:masks.add(rng.getrandbits(len(moves)))
    sample=[]
    for mask in sorted(masks):
        _,_,succ=build_tour(base,oldsets,newsets,mask,n)
        sample.append((mask,succ))
    print(json.dumps({'stage':'loaded','switches':len(moves),'changed_vertices':sum(x>=0 for x in owner),
          'tour_samples':len(sample),'graph_edges':len(W)}),flush=True)
    pair_count=0;positive_local=0;positive_seen=0;best=None
    positive_motifs={}
    gain_hist=defaultdict(int)
    for (a,b),chord_cost in W.items():
        if a==b:continue
        possible=sorted({owner[a],owner[b]}-{-1})
        for localbits in range(1<<len(possible)):
            states={x:(localbits>>i)&1 for i,x in enumerate(possible)}
            na=b1[a] if owner[a]>=0 and states[owner[a]] else b0[a]
            nb=b1[b] if owner[b]>=0 and states[owner[b]] else b0[b]
            if b in na:continue
            for aa in na:
                for bb in nb:
                    if len({a,b,aa,bb})<4:continue
                    second=edge(aa,bb)
                    if second not in W:continue
                    gain=W[edge(a,aa)]+W[edge(b,bb)]-chord_cost-W[second]
                    pair_count+=1
                    if gain<=0:continue
                    positive_local+=1
                    gain_hist[gain]+=1
                    old=tuple(sorted((edge(a,aa),edge(b,bb))))
                    new=tuple(sorted((edge(a,b),second)))
                    mkey=(old,new)
                    if mkey not in positive_motifs:
                        positive_motifs[mkey]={'gain':gain,'old':[list(z) for z in old],
                             'added':[list(z) for z in new],
                             'local_state_example':{str(i):st for i,st in states.items()}}
                    else:
                        assert positive_motifs[mkey]['gain']==gain
                    for mask,succ in sample:
                        if any(((mask>>i)&1)!=state for i,state in states.items()):
                            continue
                        # The two removed edges must have compatible tour
                        # orientation for the new pairing to be connected.
                        if (succ[a]==aa)!=(succ[b]==bb):continue
                        positive_seen+=1
                        if best is None or gain>best['gain']:
                            best={'gain':gain,'mask':mask,'old1':edge(a,aa),
                                  'old2':edge(b,bb),'new1':edge(a,b),'new2':second,
                                  'local_switch_states':states}
                        break
    if args.positive_file:
        target_motifs=Path(args.positive_file)
        target_motifs.parent.mkdir(parents=True,exist_ok=True)
        target_motifs.write_text(json.dumps({'source':'symbolic_hypercube_2opt.py',
           'baseline_score':5757191,'switches':len(moves),
           'positive_repair_motifs':sorted(positive_motifs.values(),key=lambda x:-x['gain'])},
           separators=(',',':'))+'\n')
    result={'baseline_score':5757191,'switches':len(moves),
            'sampled_global_states':len(sample),
            'unique_positive_repair_motifs':len(positive_motifs),
            'local_pairings_checked':pair_count,
            'positive_gain_pairings_ignoring_global_connectivity':positive_local,
            'positive_gain_pairings_with_connectivity_in_sample':positive_seen,
            'positive_gain_histogram':dict(sorted(gain_hist.items())),
            'seconds':round(time.monotonic()-begin,2)}
    if best:
        mask=best['mask']
        eds,_,_=build_tour(base,oldsets,newsets,mask,n)
        assert best['old1'] in eds and best['old2'] in eds
        assert best['new1'] not in eds and best['new2'] not in eds
        eds.difference_update((best['old1'],best['old2']))
        eds.update((best['new1'],best['new2']))
        adj=[[] for _ in range(n+1)]
        for a,b in eds:
            adj[a].append(b);adj[b].append(a)
        assert all(len(adj[x])==2 for x in range(1,n+1))
        visited=bytearray(n+1);cur=1;prev=0;route=[]
        while not visited[cur]:
            visited[cur]=1;route.append(cur)
            u,vv=adj[cur];nxt=u if u!=prev else vv
            prev,cur=cur,nxt
        assert cur==1 and len(route)==n
        score=v.tour_length(route)
        assert score==5757191-best['gain'] and score<5757191
        cert=Path(args.candidate);cert.parent.mkdir(parents=True,exist_ok=True)
        cert.write_text(json.dumps({'tour':route},separators=(',',':')))
        result['improvement_found']=True
        result['best_verified_score']=score
        result['best_repair']={k:(list(q) if isinstance(q,tuple) else q) for k,q in best.items()}
        result['canonical_hash']=v.canonical_hash({'tour':v.canonical_tour(route)})
    else:
        result['improvement_found']=False
        result['note']='No improving 2-edge exchange witnessed among sampled global switch states. Positive local pairings may still be disconnected in some/all states.'
    target=Path(args.report);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='positive_gain_histogram'}),flush=True)
if __name__=='__main__':main()
