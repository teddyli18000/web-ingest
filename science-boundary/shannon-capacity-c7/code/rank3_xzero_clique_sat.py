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
    xbc=[(supports[x]&bmask).bit_count() for x in xset]
    if [i for i,c in enumerate(xbc) if c==0] != [SPECIAL]: raise RuntimeError(f'zero-fiber drift: {[i for i,c in enumerate(xbc) if c==0]}')
    safe=tuple(v for v in range(g.U) if v not in bvals and (supports[v]&bmask)==0)
    if len(safe)!=18: raise RuntimeError(f'safe drift {len(safe)}')
    cand=[tuple(range(g.U)) if i==SPECIAL else safe for i in range(g.R_SIZE)]; csets=[set(a) for a in cand]

    pool=IDPool()
    def H(i,e): return pool.id(('H',i,e))
    def V(i,e): return pool.id(('V',i,e))
    allvars=[z for i in range(g.R_SIZE) for e in cand[i] for z in (H(i,e),V(i,e))]

    same_edges=[(a,b) for ai,a in enumerate(safe) for b in safe[ai+1:] if g.conflict(a,b,digits)]
    xhits=[[] for _ in range(g.U)]; xneigh=[]
    for i,x in enumerate(xset):
        n=tuple(rs.neighborhood(x,digits)); xneigh.append(set(n))
        for e in n: xhits[e].append(i)

    pair_same=0; cross=0; clique_constraints=0
    with Minicard() as s:
        # Ordinary 18-endpoint fibers: exact pair clauses.
        for i in range(g.R_SIZE):
            if i!=SPECIAL:
                for a,b in same_edges:
                    s.add_clause([-H(i,a),-H(i,b)]); s.add_clause([-V(i,a),-V(i,b)]); pair_same+=2

        # Special full endpoint fibers: conflict graph is exactly covered by
        # products of five oriented C7 edges, each a 32-vertex clique.
        for a in range(g.U):
            q=clique(a,digits)
            s.add_atmost([H(SPECIAL,e) for e in q],1)
            s.add_atmost([V(SPECIAL,e) for e in q],1)
            clique_constraints+=2

        # H/V cross conflicts.
        for i in range(g.R_SIZE):
            ni=xneigh[i]
            for e in cand[i]:
                he=H(i,e)
                for j in xhits[e]:
                    for f in ni.intersection(csets[j]):
                        s.add_clause([-he,-V(j,f)]); cross+=1

        # Direct feasibility: at least 6590 port vertices.
        s.add_atmost([-v for v in allvars],len(allvars)-NEED)
        setup={'state':rs.STATE_INDEX,'k9':list(rs.RANK3_K9),'special':SPECIAL,'safe_endpoints':len(safe),'candidate_port_variables':len(allvars),'ordinary_same_pair_clauses':pair_same,'special_clique_constraints':clique_constraints,'cross_clauses':cross,'variables':pool.top,'need_ports':NEED,'target':TARGET}
        print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
        sat=s.solve(); model=s.get_model() if sat else None

    if not sat:
        status={'candidate':False,'sat':False,'score':134753,'method':'rank3-xzero-clique-feasibility','setup':setup}
        args.status.parent.mkdir(parents=True,exist_ok=True); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('UNSAT',json.dumps(status,sort_keys=True),flush=True); return

    pos={v for v in model if v>0}; hs=[[] for _ in range(g.R_SIZE)]; vs=[[] for _ in range(g.R_SIZE)]; selected=0
    for i in range(g.R_SIZE):
        for e in cand[i]:
            if H(i,e) in pos: hs[i].append(e); selected+=1
            if V(i,e) in pos: vs[i].append(e); selected+=1
    cert=rs.build_candidate(r,xset,bidx,hs,vs,[]); score=len(cert)
    if score!=BASE_SQUARE+selected or score<TARGET: raise RuntimeError(f'bad model score {score} selected {selected}')
    baseline={int(p,7) for p in json.loads(args.baseline.read_text())['points']}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'points':[g.dec10(v) for v in sorted(cert)]},separators=(',',':'))+'\n')
    status={'candidate':True,'sat':True,'score':score,'selected_ports':selected,'method':'rank3-xzero-clique-feasibility','setup':setup,'removed_vs_baseline':len(baseline-cert),'added_vs_baseline':len(cert-baseline)}
    args.status.parent.mkdir(parents=True,exist_ok=True); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
