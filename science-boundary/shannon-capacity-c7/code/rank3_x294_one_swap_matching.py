#!/usr/bin/env python3
import argparse,json
from collections import deque
from pathlib import Path
from pysat.examples.rc2 import RC2
from pysat.formula import IDPool,WCNF
import generalized9 as g
import neutral2_maxsat as nm
import rank3_square_relax as rs

SPECIAL=294; BASELINE=134753

def hk(adj,nr):
    nl=len(adj);pu=[-1]*nl;pv=[-1]*nr;dist=[0]*nl;m=0
    while True:
        q=deque();found=False
        for u in range(nl):
            if pu[u]<0:dist[u]=0;q.append(u)
            else:dist[u]=-1
        while q:
            u=q.popleft()
            for v in adj[u]:
                w=pv[v]
                if w<0:found=True
                elif dist[w]<0:dist[w]=dist[u]+1;q.append(w)
        if not found:break
        def dfs(u):
            for v in adj[u]:
                w=pv[v]
                if w<0 or (dist[w]==dist[u]+1 and dfs(w)):
                    pu[u]=v;pv[v]=u;return True
            dist[u]=-1;return False
        for u in range(nl):
            if pu[u]<0 and dfs(u):m+=1
    return m

def closure_candidate(F,weights,xset,digits,hs,vs,r,bidx,baseline_ids):
    pool=IDPool();w=WCNF();E=[pool.id(('e',i)) for i in range(len(F))];Y=[pool.id(('y',j)) for j in range(g.R_SIZE)]
    for z in E:w.append([z],weight=1)
    for j,c in enumerate(weights):
        if c:w.append([-Y[j]],weight=c)
    for i,e in enumerate(F):
        for j,x in enumerate(xset):
            if g.conflict(e,x,digits):w.append([-E[i],Y[j]])
    with RC2(w,solver='g3',adapt=True,exhaust=True) as rc2:model=rc2.compute();cost=rc2.cost
    if model is None:raise RuntimeError('closure no model')
    pos={z for z in model if z>0};chosen=[F[i] for i,z in enumerate(E) if z in pos];hit=[j for j,z in enumerate(Y) if z in pos];pen=sum(weights[j] for j in hit);obj=len(chosen)-pen
    nh=[list(a) for a in hs];nv=[list(a) for a in vs];nh[SPECIAL]=chosen;removed=0
    for j in hit:
        keep=[]
        for f in nv[j]:
            if g.conflict(xset[SPECIAL],f,digits):removed+=1
            else:keep.append(f)
        nv[j]=keep
    if removed!=pen:raise RuntimeError('penalty replay mismatch')
    cert=rs.build_candidate(r,xset,bidx,nh,nv,[]);return obj,cert,len(chosen),pen,cost,len(baseline_ids-cert),len(cert-baseline_ids)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('baseline',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--family',choices=('r0','rank3','x'),required=True);args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U));r0=g.load_r(args.r367);xset=g.make_x(r0,digits);r=rs.load_rank3_state(r0,digits);supports,_=g.support_masks(r,digits)
    base_model,bst=nm.solve_maxsat(rs.RANK3_K9,r,xset,digits,supports)
    if base_model is None or bst['score']!=BASELINE:raise RuntimeError(f'base tie drift {bst}')
    _,hs,vs=base_model;x0=xset[SPECIAL]
    weights=[sum(1 for f in arr if g.conflict(x0,f,digits)) for arr in vs];positive=[j for j,c in enumerate(weights) if c];zero=[j for j,c in enumerate(weights) if not c]
    if len(positive)!=366 or any(weights[j]!=1 for j in positive):raise RuntimeError('weight pattern drift')
    ridx={j:k for k,j in enumerate(positive)}
    # adjacency of every ambient 5D point to positive-weight X nodes
    adj_all=[[] for _ in range(g.U)]
    for j in positive:
        k=ridx[j]
        for v in rs.neighborhood(xset[j],digits):adj_all[v].append(k)
    F=list(r0 if args.family=='r0' else r if args.family=='rank3' else xset);fset=set(F)
    # enumerate exact 1-for-1 swaps: replacement conflicts with exactly one F point
    swaps=[];owner_hist={}
    for v in range(g.U):
        if v in fset:continue
        owner=-1;cnt=0
        for i,u in enumerate(F):
            if g.conflict(v,u,digits):
                cnt+=1;owner=i
                if cnt>1:break
        if cnt==1:
            swaps.append((owner,v));owner_hist[owner]=owner_hist.get(owner,0)+1
    base_m=hk([adj_all[v] for v in F],366)
    if base_m!=366:raise RuntimeError(f'base matching {base_m}')
    best_m=366;best=[];hist={};checked=0
    for owner,v in swaps:
        G=F.copy();G[owner]=v;m=hk([adj_all[z] for z in G],366);checked+=1;hist[m]=hist.get(m,0)+1
        if m<best_m:best_m=m;best=[(owner,v)]
        elif m==best_m and len(best)<100:best.append((owner,v))
    status={'candidate':False,'family':args.family,'method':'rank3-x294-one-swap-hall','base_matching':base_m,'legal_one_swaps':len(swaps),'owners_with_swaps':len(owner_hist),'matching_histogram':{str(k):v for k,v in sorted(hist.items())},'min_matching':best_m,'max_closure_objective':367-best_m,'best_swaps':[list(z) for z in best],'zero_weight_x_indices':zero,'base_maxsat':bst}
    if best_m<=365:
        owner,v=best[0];G=F.copy();G[owner]=v;bidx=[i for i in range(g.R_SIZE) if i not in set(rs.RANK3_K9)];baseline_ids={int(p,7) for p in json.loads(args.baseline.read_text())['points']};obj,cert,nsel,pen,cost,rm,ad=closure_candidate(G,weights,xset,digits,hs,vs,r,bidx,baseline_ids);score=BASELINE+(obj-len(hs[SPECIAL]))
        if len(cert)!=score or score<=BASELINE:raise RuntimeError(f'closure replay failed obj={obj} score={score} cert={len(cert)}')
        status.update({'candidate':True,'score':score,'winning_swap_owner':owner,'winning_swap_old':F[owner],'winning_swap_new':v,'winning_swap_new_word':''.join(map(str,digits[v])),'closure_objective':obj,'selected_endpoints':nsel,'penalty_old_v_ports':pen,'rc2_cost':cost,'removed_vs_baseline':rm,'added_vs_baseline':ad})
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':[g.dec10(z) for z in sorted(cert)]},separators=(',',':'))+'\n')
    args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(('FOUND' if status['candidate'] else 'NONE'),json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
