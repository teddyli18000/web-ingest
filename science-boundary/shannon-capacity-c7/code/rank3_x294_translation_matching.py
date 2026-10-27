#!/usr/bin/env python3
import argparse,json
from collections import deque
from pathlib import Path
import generalized9 as g
import neutral2_maxsat as nm
import rank3_square_relax as rs

SPECIAL=294

def hopcroft_karp(adj,nr):
    nl=len(adj); pairu=[-1]*nl; pairv=[-1]*nr; dist=[0]*nl; matching=0
    while True:
        q=deque(); found=False
        for u in range(nl):
            if pairu[u]<0:dist[u]=0;q.append(u)
            else:dist[u]=-1
        while q:
            u=q.popleft()
            for v in adj[u]:
                pu=pairv[v]
                if pu<0:found=True
                elif dist[pu]<0:dist[pu]=dist[u]+1;q.append(pu)
        if not found:break
        def dfs(u):
            for v in adj[u]:
                pu=pairv[v]
                if pu<0 or (dist[pu]==dist[u]+1 and dfs(pu)):
                    pairu[u]=v;pairv[v]=u;return True
            dist[u]=-1;return False
        for u in range(nl):
            if pairu[u]<0 and dfs(u):matching+=1
    return matching

def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--family',choices=('r0','rank3','x'),required=True);args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U));r0=g.load_r(args.r367);xset=g.make_x(r0,digits);r=rs.load_rank3_state(r0,digits);supports,_=g.support_masks(r,digits)
    model,bst=nm.solve_maxsat(rs.RANK3_K9,r,xset,digits,supports)
    if model is None or bst['score']!=134753:raise RuntimeError(f'base drift {bst}')
    _,_,vs=model;x0=xset[SPECIAL]
    weights=[sum(1 for f in arr if g.conflict(x0,f,digits)) for arr in vs]
    positive=[j for j,w in enumerate(weights) if w>0];zero=[j for j,w in enumerate(weights) if w==0]
    if len(positive)!=366 or len(zero)!=1 or any(weights[j]!=1 for j in positive):raise RuntimeError(f'unexpected weights: zero={zero}, hist={{x:weights.count(x) for x in set(weights)}}')
    ridx={j:k for k,j in enumerate(positive)}
    hits=[[] for _ in range(g.U)]
    for j in positive:
        k=ridx[j]
        for v in rs.neighborhood(xset[j],digits):hits[v].append(k)
    base=tuple(r0 if args.family=='r0' else r if args.family=='rank3' else xset)
    bd=[digits[v] for v in base]
    best_m=367;best=[];hist={}
    for t in range(g.U):
        td=digits[t];adj=[]
        for a in bd:
            v=g.enc5(tuple((a[q]+td[q])%7 for q in range(5)));adj.append(hits[v])
        m=hopcroft_karp(adj,366);hist[m]=hist.get(m,0)+1
        if m<best_m:best_m=m;best=[t]
        elif m==best_m and len(best)<100:best.append(t)
    out={'family':args.family,'positive_weight_x_count':len(positive),'zero_weight_x_indices':zero,'min_maximum_matching':best_m,'max_closure_objective':367-best_m,'breakthrough_possible_in_translation_family':best_m<=365,'best_translation_ids':best,'best_translation_digits':[list(digits[t]) for t in best],'matching_histogram':{str(k):v for k,v in sorted(hist.items())},'base_maxsat':bst}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True),flush=True)
if __name__=='__main__':main()
