#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import generalized9 as g
import neutral2_maxsat as nm
import rank3_square_relax as rs

SPECIAL=294

def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('baseline',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U));r0=g.load_r(args.r367);xset=g.make_x(r0,digits);r=rs.load_rank3_state(r0,digits);supports,_=g.support_masks(r,digits)
    model,stats=nm.solve_maxsat(rs.RANK3_K9,r,xset,digits,supports)
    if model is None or stats['score']!=134753:raise RuntimeError(f'base drift {stats}')
    _,hs,vs=model;x0=xset[SPECIAL]
    badH=set();badV=set()
    # New H294(e) can only conflict old V(j,f) where X294~f; block N(X_j) for every such j.
    for j,arr in enumerate(vs):
        if any(g.conflict(x0,f,digits) for f in arr):badH.update(rs.neighborhood(xset[j],digits))
    for j,arr in enumerate(hs):
        if any(g.conflict(x0,f,digits) for f in arr):badV.update(rs.neighborhood(xset[j],digits))
    oldH=set(hs[SPECIAL]);oldV=set(vs[SPECIAL]);cand=[]
    for e in range(g.U):
        if e not in oldH and e not in badH and all(not g.conflict(e,f,digits) for f in oldH):cand.append(('H',e))
        if e not in oldV and e not in badV and all(not g.conflict(e,f,digits) for f in oldV):cand.append(('V',e))
    setup={'base_selected':stats['selected'],'old_h294':len(oldH),'old_v294':len(oldV),'blocked_h_endpoints':len(badH),'blocked_v_endpoints':len(badV),'direct_add_candidates':len(cand),'first_candidates':[list(x) for x in cand[:20]]}
    if not cand:
        st={'candidate':False,'score':134753,'method':'rank3-x294-direct-add','setup':setup};args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(st,sort_keys=True),flush=True);return
    o,e=cand[0];nh=[list(a) for a in hs];nv=[list(a) for a in vs];(nh if o=='H' else nv)[SPECIAL].append(e)
    bidx=[i for i in range(g.R_SIZE) if i not in set(rs.RANK3_K9)];cert=rs.build_candidate(r,xset,bidx,nh,nv,[]);score=len(cert)
    if score!=134754:raise RuntimeError(f'direct candidate score {score}')
    base={int(p,7) for p in json.loads(args.baseline.read_text())['points']};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':[g.dec10(v) for v in sorted(cert)]},separators=(',',':'))+'\n')
    st={'candidate':True,'score':score,'method':'rank3-x294-direct-add','orientation':o,'endpoint':e,'endpoint_word':''.join(map(str,digits[e])),'setup':setup,'removed_vs_baseline':len(base-cert),'added_vs_baseline':len(cert-base)};args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(st,sort_keys=True),flush=True)
if __name__=='__main__':main()
