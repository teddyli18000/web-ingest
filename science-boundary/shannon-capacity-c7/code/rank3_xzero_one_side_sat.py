#!/usr/bin/env python3
import argparse, json
from itertools import product
from pathlib import Path

from pysat.formula import IDPool
from pysat.solvers import Minicard

import generalized9 as g
import rank3_square_relax as rs

SPECIAL=294
BASE_SQUARE=358**2
TARGET=134754
NEED=TARGET-BASE_SQUARE


def clique(anchor,digits):
    a=digits[anchor]
    return [g.enc5(tuple((a[d]+bit[d])%7 for d in range(5))) for bit in product((0,1),repeat=5)]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('r367',type=Path); ap.add_argument('baseline',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U)); r0=g.load_r(args.r367); xset=g.make_x(r0,digits); r=rs.load_rank3_state(r0,digits); supports,_=g.support_masks(r,digits)
    kset=set(rs.RANK3_K9); bidx=[i for i in range(g.R_SIZE) if i not in kset]; bmask=sum(1<<i for i in bidx); bvals={r[i] for i in bidx}
    zero=[i for i,x in enumerate(xset) if (supports[x]&bmask)==0]
    if zero != [SPECIAL]: raise RuntimeError(f'zero fiber drift: {zero}')
    safe=tuple(v for v in range(g.U) if v not in bvals and (supports[v]&bmask)==0)
    if len(safe)!=18: raise RuntimeError(f'safe drift {len(safe)}')
    hcand=[tuple(range(g.U)) if i==SPECIAL else safe for i in range(g.R_SIZE)]
    vcand=[safe for _ in range(g.R_SIZE)]
    hset=[set(a) for a in hcand]; vset=[set(a) for a in vcand]
    pool=IDPool(); H=lambda i,e:pool.id(('H',i,e)); V=lambda i,e:pool.id(('V',i,e))
    allvars=[H(i,e) for i in range(g.R_SIZE) for e in hcand[i]]+[V(i,e) for i in range(g.R_SIZE) for e in vcand[i]]
    same=[(a,b) for ai,a in enumerate(safe) for b in safe[ai+1:] if g.conflict(a,b,digits)]
    xhits=[[] for _ in range(g.U)]; xneigh=[]
    for i,x in enumerate(xset):
        n=tuple(rs.neighborhood(x,digits)); xneigh.append(set(n))
        for e in n:xhits[e].append(i)
    ordinary=0; cross=0; ccons=0
    with Minicard() as s:
        for i in range(g.R_SIZE):
            if i!=SPECIAL:
                for a,b in same:s.add_clause([-H(i,a),-H(i,b)]);ordinary+=1
            for a,b in same:s.add_clause([-V(i,a),-V(i,b)]);ordinary+=1
        for a in range(g.U):
            s.add_atmost([H(SPECIAL,e) for e in clique(a,digits)],1);ccons+=1
        for i in range(g.R_SIZE):
            ni=xneigh[i]
            for e in hcand[i]:
                he=H(i,e)
                for j in xhits[e]:
                    for f in ni.intersection(vset[j]):
                        s.add_clause([-he,-V(j,f)]);cross+=1
        s.add_atmost([-v for v in allvars],len(allvars)-NEED)
        setup={'state':rs.STATE_INDEX,'special':SPECIAL,'safe_endpoints':len(safe),'candidate_port_variables':len(allvars),'ordinary_same_pair_clauses':ordinary,'special_clique_constraints':ccons,'cross_clauses':cross,'variables':pool.top,'need_ports':NEED,'target':TARGET}
        print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
        sat=s.solve();model=s.get_model() if sat else None
    if not sat:
        status={'candidate':False,'sat':False,'score':134753,'method':'rank3-xzero-one-side-clique-feasibility','setup':setup};args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('UNSAT',json.dumps(status,sort_keys=True),flush=True);return
    pos={v for v in model if v>0};hs=[[] for _ in range(g.R_SIZE)];vs=[[] for _ in range(g.R_SIZE)];sel=0
    for i in range(g.R_SIZE):
        for e in hcand[i]:
            if H(i,e) in pos:hs[i].append(e);sel+=1
        for e in vcand[i]:
            if V(i,e) in pos:vs[i].append(e);sel+=1
    cert=rs.build_candidate(r,xset,bidx,hs,vs,[]);score=len(cert)
    if score!=BASE_SQUARE+sel or score<TARGET:raise RuntimeError(f'bad score {score} sel={sel}')
    baseline={int(p,7) for p in json.loads(args.baseline.read_text())['points']};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':[g.dec10(v) for v in sorted(cert)]},separators=(',',':'))+'\n')
    status={'candidate':True,'sat':True,'score':score,'selected_ports':sel,'method':'rank3-xzero-one-side-clique-feasibility','setup':setup,'removed_vs_baseline':len(baseline-cert),'added_vs_baseline':len(cert-baseline)};args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
