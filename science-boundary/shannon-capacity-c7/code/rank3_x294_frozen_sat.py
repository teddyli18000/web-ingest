#!/usr/bin/env python3
import argparse,json
from itertools import product
from pathlib import Path
from pysat.solvers import Minicard
import generalized9 as g
import neutral2_maxsat as nm
import rank3_square_relax as rs

SPECIAL=294; TARGET=134754; BASE_SQUARE=358**2; NEED=TARGET-BASE_SQUARE

def clique(a,digits):
    x=digits[a]
    return [g.enc5(tuple((x[d]+b[d])%7 for d in range(5))) for b in product((0,1),repeat=5)]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('baseline',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U));r0=g.load_r(args.r367);xset=g.make_x(r0,digits);r=rs.load_rank3_state(r0,digits);supports,_=g.support_masks(r,digits)
    model,bst=nm.solve_maxsat(rs.RANK3_K9,r,xset,digits,supports)
    if model is None or bst['score']!=134753:raise RuntimeError(f'base drift {bst}')
    _,hs,vs=model;x0=xset[SPECIAL]
    old=[]
    for i,a in enumerate(hs):
        if i!=SPECIAL:old.extend(('H',i,e) for e in a)
    for i,a in enumerate(vs):
        if i!=SPECIAL:old.extend(('V',i,e) for e in a)
    old_h294=len(hs[SPECIAL]);old_v294=len(vs[SPECIAL])
    # Old non-special ports are mutually compatible. Make them selectable so special endpoints may evict them.
    # Index conflicts from ambient endpoint to old ports of the opposite orientation.
    oldH=[[] for _ in range(g.R_SIZE)];oldV=[[] for _ in range(g.R_SIZE)]
    for oi,(o,i,e) in enumerate(old):
        (oldH if o=='H' else oldV)[i].append((e,oi))
    xhits=[[] for _ in range(g.U)]
    for j,x in enumerate(xset):
        for e in rs.neighborhood(x,digits):xhits[e].append(j)
    h_old_conf=[set() for _ in range(g.U)];v_old_conf=[set() for _ in range(g.U)]
    # H294(e) conflicts V(j,f) iff e~X_j and X294~f.
    # V294(e) conflicts H(j,f) under the same two-factor condition.
    vbad=[[] for _ in range(g.R_SIZE)];hbad=[[] for _ in range(g.R_SIZE)]
    for j in range(g.R_SIZE):
        vbad[j]=[oi for f,oi in oldV[j] if g.conflict(x0,f,digits)]
        hbad[j]=[oi for f,oi in oldH[j] if g.conflict(x0,f,digits)]
    for e in range(g.U):
        for j in xhits[e]:
            h_old_conf[e].update(vbad[j]);v_old_conf[e].update(hbad[j])
    # IDs: special H 1..U, special V U+1..2U, old keep 2U+1..
    H=lambda e:e+1;V=lambda e:g.U+e+1;K=lambda i:2*g.U+i+1
    allvars=[H(e) for e in range(g.U)]+[V(e) for e in range(g.U)]+[K(i) for i in range(len(old))]
    hard_old=sum(len(z) for z in h_old_conf)+sum(len(z) for z in v_old_conf)
    near=list(rs.neighborhood(x0,digits));cross_special=len(near)*len(near)
    with Minicard() as s:
        for a in range(g.U):
            q=clique(a,digits);s.add_atmost([H(e) for e in q],1);s.add_atmost([V(e) for e in q],1)
        for e in near:
            for f in near:s.add_clause([-H(e),-V(f)])
        for e,cs in enumerate(h_old_conf):
            for oi in cs:s.add_clause([-H(e),-K(oi)])
        for e,cs in enumerate(v_old_conf):
            for oi in cs:s.add_clause([-V(e),-K(oi)])
        s.add_atmost([-z for z in allvars],len(allvars)-NEED)
        setup={'base_selected':bst['selected'],'old_h294':old_h294,'old_v294':old_v294,'frozen_non_special_ports':len(old),'candidate_special_ports':2*g.U,'special_clique_constraints':2*g.U,'special_cross_clauses':cross_special,'special_old_conflict_clauses':hard_old,'variables':max(allvars),'need_ports':NEED,'target':TARGET};print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
        sat=s.solve();m=s.get_model() if sat else None
    if not sat:
        st={'candidate':False,'sat':False,'score':134753,'method':'rank3-x294-frozen-full-fiber-sat','setup':setup};args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('UNSAT',json.dumps(st,sort_keys=True),flush=True);return
    pos={z for z in m if z>0};nh=[e for e in range(g.U) if H(e) in pos];nv=[e for e in range(g.U) if V(e) in pos];keep=[i for i in range(len(old)) if K(i) in pos]
    newhs=[[] for _ in range(g.R_SIZE)];newvs=[[] for _ in range(g.R_SIZE)];newhs[SPECIAL]=nh;newvs[SPECIAL]=nv
    for oi in keep:
        o,i,e=old[oi];(newhs if o=='H' else newvs)[i].append(e)
    kset=set(rs.RANK3_K9);bidx=[i for i in range(g.R_SIZE) if i not in kset];cert=rs.build_candidate(r,xset,bidx,newhs,newvs,[]);score=len(cert);sel=len(nh)+len(nv)+len(keep)
    if score!=BASE_SQUARE+sel or score<TARGET:raise RuntimeError(f'bad score {score} sel={sel}')
    base={int(p,7) for p in json.loads(args.baseline.read_text())['points']};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':[g.dec10(v) for v in sorted(cert)]},separators=(',',':'))+'\n')
    st={'candidate':True,'sat':True,'score':score,'selected_ports':sel,'selected_h294':len(nh),'selected_v294':len(nv),'kept_non_special':len(keep),'method':'rank3-x294-frozen-full-fiber-sat','setup':setup,'removed_vs_baseline':len(base-cert),'added_vs_baseline':len(cert-base)};args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(st,sort_keys=True),flush=True)
if __name__=='__main__':main()
