#!/usr/bin/env python3
import argparse,json
from itertools import combinations
from pathlib import Path
from pysat.examples.rc2 import RC2
from pysat.formula import IDPool,WCNF
import generalized9 as g
import neutral2_maxsat as nm
import rank3_square_relax as rs

SPECIAL=294; BASELINE=134753

def shifted(vals,t,digits):
    td=digits[t]
    return [g.enc5(tuple((digits[v][q]+td[q])%7 for q in range(5))) for v in vals]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('baseline',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--families',required=True);ap.add_argument('--translation-a',type=int,default=0);ap.add_argument('--translation-b',type=int,default=0);args=ap.parse_args()
    fa,fb=args.families.split('+')
    if fa not in ('r0','rank3','x') or fb not in ('r0','rank3','x') or fa==fb:raise SystemExit('families must be distinct a+b')
    digits=tuple(g.dec5(v) for v in range(g.U));r0=g.load_r(args.r367);xset=g.make_x(r0,digits);r=rs.load_rank3_state(r0,digits);supports,_=g.support_masks(r,digits)
    model,bst=nm.solve_maxsat(rs.RANK3_K9,r,xset,digits,supports)
    if model is None or bst['score']!=BASELINE:raise RuntimeError(f'base drift {bst}')
    _,hs,vs=model;x0=xset[SPECIAL];old_h=len(hs[SPECIAL])
    fam={'r0':tuple(r0),'rank3':tuple(r),'x':tuple(xset)}
    A=shifted(fam[fa],args.translation_a,digits);B=shifted(fam[fb],args.translation_b,digits);P=sorted(set(A)|set(B))
    weights=[sum(1 for f in arr if g.conflict(x0,f,digits)) for arr in vs]
    hits=[[j for j,x in enumerate(xset) if g.conflict(e,x,digits)] for e in P]
    pool=IDPool();w=WCNF();E=[pool.id(('e',i)) for i in range(len(P))];Y=[pool.id(('hit',j)) for j in range(g.R_SIZE)]
    for z in E:w.append([z],weight=1)
    for j,c in enumerate(weights):
        if c:w.append([-Y[j]],weight=c)
    impl=0
    for i,js in enumerate(hits):
        for j in js:w.append([-E[i],Y[j]]);impl+=1
    conflicts=0
    for i,e in enumerate(P):
        for j in range(i+1,len(P)):
            if g.conflict(e,P[j],digits):w.append([-E[i],-E[j]]);conflicts+=1
    with RC2(w,solver='g3',adapt=True,exhaust=True,verbose=1) as rc2:m=rc2.compute();cost=rc2.cost
    if m is None:raise RuntimeError('union closure no model')
    pos={z for z in m if z>0};chosen=[P[i] for i,z in enumerate(E) if z in pos];hitjs=[j for j,z in enumerate(Y) if z in pos];penalty=sum(weights[j] for j in hitjs);objective=len(chosen)-penalty;gain=objective-old_h;score=BASELINE+gain
    # replay chosen independence
    for i in range(len(chosen)):
        for j in range(i+1,len(chosen)):
            if g.conflict(chosen[i],chosen[j],digits):raise RuntimeError('chosen union subset conflict')
    nh=[list(a) for a in hs];nv=[list(a) for a in vs];nh[SPECIAL]=chosen;removed=0;hitset=set(hitjs)
    for j,arr in enumerate(nv):
        if j not in hitset:continue
        keep=[]
        for f in arr:
            if g.conflict(x0,f,digits):removed+=1
            else:keep.append(f)
        nv[j]=keep
    if removed!=penalty:raise RuntimeError('penalty replay mismatch')
    bidx=[i for i in range(g.R_SIZE) if i not in set(rs.RANK3_K9)];cert=rs.build_candidate(r,xset,bidx,nh,nv,[])
    if len(cert)!=score:raise RuntimeError(f'score mismatch {len(cert)}!={score}')
    base={int(p,7) for p in json.loads(args.baseline.read_text())['points']}
    st={'candidate':score>BASELINE,'score':score,'method':'rank3-x294-two-family-union-closure','families':[fa,fb],'translations':[args.translation_a,args.translation_b],'pool_size':len(P),'chosen_endpoints':len(chosen),'hit_x_indices':len(hitjs),'penalty_old_v_ports':penalty,'closure_objective':objective,'old_h294':old_h,'net_gain':gain,'endpoint_conflict_clauses':conflicts,'implications':impl,'rc2_cost':cost,'removed_vs_baseline':len(base-cert),'added_vs_baseline':len(cert-base)}
    args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print(('FOUND' if score>BASELINE else 'NONE'),json.dumps(st,sort_keys=True),flush=True)
    if score>BASELINE:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':[g.dec10(v) for v in sorted(cert)]},separators=(',',':'))+'\n')
if __name__=='__main__':main()
