#!/usr/bin/env python3
import argparse,json
from pathlib import Path

import generalized9 as g
import neutral2_maxsat as nm
import rank3_square_relax as rs

BASE_SQUARE=358**2
SPECIAL=294


def add_shift(v,t,digits):
    a=digits[v];b=digits[t]
    return g.enc5(tuple((a[i]+b[i])%7 for i in range(5)))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('baseline',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--family',choices=('r0','rank3','x'),required=True);args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U));r0=g.load_r(args.r367);xset=g.make_x(r0,digits);r=rs.load_rank3_state(r0,digits);supports,_=g.support_masks(r,digits)
    model,stats=nm.solve_maxsat(rs.RANK3_K9,r,xset,digits,supports)
    if model is None or stats['score']!=134753:raise RuntimeError(f'base tie drift: {stats}')
    _,hs,vs=model
    old_h=len(hs[SPECIAL]);x0=xset[SPECIAL]
    vweights=[]
    for j in range(g.R_SIZE):vweights.append(sum(1 for f in vs[j] if g.conflict(x0,f,digits)))
    # For every ambient 5D endpoint v, encode which X_j it conflicts with as one Python integer bitset.
    hitmask=[0]*g.U
    for j,x in enumerate(xset):
        bit=1<<j
        for v in rs.neighborhood(x,digits):hitmask[v]|=bit
    if args.family=='r0':base=tuple(r0)
    elif args.family=='rank3':base=tuple(r)
    else:base=tuple(xset)
    if len(base)!=367 or len(set(base))!=367:raise RuntimeError('bad 367 family')
    # Precompute digits of source points; each translation is exact in Z_7^5.
    bd=[digits[v] for v in base]
    best=None
    for t in range(g.U):
        td=digits[t];mask=0
        for a in bd:
            v=g.enc5(tuple((a[q]+td[q])%7 for q in range(5)))
            mask |= hitmask[v]
        drops=0;m=mask;j=0
        while m:
            b=m & -m;j=b.bit_length()-1;drops+=vweights[j];m^=b
        gain=367-old_h-drops
        if best is None or gain>best[0]:best=(gain,t,drops,mask.bit_count())
    gain,t,drops,hit_x=best
    td=digits[t];fixed=[g.enc5(tuple((a[q]+td[q])%7 for q in range(5))) for a in bd]
    # Replay 5D independence.
    for i in range(len(fixed)):
        for j in range(i+1,len(fixed)):
            if g.conflict(fixed[i],fixed[j],digits):raise RuntimeError('translated family not independent')
    new_h=[list(a) for a in hs];new_h[SPECIAL]=fixed;new_v=[];removed_v=0
    fmask=0
    for e in fixed:fmask|=hitmask[e]
    for j,arr in enumerate(vs):
        if not ((fmask>>j)&1):new_v.append(list(arr));continue
        keep=[]
        for f in arr:
            if g.conflict(x0,f,digits):removed_v+=1
            else:keep.append(f)
        new_v.append(keep)
    if removed_v!=drops:raise RuntimeError(f'drop mismatch {removed_v}!={drops}')
    kset=set(rs.RANK3_K9);bidx=[i for i in range(g.R_SIZE) if i not in kset]
    cert=rs.build_candidate(r,xset,bidx,new_h,new_v,[]);score=len(cert);expected=134753+gain
    if score!=expected:raise RuntimeError(f'score mismatch {score}!={expected}')
    baseline={int(p,7) for p in json.loads(args.baseline.read_text())['points']}
    status={'candidate':score>134753,'score':score,'method':'rank3-x294-translated-367-augmentation','family':args.family,'translation_id':t,'translation_digits':list(td),'old_h294_ports':old_h,'dropped_old_v_ports':drops,'hit_x_indices':hit_x,'net_gain':gain,'base_maxsat':stats,'removed_vs_baseline':len(baseline-cert),'added_vs_baseline':len(cert-baseline)}
    args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(('FOUND' if score>134753 else 'NONE'),json.dumps(status,sort_keys=True),flush=True)
    if score>134753:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':[g.dec10(v) for v in sorted(cert)]},separators=(',',':'))+'\n')
if __name__=='__main__':main()
