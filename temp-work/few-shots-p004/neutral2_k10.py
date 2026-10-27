#!/usr/bin/env python3
import argparse,json
from itertools import combinations
from pathlib import Path
import generalized9 as g

TARGET=134789
MODS={267:15083,294:16388}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('r367',type=Path); ap.add_argument('baseline',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U)); r0=g.load_r(args.r367); xset=g.make_x(r0,digits); r=list(r0)
    for i,v in MODS.items(): r[i]=v
    if len(set(r))!=g.R_SIZE: raise RuntimeError('duplicate neutral2 state')
    for i,j in combinations(range(g.R_SIZE),2):
        if g.conflict(r[i],r[j],digits): raise RuntimeError(f'neutral2 state conflict {i},{j}')
    supports,_=g.support_masks(r,digits); rset=set(r); owners={}
    for v,sm in enumerate(supports):
        if v in rset or sm.bit_count()!=1: continue
        i=(sm&-sm).bit_length()-1; owners.setdefault(i,[]).append(v)
    if len(owners)<10:
        status={'candidate':False,'reason':'fewer than 10 private centers','private_center_count':len(owners)}; args.status.write_text(json.dumps(status,indent=2)+'\n'); print(json.dumps(status)); return
    # Best neutral2 state has exactly ten private centers; use all ten.
    k10=tuple(sorted(owners))
    if len(k10)!=10: raise RuntimeError(f'expected exactly 10 private centers, got {len(k10)}')
    print('k10',json.dumps({'indices':k10,'centers':[r[i] for i in k10],'alternatives':owners},sort_keys=True),flush=True)
    model,stats=g.solve_structure(k10,10,r,xset,digits,supports,want_model=True)
    if model is None:
        status={'candidate':False,'score':134753,'method':'neutral2-k10-generalized-sat','neutral2_modifications':MODS,'private_center_count':len(owners),'selected_indices':list(k10),'selected_centers':[r[i] for i in k10],'sat_stats':stats}
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(status,sort_keys=True),flush=True); return
    cand=g.build_candidate(k10,model,r,xset,digits)
    if len(cand)!=TARGET: raise RuntimeError(f'wrong score {len(cand)} != {TARGET}')
    baseline={int(p,7) for p in json.loads(args.baseline.read_text())['points']}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'points':[g.dec10(v) for v in sorted(cand)]},separators=(',',':'))+'\n')
    status={'candidate':True,'score':len(cand),'method':'neutral2-k10-generalized-sat','neutral2_modifications':MODS,'private_center_count':len(owners),'selected_indices':list(k10),'selected_centers':[r[i] for i in k10],'sat_stats':stats,'removed_vs_baseline':len(baseline-cand),'added_vs_baseline':len(cand-baseline)}
    args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__': main()
