#!/usr/bin/env python3
"""Direct >=134754 feasibility for the historical rank3 K9 against K10."""
import argparse,json
from itertools import combinations
from pathlib import Path
from pysat.formula import IDPool
from pysat.solvers import Minicard
import generalized9 as g
import rank3_square_relax as rs

BASELINE=134753;SQUARE=358*357;NEED=134754-SQUARE

def solve(kl,kr,r,x,digits,supports):
    sl=tuple(g.safe_vertices(sum(1<<i for i in kl),supports));sr=tuple(g.safe_vertices(sum(1<<i for i in kr),supports));pool=IDPool();H=lambda i,e:pool.id(('H',i,e));V=lambda i,e:pool.id(('V',i,e));clauses=[]
    el=[(a,b) for a,b in combinations(range(len(sl)),2) if g.conflict(sl[a],sl[b],digits)];er=[(a,b) for a,b in combinations(range(len(sr)),2) if g.conflict(sr[a],sr[b],digits)]
    for i in range(g.R_SIZE):
        for a,b in el:clauses.append([-H(i,a),-H(i,b)])
        for a,b in er:clauses.append([-V(i,a),-V(i,b)])
    hitl=[[e for e,z in enumerate(sl) if g.conflict(z,xj,digits)] for xj in x];hitr=[[e for e,z in enumerate(sr) if g.conflict(z,xi,digits)] for xi in x];cross=0
    for i in range(g.R_SIZE):
        if not hitr[i]:continue
        for j in range(g.R_SIZE):
            if not hitl[j]:continue
            for e in hitl[j]:
                h=H(i,e)
                for f in hitr[i]:clauses.append([-h,-V(j,f)]);cross+=1
    vars_=[H(i,e) for i in range(g.R_SIZE) for e in range(len(sl))]+[V(i,e) for i in range(g.R_SIZE) for e in range(len(sr))]
    st={'safe_l':len(sl),'safe_r':len(sr),'vars':pool.top,'hard_clauses':len(clauses),'cross_clauses':cross,'candidate_ports':len(vars_),'need_ports':NEED}
    with Minicard(bootstrap_with=clauses) as s:
        s.add_atmost([-z for z in vars_],len(vars_)-NEED);sat=s.solve();model=s.get_model() if sat else None
    if not sat:return None,st
    pos={z for z in model if z>0};hs=[[sl[e] for e in range(len(sl)) if H(i,e) in pos] for i in range(g.R_SIZE)];vs=[[sr[e] for e in range(len(sr)) if V(i,e) in pos] for i in range(g.R_SIZE)];st['selected_ports']=sum(map(len,hs))+sum(map(len,vs));return (hs,vs),st

def build(kl,kr,m,r,x):
    hs,vs=m;KL=set(kl);KR=set(kr);bl=[z for i,z in enumerate(r) if i not in KL];br=[z for i,z in enumerate(r) if i not in KR];C={a*g.U+b for a in bl for b in br}
    for i,xi in enumerate(x):C.update(e*g.U+xi for e in hs[i]);C.update(xi*g.U+e for e in vs[i])
    return C

def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('baseline',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args();digits=tuple(g.dec5(v) for v in range(g.U));r0=g.load_r(args.r367);x=g.make_x(r0,digits);r=rs.load_rank3_state(r0,digits);supports,_=g.support_masks(r,digits);rset=set(r);owners=set()
    for v,sm in enumerate(supports):
        if v not in rset and sm.bit_count()==1:owners.add((sm&-sm).bit_length()-1)
    k10=tuple(sorted(owners));k9=tuple(rs.RANK3_K9);base={int(p,7) for p in json.loads(args.baseline.read_text())['points']};rows=[]
    if len(k10)!=10 or not set(k9)<set(k10):raise RuntimeError(f'owner drift {k10}')
    for orient in ('L9R10','L10R9'):
        kl,kr=(k9,k10) if orient=='L9R10' else (k10,k9);model,st=solve(kl,kr,r,x,digits,supports);row={'orientation':orient,'sat':model is not None,**st};rows.append(row);print('CASE',json.dumps(row,sort_keys=True),flush=True)
        if model is None:continue
        C=build(kl,kr,model,r,x);score=len(C)
        if score<134754:raise RuntimeError(f'cardinality model score {score}')
        status={'candidate':True,'method':'rank3-asymmetric-9x10-direct-feasibility','score':score,'orientation':orient,'k9':list(k9),'k10':list(k10),'solver':st,'removed_vs_baseline':len(base-C),'added_vs_baseline':len(C-base),'rows':rows};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':[g.dec10(z) for z in sorted(C)]},separators=(',',':'))+'\n');args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True);return
    status={'candidate':False,'method':'rank3-asymmetric-9x10-direct-feasibility','score':BASELINE,'k9':list(k9),'k10':list(k10),'rows':rows};args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
