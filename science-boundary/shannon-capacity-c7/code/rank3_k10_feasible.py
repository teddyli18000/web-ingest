#!/usr/bin/env python3
"""Direct >=134754 feasibility for the full ten-private-centre rank3 deletion set."""
import argparse,json
from pathlib import Path
import generalized9 as g
import rank3_square_relax as rs
import asymmetric_rank3_910_feasible as core

BASELINE=134753;SQUARE=357*357;NEED=134754-SQUARE

def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('baseline',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U));r0=g.load_r(args.r367);x=g.make_x(r0,digits);r=rs.load_rank3_state(r0,digits);supports,_=g.support_masks(r,digits);rset=set(r);owners=set()
    for v,sm in enumerate(supports):
        if v not in rset and sm.bit_count()==1:owners.add((sm&-sm).bit_length()-1)
    k10=tuple(sorted(owners))
    if len(k10)!=10:raise RuntimeError(f'private owner drift {k10}')
    core.NEED=NEED
    model,st=core.solve(k10,k10,r,x,digits,supports)
    status={'candidate':False,'method':'rank3-k10xk10-direct-feasibility','score':BASELINE,'k10':list(k10),'square':SQUARE,'need_ports':NEED,'sat':model is not None,'solver':st}
    print('CASE',json.dumps(status,sort_keys=True),flush=True)
    if model is not None:
        C=core.build(k10,k10,model,r,x);score=len(C)
        if score<134754:raise RuntimeError(f'cardinality replay score {score}')
        base={int(p,7) for p in json.loads(args.baseline.read_text())['points']}
        status.update({'candidate':True,'score':score,'removed_vs_baseline':len(base-C),'added_vs_baseline':len(C-base)})
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':[g.dec10(z) for z in sorted(C)]},separators=(',',':'))+'\n')
    args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(('FOUND' if status['candidate'] else 'NONE'),json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
