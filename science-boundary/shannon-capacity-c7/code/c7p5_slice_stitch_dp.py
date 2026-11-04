#!/usr/bin/env python3
"""Exact cyclic dynamic-programming recombination of C7^5 coordinate slices.

Take the full 7-slice decomposition of each known 367-word five-dimensional
source, independently translate the four remaining coordinates in each slice,
and choose one complete slice template at each cyclic symbol. A transition is
allowed exactly when the two corresponding 4D projections have no confusable
pair. Maximum-weight 7-cycle DP finds the exact largest 5D code in this
explicit structured universe (not in the full C7^5 graph).
"""
from __future__ import annotations
import argparse,itertools,json,time
from pathlib import Path
from c7p5_two_layer_repair import digits5,proj,lift,independent,dump_certificate,NEIGH4,N4

SHIFTS=[(0,0,0,0)]
for i in range(4):
    for d in (-3,-2,-1,1,2,3):
        z=[0]*4;z[i]=d;SHIFTS.append(tuple(z))
for i,j in itertools.combinations(range(4),2):
    for a,b in itertools.product((-1,1),repeat=2):
        z=[0]*4;z[i]=a;z[j]=b;SHIFTS.append(tuple(z))
assert len(SHIFTS)==49

def shifts_of(q):
    d=tuple((q//(7**j))%7 for j in range(4))
    return tuple(sum(((d[j]+h[j])%7)*(7**j) for j in range(4)) for h in SHIFTS)

SHIFT_Q=tuple(shifts_of(q) for q in range(N4))
NBITS=tuple(sum(1<<x for x in NEIGH4[q]) for q in range(N4))

def gather(raw,fam):
    sets=[('I0',sorted(map(int,raw['I0']))),('X',sorted(map(int,raw['X'])))]
    for i,L in enumerate(fam['states']):sets.append((f'familyF_{i}',sorted(map(int,L))))
    for name,L in sets:
        if len(L)!=367 or len(set(L))!=367 or not independent(L):
            raise RuntimeError(('invalid public seed',name))
    return sets

def templates(seeds,axis):
    by=[{} for _ in range(7)]
    for name,S in seeds:
        ps=[[] for _ in range(7)]
        for v in S:ps[digits5(v)[axis]].append(proj(v,axis))
        for lay,P in enumerate(ps):
            for j,shift in enumerate(SHIFTS):
                qs=tuple(sorted(SHIFT_Q[q][j] for q in P))
                mask=sum(1<<q for q in qs)
                if mask in by[lay]:continue
                nb=0
                for q in qs:nb|=NBITS[q]
                by[lay][mask]={'mask':mask,'neigh':nb,'q':qs,
                               'size':len(qs),'origin':name,'shift':list(shift)}
    return [list(D.values()) for D in by]

def cyclic_dp(T):
    ed=[];edge_sizes=[]
    for s in range(7):
        current=T[s];nxt=T[(s+1)%7]
        edges=[[] for _ in current]
        for i,a in enumerate(current):
            bad=a['neigh']
            edges[i]=[j for j,b in enumerate(nxt) if bad&b['mask']==0]
        ed.append(edges)
        edge_sizes.append(sum(map(len,edges)))
    best=(-1,None)
    # Exact longest path in a 7-partite cycle, fixing one candidate at layer 0.
    for start,a0 in enumerate(T[0]):
        dp={start:(a0['size'],(start,))}
        for layer in range(6):
            nd={}
            for j,(value,path) in dp.items():
                for k in ed[layer][j]:
                    v=value+T[layer+1][k]['size']
                    if k not in nd or v>nd[k][0]:
                        nd[k]=(v,path+(k,))
            dp=nd
            if not dp:break
        for j,(score,path) in dp.items():
            if start in ed[6][j] and score>best[0]:best=(score,path)
    return best,edge_sizes

def run(seeds,axis,cert):
    t0=time.monotonic()
    T=templates(seeds,axis)
    (score,path),edges=cyclic_dp(T)
    if path is None:raise RuntimeError(('no cycle',axis))
    S=set()
    trace=[]
    for layer,k in enumerate(path):
        x=T[layer][k]
        for q in x['q']:S.add(lift(q,axis,layer))
        trace.append({'layer':layer,'size':x['size'],'source':x['origin'],'shift':x['shift']})
    assert len(S)==score and independent(S)
    have=dump_certificate(S,cert) if score>=368 else False
    return {'axis':axis,'best_size':score,'candidate_368':have,
            'template_count_by_layer':list(map(len,T)),
            'compatible_edges_by_boundary':edges,
            'source_count':len(seeds),'shift_count':len(SHIFTS),
            'best_path':trace,'seconds':time.monotonic()-t0}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('tan',type=Path);p.add_argument('family',type=Path)
    p.add_argument('result',type=Path);p.add_argument('certificate',type=Path)
    p.add_argument('--axis',type=int,required=True)
    a=p.parse_args()
    seeds=gather(json.loads(a.tan.read_text()),json.loads(a.family.read_text()))
    out=run(seeds,a.axis,a.certificate)
    a.result.parent.mkdir(parents=True,exist_ok=True)
    a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True),flush=True)

if __name__=='__main__':main()
