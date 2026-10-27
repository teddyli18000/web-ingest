#!/usr/bin/env python3
"""Test all 8x9 asymmetric deletions inside the rank-3 neutral2 parent."""
import argparse,json
from pathlib import Path
import generalized9 as g
import rank3_square_relax as rs
import asymmetric89 as asym

BASELINE=134753

def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('baseline',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U));r0=g.load_r(args.r367);x=g.make_x(r0,digits);r=rs.load_rank3_state(r0,digits);supports,_=g.support_masks(r,digits)
    k9=tuple(rs.RANK3_K9);base={int(p,7) for p in json.loads(args.baseline.read_text())['points']};rows=[]
    for omit in k9:
        k8=tuple(i for i in k9 if i!=omit)
        for orient in ('L8R9','L9R8'):
            kl,kr=(k8,k9) if orient=='L8R9' else (k9,k8)
            model,st=asym.solve(kl,kr,r,x,digits,supports);row={'omit':omit,'orientation':orient,**st,'sat':model is not None};rows.append(row);print('CASE',json.dumps(row,sort_keys=True),flush=True)
            if model is None:continue
            C=asym.build(kl,kr,model,r,x,digits)
            status={'candidate':True,'score':len(C),'method':'rank3-asymmetric-8x9-exact-sat','omit_from_k9':omit,'orientation':orient,'k_left':list(kl),'k_right':list(kr),'solver':st,'tested':len(rows),'removed_vs_baseline':len(base-C),'added_vs_baseline':len(C-base)}
            args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':[g.dec10(z) for z in sorted(C)]},separators=(',',':'))+'\n');args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True);return
    status={'candidate':False,'score':BASELINE,'method':'rank3-asymmetric-8x9-exact-sat','tested':len(rows),'rows':rows};args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
