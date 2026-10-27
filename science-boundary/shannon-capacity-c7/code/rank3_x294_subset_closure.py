#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from pysat.examples.rc2 import RC2
from pysat.formula import IDPool,WCNF
import generalized9 as g
import neutral2_maxsat as nm
import rank3_square_relax as rs

SPECIAL=294
BASELINE=134753

def shifted(vals,t,digits):
    td=digits[t]
    return [g.enc5(tuple((digits[v][q]+td[q])%7 for q in range(5))) for v in vals]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('baseline',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--family',choices=('r0','rank3','x'),required=True);ap.add_argument('--translation-id',type=int,default=0);args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U));r0=g.load_r(args.r367);xset=g.make_x(r0,digits);r=rs.load_rank3_state(r0,digits);supports,_=g.support_masks(r,digits)
    model,bst=nm.solve_maxsat(rs.RANK3_K9,r,xset,digits,supports)
    if model is None or bst['score']!=BASELINE:raise RuntimeError(f'base drift {bst}')
    _,hs,vs=model;x0=xset[SPECIAL];old_h=list(hs[SPECIAL])
    base_family=tuple(r0 if args.family=='r0' else r if args.family=='rank3' else xset)
    F=shifted(base_family,args.translation_id,digits)
    if len(F)!=367 or len(set(F))!=367:raise RuntimeError('bad translated family')
    # F is a translate of a known independent C7^5 set; replay it.
    for i in range(len(F)):
        for j in range(i+1,len(F)):
            if g.conflict(F[i],F[j],digits):raise RuntimeError('translated family is not independent')

    # If any selected e conflicts X_j, all old V(j,f) with X294~f must be deleted.
    weights=[]
    for j,arr in enumerate(vs):weights.append(sum(1 for f in arr if g.conflict(x0,f,digits)))
    hits=[]
    for e in F:hits.append([j for j,x in enumerate(xset) if g.conflict(e,x,digits)])

    pool=IDPool();w=WCNF()
    E=[pool.id(('e',i)) for i in range(len(F))];Y=[pool.id(('hit',j)) for j in range(g.R_SIZE)]
    for z in E:w.append([z],weight=1)
    for j,cost in enumerate(weights):
        if cost:w.append([-Y[j]],weight=cost)
    implications=0
    for i,js in enumerate(hits):
        for j in js:w.append([-E[i],Y[j]]);implications+=1
    with RC2(w,solver='g3',adapt=True,exhaust=True,verbose=1) as rc2:m=rc2.compute();cost=rc2.cost
    if m is None:raise RuntimeError('closure MaxSAT returned no model')
    pos={z for z in m if z>0};chosen=[F[i] for i,z in enumerate(E) if z in pos];hitjs=[j for j,z in enumerate(Y) if z in pos];penalty=sum(weights[j] for j in hitjs)
    objective=len(chosen)-penalty;gain=objective-len(old_h);score=BASELINE+gain
    # RC2 objective identity: 367 - cost == chosen - penalty.
    if 367-cost!=objective:raise RuntimeError(f'objective mismatch {367-cost}!={objective}')

    nh=[list(a) for a in hs];nv=[list(a) for a in vs];nh[SPECIAL]=chosen;removed=0
    hitset=set(hitjs)
    for j,arr in enumerate(nv):
        if j not in hitset:continue
        keep=[]
        for f in arr:
            if g.conflict(x0,f,digits):removed+=1
            else:keep.append(f)
        nv[j]=keep
    if removed!=penalty:raise RuntimeError(f'penalty replay mismatch {removed}!={penalty}')
    bidx=[i for i in range(g.R_SIZE) if i not in set(rs.RANK3_K9)];cert=rs.build_candidate(r,xset,bidx,nh,nv,[])
    if len(cert)!=score:raise RuntimeError(f'certificate score mismatch {len(cert)}!={score}')
    baseline={int(p,7) for p in json.loads(args.baseline.read_text())['points']}
    st={'candidate':score>BASELINE,'score':score,'method':'rank3-x294-fixed-367-subset-closure','family':args.family,'translation_id':args.translation_id,'translation_digits':list(digits[args.translation_id]),'old_h294':len(old_h),'chosen_endpoints':len(chosen),'hit_x_indices':len(hitjs),'penalty_old_v_ports':penalty,'closure_objective':objective,'net_gain':gain,'rc2_cost':cost,'implications':implications,'weight_histogram':{str(x):weights.count(x) for x in sorted(set(weights))},'base_maxsat':bst,'removed_vs_baseline':len(baseline-cert),'added_vs_baseline':len(cert-baseline)}
    args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print(('FOUND' if score>BASELINE else 'NONE'),json.dumps(st,sort_keys=True),flush=True)
    if score>BASELINE:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':[g.dec10(v) for v in sorted(cert)]},separators=(',',':'))+'\n')
if __name__=='__main__':main()
