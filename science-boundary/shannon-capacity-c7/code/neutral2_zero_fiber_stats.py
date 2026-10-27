#!/usr/bin/env python3
import argparse,json
from itertools import combinations
from pathlib import Path

import generalized9 as g
import neutral2_sweep as ns


def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U));r0=g.load_r(args.r367);xset=g.make_x(r0,digits);s0,_=g.support_masks(r0,digits);states=ns.enumerate_states(r0,digits,s0)
    r,rem,add=states[17]
    if tuple(rem)!=(267,294) or tuple(add)!=(15083,16388):raise RuntimeError('state18 drift')
    supports,_=g.support_masks(r,digits);rset=set(r);owners={}
    for v,sm in enumerate(supports):
        if v in rset or sm.bit_count()!=1:continue
        i=(sm&-sm).bit_length()-1;owners.setdefault(i,[]).append(v)
    rows=[]
    for k9 in combinations(sorted(owners),9):
        bidx=[i for i in range(g.R_SIZE) if i not in set(k9)];bmask=sum(1<<i for i in bidx);bvals={r[i] for i in bidx}
        zeros=[i for i,x in enumerate(xset) if (supports[x]&bmask)==0]
        safe=[v for v in range(g.U) if v not in bvals and (supports[v]&bmask)==0]
        rows.append({'k9':list(k9),'zero_x_indices':zeros,'zero_x_count':len(zeros),'safe_nonB_endpoints':len(safe)})
    rows.sort(key=lambda z:(-z['safe_nonB_endpoints'],z['k9']))
    for rank,row in enumerate(rows):row['rank']=rank
    out={'state':18,'remove_indices':list(rem),'add':list(add),'private_centers':len(owners),'ranks':rows,'max_zero_x_count':max(r['zero_x_count'] for r in rows),'ranks_with_zero_x':[r['rank'] for r in rows if r['zero_x_count']]}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True),flush=True)
if __name__=='__main__':main()
