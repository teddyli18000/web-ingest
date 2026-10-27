#!/usr/bin/env python3
"""Exact MaxSAT over all rank-3 asymmetric 9x10 deletion cases."""
import argparse,json
from pathlib import Path
import generalized9 as g
import rank3_square_relax as rs
import asymmetric_rank3_maxsat as core

BASELINE=134753;TARGET=134754;SQUARE=358*357

def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('baseline',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U));r0=g.load_r(args.r367);x=g.make_x(r0,digits);r=rs.load_rank3_state(r0,digits);supports,_=g.support_masks(r,digits);rset=set(r)
    owners=set()
    for v,sm in enumerate(supports):
        if v not in rset and sm.bit_count()==1:owners.add((sm&-sm).bit_length()-1)
    k10=tuple(sorted(owners))
    if len(k10)!=10:raise RuntimeError(f'private owner drift {k10}')
    if not set(rs.RANK3_K9)<set(k10):raise RuntimeError(f'K9 not subset K10: {k10}')
    # Reuse the exact asymmetric MaxSAT core with the 9x10 square constant.
    core.SQUARE=SQUARE
    base={int(p,7) for p in json.loads(args.baseline.read_text())['points']};rows=[];best=None
    # Try the historically best rank-3 K9 first, then all other 9-of-10 choices.
    k9s=[tuple(rs.RANK3_K9)]+[tuple(i for i in k10 if i!=omit) for omit in k10 if tuple(i for i in k10 if i!=omit)!=tuple(rs.RANK3_K9)]
    for k9 in k9s:
        omitted=next(i for i in k10 if i not in set(k9))
        for orient in ('L9R10','L10R9'):
            kl,kr=(k9,k10) if orient=='L9R10' else (k10,k9)
            model,st=core.optimize(kl,kr,r,x,digits,supports);row={'omitted_from_k10':omitted,'orientation':orient,**st};rows.append(row);print('CASE',json.dumps(row,sort_keys=True),flush=True)
            if best is None or st['score']>best[0]:best=(st['score'],omitted,orient,kl,kr,model,st)
            if st['score']<TARGET:continue
            C=core.build(kl,kr,model,r,x)
            if len(C)!=st['score']:raise RuntimeError(f'candidate replay {len(C)} != {st["score"]}')
            status={'candidate':True,'method':'rank3-asymmetric-9x10-exact-maxsat','score':len(C),'omitted_from_k10':omitted,'orientation':orient,'k10':list(k10),'k_left':list(kl),'k_right':list(kr),'solver':st,'tested':len(rows),'removed_vs_baseline':len(base-C),'added_vs_baseline':len(C-base),'rows':rows}
            args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':[g.dec10(z) for z in sorted(C)]},separators=(',',':'))+'\n');args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True);return
    status={'candidate':False,'method':'rank3-asymmetric-9x10-exact-maxsat','score':best[0],'k10':list(k10),'best':{'omitted':best[1],'orientation':best[2],**best[6]},'rows':rows};args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
