#!/usr/bin/env python3
"""Exact MaxSAT over all rank-3 asymmetric 8x9 deletion cases."""
import argparse,json
from itertools import combinations
from pathlib import Path
from pysat.examples.rc2 import RC2
from pysat.formula import IDPool,WCNF
import generalized9 as g
import rank3_square_relax as rs

BASELINE=134753; TARGET=134754; SQUARE=359*358

def optimize(kl,kr,r,x,digits,supports):
    ml=sum(1<<i for i in kl);mr=sum(1<<i for i in kr);sl=tuple(g.safe_vertices(ml,supports));sr=tuple(g.safe_vertices(mr,supports))
    pool=IDPool();w=WCNF();H=lambda i,e:pool.id(('H',i,e));V=lambda i,e:pool.id(('V',i,e))
    el=[(a,b) for a,b in combinations(range(len(sl)),2) if g.conflict(sl[a],sl[b],digits)];er=[(a,b) for a,b in combinations(range(len(sr)),2) if g.conflict(sr[a],sr[b],digits)]
    for i in range(g.R_SIZE):
        for a,b in el:w.append([-H(i,a),-H(i,b)])
        for a,b in er:w.append([-V(i,a),-V(i,b)])
    hitl=[[e for e,z in enumerate(sl) if g.conflict(z,xj,digits)] for xj in x];hitr=[[e for e,z in enumerate(sr) if g.conflict(z,xi,digits)] for xi in x]
    cross=0
    for i in range(g.R_SIZE):
        if not hitr[i]:continue
        for j in range(g.R_SIZE):
            if not hitl[j]:continue
            for e in hitl[j]:
                h=H(i,e)
                for f in hitr[i]:w.append([-h,-V(j,f)]);cross+=1
    soft=[]
    for i in range(g.R_SIZE):
        for e in range(len(sl)):z=H(i,e);soft.append(z);w.append([z],weight=1)
        for e in range(len(sr)):z=V(i,e);soft.append(z);w.append([z],weight=1)
    with RC2(w,solver='g3',adapt=True,exhaust=True,verbose=0) as rc2:model=rc2.compute();cost=rc2.cost
    if model is None:raise RuntimeError('hard clauses UNSAT')
    pos={z for z in model if z>0};hs=[[sl[e] for e in range(len(sl)) if H(i,e) in pos] for i in range(g.R_SIZE)];vs=[[sr[e] for e in range(len(sr)) if V(i,e) in pos] for i in range(g.R_SIZE)]
    sel=sum(map(len,hs))+sum(map(len,vs));return (hs,vs),{'safe_l':len(sl),'safe_r':len(sr),'selected_ports':sel,'score':SQUARE+sel,'rc2_cost':cost,'vars':pool.top,'cross_clauses':cross,'min_h':min(map(len,hs)),'max_h':max(map(len,hs)),'min_v':min(map(len,vs)),'max_v':max(map(len,vs))}

def build(kl,kr,model,r,x):
    hs,vs=model;KL=set(kl);KR=set(kr);bl=[z for i,z in enumerate(r) if i not in KL];br=[z for i,z in enumerate(r) if i not in KR];C={a*g.U+b for a in bl for b in br}
    for i,xi in enumerate(x):C.update(e*g.U+xi for e in hs[i]);C.update(xi*g.U+e for e in vs[i])
    return C

def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('baseline',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U));r0=g.load_r(args.r367);x=g.make_x(r0,digits);r=rs.load_rank3_state(r0,digits);supports,_=g.support_masks(r,digits);k9=tuple(rs.RANK3_K9);base={int(p,7) for p in json.loads(args.baseline.read_text())['points']};rows=[];best=None
    for omit in k9:
        k8=tuple(i for i in k9 if i!=omit)
        for orient in ('L8R9','L9R8'):
            kl,kr=(k8,k9) if orient=='L8R9' else (k9,k8);model,st=optimize(kl,kr,r,x,digits,supports);row={'omit':omit,'orientation':orient,**st};rows.append(row);print('CASE',json.dumps(row,sort_keys=True),flush=True)
            if best is None or st['score']>best[0]:best=(st['score'],omit,orient,kl,kr,model,st)
            if st['score']<TARGET:continue
            C=build(kl,kr,model,r,x)
            if len(C)!=st['score']:raise RuntimeError(f'candidate replay {len(C)} != {st["score"]}')
            status={'candidate':True,'method':'rank3-asymmetric-8x9-exact-maxsat','score':len(C),'omit_from_k9':omit,'orientation':orient,'k_left':list(kl),'k_right':list(kr),'solver':st,'tested':len(rows),'removed_vs_baseline':len(base-C),'added_vs_baseline':len(C-base),'rows':rows}
            args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':[g.dec10(z) for z in sorted(C)]},separators=(',',':'))+'\n');args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True);return
    status={'candidate':False,'method':'rank3-asymmetric-8x9-exact-maxsat','score':best[0],'best':{'omit':best[1],'orientation':best[2],**best[6]},'rows':rows};args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
